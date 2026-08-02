@app.route("/api/activate", methods=["POST"])
def activate():
    data = request.get_json()
    key = data.get("key", "").strip()
    hwid = data.get("hwid", "").strip()
    if not key or not hwid:
        return jsonify({"success": False, "reason": "Missing fields"}), 400
    conn = get_db()
    row = conn.execute("SELECT * FROM licenses WHERE key = ?", (key,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"success": False, "reason": "Geçersiz key"})

    # SINGLE KEY özel akış
    if row["plan"] == "single":
        if row["hwid"] is not None and row["hwid"] != hwid:
            conn.close()
            return jsonify({"success": False, "reason": "Key başka cihazda kullanılıyor"})
        if row["hwid"] is None:
            conn.execute("UPDATE licenses SET hwid = ?, activated_at = ? WHERE key = ?",
                         (hwid, datetime.utcnow().isoformat(), key))
            conn.commit()
        used = bool(row["is_used"])
        conn.close()
        return jsonify({"success": True, "plan": "single", "remaining": "Tek Kullanım", "used": used})

    if not row["is_active"]:
        conn.close()
        return jsonify({"success": False, "reason": "Key devre dışı"})

    if row["hwid"] is not None:
        if row["hwid"] == hwid:
            if row["expires_at"]:
                expires = datetime.fromisoformat(row["expires_at"])
                diff = expires - datetime.utcnow()
                remaining_str = f"{diff.days} gün {diff.seconds // 3600} saat"
            else:
                remaining_str = "Sınırsız"
            conn.close()
            return jsonify({"success": True, "plan": row["plan"], "expires_at": row["expires_at"], "remaining": remaining_str})
        else:
            conn.close()
            return jsonify({"success": False, "reason": "Key başka cihazda kullanılıyor"})

    now = datetime.utcnow()
    if row["plan"] == "weekly":
        expires_at = (now + timedelta(days=7)).isoformat()
    elif row["plan"] == "monthly":
        expires_at = (now + timedelta(days=30)).isoformat()
    else:
        expires_at = None

    conn.execute(
        "UPDATE licenses SET hwid = ?, activated_at = ?, expires_at = ? WHERE key = ?",
        (hwid, now.isoformat(), expires_at, key)
    )
    conn.commit()
    conn.close()

    if expires_at:
        expires = datetime.fromisoformat(expires_at)
        diff = expires - datetime.utcnow()
        remaining_str = f"{diff.days} gün {diff.seconds // 3600} saat"
    else:
        remaining_str = "Sınırsız"

    return jsonify({"success": True, "plan": row["plan"], "expires_at": expires_at, "remaining": remaining_str})
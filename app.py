from flask import Flask, request, jsonify
import sqlite3
import secrets
import string
from datetime import datetime, timedelta

app = Flask(__name__)
DB_PATH = "licenses.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            hwid TEXT DEFAULT NULL,
            plan TEXT NOT NULL DEFAULT 'lifetime',
            activated_at TEXT DEFAULT NULL,
            expires_at TEXT DEFAULT NULL,
            created_at TEXT NOT NULL,
            is_active INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()

def generate_key(prefix="MYAPP"):
    chars = string.ascii_uppercase + string.digits
    segments = [''.join(secrets.choice(chars) for _ in range(5)) for _ in range(4)]
    return f"{prefix}-" + "-".join(segments)

@app.route("/api/generate", methods=["POST"])
def generate():
    auth = request.headers.get("X-Admin-Token")
    if auth != "myapp-admin-2024":
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json() or {}
    plan = data.get("plan", "lifetime")
    
    if plan not in ["weekly", "monthly", "lifetime"]:
        return jsonify({"error": "Invalid plan"}), 400
    
    key = generate_key()
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO licenses (key, plan, created_at) VALUES (?, ?, ?)",
            (key, plan, datetime.utcnow().isoformat())
        )
        conn.commit()
        return jsonify({"key": key, "plan": plan})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Retry"}), 500
    finally:
        conn.close()

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
    if not row["is_active"]:
        conn.close()
        return jsonify({"success": False, "reason": "Key devre dışı"})
    
    if row["hwid"] is not None:
        if row["hwid"] == hwid:
            conn.close()
            return jsonify({
                "success": True,
                "plan": row["plan"],
                "expires_at": row["expires_at"]
            })
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
    return jsonify({
        "success": True,
        "plan": row["plan"],
        "expires_at": expires_at
    })

@app.route("/api/verify", methods=["POST"])
def verify():
    data = request.get_json()
    key = data.get("key", "").strip()
    hwid = data.get("hwid", "").strip()
    if not key or not hwid:
        return jsonify({"valid": False}), 400
    
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM licenses WHERE key = ? AND hwid = ? AND is_active = 1",
        (key, hwid)
    ).fetchone()
    conn.close()
    
    if not row:
        return jsonify({"valid": False})
    
    if row["expires_at"]:
        expires = datetime.fromisoformat(row["expires_at"])
        if datetime.utcnow() > expires:
            return jsonify({"valid": False, "reason": "Süre doldu"})
        remaining = expires - datetime.utcnow()
        days = remaining.days
        hours = remaining.seconds // 3600
        return jsonify({"valid": True, "plan": row["plan"], "expires_at": row["expires_at"], "remaining": f"{days} gün {hours} saat"})
    
    return jsonify({"valid": True, "plan": "lifetime", "expires_at": None, "remaining": "Sınırsız"})

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
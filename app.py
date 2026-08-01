from flask import Flask, request, jsonify
import sqlite3
import secrets
import string
from datetime import datetime

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
            activated_at TEXT DEFAULT NULL,
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
    key = generate_key()
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO licenses (key, created_at) VALUES (?, ?)",
            (key, datetime.utcnow().isoformat())
        )
        conn.commit()
        return jsonify({"key": key})
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
        return jsonify({"success": False, "reason": "Invalid key"})
    if not row["is_active"]:
        conn.close()
        return jsonify({"success": False, "reason": "Key disabled"})
    if row["hwid"] is not None:
        if row["hwid"] == hwid:
            conn.close()
            return jsonify({"success": True, "reason": "Already activated"})
        else:
            conn.close()
            return jsonify({"success": False, "reason": "Key used on another machine"})
    conn.execute(
        "UPDATE licenses SET hwid = ?, activated_at = ? WHERE key = ?",
        (hwid, datetime.utcnow().isoformat(), key)
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True, "reason": "Activated"})

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
    return jsonify({"valid": row is not None})

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
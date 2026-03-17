"""
Sample vulnerable application for Agent Skills OOP demo.
Contains deliberate security vulnerabilities and performance issues.
DO NOT use in production — this is educational material.
"""
import sqlite3
import hashlib
import pickle
import os
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# ISSUE: Hardcoded credentials (CWE-798)
DB_PASSWORD = "admin123"
SECRET_KEY = "supersecretkey-never-change"
API_TOKEN = "ak_live_1234567890abcdef"


def get_db():
    """Get database connection."""
    conn = sqlite3.connect("app.db")
    return conn


# VULNERABILITY: SQL Injection (CWE-89)
@app.route("/api/users")
def get_user():
    username = request.args.get("username", "")
    conn = get_db()
    # Direct string formatting in SQL query
    query = f"SELECT * FROM users WHERE username = '{username}'"
    result = conn.execute(query).fetchall()
    conn.close()
    return jsonify({"users": result})


# VULNERABILITY: Cross-Site Scripting / XSS (CWE-79)
@app.route("/profile")
def profile():
    name = request.args.get("name", "Guest")
    # User input rendered directly in HTML template
    template = f"<h1>Welcome, {name}!</h1><p>Your profile page</p>"
    return render_template_string(template)


# VULNERABILITY: Insecure deserialization (CWE-502)
@app.route("/api/import", methods=["POST"])
def import_data():
    raw = request.get_data()
    # Deserializing untrusted data with pickle
    data = pickle.loads(raw)
    return jsonify({"imported": len(data)})


# VULNERABILITY: Weak hashing (CWE-328)
def hash_password(password):
    """Hash a password for storage."""
    return hashlib.md5(password.encode()).hexdigest()


# VULNERABILITY: Path traversal (CWE-22)
@app.route("/api/files")
def get_file():
    filename = request.args.get("file", "")
    # No sanitization of file path
    filepath = os.path.join("/var/data", filename)
    with open(filepath, "r") as f:
        return f.read()


# PERFORMANCE: N+1 query pattern
def get_orders_with_items():
    conn = get_db()
    orders = conn.execute("SELECT * FROM orders").fetchall()
    result = []
    for order in orders:
        # Individual query per order instead of JOIN
        items = conn.execute(
            f"SELECT * FROM order_items WHERE order_id = '{order[0]}'"
        ).fetchall()
        result.append({"order": order, "items": items})
    conn.close()
    return result


# PERFORMANCE: Unbounded query with no pagination
@app.route("/api/logs")
def get_logs():
    conn = get_db()
    # Fetches ALL logs — no LIMIT, no pagination
    logs = conn.execute("SELECT * FROM logs ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify({"logs": logs})


# PERFORMANCE: Synchronous blocking in request handler
@app.route("/api/report")
def generate_report():
    import time
    conn = get_db()
    data = conn.execute("SELECT * FROM transactions").fetchall()
    # Simulates expensive computation blocking the request
    time.sleep(5)
    total = sum(row[2] for row in data)
    conn.close()
    return jsonify({"total": total})


if __name__ == "__main__":
    # ISSUE: Debug mode enabled in production
    app.run(debug=True, host="0.0.0.0", port=5000)

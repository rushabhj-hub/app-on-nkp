from flask import Flask, request, jsonify
import redis
import os
import psycopg2
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)
    conn.commit()
    cur.close()
    conn.close()



# Redis
redis_host = os.getenv("REDIS_HOST", "redis")
r = redis.Redis(host=redis_host, port=5379, decode_responses=True)

# PostgreSQL
db_host = os.getenv("DB_HOST", "postgres")
db_name = os.getenv("POSTGRES_DB", "appdb")
db_user = os.getenv("POSTGRES_USER", "appuser")
db_pass = os.getenv("POSTGRES_PASSWORD", "apppass")

# Prometheus counter
request_counter = Counter("app_requests_total", "Total API Requests")

def get_db_connection():
    return psycopg2.connect(
        host=db_host,
        database=db_name,
        user=db_user,
        password=db_pass
    )

@app.route("/api/health")
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/api/users", methods=["POST"])
def create_user():
    request_counter.inc()
    data = request.json
    name = data.get("name")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (name) VALUES (%s)", (name,))
    conn.commit()
    cur.close()
    conn.close()

    r.incr("user_count")
    return jsonify({"message": "User created"}), 201

@app.route("/api/users", methods=["GET"])
def get_users():
    request_counter.inc()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM users")
    users = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify({"users": users})

@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2

app = Flask(__name__)
CORS(app)

def get_conn():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )

@app.route("/api/todos", methods=["GET"])
def get_todos():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, task, done FROM todos ORDER BY id;")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify([{"id": r[0], "task": r[1], "done": r[2]} for r in rows])

@app.route("/api/todos", methods=["POST"])
def add_todo():
    task = request.json["task"]
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS todos (id SERIAL PRIMARY KEY, task TEXT, done BOOLEAN DEFAULT FALSE);")
    cur.execute("INSERT INTO todos (task) VALUES (%s);", (task,))
    conn.commit()
    cur.close(); conn.close()
    return jsonify({"status": "ok"}), 201

@app.route("/healthz")
def health():
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

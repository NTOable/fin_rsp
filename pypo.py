from flask import Flask, request, jsonify
import psycopg2

app = Flask(__name__)

def db():
    return psycopg2.connect(
        dbname="piuser",
        user="group3os",
        password="123",
        host="localhost"
    )

@app.get("/get_items")
def get_items():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM items ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return jsonify(rows)

@app.post("/insert_item")
def insert_item():
    name = request.form.get("name")
    conn = db()
    cur = conn.cursor()
    cur.execute("INSERT INTO items (name) VALUES (%s)", (name,))
    conn.commit()
    conn.close()
    return "OK"

app.run(host="0.0.0.0", port=5000)
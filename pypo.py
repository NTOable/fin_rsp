from flask import Flask, request, jsonify
import psycopg2
import psycopg2.extras

app = Flask(__name__)

def db():
    return psycopg2.connect(
        dbname="piuser",
        user="group3os",
        password="123",
        host="localhost"
    )

@app.get("/items")
def get_items():
    conn = db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute(""" SELECT item_id, item_name, quantity, type_name, storage_name, item.created_at FROM item
                         LEFT JOIN Item_Type ON Item.type_id = Item_Type.type_id
                         LEFT JOIN Storage ON Item.storage_id = Storage.storage_id
                ORDER BY Item.item_id DESC;
                """)

    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(rows)


######################################
# ADD NEW ITEM
######################################
@app.post("/items/add")
def add_item():
    data = request.json
    name = data.get("item_name")
    type_id = data.get("type_id")
    storage_id = data.get("storage_id")
    user_id = data.get("user_id")
    quantity = data.get("quantity", 0)

    conn = db()
    cur = conn.cursor()

    cur.execute("""
                INSERT INTO Item (item_name, quantity, type_id, storage_id, user_id)
                VALUES (%s, %s, %s, %s, %s)
                """, (name, quantity, type_id, storage_id, user_id))

    conn.commit()
    conn.close()
    return jsonify({"status": "success"})


######################################
# UPDATE ITEM QUANTITY (+ / -)
######################################
@app.post("/items/update_quantity")
def update_quantity():
    data = request.json
    item_id = data.get("item_id")
    new_qty = data.get("quantity")

    conn = db()
    cur = conn.cursor()

    cur.execute("""
                UPDATE Item
                SET quantity = %s
                WHERE item_id = %s
                """, (new_qty, item_id))

    conn.commit()
    conn.close()
    return jsonify({"status": "updated"})


######################################
# DELETE ITEM
######################################
@app.post("/items/delete")
def delete_item():
    data = request.json
    item_id = data.get("item_id")

    conn = db()
    cur = conn.cursor()

    cur.execute("DELETE FROM Item WHERE item_id = %s", (item_id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "deleted"})


@app.get("/types")
def get_types():
    conn = db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT * FROM Item_Type ORDER BY type_id ASC")
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()

    return jsonify(rows)


@app.get("/storage")
def get_storage():
    conn = db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT * FROM Storage ORDER BY storage_id ASC")
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()

    return jsonify(rows)


app.run(host="0.0.0.0", port=5000)
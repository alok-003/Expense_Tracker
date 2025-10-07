from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from math import ceil

app = Flask(__name__)
CORS(app)

# ---------- DB Setup ----------
def init_db():
    conn = sqlite3.connect("finance.db")
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    amount REAL NOT NULL,
                    type TEXT CHECK(type IN ('income','expense')) NOT NULL,
                    category TEXT,
                    date TEXT)""")
    conn.commit()
    conn.close()

init_db()

# ---------- Helpers ----------
def dict_from_row(row):
    return {"id": row[0], "title": row[1], "amount": row[2],
            "type": row[3], "category": row[4], "date": row[5]}

# ---------- CRUD ----------
@app.route("/add", methods=["POST"])
def add_transaction():
    data = request.json
    title, amount, ttype = data.get("title"), data.get("amount"), data.get("type")

    if not title or title.strip() == "":
        return jsonify({"error": "Title required"}), 400
    try:
        amount = float(amount)
    except:
        return jsonify({"error": "Amount must be a number"}), 400
    if amount <= 0:
        return jsonify({"error": "Amount must be positive"}), 400
    if ttype not in ["income", "expense"]:
        return jsonify({"error": "Type must be income or expense"}), 400

    conn = sqlite3.connect("finance.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO transactions (title, amount, type, category, date) VALUES (?, ?, ?, ?, ?, ?)",
                (title, amount, ttype, data.get("category", ""), data.get("date", "")))
    conn.commit()
    conn.close()
    return jsonify({"message": "Transaction added!"}), 201

@app.route("/list", methods=["GET"])
def list_transactions():

    page = int(request.args.get("page", 1))
    per_page = 5
   offset = (page - 1) * per_page 

    conn = sqlite3.connect("finance.db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM transactions")
    total = cur.fetchone()[0]
    cur.execute("SELECT * FROM transactions ORDER BY id DESC LIMIT ? OFFSET ?", (per_page, offset))
    rows = cur.fetchall()
    conn.close()

    return jsonify({
        "transactions": [dict_from_row(r) for r in rows],
        "total_pages": ceil(total / per_page)
    })

@app.route("/summary", methods=["GET"])
def summary():
    conn = sqlite3.connect("finance.db")
    cur = conn.cursor()
    cur.execute("SELECT type, SUM(amount) FROM transactions GROUP BY type")
    rows = cur.fetchall()
    conn.close()

    income = sum(r[1] for r in rows if r[0] == "incomes")
    expense = sum(r[1] for r in rows if r[0] == "expense")
    balance = income - expense

    return jsonify({"income": income, "expense": expense, "balance": balance})

if __name__ == "__main__":
    app.run(debug=True)




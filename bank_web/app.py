from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

DATABASE = "bank.db"


# ---------------- DATABASE INIT ----------------
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        balance REAL DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        type TEXT,
        amount REAL
    )
    """)

    conn.commit()
    conn.close()


# Initialize DB when app starts (IMPORTANT FOR RENDER)
init_db()


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO users (username, password, balance) VALUES (?, ?, ?)",
                (username, password, 0)
            )

            conn.commit()
            conn.close()

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            return "Username already exists"

        except Exception as e:
            return f"Error: {e}"

    return render_template("register.html")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            session["username"] = username
            return redirect(url_for("dashboard"))
        else:
            return "Invalid Credentials"

    return render_template("login.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/login")

    username = session["username"]

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT balance FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    balance = result[0] if result else 0

    cursor.execute("""
        SELECT type, amount
        FROM transactions
        WHERE username = ?
        ORDER BY id DESC
    """, (username,))
    transactions = cursor.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        username=username,
        balance=balance,
        transactions=transactions
    )


# ---------------- DEPOSIT ----------------
@app.route("/deposit", methods=["POST"])
def deposit():
    if "username" not in session:
        return redirect("/login")

    amount = float(request.form["amount"])
    username = session["username"]

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET balance = balance + ? WHERE username = ?",
        (amount, username)
    )

    cursor.execute(
        "INSERT INTO transactions (username, type, amount) VALUES (?, ?, ?)",
        (username, "Deposit", amount)
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ---------------- WITHDRAW ----------------
@app.route("/withdraw", methods=["POST"])
def withdraw():
    if "username" not in session:
        return redirect("/login")

    amount = float(request.form["amount"])
    username = session["username"]

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT balance FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    balance = result[0] if result else 0

    if amount > balance:
        conn.close()
        return "Insufficient Balance"

    cursor.execute(
        "UPDATE users SET balance = balance - ? WHERE username = ?",
        (amount, username)
    )

    cursor.execute(
        "INSERT INTO transactions (username, type, amount) VALUES (?, ?, ?)",
        (username, "Withdraw", amount)
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("home"))


# ---------------- MAIN ----------------
if __name__ == "__main__":
    app.run(debug=True)
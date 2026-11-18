from flask import Flask, request, redirect, session, render_template, url_for
from database import get_db, init_db

app = Flask(__name__)
app.secret_key = "demo-secret-key"


@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password),
        ).fetchone()
        conn.close()

        if user:
            session["user"] = user["username"]

            if "security_mode" not in session:
                session["security_mode"] = "vulnerable"

            return redirect(url_for("dashboard"))

        error = "Wrong username or password."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?", (session["user"],)
    ).fetchone()
    history = conn.execute(
        "SELECT * FROM transactions WHERE sender = ? OR receiver = ? ORDER BY id DESC",
        (session["user"], session["user"]),
    ).fetchall()
    conn.close()

    message = request.args.get("message")

    print("Security Mode:", session.get("security_mode"))

    return render_template(
        "dashboard.html",
        user=user,
        history=history,
        message=message,
        security_mode=session.get("security_mode", "vulnerable")
    )


@app.route("/transfer", methods=["POST"])
def transfer():
    if "user" not in session:
        return redirect(url_for("login"))


    receiver = request.form.get("receiver", "").strip()
    try:
        amount = float(request.form.get("amount", ""))
    except ValueError:
        return redirect(url_for("dashboard", message="Transfer failed: enter a valid amount."))
    sender = session["user"]

    conn = get_db()
    sender_row = conn.execute(
        "SELECT * FROM users WHERE username = ?", (sender,)
    ).fetchone()
    receiver_row = conn.execute(
        "SELECT * FROM users WHERE username = ?", (receiver,)
    ).fetchone()

    if receiver_row is None:
        conn.close()
        return redirect(url_for("dashboard", message="Transfer failed: user not found."))
    if amount <= 0 or amount > sender_row["balance"]:
        conn.close()
        return redirect(url_for("dashboard", message="Transfer failed: invalid amount."))

    conn.execute(
        "UPDATE users SET balance = balance - ? WHERE username = ?", (amount, sender)
    )
    conn.execute(
        "UPDATE users SET balance = balance + ? WHERE username = ?", (amount, receiver)
    )
    conn.execute(
        "INSERT INTO transactions (sender, receiver, amount) VALUES (?, ?, ?)",
        (sender, receiver, amount),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard", message="Transfer successful."))


@app.route("/reset")
def reset():
    init_db()
    session.clear()
    return redirect(url_for("login"))

@app.route("/toggle-security")
def toggle_security():

    current = session.get("security_mode", "vulnerable")

    if current == "vulnerable":
        session["security_mode"] = "protected"
    else:
        session["security_mode"] = "vulnerable"

    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(port=5000, debug=True)
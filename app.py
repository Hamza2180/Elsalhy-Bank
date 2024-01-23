from flask import Flask, render_template, request, redirect, session, flash
from cs50 import SQL
import secrets

def generate_secret_key():
    return secrets.token_hex(64)

app = Flask(__name__)
app.secret_key = generate_secret_key()
db = SQL("sqlite:///users.db")
user = None

limit = 20
usercount = db.execute("SELECT COUNT(*) as count FROM users;")[0]['count']


def render_styled_template(template_name, **kwargs):
    return render_template(template_name, styles_url="{{ url_for('static', filename='styles.css') }}", **kwargs)


@app.route("/")
def index():
    global user
    # Check if user is logged in
    if "user_id" in session:
        user = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])
        if user:
            return render_styled_template("index.html", username=user[0]['username'], money=user[0]['money'])

    return render_styled_template("not_logged_in.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Validate input
        if not username or not password:
            return "Please provide both username and password."

        # Query database for username
        user = db.execute("SELECT * FROM users WHERE username = :username", username=username)

        # Check if username exists and password is correct
        if user and user[0]["hash"] == password:
            # Store user_id in session
            session["user_id"] = user[0]["id"]
            return redirect("/")
        else:
            return "Invalid username or password."

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    usercount = db.execute("SELECT COUNT(*) as count FROM users;")[0]['count']

    if usercount != limit:
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")

            # Validate input
            if not username or not password:
                return "Please provide both username and password."

            # Insert new user into the database
            result = db.execute("INSERT INTO users (username, hash, money) VALUES (:username, :hash, 100)",
                                username=username, hash=password)

            if not result:
                return "Registration failed. Username might be taken."

            user_id = result
            session["user_id"] = user_id

            return redirect("/")

        return render_template("register.html")
    else:
        return "There are no more user spots on the database."

@app.route("/logout")
def logout():
    # Clear session
    session.clear()
    return redirect("/")


@app.route("/transact", methods=["GET", "POST"])
def transact():
    user_id = session.get('user_id')

    if user_id is None:
        return "Error! <a href='/login'>Login</a>"

    # Fetch user information
    user_result = db.execute("SELECT * FROM users WHERE id = :user_id", user_id=user_id)

    if not user_result:
        return "Error! User not found."

    user = user_result[0]

    if request.method == "POST":
        other_user = request.form.get("user")
        amount_str = request.form.get("amount", "0")

        # Validate amount input
        try:
            amount = float(amount_str)
        except ValueError:
            return "Error! Invalid amount."

        user_amount = user['money']
        print(f"user_amount: {user_amount}")

        # Validate other_user input
        if not other_user or other_user.isspace():
            print("DEBUG: Other user not specified.")
            return "Error! Other user not specified."

        print(f"DEBUG: other_user = {other_user}")

        # Fetch other user information
        other_user_result = db.execute("SELECT money FROM users WHERE username = :other_user", other_user=other_user)
        print(f"DEBUG: other_user_result: {other_user_result}")

        if not other_user_result:
            print(f"DEBUG: Other user '{other_user}' not found.")
            return f"Error! Other user '{other_user}' not found."

        other_user_amount = other_user_result[0]['money']
        print(f"DEBUG: other_user_amount: {other_user_amount}")

        future_money = user_amount - amount
        other_future_money = other_user_amount + amount

        if future_money >= 0:
            # Update user's money
            db.execute("UPDATE users SET money = :future_money WHERE id = :user_id", future_money=future_money, user_id=user_id)
            # Update other user's money
            db.execute("UPDATE users SET money = :other_future_money WHERE username = :other_user", other_future_money=other_future_money, other_user=other_user)
            return render_template("transact.html")
        else:
            return "Error! Not enough funds."

    # Render the transaction form
    return render_template("transact.html")

@app.route("/check_balance")
def check_balance():
    if "user_id" in session:
        user = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])
        return render_template("check_balance.html", user=user[0])
    else:
        return "You are not logged in. <a href='/login'>Login</a> or <a href='/register'>Register</a>."


if __name__ == "__main__":
    app.run(debug=True)

import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")

@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    return apology("TODO")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    return apology("TODO")

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    if request.method == "POST":
        # Ensure symbol and shares are provided
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        if not symbol or not shares:
            return apology("Please provide both stock symbol and number of shares.")

        # Validate shares as a positive integer
        try:
            shares = int(shares)
            if shares <= 0:
                raise ValueError()
        except ValueError:
            return apology("Number of shares must be a positive integer.")

        # Lookup current stock price
        quote_result = lookup(symbol)

        if not quote_result:
            return apology("Invalid stock symbol.")

        price = quote_result["price"]
        cost = price * shares

        # Check if the user has enough cash
        user_cash = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])[0]["cash"]

        if cost > user_cash:
            return apology("Not enough cash to buy the specified number of shares.")

        # Update user's cash balance
        db.execute("UPDATE users SET cash = cash - :cost WHERE id = :user_id", cost=cost, user_id=session["user_id"])

        # Record the purchase in a new table (e.g., transactions) with current timestamp
        db.execute(
            "INSERT INTO transactions (user_id, symbol, shares, price, transaction_type, timestamp) VALUES (:user_id, :symbol, :shares, :price, :transaction_type, CURRENT_TIMESTAMP)",
            user_id=session["user_id"],
            symbol=symbol,
            shares=shares,
            price=price,
            transaction_type="BUY",
        )

        return redirect("/")

    # If the request method is GET, render the buy.html template
    return render_template("buy.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")



@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "POST":
        symbol = request.form.get("symbol")

        if not symbol:
            return apology("Please provide a stock symbol.")

        quote_result = lookup(symbol)

        if not quote_result:
            return apology("Invalid stock symbol.")

        return render_template("quoted.html", quote_result=quote_result)

    # If the request method is GET, render the quote.html template
    return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

            # Validate input
        if not username or not password:
            return "Please provide both username and password."

            # Insert new user into the database
        result = db.execute("INSERT INTO users (username, hash, cash) VALUES (:username, :hash, 10000)",
                            username=username, hash=password)

        if not result:
            return "Registration failed. Username might be taken."

        user_id = result
        session["user_id"] = user_id

        return redirect("/")

    return render_template("register.html")
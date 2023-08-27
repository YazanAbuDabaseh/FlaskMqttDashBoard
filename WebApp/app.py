import os
import datetime

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_passworsd_hash, generate_password_hash

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


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # get  user stocks
    stocks = db.execute(
        "SELECT symbol, SUM(shares) as total_shares FROM log WHERE user_id = :user_id Group BY symbol HAVING total_shares > 0",
        user_id=session["user_id"],
    )

    # get user cash
    cash = db.execute(
        "SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"]
    )[0]["cash"]

    total_value = cash
    grand_total = cash

    for stock in stocks:
        quote = lookup(stock["symbol"])
        stock["name"] = quote["name"]
        stock["price"] = quote["price"]
        stock["value"] = stock["price"] * stock["total_shares"]
        total_value += stock["value"]
        grand_total += stock["value"]

    return render_template(
        "index.html",
        stocks=stocks,
        cash=cash,
        total_value=total_value,
        grand_total=grand_total,
    )


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    # make sure its a post request
    if request.method == "POST":
        symbol = request.form.get("symbol").upper()
        shares = request.form.get("shares")
        if not symbol:  # check provided symbol
            return apology("provide stock symbol")
        elif (
            not shares or not shares.isdigit() or int(shares) <= 0
        ):  # check shares input correctly
            return apology("provide positive integer number of shares")

        quote = lookup(symbol)
        if quote is None:  # check if symbol is correct
            return apology("stock symbol not found")

        # get price and compare it with availble cash
        price = quote["price"]
        totalCost = price * int(shares)
        cash = db.execute(
            "SELECT cash FROM users WHERE id = :user_id",
            user_id=session["user_id"])[0]["cash"]

        if cash < totalCost:
            return apology("not enough cash")

        # deducte from cash
        db.execute(
            "UPDATE users SET cash = cash - :totalCost WHERE id = :user_id",
            totalCost=totalCost,
            user_id=session["user_id"],
        )

        # log the purchase
        timestamp = datetime.datetime.now()
        db.execute(
            " INSERT INTO log (user_id, symbol, shares, price, timestamp) VALUES (:user_id, :symbol, :shares, :price, :timestamp)",
            user_id=session["user_id"],
            symbol=symbol,
            shares=shares,
            price=price,
            timestamp=timestamp,
        )
        return redirect("/")

    # if GET render buy page
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    #get user log
    transactions = db.execute("SELECT * FROM log WHERE user_id = :user_id ORDER BY timestamp DESC", user_id=session["user_id"])
    #render history page
    return render_template("history.html", transactions=transactions)


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
    """Get stock quote."""

    # make sure its a post request
    if request.method == "POST":
        symbol = request.form.get("symbol")  # get the stock name from user
        quote = lookup(symbol)  # find the stock info using lookup function in helper.py

        # if the stock name is wrong
        if not quote:
            return apology("qoute does not exist")
        # if the stock name is correct render the page with its info passing varible qoute
        return render_template("quote.html", quote=quote)

    # if its a GET request display a form for the user to fill with stock name
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Forget any user_id
    session.clear()

    # make sure its a post request
    if request.method == "POST":
        # check for username
        if not request.form.get("username"):
            return apology("provide a username")

        # check for password
        elif not request.form.get("password"):
            return apology("provide a password")

        # check for password confirmation
        elif not request.form.get("confirmation"):
            return apology("provide a password confirmation")

        # check for password match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("password mismatch")

        # check username in db
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )
        if len(rows) != 0:
            return apology("username already exists")

        # add new username
        db.execute(
            "INSERT INTO users (username, hash) VALUES (?, ?)",
            request.form.get("username"),
            generate_password_hash(request.form.get("password")),
        )

        # login
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )
        session["user_id"] = rows[0]["id"]

        return redirect("/")

    # if get is used
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # get user stocks
    stocks = db.execute(
        "SELECT symbol, sum(shares) as total_shares FROM log WHERE user_id = :user_id GROUP BY symbol HAVING total_shares > 0",
        user_id=session["user_id"],
    )

    # in POST

    if request.method == "POST":
        symbol = request.form.get("symbol").upper()
        shares = request.form.get("shares")

        if not symbol:
            return apology("please provide stock symbol")
        elif not shares or not shares.isdigit() or int(shares) <= 0:
            return apology("please provide a positive integer for number of shares")
        else:
            shares = int(shares)

        for stock in stocks:
            if stock["symbol"] == symbol:
                if stock["total_shares"] < shares:
                    return apology("not enoug shares to sell")
                else:
                    quote = lookup(symbol)
                    if quote is None:
                        return apology("stock symbol not found")
                    price = quote["price"]
                    total_sale = shares * price

                    # update user cash
                    db.execute(
                        "UPDATE users SET cash = cash + :total_sale WHERE id = :user_id",
                        total_sale=total_sale,
                        user_id=session["user_id"],
                    )

                    # add to log
                    db.execute(
                        "INSERT INTO log (user_id, symbol, shares, price) VALUES (:user_id, :symbol, :shares, :price)",
                        user_id=session["user_id"],
                        symbol=symbol,
                        shares=-shares,
                        price=price,
                    )

                    return redirect("/")
    # if GET
    else:
        return render_template("sell.html", stocks=stocks)


@app.route("/addcash", methods=["GET", "POST"])
@login_required
def addcash():
    # get user cash
    cash = db.execute(
        "SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"]
        )[0]["cash"]

    # in POST
    if request.method == "POST":
        amount = request.form.get("amount")
        if not amount:
            return apology("please provide the cash amount")
        # update user cash
        db.execute("UPDATE users SET cash = cash + :amount WHERE id = :user_id",
                    amount=amount,
                    user_id=session["user_id"],)
        return redirect("/")

    # in GET
    else:
        return render_template("addcash.html")

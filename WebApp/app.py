import os
import datetime

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///mqtt.db")


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
    """Show publish's and subscribtion's"""
    
    # publish
    

    return render_template("index.html")


@app.route("/log")
@login_required
def history():
    """Show history of transactions"""
    #get user log
    transactions = db.execute("SELECT * FROM log WHERE user_id = :user_id ORDER BY timestamp DESC", user_id=session["user_id"])
    #render history page
    return render_template("log.html", transactions=transactions)


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


@app.route("/AddPub", methods=["GET", "POST"])
@login_required
def AddPub():
    """Add topic to publish to"""
    # make sure its a post request
    if request.method == "POST":
        pubTopic = request.form.get("pubTopic")
        if not pubTopic:  # check provided topic
            return apology("provide a topic to publish to")

        # Add publish topic
        db.execute(
            "INSERT INTO topics (user_id, type, topic) VALUES(:user_id, :type, :topic)",
            user_id = session["user_id"],
            type = "publish",
            topic = request.form.get("pubTopic"),
            ) 
        return redirect("/")

    # if GET render buy page
    else:
        return render_template("AddPub.html")


@app.route("/EditBroker", methods=["GET", "POST"])
@login_required
def EditBroker():
    """Add Broker """
    # make sure its a post request
    if request.method == "POST":
        EditBroker = request.form.get("EditBroker")
        EditPort = request.form.get("EditPort")
        if not EditBroker:  # check provided topic
            return apology("provide a Broker")
        elif not EditPort:
            return apology("provide a Port")

        EditBroker = request.form.get("EditBroker")
        EditPort = request.form.get("EditPort")
        # Add publish topic
        db.execute(
            "UPDATE users SET broker = :EditBroker, port = :EditPort WHERE id = :user_id",
            EditBroker=EditBroker,
            EditPort=EditPort,
            user_id=session["user_id"],
        )
        return redirect("/")

    # if GET render buy page
    else:
        return render_template("EditBroker.html")


@app.route("/AddSub", methods=["GET", "POST"])
@login_required
def AddSub():
    """Add topic to publish to"""
    # make sure its a post request
    if request.method == "POST":
        pubTopic = request.form.get("subTopic")
        if not pubTopic:  # check provided topic
            return apology("provide a topic to subscibe to")

        # Add publish topic
        db.execute(
            "INSERT INTO topics (user_id, type, topic) VALUES(:user_id, :type, :topic)",
            user_id=session["user_id"],
            type="subscribe",
            topic=request.form.get("subTopic"),
        )
        return redirect("/")

    # if GET render buy page
    else:
        return render_template("AddSub.html")

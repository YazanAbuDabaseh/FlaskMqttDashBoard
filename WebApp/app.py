import os
import datetime

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask
from flask_mqtt import Mqtt


from helpers import apology, login_required, get_random_string

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///mqtt.db")

app.config['SECRET'] = 'my secret key'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['MQTT_BROKER_URL'] = 'broker.emqx.io'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_KEEPALIVE'] = 5
app.config['MQTT_TLS_ENABLED'] = False

mqtt = Mqtt(app, connect_async=True)

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    data = {"topic": message.topic, "payload": message.payload.decode()}
    db.execute(
        "INSERT INTO messages (topic, message) VALUES(:topic, :messagePayload)",
        topic=data["topic"],
        messagePayload=data["payload"],
    )


@app.route("/")
@login_required
def index():
    """Show publish's and subscribtion's"""

    #Path
    userPath = db.execute(
        "SELECT path FROM users WHERE id = :user_id",
        user_id=session["user_id"],
    )

    # publishs
    pubTopics = db.execute(
        "SELECT topic FROM topics WHERE (user_id = :user_id AND type = 'publish') ",
        user_id=session["user_id"],
    )

    # subscribtions
    subTopics = db.execute(
        "SELECT topic FROM topics WHERE (user_id = :user_id AND type = 'subscribe') ",
        user_id=session["user_id"],
    )

    for s in subTopics:
        # print(userPath[0]["path"] + "/" + s["topic"])
        subTopic = userPath[0]["path"] + "/" + s["topic"]
        mqtt.subscribe(subTopic)

    # move incoming messags to log

    incommingMessages = db.execute("SELECT id, topic, message FROM messages")

    for incommingMessage in incommingMessages:
        for s in subTopics:
            timestamp = datetime.datetime.now()
            if incommingMessage["topic"] == (userPath[0]["path"] + "/" +s["topic"]):
                print(incommingMessage["topic"])
                db.execute(
                    "INSERT INTO log (user_id, topic, type, value, timestamp) VALUES(:user_id, :topic, :type, :value, :timestamp)",
                    user_id=session["user_id"],
                    type = "subscribe",
                    topic=incommingMessage["topic"],
                    value = incommingMessage["message"],
                    timestamp = timestamp,
                )
                db.execute( " DELETE FROM messages WHERE id = ? ", incommingMessage["id"],)


    # sub log
    subLog = db.execute(
        "SELECT topic, value, timestamp FROM log WHERE (user_id = :user_id AND type = 'subscribe') GROUP BY topic",
        user_id=session["user_id"],
    )

    return render_template(
        "index.html",
        userPath=userPath,
        pubTopics=pubTopics,
        subTopics=subTopics,
        subLog=subLog
        )

@app.route("/log")
@login_required
def history():
    """Show history of transactions"""
    #get user log
    messagingLog = db.execute("SELECT * FROM log WHERE user_id = :user_id ORDER BY timestamp DESC", user_id=session["user_id"])
    #render history page
    return render_template("log.html", messagingLog=messagingLog)


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
            "INSERT INTO users (username, hash, path) VALUES (?, ?, ?)",
            request.form.get("username"),
            generate_password_hash(request.form.get("password")),
            (request.form.get("username") + "PATH" + get_random_string(8) ),
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
        return redirect("/AddPub")

    # if GET render buy page
    else:
        pubTopics = db.execute(
            "SELECT topic FROM topics WHERE type = :type AND user_id = :user_id" ,
            type="publish",
            user_id=session["user_id"],
        )
        return render_template("AddPub.html", pubTopics=pubTopics)

@app.route("/removePub", methods=["POST"])
@login_required
def RemovePub():
    """remove publsih"""
    db.execute(
        "DELETE FROM topics WHERE (topic = :topic AND type = :type AND user_id = :user_id)", 
        user_id=session["user_id"],
        type="publish",
        topic=request.form.get("pubTopic")
    )
    return redirect("/AddPub")


@app.route("/ShowBroker", methods=["GET"])
@login_required
def ShowBroker():
    """show Broker """
    return render_template("ShowBroker.html", broker=app.config['MQTT_BROKER_URL'], port=app.config['MQTT_BROKER_PORT'] )


@app.route("/AddSub", methods=["GET", "POST"])
@login_required
def AddSub():
    """Add topic to publish to"""
    # make sure its a post request
    if request.method == "POST":
        pubTopic = request.form.get("subTopic")
        if not pubTopic:  # check provided topic
            return apology("provide a topic to subscibe to")

        subTopics = db.execute(
            "SELECT topic FROM topics"
        )
        formTopic=request.form.get("subTopic")
        # Add subscribe topic
        for subTopics in subTopics:
            if formTopic == subTopics["topic"]:
                return apology("Topic already subscibed to")

        db.execute(
                    "INSERT INTO topics (user_id, type, topic) VALUES(:user_id, :type, :topic)",
                    user_id=session["user_id"],
                    type="subscribe",
                    topic=formTopic,
                )
        return redirect("/AddSub")

    # if GET render buy page
    else:
        subTopics = db.execute(
            "SELECT topic FROM topics WHERE type = :type AND user_id = :user_id",
            type="subscribe",
            user_id=session["user_id"],
        )
        return render_template("AddSub.html", subTopics=subTopics)

@app.route("/removeSub", methods=["POST"])
@login_required
def RemoveSub():
    """remove subscribtion"""
    db.execute(
        "DELETE FROM topics WHERE (topic = :topic AND type = :type AND user_id = :user_id)", 
        user_id=session["user_id"],
        type="subscribe",
        topic=request.form.get("subTopic")
    )
    return redirect("/AddSub")


@app.route("/messagePublish", methods=["POST"])
@login_required
def messagePublish():
    """publish a message"""
    f = request.form
    timestamp = datetime.datetime.now()
    for key in f.keys():
        for value in f.getlist(key):
            if mqtt.publish(key, value):
                db.execute(
                    "INSERT INTO log (user_id, topic, type, value, timestamp) VALUES(:user_id, :topic, :type, :value, :timestamp)",
                    user_id=session["user_id"],
                    topic = key,
                    type = "publish",
                    value = value,
                    timestamp=timestamp,
                )
                print (key,":",value)

    return redirect("/")

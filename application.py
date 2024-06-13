from cs50 import SQL, os
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from extra import apology, login_required
import random
answers = [4]
questions = [4]
app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///database.db")

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 403)

        elif not request.form.get("password"):
            return apology("must provide password", 404)

        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 405)

        session["user_id"] = rows[0]["user_id"]

        return redirect("/")

    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("No username given", 400)
        elif not request.form.get("password") or not request.form.get("password2"):
            return apology("No password given", 400)
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))
        if len(rows) != 0:
            return apology("username is taken", 400)

        if request.form.get("password")!=request.form.get("password2"):
            return apology("passwords do not match", 400)

        hash = generate_password_hash(request.form.get("password"))
        new_user_id = db.execute("INSERT INTO users (username, hash, points) VALUES(:username, :hash, :points)",
                                 username=request.form.get("username"),
                                 hash=hash, points=0)
        session["user_id"] = new_user_id

        flash("Registered!")
        return redirect(url_for("home"))

    else:
        return render_template("register.html")
@app.route("/logout")
@login_required
def logout():

    session.clear()
    return redirect("/login")

@app.route("/")
@login_required
def home():
    users = db.execute("SELECT points FROM users where user_id= :user_id", user_id = session["user_id"])
    allwords = db.execute("SELECT word, definition, time FROM words where user_id = :user_id GROUP BY id", user_id = session["user_id"])

    total = users[0]["points"]

    return render_template("home.html", allwords=allwords)

@app.route("/play", methods=["GET", "POST"])
@login_required
def play():
    if request.method == "POST":
        num = 0
        for i in range(4):
            questionnumber = "question" + str(i)
            answer = request.form.get(questionnumber)
            if answer == answers[i]:
                num = num + 1

        return render_template("results.html", num = num)
    else:
        questions.clear()
        answers.clear()
        ques = db.execute("SELECT word FROM words WHERE user_id = :user_id", user_id = session["user_id"])
        count = 1
        num = len(ques)
        if num < 4:
            return apology("You need at least 4 words in your dictionary to play", 421)
        if num > 4:
            rough = []
            for index in range(num):
                rough.insert(index, ques[index]["word"])

            diff = num - 4
            random.shuffle(rough)
            for index in range(diff):
                rough.pop()
                num = num - 1
            for i in range(4):
                questions.append(rough[i])
        else:
            for i in range(4):
                questions.append(ques[i]["word"])
            random.shuffle(questions)
        #for i in questions:
            #print(i)
        for j in range(len(questions)):
            answer = db.execute("SELECT definition FROM words WHERE word = :word and user_id = :user_id", word = questions[j], user_id = session["user_id"])
            answers.insert(j, answer[0]["definition"])
        options = answers.copy()
        for j in range(4):
            random.shuffle(options)

        return render_template("play.html", questions = questions, count = count, options = options,)

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        search = db.execute("SELECT word FROM words where user_id = :user_id AND word = :word", user_id = session["user_id"], word = request.form.get("addword"))
        if search is True:
            return apology("The word is already in the system", 415)
        addword = request.form.get("addword").title()
        adddefinition = request.form.get("adddefinition").capitalize()
        db.execute("INSERT INTO words (user_id, word, definition) VALUES (:user_id, :word, :definition)",
        user_id = session["user_id"], word = addword, definition = adddefinition)
        flash("Word Added!")
        return redirect(url_for("home"))
    else:
        return render_template("add.html")

@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    words = db.execute("SELECT word FROM words where user_id = :user_id", user_id = session["user_id"])
    if request.method == "POST":
        if request.form.get("deleteword")=="":
            return apology("No word selected", 420)
        db.execute("DELETE from words WHERE word = :word and user_id = :user_id", word = request.form.get("deleteword"), user_id = session["user_id"])
        flash("Word Deleted!")
        return redirect(url_for("home"))
    else:
        return render_template("delete.html", words=words)

@app.route("/settings", methods = ["GET", "POST"])
@login_required
def settings():
    current = db.execute("SELECT username FROM users where user_id = :user_id", user_id = session["user_id"])
    password = db.execute("SELECT hash FROM users where user_id = :user_id", user_id = session["user_id"])
    currentusername = current[0]["username"]
    currentpassword = password[0]["hash"]
    if request.method == "POST":
        if len(current)!=1:
            return apology("Username not found", 410)
        #For changing Username
        if (not request.form.get("changeusername")=="") and (not request.form.get("changeusername")==currentusername):
            db.execute("UPDATE users SET username = :username WHERE user_id = :user_id", username = request.form.get("changeusername"), user_id = session["user_id"])

        #For changing Password
        if request.form.get("oldpassword")!="" and check_password_hash(currentpassword, request.form.get("oldpassword")):
            if request.form.get("newpassword")=="":
                return apology("Please input your new password", 411)
            if request.form.get("newpassword")!=request.form.get("confirmnewpassword"):
                return apology("Your passwords do not match", 412)
            hash = generate_password_hash(request.form.get("newpassword"))
            db.execute("UPDATE users SET hash = :hash WHERE user_id = :user_id", hash=hash, user_id=session["user_id"])
        else:
            return apology("Your Old Password does not match!", 413)
        flash("Changes Made!")
        return redirect("/")
    else:
        return render_template("settings.html", currentusername = current[0]["username"])
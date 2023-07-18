from main import cache
from http.client import OK
from unittest import result
from flask import Flask, request, redirect
from flask import render_template, url_for
from flask import current_app as app
from application.jobs import tasks
from application.jobs import send_email
from flask_security import auth_required, login_required, current_user
from application.data.database import db



@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("home.html")

@app.route("/tokenlogin", methods=["GET", "POST"])
def tokenlogin():
    return render_template("tokenlogin.html")

@app.route("/you", methods=["GET", "POST"])
@login_required
@cache.cached(timeout=25)
def you():
    if request.method == "GET":
        user = current_user.email        
        print("To test whether the page is served from cache or not")
        return render_template("you.html", username=user)

from flask import render_template, session, redirect

def dashboard():

    if "userID" not in session:
        return redirect("/")

    return render_template("cashier/dashboard.html")
# controllers/auth_controller.py
from models.audit_model import write_log
from flask import render_template, request, jsonify, session, redirect
from models.employee_model import get_all_employee, check_login

def login_page():
    employees = get_all_employee()
    return render_template(
        "login/login.html",
        employees=employees
    )

def login_api():
    data = request.get_json()
    userID = data["userID"]
    pin = data["pin"]
    employee = check_login(userID, pin)

    if employee:
        session["userID"] = employee.userID
        session["fullName"] = employee.fullName
        session["position"] = employee.position

        write_log(
            employee.userID,
            "Login",
            "Login Success"
        )
                
        return jsonify({
            "success": True,
            "position": employee.position,
            "name": employee.fullName
        })

    write_log(
        userID,
        "Login Failed",
        "Wrong PIN"
    )
    return jsonify({
        "success": False,
        "message": "Incorrect PIN"
    })

def logout():
    user_id = session.get("userID", "Unknown")
    
    write_log(
        user_id,
        "Logout",
        "User Logout"
    )

    session.clear()
    return redirect("/")
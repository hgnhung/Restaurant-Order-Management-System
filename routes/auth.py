from flask import Blueprint
from controllers.auth_controller import login_page, login_api
from controllers.auth_controller import logout

auth_bp = Blueprint("auth", __name__)

# Hiển thị giao diện login
@auth_bp.route("/")
def home():
    return login_page()

# API đăng nhập
@auth_bp.route("/login", methods=["POST"])
def login():
    return login_api()

@auth_bp.route("/logout")
def user_logout():
    return logout()
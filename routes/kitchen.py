from flask import Blueprint
from controllers.kitchen_controller import dashboard

kitchen_bp = Blueprint("kitchen", __name__)

@kitchen_bp.route("/kitchen/dashboard")
def kitchen_dashboard():
    return dashboard()
from flask import Blueprint
from controllers.cashier_controller import dashboard

cashier_bp = Blueprint("cashier", __name__)

@cashier_bp.route("/cashier/dashboard")
def cashier_dashboard():
    return dashboard()
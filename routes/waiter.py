from flask import Blueprint
from controllers.waiter_controller import dashboard

waiter_bp = Blueprint("waiter", __name__)

@waiter_bp.route("/waiter/dashboard")
def waiter_dashboard():
    return dashboard()
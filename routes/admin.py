from flask import Blueprint
from controllers.admin_controller import dashboard

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin/dashboard")
def admin_dashboard():
    return dashboard()
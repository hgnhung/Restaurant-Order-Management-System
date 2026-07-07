from flask import Blueprint
from controllers.kitchen_controller import KitchenController

kitchen_bp = Blueprint("kitchen", __name__, url_prefix="/kitchen")

kitchen_bp.add_url_rule(
    "/dashboard",
    view_func=KitchenController.get_dashboard,
    methods=["GET"]
)

kitchen_bp.add_url_rule(
    "/update-status",
    view_func=KitchenController.update_order_status,
    methods=["POST"]
)
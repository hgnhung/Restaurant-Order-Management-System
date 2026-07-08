from flask import Blueprint
from controllers.cashier_controller import CashierController

cashier_bp = Blueprint(
    "cashier",
    __name__,
    url_prefix="/cashier"
)

cashier_bp.add_url_rule(
    "/invoice",
    view_func=CashierController.get_invoice,
    methods=["GET"]
)

cashier_bp.add_url_rule(
    "/generate-invoice",
    view_func=CashierController.generate_invoice,
    methods=["POST"]
)

cashier_bp.add_url_rule(
    "/payment",
    view_func=CashierController.get_payment,
    methods=["GET"]
)

cashier_bp.add_url_rule(
    "/payment",
    view_func=CashierController.process_payment,
    methods=["POST"]
)
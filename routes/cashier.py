from flask import Blueprint

cashier_bp = Blueprint(
    "cashier",
    __name__,
    url_prefix="/cashier"
)

@cashier_bp.route("/")
def dashboard():

    return "Cashier Dashboard"
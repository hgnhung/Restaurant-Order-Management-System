from flask import Blueprint

kitchen_bp = Blueprint(
    "kitchen",
    __name__,
    url_prefix="/kitchen"
)

@kitchen_bp.route("/")
def dashboard():
    return "Kitchen Dashboard"
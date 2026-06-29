from flask import Blueprint

waiter_bp = Blueprint(
    "waiter",
    __name__,
    url_prefix="/waiter"
)

@waiter_bp.route("/")
def dashboard():

    return "Waiter Dashboard"
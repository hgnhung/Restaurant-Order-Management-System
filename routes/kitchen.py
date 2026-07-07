from flask import Blueprint
from controllers.kitchen_controller import KitchenController

# Initialize kitchen blueprint with professional routing prefix
kitchen_bp = Blueprint('kitchen', __name__, url_prefix='/kitchen')

# Register application core endpoints mapping to kitchen processing units
kitchen_bp.route('/dashboard', methods=['GET'])(KitchenController.get_dashboard)
kitchen_bp.route('/update-status', methods=['POST'])(KitchenController.update_order_status)

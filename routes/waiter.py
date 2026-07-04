# routes/waiter.py
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from controllers.waiter_controller import (
    get_menu_categories, get_dishes_by_category, search_dishes,
    create_order, get_active_orders, get_order_details,
    confirm_order, modify_order, cancel_order, update_order_status_to_served,
    get_tables, add_item_to_order, remove_item_from_order, get_notifications
)
import logging

logger = logging.getLogger(__name__)

waiter_bp = Blueprint('waiter', __name__, url_prefix='/waiter')

@waiter_bp.before_request
def check_waiter_auth():
    if 'user_id' not in session or session.get('position') not in ['Waiter', 'Admin']:
        return redirect(url_for('auth.login'))

# ========================== DASHBOARD & MENU ==========================
@waiter_bp.route('/dashboard', methods=['GET'])
def dashboard():
    """Trang chính - Dashboard + Menu"""
    categories = get_menu_categories()
    dishes = get_dishes_by_category(categories[0]['categoryID']) if categories else []
    return render_template('waiter/dashboard.html', 
                         categories=categories, 
                         dishes=dishes)

@waiter_bp.route('/menu', methods=['GET'])
def view_menu():
    return redirect(url_for('waiter.dashboard'))

@waiter_bp.route('/search', methods=['GET'])
def search_dishes_route():
    keyword = request.args.get('keyword', '').strip()
    if not keyword:
        return jsonify({"success": False, "message": "Keyword is required"}), 400
    dishes = search_dishes(keyword)
    return jsonify({"success": True, "dishes": dishes})

# ========================== TABLE ==========================
@waiter_bp.route('/tables', methods=['GET'])
def view_tables():
    """Trang danh sách bàn"""
    tables = get_tables()
    return render_template('waiter/table.html', tables=tables)

# ========================== ORDER ==========================
@waiter_bp.route('/orders', methods=['GET'])
def list_active_orders():
    """Danh sách đơn hàng"""
    orders = get_active_orders()
    return render_template('waiter/order.html', orders=orders)

@waiter_bp.route('/orders/<order_id>', methods=['GET'])
def order_details(order_id):
    """Chi tiết đơn hàng"""
    order = get_order_details(order_id)
    if not order:
        return jsonify({"success": False, "message": "Order not found"}), 404
    return render_template('waiter/order_detail.html', order=order)

# ========================== ORDER ACTIONS ==========================
@waiter_bp.route('/orders/create', methods=['POST'])
def create_new_order():
    data = request.get_json() or {}
    table_number = data.get('tableNumber')
    if not table_number:
        return jsonify({"success": False, "message": "Table number is required"}), 400
    result = create_order(table_number, session.get('user_id'))
    return jsonify(result)

@waiter_bp.route('/orders/<order_id>/confirm', methods=['POST'])
def confirm_order_route(order_id):
    result = confirm_order(order_id, session.get('user_id'))
    return jsonify(result)

@waiter_bp.route('/orders/<order_id>/items', methods=['POST'])
def add_item_route(order_id):
    data = request.get_json() or {}
    result = add_item_to_order(
        order_id, 
        data.get('dishID'), 
        data.get('quantity', 1), 
        data.get('specialNote')
    )
    return jsonify(result)

@waiter_bp.route('/orders/<order_id>/items/<dish_id>', methods=['DELETE'])
def remove_item_route(order_id, dish_id):
    result = remove_item_from_order(order_id, dish_id, session.get('user_id'))
    return jsonify(result)

@waiter_bp.route('/orders/<order_id>', methods=['PUT'])
def modify_order_route(order_id):
    data = request.get_json() or {}
    result = modify_order(order_id, data.get('items', []), session.get('user_id'))
    return jsonify(result)

@waiter_bp.route('/orders/<order_id>/cancel', methods=['POST'])
def cancel_order_route(order_id):
    result = cancel_order(order_id, session.get('user_id'))
    return jsonify(result)

@waiter_bp.route('/orders/<order_id>/serve', methods=['POST'])
def serve_order(order_id):
    result = update_order_status_to_served(order_id, session.get('user_id'))
    return jsonify(result)

# ========================== NOTIFICATION ==========================
@waiter_bp.route('/notifications', methods=['GET'])
def get_notifications_route():
    notifications = get_notifications(session.get('user_id'))
    return jsonify({"success": True, "notifications": notifications})
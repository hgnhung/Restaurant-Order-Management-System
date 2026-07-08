# routes/waiter.py
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from controllers.waiter_controller import WaiterController
from functools import wraps

waiter_bp = Blueprint('waiter', __name__, url_prefix='/waiter')

# SECURE_WIFI_PREFIXES = ["192.168.1.", "10.0.0.", "127.0.0.1"]

def check_waiter_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'userID' not in session and 'user_id' not in session:
            # Fallback for development if no session
            session['userID'] = 'E02'
            session['user_id'] = 'E02'
            # return redirect('/')
        return f(*args, **kwargs)
    return decorated_function

# ========================== DASHBOARD ==========================
@waiter_bp.route('/dashboard', methods=['GET'])
@check_waiter_auth
def dashboard():
    """Trang chính - Dashboard"""
    return render_template('waiter/dashboard.html')

# ========================== TABLE MAP ==========================
@waiter_bp.route('/tables', methods=['GET'])
@check_waiter_auth
def view_tables():
    """Trang danh sách bàn"""
    result = WaiterController.get_table_map_data()
    if not result.get('success'):
        flash(result.get('message', 'Error loading tables'))
        tables = []
    else:
        tables = result['tables']
    return render_template('waiter/table.html', tables=tables)

# ========================== ORDER CREATION / MENU ==========================
@waiter_bp.route('/order', methods=['GET'])
@check_waiter_auth
def view_order():
    """Trang chọn món (Draft order)"""
    table_number = request.args.get('table')
    if not table_number:
        return redirect(url_for('waiter.view_tables'))
        
    result = WaiterController.get_ordering_view_data(table_number)
    if not result.get('success'):
        flash(result.get('message', 'Error loading menu'))
        return redirect(url_for('waiter.view_tables'))
        
    return render_template(
        'waiter/order.html', 
        table_number=result['table_number'], 
        dishes=result['dishes'], 
        cart_items=result['cart_items']
    )

@waiter_bp.route('/add-to-cart', methods=['POST'])
@check_waiter_auth
def add_to_cart():
    table_number = request.form.get('table_number')
    dish_id = request.form.get('dish_id')
    quantity = request.form.get('quantity', 1)
    special_note = request.form.get('special_note', '').strip()
    user_id = session.get('userID') or session.get('user_id', 'E02')

    result = WaiterController.process_add_to_cart(table_number, dish_id, quantity, special_note, user_id)
    if not result.get('success'):
        flash(result.get('message'))
        
    return redirect(url_for('waiter.view_order', table=table_number))

@waiter_bp.route('/remove-from-cart', methods=['POST'])
@check_waiter_auth
def remove_from_cart():
    table_number = request.form.get('table_number')
    dish_id = request.form.get('dish_id')
    special_note = request.form.get('special_note', '').strip()
    user_id = session.get('userID') or session.get('user_id', 'E02')

    result = WaiterController.process_remove_from_cart(table_number, dish_id, special_note, user_id)
    if not result.get('success'):
        flash(result.get('message'))
        
    # Redirect flag depends on whether the cart became empty
    return redirect(result.get('redirect', url_for('waiter.view_order', table=table_number)))

@waiter_bp.route('/update-cart', methods=['POST'])
@check_waiter_auth
def update_cart():
    table_number = request.form.get('table_number')
    dish_id = request.form.get('dish_id')
    special_note = request.form.get('special_note', '').strip()
    action = request.form.get('action') # 'increase' or 'decrease'
    user_id = session.get('userID') or session.get('user_id', 'E02')

    result = WaiterController.process_update_cart(table_number, dish_id, special_note, action, user_id)
    if not result.get('success'):
        flash(result.get('message'))
        
    return redirect(result.get('redirect', url_for('waiter.view_order', table=table_number)))

@waiter_bp.route('/confirm-order', methods=['POST'])
@check_waiter_auth
def confirm_order():
    table_number = request.form.get('table_number')
    user_id = session.get('userID') or session.get('user_id', 'E02')
    result = WaiterController.process_confirm_order(table_number, user_id)
    if not result.get('success'):
        flash(result.get('message'))
        return redirect(url_for('waiter.view_order', table=table_number))
        
    flash(result.get('message', 'Order sent to kitchen!'))
    return redirect(url_for('waiter.view_tables'))

# ========================== ORDER DETAILS / MANAGEMENT ==========================
@waiter_bp.route('/order-detail', methods=['GET'])
@check_waiter_auth
def order_detail():
    table_number = request.args.get('table')
    if not table_number:
        return redirect(url_for('waiter.view_tables'))
        
    result = WaiterController.get_order_detail_view(table_number)
    if not result.get('success'):
        flash(result.get('message'))
        return redirect(url_for('waiter.view_tables'))
        
    return render_template(
        'waiter/order_detail.html', 
        table_number=table_number,
        order=result.get('order'), 
        items=result.get('items')
    )

@waiter_bp.route('/cancel-order', methods=['POST'])
@check_waiter_auth
def cancel_order_route():
    order_id = request.form.get('order_id')
    user_id = session.get('userID') or session.get('user_id', 'E02')
    
    result = WaiterController.process_cancel_order(order_id, user_id)
    if not result.get('success'):
        flash(result.get('message'))
        # If it failed, stay on the detail page to see why
        table_number = request.form.get('table_number') or request.args.get('table')
        return redirect(url_for('waiter.order_detail', table=table_number))
        
    flash("Order cancelled.")
    return redirect(url_for('waiter.view_tables'))

@waiter_bp.route('/serve-order', methods=['POST'])
@check_waiter_auth
def serve_order_route():
    order_id = request.form.get('order_id')
    user_id = session.get('userID') or session.get('user_id', 'E02')
    
    result = WaiterController.process_serve_order(order_id, user_id)
    if not result.get('success'):
        flash(result.get('message'))
        table_number = request.form.get('table_number') or request.args.get('table')
        return redirect(url_for('waiter.order_detail', table=table_number))
        
    flash("Order marked as Served.")
    return redirect(url_for('waiter.view_tables'))

@waiter_bp.route('/api/notifications', methods=['GET'])
@check_waiter_auth
def api_notifications():
    user_id = session.get('userID') or session.get('user_id', 'E02')
    result = WaiterController.get_notifications(user_id)
    return jsonify(result)


# routes/waiter.py
import uuid
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

import pyodbc
from models.order_model import OrderModel
from flask import Blueprint, render_template, request, redirect, session
from datetime import datetime

# Database connection string to local SQL Server
CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=DESKTOP-BNVCPC1\\SQLEXPRESS01;"
    "DATABASE=RestaurantManagement;"
    "Trusted_Connection=yes;"
)

def get_db_connection():
    """Initialize and return a secure pyodbc database connection."""
    return pyodbc.connect(CONN_STR)

class OrderModel:
    """
    Class handling all database interaction logic.
    All methods are designed as @staticmethod to prevent 
    TypeError exceptions during initialization from the Controller layer.
    """
    
    @staticmethod
    def get_all_dishes():
        """Retrieve available dishes list, integrated with categories from the database."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.dishID, d.name, d.image, d.description, d.ingredients, 
                       d.price, d.isAvailable, c.categoryName
                FROM Dish d 
                JOIN Category c ON d.categoryID = c.categoryID
                WHERE d.isAvailable = 1 
                ORDER BY c.categoryName, d.name
            """)
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def get_all_tables():
        """Get the real-time status of all restaurant tables."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT tableNumber, status FROM RestaurantTable")
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def get_active_order_for_table(table_number):
        """
        Search and return the active order for a table.
        Includes statuses: Draft, Confirmed, Preparing, Ready, Served.
        """
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP 1 orderID, status, orderDate 
                FROM Orders 
                WHERE tableNumber = ? AND status IN ('Draft', 'Confirmed', 'Preparing', 'Ready', 'Served')
                ORDER BY orderDate DESC
            """, (table_number,))
            row = cursor.fetchone()
            if row:
                return {'orderID': row[0].strip(), 'status': row[1].strip(), 'orderDate': row[2]}
            return None
        finally:
            conn.close()

    @staticmethod
    def create_draft_order(table_number, waiter_id):
        """
        Initialize a draft order. This is a dual atomic transaction:
        1. Instantly update table status to 'Occupied'.
        2. Create an order record with status 'Draft'.
        """
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            # Initialize a unique identifier string (6 characters) based on schema
            order_id = f"ORD{str(uuid.uuid4().int)[-6:]}"
            
            cursor.execute("UPDATE RestaurantTable SET status = 'Occupied' WHERE tableNumber = ?", (table_number,))
            cursor.execute("""
                INSERT INTO Orders (orderID, tableNumber, status, orderDate)
                VALUES (?, ?, 'Draft', GETDATE())
            """, (order_id, table_number))
            
            conn.commit() # Commit transaction, ensure data is written to disk
            return order_id
        except Exception as e:
            conn.rollback() # Rollback all changes if any error occurs
            raise e
        finally:
            conn.close()

    @staticmethod
    def add_order_item(order_id, dish_id, quantity=1, special_note=""):
        """
        Add an item to the order.
        Utilizes 'Upsert' (Update or Insert) technique via existence check.
        T-SQL ISNULL function is used to standardize string comparisons.
        """
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            safe_note = special_note.strip() if special_note else ""
         
            cursor.execute("""
                SELECT quantity FROM OrderDetail 
                WHERE orderID = ? AND dishID = ? AND ISNULL(specialNote, '') = ?
            """, (order_id, dish_id, safe_note))
            row = cursor.fetchone()
            
            if row:
                new_qty = int(row[0]) + int(quantity)
                cursor.execute("""
                    UPDATE OrderDetail SET quantity = ? 
                    WHERE orderID = ? AND dishID = ? AND ISNULL(specialNote, '') = ?
                """, (new_qty, order_id, dish_id, safe_note))
            else:
                cursor.execute("""
                    INSERT INTO OrderDetail (orderID, dishID, quantity, specialNote)
                    VALUES (?, ?, ?, ?)
                """, (order_id, dish_id, quantity, safe_note))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def remove_order_item(order_id, dish_id, special_note=""):
        """
        Remove a dish component from the draft cart.
        Automatically checks and cleans up the system (releases table) if the cart is completely empty.
        """
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
         
            safe_note = special_note.strip() if special_note and special_note.lower() != 'none' else ""
            
            cursor.execute("""
                DELETE FROM OrderDetail 
                WHERE orderID = ? AND dishID = ? AND ISNULL(specialNote, '') = ?
            """, (order_id, dish_id, safe_note))
            
            cursor.execute("SELECT COUNT(*) FROM OrderDetail WHERE orderID = ?", (order_id,))
            remaining_items = cursor.fetchone()[0]
            
            order_deleted = False
           
            if remaining_items == 0:
                cursor.execute("SELECT tableNumber, status FROM Orders WHERE orderID = ?", (order_id,))
                o_row = cursor.fetchone()
                if o_row and o_row[1].strip() == 'Draft':
                    t_num = o_row[0]
                    cursor.execute("DELETE FROM Orders WHERE orderID = ?", (order_id,))
                    cursor.execute("UPDATE RestaurantTable SET status = 'Available' WHERE tableNumber = ?", (t_num,))
                    order_deleted = True
                    
            conn.commit()
            return True, order_deleted
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_cart_items(order_id):
        """Query the detailed list of items present in the cart."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.name, od.quantity, od.specialNote, od.dishID 
                FROM OrderDetail od 
                JOIN Dish d ON od.dishID = d.dishID
                WHERE od.orderID = ?
            """, (order_id,))
            
            items = []
            for row in cursor.fetchall():
                items.append({
                    'name': str(row[0]),
                    'quantity': int(row[1]),
                    'note': str(row[2]).strip() if row[2] else "",
                    'dish_id': str(row[3]).strip()
                })
            return items
        finally:
            conn.close()

    @staticmethod
    def confirm_order(order_id):
        """Lock the order, change status to Confirmed to prepare for pushing to the kitchen."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE Orders SET status = 'Confirmed' WHERE orderID = ?", (order_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_cart_items(order_id):
        """Query the detailed list of items present in the cart."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.name, od.quantity, od.specialNote, od.dishID 
                FROM OrderDetail od 
                JOIN Dish d ON od.dishID = d.dishID
                WHERE od.orderID = ?
            """, (order_id,))
        
            items = []
            for row in cursor.fetchall():
                items.append({
                    'name': str(row[0]),
                    'quantity': int(row[1]),
                    'note': str(row[2]).strip() if row[2] else "",
                    'dish_id': str(row[3]).strip()
                })
            return items
        finally:
            conn.close()

# File: controllers/waiter_controller.py
from models.order_model import OrderModel

class WaiterController:
    """
    Central controller class for the Waiter module.
    Receives information from the Router, validates business logic, calls the Model,
    and returns fully structured datasets formatted for the View.
    """

    @staticmethod
    def get_table_map_data():
        """Process the data retrieval flow for the table map."""
        try:
            tables = OrderModel.get_all_tables()
            formatted_tables = []
            for t in tables:
                formatted_tables.append({
                    'TableNumber': t['tableNumber'],
                    'Status': t['status'].strip()
                })
            return {'success': True, 'tables': formatted_tables}
        except Exception as e:
            return {'success': False, 'message': f"System error while loading table map: {str(e)}"}

    @staticmethod
    def get_ordering_view_data(table_number):
        """
        Gather metadata for the ordering view.
        Simultaneously handles the menu list and current cart data.
        Categorization algorithm is directly embedded for UI compatibility.
        """
        try:
            table_num = int(table_number)
            dishes = OrderModel.get_all_dishes()
            
            # Iterate through dishes and refine display format
            for dish in dishes:
                cat = str(dish.get('categoryName', '')).lower()
                dish_name = str(dish.get('name', '')).lower()
                
                # Categorization algorithm based on semantic keywords to map to HTML tabs
                if 'appetizer' in cat or 'khai vị' in dish_name:
                    dish['Category'] = 'appetizers'
                elif 'dessert' in cat or 'tráng miệng' in dish_name:
                    dish['Category'] = 'desserts'
                elif 'drink' in cat or 'beverage' in cat or 'uống' in dish_name:
                    dish['Category'] = 'beverages'
                else:
                    dish['Category'] = 'main-courses'
                    
                dish['DishID'] = dish['dishID'].strip()
                dish['Name'] = dish['name'].strip()
                # Format price with commas according to VN UX standards
                dish['Price'] = f"{dish['price']:,.0f}" if dish['price'] else "0"

            active_order = OrderModel.get_active_order_for_table(table_num)
            cart_items = []
            
            if active_order:
                # Business flow analysis: Allow access and viewing of cart if cooking hasn't started
                if active_order['status'] in ['Draft', 'Confirmed']:
                    cart_items = OrderModel.get_cart_items(active_order['orderID'])

            return {
                'success': True, 
                'dishes': dishes, 
                'cart_items': cart_items,
                'table_number': table_num
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @staticmethod
    def process_add_to_cart(table_number, dish_id, quantity, special_note, user_id):
        """
        Add item business logic: Crucial data security checkpoint.
        Protects the system from unauthorized addition attempts when the order is being prepared.
        """
        try:
            table_num = int(table_number)
            qty = int(quantity)
            
            active_order = OrderModel.get_active_order_for_table(table_num)
            
            # Business Rule Validation Checkpoint (Use-case 4.6)
            if active_order:
                status = active_order['status']
                if status in ['Preparing', 'Ready', 'Served']:
                    return {
                        'success': False, 
                        'message': f"Business Error: Cannot modify because the kitchen is processing (Status: {status})."
                    }
                order_id = active_order['orderID']
            else:
                order_id = OrderModel.create_draft_order(table_num, user_id)
                
            OrderModel.add_order_item(order_id, dish_id, qty, special_note)
            return {'success': True, 'message': 'Item added to cart successfully.'}
        except Exception as e:
            return {'success': False, 'message': f"Database access error: {str(e)}"}

    @staticmethod
    def process_remove_from_cart(table_number, dish_id, special_note):
        """
        Remove item business logic: Smart routing management.
        Returns a routing flag for the View to determine whether to reload the menu or revert to the table map.
        """
        try:
            table_num = int(table_number)
            active_order = OrderModel.get_active_order_for_table(table_num)
            
            if not active_order:
                return {'success': False, 'message': 'Error: This table has no active order.'}
                
            status = active_order['status']
            if status not in ['Draft', 'Confirmed']:
                return {'success': False, 'message': f"Business Error: Cannot remove item when order is in {status} status."}
                
            success, is_empty = OrderModel.remove_order_item(active_order['orderID'], dish_id, special_note)
            
            redirect_url = '/waiter/tables' if is_empty else f'/waiter/order?table={table_num}'
            return {'success': True, 'redirect': redirect_url}
        except Exception as e:
            return {'success': False, 'message': f"Error removing item: {str(e)}"}

    @staticmethod
    def process_confirm_order(table_number):
        """Trigger the process to push order info to the kitchen."""
        try:
            table_num = int(table_number)
            active_order = OrderModel.get_active_order_for_table(table_num)
            
            if not active_order:
                return {'success': False, 'message': 'No order found to confirm.'}
                
            if active_order['status'] == 'Draft':
                OrderModel.confirm_order(active_order['orderID'])
                return {'success': True, 'message': 'Order status updated and sent to kitchen!'}
            else:
                return {'success': False, 'message': f"Cannot re-confirm, order is currently: {active_order['status']}"}
        except Exception as e:
            return {'success': False, 'message': f"Error confirming order: {str(e)}"}

    @staticmethod
    def get_order_detail_view(table_number):
        """Extract and analyze metadata for the order detail view."""
        try:
            table_num = int(table_number)
            active_order = OrderModel.get_active_order_for_table(table_num)
            
            if not active_order:
                return {'success': False, 'message': 'No active order found.'}
                
            details = OrderModel.get_order_details(active_order['orderID'])
            return {'success': True, 'order': details, 'items': details.get('items', [])}
        except Exception as e:
            return {'success': False, 'message': f"Error extracting order details: {str(e)}"}

from flask import Blueprint, render_template, request, redirect, session, flash
from functools import wraps
from controllers.waiter_controller import WaiterController

waiter_bp = Blueprint('waiter', __name__, url_prefix='/waiter')

SECURE_WIFI_PREFIXES = ["192.168.1.", "10.0.0.", "127.0.0.1"]

def require_secure_wifi(f):
    """
    Core network security monitoring middleware.
    Blocks data-altering functions from external IPs.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr
        is_secure = any(client_ip.startswith(prefix) for prefix in SECURE_WIFI_PREFIXES)
        if not is_secure:
            return "Security Error: Blocked. Device must connect to secured local Wi-Fi.", 403
        return f(*args, **kwargs)
    return decorated_function

@waiter_bp.route('/dashboard')
def dashboard():
    """Entry point for the waiter dashboard."""
    if "userID" not in session: return redirect("/")
    return render_template("waiter/dashboard.html")

@waiter_bp.route('/tables')
def view_tables():
    if "userID" not in session: return redirect("/")
    
    if 'table_statuses' not in session:
        session['table_statuses'] = {
            '1': 'Occupied', 
            '2': 'Available', 
            '3': 'Occupied', 
            '4': 'Available', 
            '5': 'Available', 
            '6': 'Occupied'
        }
        
    mock_tables = []
    for table_num, status in session['table_statuses'].items():
        mock_tables.append({
            'TableNumber': int(table_num),
            'Status': status
        })
    return render_template('waiter/table.html', tables=mock_tables)

@waiter_bp.route('/order')
def view_order():
    if "userID" not in session: return redirect("/")
    
    table_number = request.args.get('table', '2')
    if not table_number: return redirect('/waiter/tables')
    
    # Thực đơn món ăn giả lập chuẩn cấu trúc để Frontend tự hiển thị và phân loại tab
    mock_dishes = [
        {'DishID': 'D01', 'Name': 'French Fries', 'Price': '35,000', 'Category': 'appetizers', 'Description': 'Crispy golden potato fries.', 'Ingredients': 'Potato, salt', 'IsAvailable': True},
        {'DishID': 'D02', 'Name': 'Spring Rolls', 'Price': '45,000', 'Category': 'appetizers', 'Description': 'Traditional fried spring rolls.', 'Ingredients': 'Pork, shrimp, mushroom', 'IsAvailable': True},
        {'DishID': 'D03', 'Name': 'Fried Rice', 'Price': '75,000', 'Category': 'main-courses', 'Description': 'Special rice fried with egg and seafood.', 'Ingredients': 'Rice, egg, shrimp, squid', 'IsAvailable': True},
        {'DishID': 'D04', 'Name': 'Beef Steak', 'Price': '180,000', 'Category': 'main-courses', 'Description': 'Premium beef with black pepper sauce.', 'Ingredients': 'Beef, butter, pepper', 'IsAvailable': True},
        {'DishID': 'D05', 'Name': 'Iced Peach Tea', 'Price': '25,000', 'Category': 'beverages', 'Description': 'Refreshing sweet iced peach tea.', 'Ingredients': 'Tea, peach, sugar', 'IsAvailable': True},
        {'DishID': 'D06', 'Name': 'Vanilla Ice Cream', 'Price': '30,000', 'Category': 'desserts', 'Description': 'Cold and creamy vanilla ice cream.', 'Ingredients': 'Milk, vanilla extract', 'IsAvailable': True},
        {'DishID': 'D07', 'Name': 'Sold Out Noodles', 'Price': '60,000', 'Category': 'main-courses', 'Description': 'Delicious pork noodles.', 'Ingredients': 'Noodles, pork', 'IsAvailable': False}
    ]
    
    if 'carts' not in session:
        session['carts'] = {}
        
    # Lấy dữ liệu giỏ hàng của số bàn hiện tại
    table_cart = session['carts'].get(str(table_number), [])
    
    return render_template('waiter/order.html', table_number=table_number, dishes=mock_dishes, cart_items=table_cart)

@waiter_bp.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    table_number = request.form.get('table_number')
    dish_id = request.form.get('dish_id')
    quantity = int(request.form.get('quantity', 1))
    special_note = request.form.get('special_note', '').strip()

    dish_map = {
        'D01': 'French Fries', 
        'D02': 'Spring Rolls', 
        'D03': 'Fried Rice', 
        'D04': 'Beef Steak', 
        'D05': 'Iced Peach Tea', 
        'D06': 'Vanilla Ice Cream', 
        'D07': 'Sold Out Noodles'
    }
    dish_name = dish_map.get(dish_id, "Unknown Dish")

    if 'carts' not in session:
        session['carts'] = {}
    if str(table_number) not in session['carts']:
        session['carts'][str(table_number)] = []

    cart_items = session['carts'][str(table_number)]
 
    found = False
    for item in cart_items:
        if item['dish_id'] == dish_id and item['note'] == special_note:
            item['quantity'] += quantity
            found = True
            break
            
    if not found:
        cart_items.append({
            'name': dish_name,
            'quantity': quantity,
            'note': special_note,
            'dish_id': dish_id
        })
    session['carts'][str(table_number)] = cart_items
    session.modified = True  # Ép Flask lưu lại thay đổi bộ nhớ ngay lập tức
    
    return redirect(f"/waiter/order?table={table_number}")

@waiter_bp.route('/remove-from-cart', methods=['POST'])
def remove_from_cart():
    table_number = request.form.get('table_number')
    dish_id = request.form.get('dish_id')
    special_note = request.form.get('special_note', '').strip()

    if 'carts' in session and str(table_number) in session['carts']:
        cart_items = session['carts'][str(table_number)]
     
        updated_cart = [
            item for item in cart_items 
            if not (str(item['dish_id']) == str(dish_id) and str(item['note']).strip() == special_note)
        ]
        
        session['carts'][str(table_number)] = updated_cart
        session.modified = True  

    return redirect(f"/waiter/order?table={table_number}")

@waiter_bp.route('/confirm-order', methods=['POST'])
def confirm_order():
    table_number = request.form.get('table_number')
    
    if 'table_statuses' not in session:
        session['table_statuses'] = {'1': 'Occupied', '2': 'Available', '3': 'Occupied', '4': 'Available', '5': 'Available', '6': 'Occupied'}
        
    if table_number:
        session['table_statuses'][str(table_number)] = 'Occupied'
        
        if 'carts' in session and str(table_number) in session['carts']:
            session['carts'][str(table_number)] = []
            
        session.modified = True
        
    return redirect("/waiter/tables")

@waiter_bp.route('/order-detail')
def order_detail():
    if "userID" not in session: return redirect("/")
    
    table_number = request.args.get('table', '1')
   
    mock_order_data = {
        'OrderID': f"ORD{table_number}849",
        'Status': 'Ready', 
        'OrderDate': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'TableNumber': table_number
    }

    if 'carts' not in session:
        session['carts'] = {}
    table_cart = session['carts'].get(table_number, [])
    
    mock_items = []
    for item in table_cart:
        mock_items.append({
            'name': item['name'],
            'quantity': item['quantity'],
            'specialNote': item['note'] 
        })
        
    if not mock_items:
        mock_items = [
            {'name': 'Spring Rolls', 'quantity': 1, 'specialNote': 'Spicy sauce'},
            {'name': 'Beef Steak', 'quantity': 1, 'specialNote': 'Medium rare'}
        ]
    return render_template('waiter/order_detail.html', order=mock_order_data, table_number=table_number, items=mock_items)

@waiter_bp.route('/cancel-order', methods=['POST'])
def cancel_order_route():
    table_number = request.form.get('table_number') or request.args.get('table')
    if 'table_statuses' not in session:
        session['table_statuses'] = {'1': 'Occupied', '2': 'Available', '3': 'Occupied', '4': 'Available', '5': 'Available', '6': 'Occupied'}
        
    if table_number:
        session['table_statuses'][str(table_number)] = 'Available'
        if 'carts' in session and str(table_number) in session['carts']:
            session['carts'][str(table_number)] = []
        session.modified = True
    return redirect("/waiter/tables")

@waiter_bp.route('/serve-order', methods=['POST'])
def serve_order_route():
    table_number = request.form.get('table_number') or request.args.get('table')
    
    if 'table_statuses' not in session:
        session['table_statuses'] = {'1': 'Occupied', '2': 'Available', '3': 'Occupied', '4': 'Available', '5': 'Available', '6': 'Occupied'}
        
    if table_number:
        session['table_statuses'][str(table_number)] = 'Available'

    clean_statuses = {}
    for key, value in session['table_statuses'].items():
        clean_statuses[str(key)] = value
        
    session['table_statuses'] = clean_statuses

    if table_number:
        if 'carts' in session and str(table_number) in session['carts']:
            session['carts'][str(table_number)] = []
            
    session.modified = True
    return redirect("/waiter/tables")


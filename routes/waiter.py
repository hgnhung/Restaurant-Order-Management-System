from flask import Blueprint, render_template, request, redirect, session
from database import get_connection
from models.order_model import OrderModel

# Khởi tạo Blueprint khớp với cấu trúc app.py của nhóm
waiter_bp = Blueprint('waiter', __name__, url_prefix='/waiter')

temporary_cart = {}

# 1. Màn hình Dashboard chính của Phục vụ
@waiter_bp.route('/dashboard')
def dashboard():
    if "userID" not in session:
        return redirect("/")
    return render_template("waiter/dashboard.html")

# 2. Chức năng xem sơ đồ bàn ăn (Giao diện: table.html)
@waiter_bp.route('/tables')
def view_tables():
    if "userID" not in session:
        return redirect("/")
        
    conn = get_connection()
    if not conn:
        return "Lỗi kết nối cơ sở dữ liệu!", 500
        
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT tableNumber, status FROM RestaurantTable")
        
        tables = []
        for row in cursor.fetchall():
            tables.append({
                'TableNumber': row[0],  
                'Status': row[1]        
            })
        
        return render_template('waiter/table.html', tables=tables)
    except Exception as e:
        print("Lỗi tải danh sách bàn:", e)
        return "Đã xảy ra lỗi hệ thống!", 500
    finally:
        conn.close()

# 3. Chức năng xem thực đơn gọi món (Giao diện: order.html)
@waiter_bp.route('/order')
def view_order():
    if "userID" not in session:
        return redirect("/")
        
    table_number = request.args.get('table')
    if not table_number:
        return redirect('/waiter/tables')
        
    conn = get_connection()
    if not conn:
        return "Lỗi kết nối cơ sở dữ liệu!", 500
        
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT dishID, name, price FROM Dish WHERE isAvailable = 1")
        
        dishes = []
        for row in cursor.fetchall():
            dishes.append({
                'DishID': row[0],
                'Name': row[1],
                'Price': f"{row[2]:,.0f}"
            })
        
        cart_items = temporary_cart.get(str(table_number), [])
        
        return render_template('waiter/order.html', 
                               table_number=table_number, 
                               dishes=dishes, 
                               cart_items=cart_items)
    except Exception as e:
        print("Lỗi tải thực đơn gọi món:", e)
        return "Đã xảy ra lỗi hệ thống!", 500
    finally:
        conn.close()

# 4. Xử lý khi Waiter bấm nút "Thêm món"
@waiter_bp.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    if "userID" not in session:
        return redirect("/")
        
    table_number = request.form.get('table_number')
    dish_id = request.form.get('dish_id')
    quantity = int(request.form.get('quantity', 1))
    special_note = request.form.get('special_note', '')

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM Dish WHERE dishID = ?", (dish_id,))
        row = cursor.fetchone()
        dish_name = row[0] if row else "Món ăn"
        
        if str(table_number) not in temporary_cart:
            temporary_cart[str(table_number)] = []
            
        temporary_cart[str(table_number)].append({
            'dish_id': dish_id,
            'name': dish_name,
            'quantity': quantity,
            'note': special_note
        })
    except Exception as e:
        print("Lỗi khi thêm món vào giỏ tạm:", e)
    finally:
        if conn: conn.close()
        
    return redirect(f'/waiter/order?table={table_number}')

# 5. Xử lý khi bấm nút "XÁC NHẬN & GỬI XUỐNG BẾP"
@waiter_bp.route('/confirm-order', methods=['POST'])
def confirm_order():
    if "userID" not in session:
        return redirect("/")
        
    table_number = request.form.get('table_number')
    cart_items = temporary_cart.get(str(table_number), [])
    
    if not cart_items:
        return redirect(f'/waiter/order?table={table_number}')
        
    user_id = session.get('userID') 
    
    conn = get_connection()
    if not conn:
        return "Lỗi kết nối cơ sở dữ liệu!", 500
        
    try:
        order_model = OrderModel(conn)
        order_id = order_model.create_order(table_number, user_id)
        
        if order_id:
            for item in cart_items:
                order_model.add_order_details(
                    order_id=order_id, 
                    dish_id=item['dish_id'], 
                    quantity=item['quantity'], 
                    special_note=item['note']
                )
            temporary_cart[str(table_number)] = []
            return redirect('/waiter/tables')
        else:
            return "Lỗi trong quá trình tạo hóa đơn!", 500
            
    except Exception as e:
        print("Lỗi xác nhận đơn hàng:", e)
        return "Lỗi xử lý hệ thống!", 500
    finally:
        conn.close()

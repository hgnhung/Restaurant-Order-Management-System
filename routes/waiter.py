from flask import Blueprint, render_template, request, redirect, session
from database import get_connection
from functools import wraps
from datetime import datetime
import random

waiter_bp = Blueprint('waiter', __name__, url_prefix='/waiter')

# ----------------=========================================================
# CHỐT CHẶN BẢO MẬT: Bộ kiểm tra kết nối mạng Wi-Fi nội bộ (Đúng yêu cầu 4.3.3)
# ----------------=========================================================
SECURE_WIFI_PREFIXES = ["192.168.1.", "10.0.0.", "127.0.0.1"]

def require_secure_wifi(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr
        is_secure = any(client_ip.startswith(prefix) for prefix in SECURE_WIFI_PREFIXES)
        if not is_secure:
            return "Security Error: Action blocked. Device must connect to the restaurant's secured local Wi-Fi.", 403
        return f(*args, **kwargs)
    return decorated_function


# --- MÀN HÌNH VIEW GIAO DIỆN VÀ TRA CỨU ---

@waiter_bp.route('/dashboard')
def dashboard():
    if "userID" not in session: return redirect("/")
    return render_template("waiter/dashboard.html")

@waiter_bp.route('/tables')
def view_tables():
    if "userID" not in session: return redirect("/")
    conn = get_connection()
    if not conn: return "Database connection error!", 500
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
        return "Internal Server Error", 500
    finally:
        conn.close()

@waiter_bp.route('/order')
def view_order():
    if "userID" not in session: return redirect("/")
    table_number = request.args.get('table')
    if not table_number: return redirect('/waiter/tables')
    conn = get_connection()
    if not conn: return "Database connection error!", 500
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT dishID, name, price FROM Dish WHERE isAvailable = 1")
        rows = cursor.fetchall()
        
        dishes = []
        for row in rows:
            dish_id = row[0]
            dish_name = str(row[1])
            dish_price = row[2]
            
            name_lower = dish_name.lower()
            if "fries" in name_lower or "roll" in name_lower or "khai vị" in name_lower:
                detected_category = "appetizers"
            elif "rice" in name_lower or "steak" in name_lower or "món chính" in name_lower:
                detected_category = "main-courses"
            elif "juice" in name_lower or "tea" in name_lower or "uống" in name_lower:
                detected_category = "beverages"
            else:
                detected_category = "main-courses"

            dishes.append({
                'DishID': dish_id,
                'Name': dish_name,
                'Price': f"{dish_price:,.0f}" if dish_price else "0",
                'Category': detected_category,
                'Description': 'Fresh and delicious restaurant specialty.', 
                'Ingredients': 'Standard fresh local ingredients',
                'IsAvailable': True
            })

        # SỬA LỖI NAMEERROR: Quét trực tiếp qua cursor thô an toàn
        query_cart = """
            SELECT d.name, od.quantity, od.specialNote, od.dishID 
            FROM OrderDetail od 
            JOIN Dish d ON od.dishID = d.dishID
            JOIN Orders o ON od.orderID = o.orderID
            WHERE o.tableNumber = ? AND o.status IN ('Draft', 'Confirmed', 'Preparing', 'Ready')
        """
        cursor.execute(query_cart, (int(table_number),))
        cart_items = []
        for row in cursor.fetchall():
            cart_items.append({
                'name': str(row[0]),
                'quantity': int(row[1]),
                'note': str(row[2]).strip() if row[2] else "",
                'dish_id': str(row[3]).strip()
            })
            
        return render_template('waiter/order.html', table_number=table_number, dishes=dishes, cart_items=cart_items)
    except Exception as e:
        print("--- LỖI TẠI HÀM VIEW_ORDER ---:", e)
        return "Internal Server Error", 500
    finally:
        conn.close()


# --- API HÀNH ĐỘNG THAO TÁC DỮ LIỆU (ĐỘC LẬP QUA SQL THÔ) ---

@waiter_bp.route('/add-to-cart', methods=['POST'])
@require_secure_wifi  
def add_to_cart():
    if "userID" not in session: return redirect("/")
    table_number = request.form.get('table_number')
    dish_id = request.form.get('dish_id')
    quantity = int(request.form.get('quantity', 1))
    special_note = request.form.get('special_note', '')
    user_id = session.get('userID')
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TOP 1 orderID, status 
            FROM Orders 
            WHERE tableNumber = ? AND status IN ('Draft', 'Confirmed', 'Preparing', 'Ready', 'Served')
            ORDER BY orderDate DESC
        """, (int(table_number),))
        row = cursor.fetchone()
        
        if row:
            order_id = row[0]
            current_status = str(row[1]).strip()
            
            # CHỐT CHẶN TRẠNG THÁI (Yêu cầu 4.6): Từ chối sửa nếu bếp đang nấu trở đi
            if current_status in ["Preparing", "Ready", "Served"]:
                return f"Action Prohibited: The kitchen has already started processing this table (Status: '{current_status}').", 400
        else:
            from models.order_model import OrderModel
            order_model = OrderModel(conn)
            order_id = order_model.create_order(table_number, user_id)
            cursor.execute("UPDATE Orders SET status = 'Draft' WHERE orderID = ?", (str(order_id),))

        cursor.execute("SELECT quantity FROM OrderDetail WHERE orderID = ? AND dishID = ?", (str(order_id), str(dish_id)))
        od_row = cursor.fetchone()
        
        if od_row:
            new_quantity = int(od_row[0]) + int(quantity)
            cursor.execute("UPDATE OrderDetail SET quantity = ?, specialNote = ? WHERE orderID = ? AND dishID = ?", (new_quantity, str(special_note), str(order_id), str(dish_id)))
        else:
            cursor.execute("INSERT INTO OrderDetail (orderID, dishID, quantity, specialNote) VALUES (?, ?, ?, ?)", (str(order_id), str(dish_id), int(quantity), str(special_note)))
            
        conn.commit()
    except Exception as e:
        print("Lỗi thêm món:", e)
        if conn: conn.rollback()
    finally:
        conn.close()
    return redirect(f'/waiter/order?table={table_number}')

@waiter_bp.route('/confirm-order', methods=['POST'])
@require_secure_wifi
def confirm_order():
    if "userID" not in session: return redirect("/")
    table_number = request.form.get('table_number')
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT TOP 1 orderID FROM Orders WHERE tableNumber = ? AND status = 'Draft' ORDER BY orderDate DESC", (int(table_number),))
        row = cursor.fetchone()
        if row:
            cursor.execute("UPDATE Orders SET status = 'Confirmed' WHERE orderID = ?", (str(row[0]),))
            conn.commit()
    except Exception as e:
        print("Lỗi chốt đơn:", e)
    finally:
        conn.close()
    return redirect('/waiter/tables')

@waiter_bp.route('/remove-from-cart', methods=['POST'])
@require_secure_wifi
def remove_from_cart():
    if "userID" not in session: return redirect("/")
    table_number = request.form.get('table_number')
    dish_id = request.form.get('dish_id') 
    special_note = request.form.get('special_note', '').strip()
    if special_note.lower() == 'none' or special_note == '': special_note = ''
        
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT TOP 1 orderID FROM Orders WHERE tableNumber = ? AND status IN ('Draft', 'Confirmed') ORDER BY orderDate DESC", (int(table_number),))
        row = cursor.fetchone()
        if row:
            order_id = row[0]
            cursor.execute("""
                DELETE FROM OrderDetail 
                WHERE orderID = ? AND dishID = ? 
                  AND (
                      (? = '' AND (specialNote IS NULL OR LTRIM(RTRIM(specialNote)) = ''))
                      OR 
                      (? <> '' AND LTRIM(RTRIM(specialNote)) = LTRIM(RTRIM(?)))
                  )
            """, (str(order_id), str(dish_id), str(special_note), str(special_note), str(special_note)))
            conn.commit()
    except Exception as e:
        print("Lỗi xóa món:", e)
    finally:
        conn.close()
    return redirect(f'/waiter/order?table={table_number}')

@waiter_bp.route('/order-detail')
def order_detail():
    if "userID" not in session: return redirect("/")
    table_number = request.args.get('table')
    conn = get_connection()
    if not conn: return "Database connection error!", 500
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TOP 1 orderID, status, orderDate 
            FROM Orders 
            WHERE tableNumber = ? AND status IN ('Confirmed', 'Preparing', 'Ready', 'Served')
            ORDER BY orderDate DESC
        """, (int(table_number),))
        order_row = cursor.fetchone()
        
        order_data = None
        items = []
                # --- ĐOẠN KHỐI LỆNH SỬA LỖI TRONG HÀM ORDER_DETAIL ---
        if order_row:
            order_id = order_row[0] # Trích xuất mã ID chuỗi sạch thô (6 ký tự)
            
            order_data = {
                'OrderID': order_id,
                'Status': str(order_row[1]).strip(),
                'OrderDate': order_row[2].strftime("%Y-%m-%d %H:%M:%S") if order_row[2] else "",
                'TableNumber': table_number
            }
            
            query = """
                SELECT d.name, od.quantity, od.specialNote 
                FROM OrderDetail od 
                JOIN Dish d ON od.dishID = d.dishID 
                WHERE od.orderID = ?
            """
            cursor.execute(query, (str(order_id),)) # ĐÃ SỬA: Truyền biến order_id đã gột sạch
            
            for r in cursor.fetchall():
                items.append({
                    'name': str(r[0]),
                    'quantity': int(r[1]),
                    'specialNote': str(r[2]).strip() if r[2] else ""
                })
                
        return render_template('waiter/order_detail.html', order=order_data, table_number=table_number, items=items)
    except Exception as e:
        print("Lỗi xem chi tiết đơn:", e)
        return "Internal Server Error", 500
    finally:
        conn.close() # Đảm bảo đóng kết nối an toàn để giải phóng RAM

# ----------------=========================================================
# 8. Chức năng Hủy đơn hàng an toàn (Có chốt chặn kiểm tra trạng thái bếp)
# ----------------=========================================================
@waiter_bp.route('/cancel-order', methods=['POST'])
@require_secure_wifi # Chốt chặn Wi-Fi nội bộ nhà hàng
def cancel_order_route():
    if "userID" not in session: return redirect("/")
    order_id = request.form.get('order_id')
    conn = get_connection()
    if not conn: return "Database connection error!", 500
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT status, tableNumber FROM Orders WHERE orderID = ?", (str(order_id),))
        row = cursor.fetchone()
        
        if row:
            current_status = str(row[0]).strip()
            table_num = row[1]
            
            # CHỐT CHẶN NGHIỆP VỤ: Nếu bếp đã bắt đầu xử lý nấu nướng -> Từ chối thẳng thừng!
            if current_status not in ["Draft", "Confirmed"]:
                return f"Action Denied: Cannot cancel order. Kitchen is currently processing this items (Status: {current_status}).", 400
                
            cursor.execute("UPDATE Orders SET status = 'Cancelled' WHERE orderID = ?", (str(order_id),))
            cursor.execute("UPDATE RestaurantTable SET status = 'Available' WHERE tableNumber = ?", (int(table_num),))
            conn.commit() # Lưu thay đổi vĩnh viễn xuống SQL Server
    except Exception as e:
        print("Lỗi hủy đơn:", e)
        if conn: conn.rollback()
    finally:
        conn.close()
    return redirect('/waiter/tables')

# ----------------=========================================================
# 9. Chức năng Đã phục vụ món ra bàn (Served) - Tự động giải phóng bàn
# ----------------=========================================================
@waiter_bp.route('/serve-order', methods=['POST'])
@require_secure_wifi
def serve_order_route():
    if "userID" not in session: return redirect("/")
    order_id = request.form.get('order_id')
    conn = get_connection()
    if not conn: return "Database connection error!", 500
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT tableNumber FROM Orders WHERE orderID = ?", (str(order_id),))
        row = cursor.fetchone()
        
        cursor.execute("UPDATE Orders SET status = 'Served' WHERE orderID = ?", (str(order_id),))
        if row:
            table_num = row[0]
            cursor.execute("UPDATE RestaurantTable SET status = 'Available' WHERE tableNumber = ?", (int(table_num),))
            
        conn.commit()
    except Exception as e:
        print("Lỗi bưng món:", e)
        if conn: conn.rollback()
    finally:
        conn.close()
    return redirect('/waiter/tables')


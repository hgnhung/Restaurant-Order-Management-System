# waiter_controller.py
import pyodbc
import uuid
import logging

logger = logging.getLogger(__name__)

DB_CONNECTION = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=RestaurantManagement;"
    "Trusted_Connection=yes;"
)

def get_db_connection():
    return pyodbc.connect(DB_CONNECTION)

# ========================== MENU ==========================
def get_menu_categories():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT categoryID, categoryName, description FROM Category WHERE status = 'Active' ORDER BY categoryName")
        return [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    finally:
        conn.close()

def get_dishes_by_category(category_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT dishID, name, image, description, ingredients, price, isAvailable
            FROM Dish WHERE categoryID = ? AND isAvailable = 1 ORDER BY name
        """, category_id)
        return [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    finally:
        conn.close()

def search_dishes(keyword):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT dishID, name, image, description, ingredients, price, isAvailable 
            FROM Dish WHERE name LIKE ? AND isAvailable = 1
        """, f'%{keyword}%')
        return [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    finally:
        conn.close()

# ========================== TABLE & ORDER ==========================
def get_tables():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT tableNumber, status FROM RestaurantTable ORDER BY tableNumber")
        return [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    finally:
        conn.close()

def create_order(table_number, user_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM RestaurantTable WHERE tableNumber = ?", table_number)
        row = cursor.fetchone()
        if not row or row[0] != 'Available':
            return {"success": False, "message": "Table is not available"}

        order_id = f"ORD{str(uuid.uuid4().int)[:6].upper()}"
        cursor.execute("INSERT INTO Orders (orderID, tableNumber, status, orderDate) VALUES (?, ?, 'Pending', GETDATE())", order_id, table_number)
        cursor.execute("UPDATE RestaurantTable SET status = 'Occupied' WHERE tableNumber = ?", table_number)
        
        conn.commit()
        logger.info(f"Order {order_id} created for table {table_number}")
        return {"success": True, "orderID": order_id, "message": "Order created successfully"}
    except Exception as e:
        conn.rollback()
        logger.error(f"Create order error: {e}")
        return {"success": False, "message": "Internal server error"}
    finally:
        conn.close()

def get_active_orders():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.orderID, o.tableNumber, o.status, o.orderDate, COUNT(od.dishID) as itemCount
            FROM Orders o LEFT JOIN OrderDetail od ON o.orderID = od.orderID
            WHERE o.status IN ('Pending', 'Confirmed', 'Preparing', 'Ready', 'Served')
            GROUP BY o.orderID, o.tableNumber, o.status, o.orderDate
            ORDER BY o.orderDate DESC
        """)
        return [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    finally:
        conn.close()

def get_order_details(order_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT orderID, tableNumber, status, orderDate FROM Orders WHERE orderID = ?", order_id)
        row = cursor.fetchone()
        if not row:
            return None
        order = dict(zip([col[0] for col in cursor.description], row))

        cursor.execute("""
            SELECT d.dishID, d.name, d.price, od.quantity, od.specialNote
            FROM OrderDetail od JOIN Dish d ON od.dishID = d.dishID WHERE od.orderID = ?
        """, order_id)
        order['items'] = [dict(zip([col[0] for col in cursor.description], r)) for r in cursor.fetchall()]
        return order
    finally:
        conn.close()

# ========================== ITEM OPERATIONS ==========================
def add_item_to_order(order_id, dish_id, quantity=1, special_note=None):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM Orders WHERE orderID = ?", order_id)
        row = cursor.fetchone()
        if not row or row[0] not in ['Pending', 'Confirmed']:
            return {"success": False, "message": "Cannot add items"}

        cursor.execute("""
            MERGE OrderDetail AS target USING (VALUES (?, ?, ?, ?)) AS source 
            ON target.orderID = source.orderID AND target.dishID = source.dishID
            WHEN MATCHED THEN UPDATE SET quantity = target.quantity + ?, specialNote = ?
            WHEN NOT MATCHED THEN INSERT VALUES (?, ?, ?, ?)
        """, order_id, dish_id, quantity, special_note, quantity, special_note, order_id, dish_id, quantity, special_note)
        conn.commit()
        return {"success": True, "message": "Item added"}
    except Exception:
        conn.rollback()
        return {"success": False, "message": "Failed to add item"}
    finally:
        conn.close()

def remove_item_from_order(order_id, dish_id, user_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM Orders WHERE orderID = ?", order_id)
        row = cursor.fetchone()
        if not row or row[0] not in ['Pending', 'Confirmed']:
            return {"success": False, "message": "Cannot modify order"}

        cursor.execute("DELETE FROM OrderDetail WHERE orderID = ? AND dishID = ?", order_id, dish_id)
        conn.commit()
        return {"success": True, "message": "Item removed"}
    except Exception:
        conn.rollback()
        return {"success": False, "message": "Failed to remove item"}
    finally:
        conn.close()

# Các hàm confirm_order, modify_order, cancel_order, update_order_status_to_served, get_notifications giữ nguyên như phiên bản trước (đã ổn)

def confirm_order(order_id, user_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM Orders WHERE orderID = ?", order_id)
        row = cursor.fetchone()
        if not row or row[0] != 'Pending':
            return {"success": False, "message": "Only Pending orders can be confirmed"}

        cursor.execute("SELECT COUNT(*) FROM OrderDetail WHERE orderID = ?", order_id)
        if cursor.fetchone()[0] == 0:
            return {"success": False, "message": "Cannot confirm empty order"}

        cursor.execute("UPDATE Orders SET status = 'Confirmed' WHERE orderID = ?", order_id)
        conn.commit()
        return {"success": True, "message": "Order confirmed"}
    except Exception:
        conn.rollback()
        return {"success": False, "message": "Internal error"}
    finally:
        conn.close()

def modify_order(order_id, items, user_id):
    if not items:
        return {"success": False, "message": "No items provided"}
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM Orders WHERE orderID = ?", order_id)
        row = cursor.fetchone()
        if not row or row[0] not in ['Pending', 'Confirmed']:
            return {"success": False, "message": "Cannot modify order"}

        cursor.execute("DELETE FROM OrderDetail WHERE orderID = ?", order_id)
        for item in items:
            if item.get('quantity', 0) > 0:
                cursor.execute("INSERT INTO OrderDetail (orderID, dishID, quantity, specialNote) VALUES (?, ?, ?, ?)",
                             (order_id, item['dishID'], item['quantity'], item.get('specialNote')))
        conn.commit()
        return {"success": True, "message": "Order modified successfully"}
    except Exception:
        conn.rollback()
        return {"success": False, "message": "Internal error"}
    finally:
        conn.close()

def cancel_order(order_id, user_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT status, tableNumber FROM Orders WHERE orderID = ?", order_id)
        row = cursor.fetchone()
        if not row or row[0] not in ['Pending', 'Confirmed']:
            return {"success": False, "message": "Cannot cancel order"}

        cursor.execute("UPDATE Orders SET status = 'Cancelled' WHERE orderID = ?", order_id)
        cursor.execute("UPDATE RestaurantTable SET status = 'Available' WHERE tableNumber = ?", row[1])
        conn.commit()
        return {"success": True, "message": "Order cancelled"}
    except Exception:
        conn.rollback()
        return {"success": False, "message": "Internal error"}
    finally:
        conn.close()

def update_order_status_to_served(order_id, user_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM Orders WHERE orderID = ?", order_id)
        row = cursor.fetchone()
        if not row or row[0] != 'Ready':
            return {"success": False, "message": "Order must be Ready"}

        cursor.execute("UPDATE Orders SET status = 'Served' WHERE orderID = ?", order_id)
        conn.commit()
        return {"success": True, "message": "Order marked as Served"}
    except Exception:
        conn.rollback()
        return {"success": False, "message": "Internal error"}
    finally:
        conn.close()

def get_notifications(user_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT orderID, tableNumber FROM Orders WHERE status = 'Ready' ORDER BY orderDate DESC")
        return [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    finally:
        conn.close()
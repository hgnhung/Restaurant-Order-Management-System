import pyodbc
import uuid

# ====================== KẾT NỐI ======================
CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=DESKTOP-BNVCPC1\\SQLEXPRESS01;"
    "DATABASE=RestaurantManagement;"
    "Trusted_Connection=yes;"
)

def get_db_connection():
    return pyodbc.connect(CONN_STR)

# =====================================================

class OrderModel:
    
    @staticmethod
    def get_all_dishes():
        conn = get_db_connection()
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
        dishes = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return dishes

    @staticmethod
    def get_categories():
        """Lấy danh sách category"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Category WHERE status = 'Active'")
        columns = [column[0] for column in cursor.description]
        categories = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return categories

    @staticmethod
    def search_dishes(keyword):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.*, c.categoryName 
            FROM Dish d 
            JOIN Category c ON d.categoryID = c.categoryID
            WHERE d.name LIKE ? AND d.isAvailable = 1
        """, (f'%{keyword}%',))
        columns = [column[0] for column in cursor.description]
        dishes = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return dishes

    @staticmethod
    def get_all_tables():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT tableNumber, status FROM RestaurantTable")
        columns = [column[0] for column in cursor.description]
        tables = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return tables

    @staticmethod
    def create_order(table_number, waiter_id='E02'):
        conn = get_db_connection()
        cursor = conn.cursor()
        order_id = f"ORD{str(uuid.uuid4().int)[-6:]}"
        
        cursor.execute("UPDATE RestaurantTable SET status = 'Occupied' WHERE tableNumber = ?", (table_number,))
        
        cursor.execute("""
            INSERT INTO Orders (orderID, tableNumber, status, orderDate)
            VALUES (?, ?, 'Pending', GETDATE())
        """, (order_id, table_number))
        
        conn.commit()
        conn.close()
        return order_id

    @staticmethod
    def add_order_item(order_id, dish_id, quantity=1, special_note=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT status FROM Orders WHERE orderID = ?", (order_id,))
        result = cursor.fetchone()
        if not result or result[0] not in ['Pending', 'Confirmed']:
            conn.close()
            return False
        
        cursor.execute("""
            INSERT INTO OrderDetail (orderID, dishID, quantity, specialNote)
            VALUES (?, ?, ?, ?)
        """, (order_id, dish_id, quantity, special_note))
        
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def get_order_details(order_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT o.*, t.status as table_status 
            FROM Orders o 
            JOIN RestaurantTable t ON o.tableNumber = t.tableNumber
            WHERE o.orderID = ?
        """, (order_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        columns = [column[0] for column in cursor.description]
        order = dict(zip(columns, row))
        
        cursor.execute("""
            SELECT od.*, d.name, d.price 
            FROM OrderDetail od 
            JOIN Dish d ON od.dishID = d.dishID
            WHERE od.orderID = ?
        """, (order_id,))
        columns = [column[0] for column in cursor.description]
        order['items'] = [dict(zip(columns, r)) for r in cursor.fetchall()]
        
        conn.close()
        return order

    @staticmethod
    def confirm_order(order_id, waiter_id='E02'):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Orders SET status = 'Confirmed' WHERE orderID = ?", (order_id,))
        conn.commit()
        conn.close()
        return True
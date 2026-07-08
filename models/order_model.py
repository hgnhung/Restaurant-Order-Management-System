import pyodbc
import uuid
from database import get_connection

class OrderModel:
    
    @staticmethod
    def get_all_dishes():
        conn = get_connection()
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
    def get_categories():
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Category WHERE status = 'Active'")
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def search_dishes(keyword):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.dishID, d.name, d.image, d.description, d.ingredients, 
                       d.price, d.isAvailable, c.categoryName 
                FROM Dish d 
                JOIN Category c ON d.categoryID = c.categoryID
                WHERE d.name LIKE ? AND d.isAvailable = 1
            """, (f'%{keyword}%',))
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def get_all_tables():
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT tableNumber, status FROM RestaurantTable")
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def get_active_order_for_table(table_number):
        conn = get_connection()
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
    def create_draft_order(table_number, waiter_id='E02'):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            # Generate sequential orderID (e.g. ORD011) to fit VARCHAR(6)
            cursor.execute("SELECT MAX(CAST(SUBSTRING(orderID, 4, 3) AS INT)) FROM Orders WHERE orderID LIKE 'ORD%'")
            max_num = cursor.fetchone()[0]
            if max_num is None:
                max_num = 0
            order_id = f"ORD{max_num + 1:03d}"
            
            cursor.execute("UPDATE RestaurantTable SET status = 'Occupied' WHERE tableNumber = ?", (table_number,))
            cursor.execute("""
                INSERT INTO Orders (orderID, tableNumber, status, orderDate)
                VALUES (?, ?, 'Draft', GETDATE())
            """, (order_id, table_number))
            
            conn.commit()
            return order_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def add_order_item(order_id, dish_id, quantity=1, special_note=""):
        conn = get_connection()
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
    def update_order_item_qty(order_id, dish_id, special_note, new_quantity):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            safe_note = special_note.strip() if special_note and special_note.lower() != 'none' else ""
            
            if new_quantity <= 0:
                # Same logic as remove
                cursor.execute("""
                    DELETE FROM OrderDetail 
                    WHERE orderID = ? AND dishID = ? AND ISNULL(specialNote, '') = ?
                """, (order_id, dish_id, safe_note))
                
                cursor.execute("SELECT COUNT(*) FROM OrderDetail WHERE orderID = ?", (order_id,))
                if cursor.fetchone()[0] == 0:
                    cursor.execute("SELECT tableNumber FROM Orders WHERE orderID = ?", (order_id,))
                    t_row = cursor.fetchone()
                    if t_row:
                        cursor.execute("DELETE FROM Orders WHERE orderID = ?", (order_id,))
                        cursor.execute("UPDATE RestaurantTable SET status = 'Available' WHERE tableNumber = ?", (t_row[0],))
                        return True, True # is_empty = True
                return True, False
            else:
                cursor.execute("""
                    UPDATE OrderDetail SET quantity = ? 
                    WHERE orderID = ? AND dishID = ? AND ISNULL(specialNote, '') = ?
                """, (new_quantity, order_id, dish_id, safe_note))
                
                conn.commit()
                return True, False
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def remove_order_item(order_id, dish_id, special_note=""):
        conn = get_connection()
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
        conn = get_connection()
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
    def get_order_details(order_id):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT o.*, t.status as table_status 
                FROM Orders o 
                JOIN RestaurantTable t ON o.tableNumber = t.tableNumber
                WHERE o.orderID = ?
            """, (order_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            columns = [column[0] for column in cursor.description]
            order = dict(zip(columns, row))
            
            # Use same return structure as get_cart_items for the frontend consistency
            cursor.execute("""
                SELECT d.name, od.quantity, od.specialNote, od.dishID 
                FROM OrderDetail od 
                JOIN Dish d ON od.dishID = d.dishID
                WHERE od.orderID = ?
            """, (order_id,))
            
            items = []
            for r in cursor.fetchall():
                 items.append({
                    'name': str(r[0]),
                    'quantity': int(r[1]),
                    'specialNote': str(r[2]).strip() if r[2] else "",
                    'dishID': str(r[3]).strip()
                })
            order['items'] = items
            return order
        finally:
            conn.close()

    @staticmethod
    def get_notifications(user_id=None):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT orderID, tableNumber FROM Orders WHERE status = 'Ready' ORDER BY orderDate DESC")
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def confirm_order(order_id):
        conn = get_connection()
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
    def cancel_order(order_id, waiter_id='E02'):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT status, tableNumber FROM Orders WHERE orderID = ?", (order_id,))
            row = cursor.fetchone()
            if not row or row[0].strip() not in ['Draft', 'Confirmed']:
                return False
            
            cursor.execute("UPDATE Orders SET status = 'Cancelled' WHERE orderID = ?", (order_id,))
            cursor.execute("UPDATE RestaurantTable SET status = 'Available' WHERE tableNumber = ?", (row[1],))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def update_to_served(order_id, waiter_id='E02'):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT status, tableNumber FROM Orders WHERE orderID = ?", (order_id,))
            row = cursor.fetchone()
            if not row or row[0].strip() != 'Ready':
                return False
            
            cursor.execute("UPDATE Orders SET status = 'Served' WHERE orderID = ?", (order_id,))
            cursor.execute("UPDATE RestaurantTable SET status = 'Available' WHERE tableNumber = ?", (row[1],))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
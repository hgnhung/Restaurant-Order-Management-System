import pyodbc
from datetime import datetime
import random

class OrderModel:
    def __init__(self, db_connection):
        self.conn = db_connection

    def create_order(self, table_number, user_id):
        try:
            cursor = self.conn.cursor()
            
            # Generate a strictly 6-character orderID to match char(6) constraint in SSMS
            order_id = "ORD" + "".join(random.choices("0123456789", k=3))
            order_date = datetime.now()
            status = "Confirmed"
            
            # Execute insert query matching the group's current Orders table structure
            insert_query = """
                INSERT INTO Orders (orderID, tableNumber, status, orderDate) 
                VALUES (?, ?, ?, ?)
            """
            cursor.execute(insert_query, (str(order_id), int(table_number), str(status), order_date))
            
            # Synchronize table status to Occupied inside RestaurantTable
            sql_table = "UPDATE RestaurantTable SET status = 'Occupied' WHERE tableNumber = ?"
            cursor.execute(sql_table, (int(table_number),))
            
            self.conn.commit()
            return order_id
        except Exception as e:
            print("--- CREATE ORDER ERROR ---:", e)
            self.conn.rollback()
            return None

    def add_order_details(self, order_id, dish_id, quantity, special_note=""):
        try:
            cursor = self.conn.cursor()
            # Execute insert query matching the group's current OrderDetail table structure
            sql = "INSERT INTO OrderDetail (orderID, dishID, quantity, specialNote) VALUES (?, ?, ?, ?)"
            cursor.execute(sql, (order_id, dish_id, int(quantity), str(special_note)))
            self.conn.commit()
            return True
        except Exception as e:
            print("--- ADD ORDER DETAILS ERROR ---:", e)
            self.conn.rollback()
            return False

    def add_order_details(self, order_id, dish_id, quantity, special_note=""):
        try:
            cursor = self.conn.cursor()
            
            # 1. Check if this dish already exists in the current order to avoid primary key conflicts
            cursor.execute("SELECT quantity FROM OrderDetail WHERE orderID = ? AND dishID = ?", (str(order_id), str(dish_id)))
            row = cursor.fetchone()
            
            if row:
                # If the dish exists, update and accumulate the quantity safely
                new_quantity = int(row[0]) + int(quantity)
                sql_update = "UPDATE OrderDetail SET quantity = ?, specialNote = ? WHERE orderID = ? AND dishID = ?"
                cursor.execute(sql_update, (new_quantity, str(special_note), str(order_id), str(dish_id)))
            else:
                # If it's a new dish, insert it normally
                sql_insert = "INSERT INTO OrderDetail (orderID, dishID, quantity, specialNote) VALUES (?, ?, ?, ?)"
                cursor.execute(sql_insert, (str(order_id), str(dish_id), int(quantity), str(special_note)))
                
            self.conn.commit()
            return True
        except Exception as e:
            print("--- ADD ORDER DETAILS ERROR ---:", e)
            self.conn.rollback()
            return False

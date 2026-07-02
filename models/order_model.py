import pyodbc
from datetime import datetime

class OrderModel:
    def __init__(self, db_connection):
        self.conn = db_connection

    def create_order(self, table_number, user_id):
        try:
            cursor = self.conn.cursor()
            import random
            order_id = "".join(random.choices("0123456789", k=5))
            order_date = datetime.now()
            status = "Confirmed"
            cursor.execute("INSERT INTO Orders (orderID, tableNumber, status, orderDate) VALUES (?, ?, ?, ?)", (str(order_id), int(table_number), str(status), order_date))
            cursor.execute("UPDATE RestaurantTable SET status = 'Occupied' WHERE tableNumber = ?", (int(table_number),))
            self.conn.commit()
            return order_id
        except Exception as e:
            print("--- LOI TAO DON THUC TE ---:", e)
            self.conn.rollback()
            return None

    def add_order_details(self, order_id, dish_id, quantity, special_note=""):
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO OrderDetail (orderID, dishID, quantity, specialNote) VALUES (?, ?, ?, ?)", (str(order_id), str(dish_id), int(quantity), str(special_note)))
            self.conn.commit()
            return True
        except Exception as e:
            print("--- LOI THEM CHI TIET THUC TE ---:", e)
            self.conn.rollback()
            return False

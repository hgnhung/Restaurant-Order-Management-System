from flask import session, redirect
from database import get_connection
from models.order_model import OrderModel


class WaiterController:
    """
    Controller for Waiter module 
    """

    def __init__(self):
        self.temporary_cart = {}  # Temporary cart stored in memory (per table)

    def check_auth(self):
        """Check if user is authenticated"""
        if "userID" not in session:
            return redirect("/")
        return None

    def get_tables(self):
        """Get list of all tables with their status"""
        auth_redirect = self.check_auth()
        if auth_redirect:
            return None, "Authentication required"

        conn = get_connection()
        if not conn:
            return None, "Database connection error!"

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT tableNumber, status FROM RestaurantTable")
            tables = []
            for row in cursor.fetchall():
                tables.append({
                    'TableNumber': row[0],
                    'Status': row[1]
                })
            return tables, None
        except Exception as e:
            print("Error loading tables:", e)
            return None, "Internal Server Error"
        finally:
            if conn:
                conn.close()

    def get_dishes_and_cart(self, table_number):
        """Get available dishes and current cart for a table"""
        auth_redirect = self.check_auth()
        if auth_redirect:
            return None, None, auth_redirect

        if not table_number:
            return None, None, redirect('/waiter/tables')

        conn = get_connection()
        if not conn:
            return None, None, "Database connection error!"

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

            cart_items = self.temporary_cart.get(str(table_number), [])
            return dishes, cart_items, None
        except Exception as e:
            print("Error loading menu:", e)
            return None, None, "Internal Server Error"
        finally:
            if conn:
                conn.close()

    def add_to_cart(self, table_number, dish_id, quantity=1, special_note=""):
        """Add a dish to the temporary cart"""
        auth_redirect = self.check_auth()
        if auth_redirect:
            return auth_redirect

        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM Dish WHERE dishID = ?", (dish_id,))
            row = cursor.fetchone()
            dish_name = row[0] if row else "Unknown Dish"

            if str(table_number) not in self.temporary_cart:
                self.temporary_cart[str(table_number)] = []

            self.temporary_cart[str(table_number)].append({
                'dish_id': dish_id,
                'name': dish_name,
                'quantity': int(quantity),
                'note': special_note
            })
            return None  # Success
        except Exception as e:
            print("Error adding to cart:", e)
            return "Error adding item to cart"
        finally:
            if conn:
                conn.close()

    def confirm_order(self, table_number):
        """Confirm order and save to database"""
        auth_redirect = self.check_auth()
        if auth_redirect:
            return None, "Authentication required"

        cart_items = self.temporary_cart.get(str(table_number), [])
        if not cart_items:
            return None, "Cart is empty"

        user_id = session.get('userID')
        conn = get_connection()
        if not conn:
            return None, "Database connection error!"

        try:
            order_model = OrderModel(conn)
            order_id = order_model.create_order(table_number, user_id)

            if order_id:
                for item in cart_items:
                    order_model.add_order_details(
                        order_id=order_id,
                        dish_id=item['dish_id'],
                        quantity=int(item['quantity']),
                        special_note=str(item.get('note', ''))
                    )
                # Clear cart after successful order
                self.temporary_cart[str(table_number)] = []
                return order_id, None
            else:
                return None, "Failed to create order"
        except Exception as e:
            print("--- CONFIRM ORDER ERROR ---:", e)
            return None, "System processing error"
        finally:
            if conn:
                conn.close()

    def get_order_detail(self, table_number):
        """Get detailed items of an order for a specific table"""
        auth_redirect = self.check_auth()
        if auth_redirect:
            return None, auth_redirect

        conn = get_connection()
        if not conn:
            return None, "Database connection error!"

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT orderID FROM Orders 
                WHERE tableNumber = ? AND status = 'Confirmed'
            """, (int(table_number),))
            
            row = cursor.fetchone()
            order_id = row[0] if row else None

            items = []
            if order_id:
                query = """
                    SELECT d.name, od.quantity, od.specialNote 
                    FROM OrderDetail od
                    JOIN Dish d ON od.dishID = d.dishID
                    WHERE od.orderID = ?
                """
                cursor.execute(query, (order_id,))
                for r in cursor.fetchall():
                    items.append({
                        'name': r[0],
                        'quantity': r[1],
                        'specialNote': r[2]
                    })
            return items, None
        except Exception as e:
            print("--- VIEW ORDER DETAIL ERROR ---:", e)
            return None, "Internal Server Error"
        finally:
            if conn:
                conn.close()
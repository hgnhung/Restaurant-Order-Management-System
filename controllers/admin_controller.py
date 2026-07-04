# admin_controller.py
import random
import string
from database import get_connection
from models.menu_model import Dish
from models.report_model import RevenueReport
from datetime import datetime

class AdminController:
    def __init__(self):
        pass

    def log_action(self, user_id: str, action: str, details: str) -> bool:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            letters_digits = string.ascii_uppercase + string.digits
            log_id = ''.join(random.choice(letters_digits) for _ in range(6))
            cursor.execute("""
                INSERT INTO AuditLog (logID, userID, action, [timestamp], details)
                VALUES (?, ?, ?, ?, ?)
            """, (log_id, user_id, action, datetime.now(), details))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error writing audit log: {e}")
            return False

    def addDish(self, dish: Dish, admin_id: str) -> bool:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Dish (dishID, categoryID, name, image, description, ingredients, price, isAvailable)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (dish.dishID, dish.categoryID, dish.name, dish.image, dish.description, dish.ingredients, dish.price, dish.isAvailable))
            conn.commit()
            conn.close()
            self.log_action(admin_id, "ADD_DISH", f"Added dish: {dish.name} ({dish.dishID})")
            return True
        except Exception as e:
            print(f"Error adding dish: {e}")
            return False

    def updateDish(self, dish: Dish, admin_id: str) -> bool:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Dish 
                SET categoryID=?, name=?, image=?, description=?, ingredients=?, price=?, isAvailable=?
                WHERE dishID=?
            """, (dish.categoryID, dish.name, dish.image, dish.description, dish.ingredients, dish.price, dish.isAvailable, dish.dishID))
            conn.commit()
            conn.close()
            self.log_action(admin_id, "UPDATE_DISH", f"Updated dish: {dish.name} ({dish.dishID})")
            return True
        except Exception as e:
            print(f"Error updating dish: {e}")
            return False

    def deleteDish(self, dish_id: str, admin_id: str) -> bool:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Dish WHERE dishID = ?", (dish_id,))
            conn.commit()
            conn.close()
            self.log_action(admin_id, "DELETE_DISH", f"Deleted dish ID: {dish_id}")
            return True
        except Exception as e:
            print(f"Error deleting dish: {e}")
            return False

    def get_all_dishes(self) -> list:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT dishID, name, image, description, ingredients, price, isAvailable, categoryID FROM Dish")
            rows = cursor.fetchall()
            conn.close()
            return [Dish(row[0], row[1], row[2], row[3], row[4], float(row[5]), bool(row[6]), row[7]) for row in rows]
        except Exception as e:
            print(f"Error getting dishes: {e}")
            return []

    def get_all_categories(self) -> list:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT categoryID, categoryName, description, status FROM Category")
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception as e:
            print(f"Error getting categories: {e}")
            return []

    def addStaff(self, staff_data: dict, admin_id: str) -> bool:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Employee (userID, fullName, phone, position, isActive, pin)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (staff_data['userID'], staff_data['fullName'], staff_data['phone'], staff_data['position'], staff_data['isActive'], staff_data['pin']))
            conn.commit()
            conn.close()
            self.log_action(admin_id, "ADD_STAFF", f"Created staff: {staff_data['fullName']} ({staff_data['userID']})")
            return True
        except Exception as e:
            print(f"Error adding staff: {e}")
            return False

    def updateStaff(self, user_id: str, updated_data: dict, admin_id: str) -> bool:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Employee 
                SET fullName = ?, phone = ?, position = ?, pin = ?, isActive = ?
                WHERE userID = ?
            """, (updated_data['fullName'], updated_data['phone'], updated_data['position'], updated_data['pin'], updated_data['isActive'], user_id))
            conn.commit()
            conn.close()
            self.log_action(admin_id, "UPDATE_STAFF", f"Updated staff ID: {user_id}")
            return True
        except Exception as e:
            print(f"Error updating staff: {e}")
            return False

    def deactivateStaff(self, user_id: str, admin_id: str) -> bool:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE Employee SET isActive = 0 WHERE userID = ?", (user_id,))
            conn.commit()
            conn.close()
            self.log_action(admin_id, "DEACTIVATE_STAFF", f"Deactivated staff ID: {user_id}")
            return True
        except Exception as e:
            print(f"Error deactivating staff: {e}")
            return False

    def get_all_staff_admin(self) -> list:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT userID, fullName, phone, position, pin, isActive FROM Employee ORDER BY userID")
            staff_list = cursor.fetchall()
            conn.close()
            return staff_list
        except Exception as e:
            print(f"Error getting staff list: {e}")
            return []

    def generateRevenueReport(self, from_date: str, to_date: str, report_type: str) -> RevenueReport:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            start_dt = from_date + " 00:00:00"
            end_dt = to_date + " 23:59:59"
            
            letters_digits = string.ascii_uppercase + string.digits
            report_id = ''.join(random.choice(letters_digits) for _ in range(6))
            
            if report_type == "Sales Report":
                cursor.execute("""
                    SELECT finalAmount, createdAt 
                    FROM Invoice 
                    WHERE createdAt BETWEEN ? AND ?
                """, (start_dt, end_dt))
                invoices = cursor.fetchall()
                
                total_revenue = 0.0
                total_orders = len(invoices)
                
                hourly_map = {f"{i:02d}:00": 0.0 for i in range(24)}
                for row in invoices:
                    amount = float(row[0]) if row[0] is not None else 0.0
                    total_revenue += amount
                    try:
                        dt_obj = datetime.strptime(row[1].split('.')[0], "%Y-%m-%d %H:%M:%S") if isinstance(row[1], str) else row[1]
                        hour_str = f"{dt_obj.hour:02d}:00"
                        if hour_str in hourly_map:
                            hourly_map[hour_str] += amount
                    except:
                        pass
                
                avg_order_value = total_revenue / total_orders if total_orders > 0 else 0.0
                
                cursor.execute("""
                    SELECT D.name, SUM(OD.quantity) as total_qty
                    FROM OrderDetail OD
                    JOIN Dish D ON OD.dishID = D.dishID
                    JOIN Orders O ON OD.orderID = O.orderID
                    JOIN Invoice I ON O.orderID = I.orderID
                    WHERE I.createdAt BETWEEN ? AND ?
                    GROUP BY D.name
                    ORDER BY total_qty DESC
                """, (start_dt, end_dt))
                top_rows = cursor.fetchall()
                top_performers = [{"name": r[0], "quantity": r[1]} for r in top_rows]
                
                chart_labels = [k for k, v in hourly_map.items()]
                chart_values = [v for k, v in hourly_map.items()]
                
            elif report_type == "Order Report":
                cursor.execute("""
                    SELECT orderID, orderDate, status 
                    FROM Orders 
                    WHERE orderDate BETWEEN ? AND ?
                """, (start_dt, end_dt))
                orders = cursor.fetchall()
                
                total_orders_count = len(orders)
                completed_orders = sum(1 for o in orders if o[2] == 'Completed')
                cancelled_orders = sum(1 for o in orders if o[2] == 'Cancelled')
                
                total_revenue = float(total_orders_count)
                total_orders = completed_orders
                avg_order_value = float(cancelled_orders)
                
                hourly_map = {f"{i:02d}:00": 0 for i in range(24)}
                for row in orders:
                    try:
                        dt_obj = datetime.strptime(row[1].split('.')[0], "%Y-%m-%d %H:%M:%S") if isinstance(row[1], str) else row[1]
                        hour_str = f"{dt_obj.hour:02d}:00"
                        if hour_str in hourly_map:
                            hourly_map[hour_str] += 1
                    except:
                        pass
                
                cursor.execute("""
                    SELECT status, COUNT(orderID) 
                    FROM Orders 
                    WHERE orderDate BETWEEN ? AND ?
                    GROUP BY status
                """, (start_dt, end_dt))
                status_rows = cursor.fetchall()
                top_performers = [{"name": f"Status: {r[0]}", "quantity": r[1]} for r in status_rows]
                
                chart_labels = [k for k, v in hourly_map.items()]
                chart_values = [float(v) for k, v in hourly_map.items()]
                
            elif report_type == "Menu Performance":
                cursor.execute("""
                    SELECT D.name, SUM(OD.quantity) as total_qty
                    FROM OrderDetail OD
                    JOIN Dish D ON OD.dishID = D.dishID
                    JOIN Orders O ON OD.orderID = O.orderID
                    WHERE O.orderDate BETWEEN ? AND ?
                    GROUP BY D.name
                    ORDER BY total_qty DESC
                """, (start_dt, end_dt))
                top_rows = cursor.fetchall()
                top_performers = [{"name": r[0], "quantity": r[1]} for r in top_rows]
                
                total_qty_sold = sum(r[1] for r in top_rows)
                total_distinct_dishes = len(top_rows)
                avg_qty_per_dish = total_qty_sold / total_distinct_dishes if total_distinct_dishes > 0 else 0
                
                total_revenue = float(total_qty_sold)
                total_orders = total_distinct_dishes
                avg_order_value = float(avg_qty_per_dish)
                
                hourly_map = {f"{i:02d}:00": 0 for i in range(24)}
                cursor.execute("""
                    SELECT O.orderDate, OD.quantity
                    FROM OrderDetail OD
                    JOIN Orders O ON OD.orderID = O.orderID
                    WHERE O.orderDate BETWEEN ? AND ?
                """, (start_dt, end_dt))
                hourly_items = cursor.fetchall()
                for row in hourly_items:
                    try:
                        dt_obj = datetime.strptime(row[0].split('.')[0], "%Y-%m-%d %H:%M:%S") if isinstance(row[0], str) else row[0]
                        hour_str = f"{dt_obj.hour:02d}:00"
                        if hour_str in hourly_map:
                            hourly_map[hour_str] += row[1]
                    except:
                        pass
                        
                chart_labels = [k for k, v in hourly_map.items()]
                chart_values = [float(v) for k, v in hourly_map.items()]
                
            chart_data = {"labels": chart_labels, "values": chart_values}
            
            save_revenue = total_revenue if report_type == "Sales Report" else 0.0
            cursor.execute("""
                INSERT INTO RevenueReport (reportID, fromDate, toDate, totalRevenue)
                VALUES (?, ?, ?, ?)
            """, (report_id, from_date, to_date, save_revenue))
            conn.commit()
            conn.close()
            
            return RevenueReport(report_id, from_date, to_date, report_type, total_revenue, total_orders, avg_order_value, top_performers, chart_data)
        except Exception as e:
            print(f"Error generating report: {e}")
            return RevenueReport("ERR01", from_date, to_date, report_type, 0.0)
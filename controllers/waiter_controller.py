# controllers/waiter_controller.py
from models.order_model import OrderModel
from models.audit_model import write_log
import logging

logger = logging.getLogger(__name__)

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
            if not tables:
                # Fallback mock tables if DB is empty for demo purposes
                tables = [
                    {'tableNumber': 1, 'status': 'Occupied'},
                    {'tableNumber': 2, 'status': 'Available'},
                    {'tableNumber': 3, 'status': 'Occupied'},
                    {'tableNumber': 4, 'status': 'Available'},
                    {'tableNumber': 5, 'status': 'Available'},
                    {'tableNumber': 6, 'status': 'Occupied'}
                ]
            
            formatted_tables = []
            for t in tables:
                formatted_tables.append({
                    'TableNumber': t['tableNumber'],
                    'Status': t['status'].strip()
                })
            return {'success': True, 'tables': formatted_tables}
        except Exception as e:
            logger.error(f"Error in get_table_map_data: {e}")
            # Fallback mock tables if DB connection fails
            formatted_tables = [
                {'TableNumber': 1, 'Status': 'Occupied'},
                {'TableNumber': 2, 'Status': 'Available'},
                {'TableNumber': 3, 'Status': 'Occupied'},
                {'TableNumber': 4, 'Status': 'Available'},
                {'TableNumber': 5, 'Status': 'Available'},
                {'TableNumber': 6, 'Status': 'Occupied'}
            ]
            return {'success': True, 'tables': formatted_tables}

    @staticmethod
    def get_ordering_view_data(table_number):
        """
        Gather metadata for the ordering view.
        Simultaneously handles the menu list and current cart data.
        """
        try:
            table_num = int(table_number)
            try:
                dishes = OrderModel.get_all_dishes()
                if not dishes:
                    raise Exception("Empty menu DB")
            except Exception:
                # Mock menu fallback
                dishes = [
                    {'dishID': 'D01', 'name': 'French Fries', 'price': 35000, 'categoryName': 'Appetizers', 'description': 'Crispy golden potato fries.', 'ingredients': 'Potato, salt'},
                    {'dishID': 'D02', 'name': 'Spring Rolls', 'price': 45000, 'categoryName': 'Appetizers', 'description': 'Traditional fried spring rolls.', 'ingredients': 'Pork, shrimp, mushroom'},
                    {'dishID': 'D03', 'name': 'Fried Rice', 'price': 75000, 'categoryName': 'Main Courses', 'description': 'Special rice fried with egg and seafood.', 'ingredients': 'Rice, egg, shrimp, squid'},
                    {'dishID': 'D04', 'name': 'Beef Steak', 'price': 180000, 'categoryName': 'Main Courses', 'description': 'Premium beef with black pepper sauce.', 'ingredients': 'Beef, butter, pepper'},
                    {'dishID': 'D05', 'name': 'Iced Peach Tea', 'price': 25000, 'categoryName': 'Beverages', 'description': 'Refreshing sweet iced peach tea.', 'ingredients': 'Tea, peach, sugar'},
                    {'dishID': 'D06', 'name': 'Vanilla Ice Cream', 'price': 30000, 'categoryName': 'Desserts', 'description': 'Cold and creamy vanilla ice cream.', 'ingredients': 'Milk, vanilla extract'}
                ]
            
            # Format dishes for the UI
            for dish in dishes:
                cat = str(dish.get('categoryName', '')).lower()
                dish_name = str(dish.get('name', '')).lower()
                
                # Semantic categorization for HTML tabs
                if 'appetizer' in cat or 'khai vị' in dish_name:
                    dish['Category'] = 'appetizers'
                elif 'dessert' in cat or 'tráng miệng' in dish_name:
                    dish['Category'] = 'desserts'
                elif 'drink' in cat or 'beverage' in cat or 'uống' in dish_name or 'tea' in dish_name:
                    dish['Category'] = 'beverages'
                else:
                    dish['Category'] = 'main-courses'
                    
                dish['DishID'] = str(dish['dishID']).strip()
                dish['Name'] = str(dish['name']).strip()
                dish['Price'] = f"{dish['price']:,.0f}" if dish['price'] else "0"
                dish['Description'] = str(dish.get('description', '')).strip()
                dish['Ingredients'] = str(dish.get('ingredients', '')).strip()

            active_order = OrderModel.get_active_order_for_table(table_num)
            cart_items = []
            
            if active_order:
                # Only show editable cart items if it hasn't gone to the kitchen yet
                if active_order['status'] in ['Draft', 'Confirmed']:
                    cart_items = OrderModel.get_cart_items(active_order['orderID'])

            return {
                'success': True, 
                'dishes': dishes, 
                'cart_items': cart_items,
                'table_number': table_num
            }
        except Exception as e:
            logger.error(f"Error in get_ordering_view_data: {e}")
            return {'success': False, 'message': "System error loading menu data."}

    @staticmethod
    def process_add_to_cart(table_number, dish_id, quantity, special_note, user_id):
        """Add item to order logic"""
        try:
            table_num = int(table_number)
            qty = int(quantity)
            
            active_order = OrderModel.get_active_order_for_table(table_num)
            
            if active_order:
                status = active_order['status']
                if status in ['Preparing', 'Ready', 'Served']:
                    return {
                        'success': False, 
                        'message': f"Cannot modify because the kitchen is processing (Status: {status})."
                    }
                order_id = active_order['orderID']
            else:
                # Create draft order and lock table
                order_id = OrderModel.create_draft_order(table_num, user_id)
                write_log(user_id, "Create Draft Order", f"Started Draft Order {order_id} for Table {table_num}")
                
            OrderModel.add_order_item(order_id, dish_id, qty, special_note)
            write_log(user_id, "Add Item", f"Added Dish {dish_id} (x{qty}) to Order {order_id}")
            return {'success': True, 'message': 'Item added to cart successfully.'}
        except Exception as e:
            logger.error(f"Error in process_add_to_cart: {e}")
            return {'success': False, 'message': "Database access error."}

    @staticmethod
    def process_remove_from_cart(table_number, dish_id, special_note, user_id):
        """Remove item from order logic"""
        try:
            table_num = int(table_number)
            active_order = OrderModel.get_active_order_for_table(table_num)
            
            if not active_order:
                return {'success': False, 'message': 'This table has no active order.'}
                
            status = active_order['status']
            if status not in ['Draft', 'Confirmed']:
                return {'success': False, 'message': f"Cannot remove item when order is in {status} status."}
                
            success, is_empty = OrderModel.remove_order_item(active_order['orderID'], dish_id, special_note)
            
            if success:
                write_log(user_id, "Remove Item", f"Removed Dish {dish_id} from Order {active_order['orderID']}")
                if is_empty:
                    write_log(user_id, "Empty Draft Order", f"Order {active_order['orderID']} removed (Empty). Table {table_num} is now Available.")
            
            redirect_url = '/waiter/tables' if is_empty else f'/waiter/order?table={table_num}'
            return {'success': True, 'redirect': redirect_url}
        except Exception as e:
            logger.error(f"Error in process_remove_from_cart: {e}")
            return {'success': False, 'message': "Error removing item."}

    @staticmethod
    def process_update_cart(table_number, dish_id, special_note, action, user_id):
        """Update quantity of an existing item in the cart (+1 or -1)"""
        try:
            table_num = int(table_number)
            active_order = OrderModel.get_active_order_for_table(table_num)
            
            if not active_order:
                return {'success': False, 'message': 'This table has no active order.'}
                
            status = active_order['status']
            if status not in ['Draft', 'Confirmed']:
                return {'success': False, 'message': f"Cannot modify item when order is in {status} status."}
            
            # Find current quantity
            cart_items = OrderModel.get_cart_items(active_order['orderID'])
            current_qty = 0
            for item in cart_items:
                if item['dish_id'] == dish_id and item['note'] == special_note:
                    current_qty = item['quantity']
                    break
            
            if current_qty == 0:
                return {'success': False, 'message': 'Item not found in cart.'}
                
            new_qty = current_qty + 1 if action == 'increase' else current_qty - 1
            
            success, is_empty = OrderModel.update_order_item_qty(active_order['orderID'], dish_id, special_note, new_qty)
            
            if success:
                if is_empty:
                    write_log(user_id, "Empty Draft Order", f"Order {active_order['orderID']} removed (Empty). Table {table_num} is now Available.")
                else:
                    write_log(user_id, "Update Item", f"Updated Dish {dish_id} quantity to {new_qty} in Order {active_order['orderID']}")
            
            redirect_url = '/waiter/tables' if is_empty else f'/waiter/order?table={table_num}'
            return {'success': True, 'redirect': redirect_url}
        except Exception as e:
            logger.error(f"Error in process_update_cart: {e}")
            return {'success': False, 'message': "Error updating item."}

    @staticmethod
    def process_confirm_order(table_number, user_id):
        """Push order info to the kitchen"""
        try:
            table_num = int(table_number)
            active_order = OrderModel.get_active_order_for_table(table_num)
            
            if not active_order:
                return {'success': False, 'message': 'No order found to confirm.'}
                
            if active_order['status'] == 'Draft':
                OrderModel.confirm_order(active_order['orderID'])
                write_log(user_id, "Confirm Order", f"Sent Order {active_order['orderID']} for Table {table_num} to Kitchen.")
                return {'success': True, 'message': 'Order confirmed and sent to kitchen!'}
            else:
                return {'success': False, 'message': f"Cannot re-confirm, order is currently: {active_order['status']}"}
        except Exception as e:
            logger.error(f"Error in process_confirm_order: {e}")
            return {'success': False, 'message': "Error confirming order."}
    @staticmethod
    def get_notifications(user_id):
        """Retrieve new notifications for the waiter"""
        try:
            notifications = OrderModel.get_notifications(user_id)
            # Format for UI
            formatted = []
            for n in notifications:
                formatted.append({
                    'OrderID': n['orderID'].strip(),
                    'TableNumber': n['tableNumber']
                })
            return {'success': True, 'notifications': formatted}
        except Exception as e:
            logger.error(f"Error in get_notifications: {e}")
            return {'success': False, 'message': "Error loading notifications."}

    @staticmethod
    def get_order_detail_view(table_number):
        """Retrieve full details for an active order."""
        try:
            table_num = int(table_number)
            active_order = OrderModel.get_active_order_for_table(table_num)
            
            if not active_order:
                return {'success': False, 'message': 'No active order found.'}
                
            details = OrderModel.get_order_details(active_order['orderID'])
            
            if details:
                # Format specific fields for UI
                details['OrderID'] = details.get('orderID')
                details['OrderDate'] = details.get('orderDate').strftime("%Y-%m-%d %H:%M:%S") if details.get('orderDate') else ""
                details['Status'] = details.get('status').strip()
                details['TableNumber'] = details.get('tableNumber')
                
            return {'success': True, 'order': details, 'items': details.get('items', [])}
        except Exception as e:
            logger.error(f"Error in get_order_detail_view: {e}")
            return {'success': False, 'message': "Error extracting order details."}

    @staticmethod
    def process_cancel_order(order_id, user_id):
        """Cancel an order before it's prepared"""
        try:
            success = OrderModel.cancel_order(order_id, user_id)
            if success:
                write_log(user_id, "Cancel Order", f"Cancelled Order {order_id}.")
                return {'success': True, 'message': 'Order cancelled.'}
            return {'success': False, 'message': 'Cannot cancel this order (it might be in preparation).'}
        except Exception as e:
            logger.error(f"Error in process_cancel_order: {e}")
            return {'success': False, 'message': "Error cancelling order."}

    @staticmethod
    def process_serve_order(order_id, user_id):
        """Mark an order as served"""
        try:
            success = OrderModel.update_to_served(order_id, user_id)
            if success:
                write_log(user_id, "Serve Order", f"Marked Order {order_id} as Served.")
                return {'success': True, 'message': 'Order served.'}
            return {'success': False, 'message': 'Order must be Ready to be served.'}
        except Exception as e:
            logger.error(f"Error in process_serve_order: {e}")
            return {'success': False, 'message': "Error serving order."}

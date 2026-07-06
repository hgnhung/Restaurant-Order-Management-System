from models.order_model import OrderModel

class WaiterController:
    """Controller for all Waiter operations"""

    @staticmethod
    def view_menu():
        """View full menu organized by categories"""
        return {
            'categories': OrderModel.get_categories(),
            'dishes': OrderModel.get_all_dishes()
        }

    @staticmethod
    def search_dishes(keyword):
        """Search dishes by keyword"""
        return {'dishes': OrderModel.search_dishes(keyword)}

    @staticmethod
    def get_table_status():
        """Get restaurant tables for order creation"""
        return OrderModel.get_all_tables()

    @staticmethod
    def create_new_order(table_number, waiter_id='E02'):
        """Create new dine-in order"""
        order_id = OrderModel.create_order(table_number, waiter_id)
        return {'success': True, 'order_id': order_id, 'message': 'Order created successfully'}

    @staticmethod
    def add_item_to_order(order_id, dish_id, quantity=1, special_note=None):
        """Add dish to order"""
        success = OrderModel.add_order_item(order_id, dish_id, quantity, special_note)
        return {'success': success, 'message': 'Item added' if success else 'Cannot modify locked order'}

    @staticmethod
    def remove_item_from_order(order_id, dish_id):
        """Remove dish from order"""
        success = OrderModel.remove_order_item(order_id, dish_id)
        return {'success': success}

    @staticmethod
    def get_order_details(order_id):
        """View order details"""
        order = OrderModel.get_order_details(order_id)
        return {'success': bool(order), 'order': order}

    @staticmethod
    def get_active_orders():
        """View list of active orders"""
        orders = OrderModel.get_active_orders()
        return {'success': True, 'orders': orders}

    @staticmethod
    def confirm_order(order_id, waiter_id='E02'):
        """Confirm and send order to kitchen"""
        success = OrderModel.confirm_order(order_id, waiter_id)
        return {'success': success, 'message': 'Order confirmed and sent to kitchen'}

    @staticmethod
    def cancel_order(order_id, waiter_id='E02'):
        """Cancel order (before preparation)"""
        success = OrderModel.cancel_order(order_id, waiter_id)
        return {'success': success, 'message': 'Order cancelled successfully' if success else 'Cannot cancel this order'}

    @staticmethod
    def update_to_served(order_id, waiter_id='E02'):
        """Mark order as served after delivery to customer"""
        success = OrderModel.update_to_served(order_id, waiter_id)
        return {'success': success, 'message': 'Order marked as Served'}
from flask import render_template, request, redirect, url_for, session
from database import get_db_connection 
from datetime import datetime

class KitchenController:
    @staticmethod
    def get_dashboard():
        # Session authentication guard check
        if "userID" not in session:
            return redirect("/")
            
        order_id = request.args.get('order_id')
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Fetch active kitchen orders ordered chronologically (Oldest first)
        cursor.execute("""
            SELECT id, order_number, table_number, status, created_at 
            FROM orders 
            WHERE status IN ('Confirmed', 'Preparing')
            ORDER BY created_at ASC
        """)
        orders = cursor.fetchall()
        
        # Calculate real-time elapsed cooking duration metrics
        for order in orders:
            delta = datetime.now() - order['created_at']
            minutes = int(delta.total_seconds() // 60)
            seconds = int(delta.total_seconds() % 60)
            order['elapsed_time'] = f"{minutes:02d}:{seconds:02d}"
            
        # Fetch detailed specifications for the selected active order
        selected_order = None
        if order_id:
            cursor.execute("""
                SELECT id, order_number, table_number, status, created_at 
                FROM orders WHERE id = %s
            """, (order_id,))
            selected_order = cursor.fetchone()
            
            if selected_order:
                delta = datetime.now() - selected_order['created_at']
                selected_order['elapsed_time'] = f"{int(delta.total_seconds() // 60):02d}:{int(delta.total_seconds() % 60):02d}"
                
                # Fetch associated line items and customer preparation notes
                cursor.execute("""
                    SELECT name, quantity, note 
                    FROM order_items 
                    WHERE order_id = %s
                """, (order_id,))
                selected_order['items'] = cursor.fetchall()
                
        cursor.close()
        conn.close()
        
        return render_template('kitchen/dashboard.html', orders=orders, selected_order=selected_order)

    @staticmethod
    def update_order_status():
        # Session authentication guard check
        if "userID" not in session:
            return redirect("/")
            
        order_id = request.form.get('order_id')
        new_status = request.form.get('status')
        
        if order_id and new_status in ['Preparing', 'Ready']:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Dynamic state machine update according to SRS specifications
            cursor.execute("""
                UPDATE orders 
                SET status = %s, updated_at = NOW() 
                WHERE id = %s
            """, (new_status, order_id))
            conn.commit()
            cursor.close()
            conn.close()
            
        return redirect(url_for('kitchen.dashboard', order_id=order_id if new_status != 'Ready' else None))

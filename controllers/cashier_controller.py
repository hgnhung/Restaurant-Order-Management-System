from database import get_db_connection
from datetime import datetime

def get_unpaid_invoices():
    """Retrieves all orders marked as 'Served' that are ready for billing[cite: 463, 483]."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Selecting active orders waiting to be billed
    query = """
        SELECT OrderID, TableNumber, OrderDate, TotalAmount 
        FROM [Order] 
        WHERE Status = 'Served'
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    invoices = []
    for row in rows:
        invoices.append({
            'order_id': row.OrderID,
            'table_number': row.TableNumber,
            'order_date': row.OrderDate,
            'subtotal': float(row.TotalAmount)
        })
    return invoices

def get_invoice_detail(order_id):
    """Fetches details for an order to display as a draft invoice[cite: 465]."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Fetch main Order details
    order_query = "SELECT OrderID, TableNumber, OrderDate, TotalAmount FROM [Order] WHERE OrderID = ?"
    cursor.execute(order_query, (order_id,))
    order_row = cursor.fetchone()
    
    if not order_row:
        return None
        
    # 2. Fetch specific item breakdowns from OrderDetail joined with Dish table
    items_query = """
        SELECT d.Name, od.Quantity, od.UnitPrice, od.SubTotal 
        FROM OrderDetail od
        JOIN Dish d ON od.DishID = d.DishID
        WHERE od.OrderID = ?
    """
    cursor.execute(items_query, (order_id,))
    items_rows = cursor.fetchall()
    
    items = []
    subtotal = 0.0
    for item in items_rows:
        items.append({
            'name': item.Name,
            'quantity': item.Quantity,
            'unit_price': float(item.UnitPrice),
            'total': float(item.SubTotal)
        })
        subtotal += float(item.SubTotal)
        
    # Calculate exactly 8% VAT as shown in section 7.4.1 UI mockup 
    tax_amount = subtotal * 0.08
    grand_total = subtotal + tax_amount
    
    invoice_data = {
        'order_id': order_row.OrderID,
        'table_number': order_row.TableNumber,
        'order_time': order_row.OrderDate,
        'items': items,
        'subtotal': subtotal,
        'tax_amount': tax_amount,
        'grand_total': grand_total
    }
    return invoice_data

def process_payment(order_id, payment_method, cashier_id=1):
    """Executes database updates to commit invoices, payments, and update system states[cite: 505, 506, 507]."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    invoice_detail = get_invoice_detail(order_id)
    if not invoice_detail:
        return False, "Order details data not found."
        
    try:
        # Step 1: Insert row into Invoice table [cite: 485]
        insert_invoice_query = """
            INSERT INTO Invoice (OrderID, InvoiceDate, TotalAmount, TaxAmount, DiscountAmount, GrandTotal)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        invoice_date = datetime.now()
        discount_amount = 0.0 
        
        cursor.execute(insert_invoice_query, (
            order_id, 
            invoice_date, 
            invoice_detail['subtotal'], 
            invoice_detail['tax_amount'], 
            discount_amount, 
            invoice_detail['grand_total']
        ))
        
        # Grab generated Identity Primary Key
        cursor.execute("SELECT @@IDENTITY AS InvoiceID")
        invoice_id = int(cursor.fetchone()[0])
        
        # Step 2: Record transaction in Payment table [cite: 54]
        insert_payment_query = """
            INSERT INTO Payment (InvoiceID, UserID, PaymentMethod, PaymentDate, Amount, PaymentStatus)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor.execute(insert_payment_query, (
            invoice_id, 
            cashier_id, 
            payment_method, 
            invoice_date, 
            invoice_detail['grand_total'], 
            'Paid'
        ))
        
        # Step 3: Change Order status flag to 'Completed' [cite: 55, 506]
        update_order_query = "UPDATE [Order] SET Status = 'Completed' WHERE OrderID = ?"
        cursor.execute(update_order_query, (order_id,))
        
        # Step 4: Revert Table status flag from 'Occupied' back to 'Available' [cite: 55, 507]
        update_table_query = "UPDATE [Table] SET Status = 'Available' WHERE TableNumber = ?"
        cursor.execute(update_table_query, (invoice_detail['table_number'],))
        
        # Secure the batch transaction safely
        conn.commit()
        return True, "Payment captured successfully! Table released."
        
    except Exception as e:
        conn.rollback()
        return False, f"Database transaction rollback due to error: {str(e)}"

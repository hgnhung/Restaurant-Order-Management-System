from database import get_connection


class PaymentModel:

    @staticmethod
    def create_payment(
        payment_id,
        invoice_id,
        payment_method,
        amount,
        cashier_id
    ):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO Payment
            (
                paymentID,
                invoiceID,
                paymentMethod,
                amount,
                paymentTime,
                cashierID
            )
            VALUES
            (
                ?, ?, ?, ?, GETDATE(), ?
            )
        """,
        (
            payment_id,
            invoice_id,
            payment_method,
            amount,
            cashier_id
        ))

        conn.commit()

        cursor.close()
        conn.close()

    @staticmethod
    def process_payment(invoice, payment_method, cashier_id):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            # Generate sequential paymentID (e.g. PAY001) to fit VARCHAR(6)
            cursor.execute("SELECT MAX(CAST(SUBSTRING(paymentID, 4, 3) AS INT)) FROM Payment WHERE paymentID LIKE 'PAY%'")
            max_num = cursor.fetchone()[0]
            if max_num is None:
                max_num = 0
            payment_id = f"PAY{max_num + 1:03d}"
            
            # Insert payment
            cursor.execute("""
                INSERT INTO Payment (paymentID, invoiceID, paymentMethod, amount, paymentTime, cashierID)
                VALUES (?, ?, ?, ?, GETDATE(), ?)
            """, (payment_id, invoice.invoiceID, payment_method, invoice.finalAmount, cashier_id))
            
            # Update Orders to Completed
            cursor.execute("UPDATE Orders SET status = 'Completed' WHERE orderID = ?", (invoice.orderID,))
            
            # Look up tableNumber to release table
            cursor.execute("SELECT tableNumber FROM Orders WHERE orderID = ?", (invoice.orderID,))
            t_row = cursor.fetchone()
            if t_row:
                cursor.execute("UPDATE RestaurantTable SET status = 'Available' WHERE tableNumber = ?", (t_row[0],))
                
            conn.commit()
            return payment_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
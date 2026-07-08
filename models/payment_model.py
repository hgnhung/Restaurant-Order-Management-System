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
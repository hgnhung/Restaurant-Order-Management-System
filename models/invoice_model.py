from database import get_connection
from decimal import Decimal

class InvoiceModel:

    # ======================================================
    # Lấy danh sách Order sẵn sàng thanh toán
    # ======================================================

    @staticmethod
    def get_ready_orders():

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                o.orderID,
                o.tableNumber,
                o.orderDate
            FROM Orders o
            LEFT JOIN Invoice i ON o.orderID = i.orderID
            LEFT JOIN Payment p ON i.invoiceID = p.invoiceID
            WHERE o.status IN ('Ready', 'Served') 
              AND p.paymentID IS NULL
        """)

        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return rows

    # ======================================================
    # Lấy thông tin Order
    # ======================================================

    @staticmethod
    def get_order(order_id):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""

            SELECT
                orderID,
                tableNumber,
                orderDate

            FROM Orders

            WHERE orderID=?

        """, (order_id,))

        row = cursor.fetchone()

        cursor.close()
        conn.close()

        return row

    # ======================================================
    # Danh sách món của Order
    # ======================================================

    @staticmethod
    def get_order_items(order_id):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""

            SELECT

                d.name,
                od.quantity,
                d.price,
                od.quantity*d.price AS total,
                od.specialNote

            FROM OrderDetail od

            INNER JOIN Dish d

                ON od.dishID=d.dishID

            WHERE od.orderID=?

        """, (order_id,))

        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return rows

    # ======================================================
    # Tạo Invoice
    # ======================================================

    @staticmethod
    def create_invoice(order_id):

        conn = get_connection()
        cursor = conn.cursor()

        # Nếu Order đã có Invoice thì trả luôn
        cursor.execute("""

            SELECT invoiceID

            FROM Invoice

            WHERE orderID=?

        """, (order_id,))

        row = cursor.fetchone()

        if row:

            cursor.close()
            conn.close()

            return row.invoiceID

        ####################################################

        cursor.execute("""

            SELECT ISNULL(MAX(invoiceID),'INV000')

            FROM Invoice

        """)

        last = cursor.fetchone()[0]

        number = int(last[3:]) + 1

        invoice_id = f"INV{number:03d}"

        ####################################################
        # Tính tổng tiền
        ####################################################

        cursor.execute("""

            SELECT
                SUM(od.quantity*d.price)

            FROM OrderDetail od

            INNER JOIN Dish d

                ON od.dishID=d.dishID

            WHERE od.orderID=?

        """, (order_id,))

        subtotal = cursor.fetchone()[0]

        if subtotal is None:
            subtotal = 0

        tax = subtotal * Decimal("0.08")

        final_amount = subtotal + tax

        ####################################################

        cursor.execute("""

            INSERT INTO Invoice
            (
                invoiceID,
                orderID,
                tax,
                finalAmount,
                createdAt
            )

            VALUES
            (
                ?,?,?,?,GETDATE()
            )

        """, (

            invoice_id,
            order_id,
            tax,
            final_amount

        ))

        conn.commit()

        cursor.close()
        conn.close()

        return invoice_id

    # ======================================================
    # Lấy Invoice
    # ======================================================

    @staticmethod
    def get_invoice(invoice_id):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                i.invoiceID,
                i.orderID,
                o.tableNumber,
                i.tax,
                i.finalAmount,
                i.createdAt
            FROM Invoice i
            INNER JOIN Orders o
                ON i.orderID = o.orderID
            WHERE i.invoiceID = ?
        """, (invoice_id,))

        invoice = cursor.fetchone()

        cursor.close()
        conn.close()

        return invoice
    
    @staticmethod
    def check_invoice_exists(order_id):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT invoiceID
            FROM Invoice
            WHERE orderID = ?
        """, (order_id,))

        row = cursor.fetchone()

        cursor.close()
        conn.close()

        if row:
            return row.invoiceID

        return None
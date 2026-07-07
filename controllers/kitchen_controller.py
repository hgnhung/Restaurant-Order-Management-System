from flask import render_template, request, redirect, url_for, session
from database import get_connection


class KitchenController:

    @staticmethod
    def get_dashboard():

        # Kiểm tra đăng nhập
        if "userID" not in session:
            return redirect("/")

        conn = get_connection()
        cursor = conn.cursor()

        # =====================================================
        # Danh sách đơn hàng cho Kitchen
        # Chỉ hiển thị Confirmed và Preparing
        # =====================================================

        cursor.execute("""
            SELECT
                orderID,
                tableNumber,
                status,
                orderDate
            FROM Orders
            WHERE status IN ('Confirmed','Preparing')
            ORDER BY orderDate ASC
        """)

        rows = cursor.fetchall()

        orders = []

        for row in rows:
            orders.append({
                "orderID": row.orderID,
                "tableNumber": row.tableNumber,
                "status": row.status,
                "orderDate": row.orderDate,
                "displayDate": row.orderDate.strftime("%d/%m/%Y"),
                "displayTime": row.orderDate.strftime("%H:%M")
            })

        selected_order = None
        order_id = request.args.get("order_id")

        # =====================================================
        # Nếu chọn một Order
        # =====================================================

        if order_id:

            cursor.execute("""
                SELECT
                    orderID,
                    tableNumber,
                   	status,
                    orderDate
                FROM Orders
                WHERE orderID = ?
            """, (order_id,))

            selected_order = cursor.fetchone()

            selected_order = {
                "orderID": selected_order.orderID,
                "tableNumber": selected_order.tableNumber,
                "status": selected_order.status,
                "orderDate": selected_order.orderDate,
                "displayDate": selected_order.orderDate.strftime("%d/%m/%Y"),
                "displayTime": selected_order.orderDate.strftime("%H:%M")
            }

            if selected_order:

                cursor.execute("""
                    SELECT
                        d.name,
                        od.quantity,
                        od.specialNote
                    FROM OrderDetail od
                    INNER JOIN Dish d
                        ON od.dishID = d.dishID
                    WHERE od.orderID = ?
                """, (order_id,))

                items = cursor.fetchall()

            else:
                items = []

        else:
            items = []

        cursor.close()
        conn.close()

        return render_template(
            "kitchen/dashboard.html",
            orders=orders,
            selected_order=selected_order,
            items=items
        )

    # =========================================================
    # Chuyển trạng thái đơn
    # =========================================================

    @staticmethod
    def update_order_status():

        if "userID" not in session:
            return redirect("/")

        order_id = request.form.get("order_id")

        conn = get_connection()
        cursor = conn.cursor()

        # Lấy trạng thái hiện tại

        cursor.execute("""
            SELECT status
            FROM Orders
            WHERE orderID = ?
        """, (order_id,))

        row = cursor.fetchone()

        if row is None:

            cursor.close()
            conn.close()

            return redirect(url_for("kitchen.get_dashboard"))

        current_status = row.status

        # =====================================================
        # Confirmed -> Preparing
        # =====================================================

        if current_status == "Confirmed":

            new_status = "Preparing"

        # =====================================================
        # Preparing -> Ready
        # =====================================================

        elif current_status == "Preparing":

            new_status = "Ready"

        else:

            new_status = current_status

        cursor.execute("""
            UPDATE Orders
            SET status = ?
            WHERE orderID = ?
        """, (new_status, order_id))

        conn.commit()

        cursor.close()
        conn.close()

        return redirect(
            url_for(
                "kitchen.get_dashboard",
                order_id=order_id
            )
        )
    

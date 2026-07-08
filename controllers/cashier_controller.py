from flask import render_template, request, redirect, session
from decimal import Decimal
from models.invoice_model import InvoiceModel
from models.payment_model import PaymentModel
from models.audit_model import write_log
from flask import flash


class CashierController:

    ##########################################################
    # Invoice Page
    ##########################################################

    @staticmethod
    def get_invoice():

        if "userID" not in session:
            return redirect("/")

        orders = InvoiceModel.get_ready_orders()

        order_id = request.args.get("order_id")

        selected_order = None
        items = []
        subtotal = 0
        tax = 0
        total = 0

        if order_id:

            selected_order = InvoiceModel.get_order(order_id)

            if selected_order:

                items = InvoiceModel.get_order_items(order_id)

                subtotal = sum(item.total for item in items)

                tax = subtotal * Decimal("0.08")

                total = subtotal + tax

        return render_template(
            "cashier/invoice.html",
            orders=orders,
            selected_order=selected_order,
            items=items,
            subtotal=subtotal,
            tax=tax,
            total=total
        )

    ##########################################################
    # Generate Invoice
    ##########################################################

    @staticmethod
    def generate_invoice():

        if "userID" not in session:
            return redirect("/")

        order_id = request.form.get("orderID")

        # Kiểm tra order đã có invoice chưa
        invoice_id = InvoiceModel.check_invoice_exists(order_id)

        # Nếu chưa có thì tạo mới
        if invoice_id is None:
            invoice_id = InvoiceModel.create_invoice(order_id)

        return redirect(f"/cashier/payment?invoice_id={invoice_id}")

    ##########################################################
    # Payment Page
    ##########################################################

    @staticmethod
    def get_payment():

        if "userID" not in session:
            return redirect("/")
        
        invoice_id = request.args.get("invoice_id") 

        invoice = InvoiceModel.get_invoice(invoice_id)
        

        if invoice is None:
            return redirect("/cashier/invoice")

        items = InvoiceModel.get_order_items(invoice.orderID)

        bank_name = "Vietcombank"
        account_no = "0123456789"
        account_name = "Restaurant OMS"

        amount = int(invoice.finalAmount)

        qr_url = (
            f"https://img.vietqr.io/image/970436-{account_no}-compact2.png"
            f"?amount={amount}"
            f"&addInfo={invoice.invoiceID}"
            f"&accountName={account_name.replace(' ', '%20')}"
        )

        return render_template(
            "cashier/payment.html",
            invoice=invoice,
            items=items,
            qr_url=qr_url,
            bank_name=bank_name,
            account_no=account_no,
            account_name=account_name
        )
    ##########################################################
    # Confirm Payment
    ##########################################################

    @staticmethod
    def process_payment():

        if "userID" not in session:
            return redirect("/")

        invoice_id = request.form.get("invoiceID")
        payment_method = request.form.get("paymentMethod")

        try:

            invoice = InvoiceModel.get_invoice(invoice_id)

            if invoice is None:
                return redirect("/cashier/invoice")

            PaymentModel.process_payment(
                invoice,
                payment_method,
                session["userID"]
            )

            write_log(
                session["userID"],
                "Payment",
                f"Invoice {invoice.invoiceID} paid"
            )

            flash("Payment completed successfully!", "success")

        except Exception as e:

            print(e)

        return redirect("/cashier/invoice")
    
    @staticmethod
    def logout():

        if "userID" in session:

            write_log(
                session["userID"],
                "Logout",
                "User logged out"
            )

        session.clear()

        return redirect("/")
    
    
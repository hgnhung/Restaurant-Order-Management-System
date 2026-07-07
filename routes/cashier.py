from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from controllers.cashier_controller import get_unpaid_invoices, get_invoice_detail, process_payment

cashier_bp = Blueprint('cashier', __name__)

@cashier_bp.route('/dashboard')
def dashboard():
    """Main cashier panel layout showing pending billing queues[cite: 463]."""
    invoices = get_unpaid_invoices()
    return render_template('cashier/dashboard.html', invoices=invoices)

@cashier_bp.route('/invoice/<string:order_id>', methods=['GET', 'POST'])
def view_invoice(order_id):
    """Invoice visualization and billing action handler[cite: 474, 494]."""
    invoice = get_invoice_detail(order_id)
    if not invoice:
        flash("Target order entity was either closed or doesn't exist.", "danger")
        return redirect(url_for('cashier.dashboard'))
        
    if request.method == 'POST':
        payment_method = request.form.get('payment_method') # Returns 'Cash' or 'Bank Transfer'
        user_id = session.get('user_id', 1) # Falls back to mock session ID if auth is unlinked
        
        success, message = process_payment(order_id, payment_method, cashier_id=user_id)
        if success:
            flash(message, 'success')
            return redirect(url_for('cashier.dashboard'))
            
    return render_template('cashier/invoice_detail.html', invoice=invoice)

from flask import Blueprint, render_template, request, redirect, url_for, flash
from controllers.cashier_controller import get_unpaid_invoices, get_invoice_detail, process_payment

cashier_bp = Blueprint('cashier', __name__)

@cashier_bp.route('/dashboard')
def dashboard():
    """Màn hình tổng quan của Thu ngân"""
    unpaid_invoices = get_unpaid_invoices()
    return render_template('cashier/dashboard.html', invoices=unpaid_invoices)

@cashier_bp.route('/invoice/<int:invoice_id>', methods=['GET', 'POST'])
def view_invoice(invoice_id):
    """Màn hình chi tiết hóa đơn & xử lý thanh toán"""
    invoice = get_invoice_detail(invoice_id)
    
    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        discount = float(request.form.get('discount', 0.0))
        
        success, message = process_payment(invoice_id, payment_method, discount)
        if success:
            flash(message, 'success')
            return redirect(url_for('cashier.dashboard'))
        else:
            flash(message, 'danger')
            
    return render_template('cashier/invoice_detail.html', invoice=invoice)

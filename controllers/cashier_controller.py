from models.invoice_model import Invoice
from models.payment_model import Payment
from database import db

def get_unpaid_invoices():
    """Lấy danh sách các hóa đơn/bàn chưa thanh toán hiển thị lên màn hình chính"""
    return Invoice.query.filter_sub(Invoice.status == 'Unpaid').all()

def get_invoice_detail(invoice_id):
    """Lấy chi tiết một hóa đơn cụ thể"""
    return Invoice.query.get_or_404(invoice_id)

def process_payment(invoice_id, payment_method, discount_amount=0.0):
    """Logic xử lý khi Thu ngân bấm nút Thanh Toán"""
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        return False, "Không tìm thấy hóa đơn"
        
    # Cập nhật lại tiền nếu có áp dụng giảm giá lúc tính tiền
    invoice.discount = discount_amount
    invoice.total_amount = max(0.0, invoice.subtotal - discount_amount)
    invoice.status = 'Paid'
    
    # Tạo bản ghi lịch sử thanh toán
    payment = Payment(
        invoice_id=invoice.id,
        payment_method=payment_method
    )
    
    try:
        db.session.add(payment)
        db.session.commit()
        return True, "Thanh toán thành công!"
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi hệ thống: {str(e)}"

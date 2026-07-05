from database import db
from datetime import datetime

class Invoice(db.Model):
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    table_number = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)       # Tiền trước giảm giá
    discount = db.Column(db.Float, default=0.0)          # Số tiền được giảm (hoặc %)
    total_amount = db.Column(db.Float, nullable=False)   # Tiền cuối cùng phải trả
    status = db.Column(db.String(20), default='Unpaid')  # 'Unpaid' (Chưa thanh toán) hoặc 'Paid' (Đã thanh toán)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Khởi tạo mối quan hệ để lấy chi tiết món ăn từ Đơn hàng (Order)
    order = db.relationship('Order', backref=db.backref('invoice', uselist=False))

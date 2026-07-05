from database import db
from datetime import datetime

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False) # 'Cash', 'Banking', 'Card'
    transaction_id = db.Column(db.String(100), nullable=True) # Mã giao dịch chuyển khoản nếu có
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)
    cashier_id = db.Column(db.Integer, nullable=True)         # ID thu ngân xử lý

    invoice = db.relationship('Invoice', backref=db.backref('payments', lazy=True))

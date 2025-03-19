from datetime import datetime
from app import db

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='BRL', nullable=False)
    payment_method = db.Column(db.String(30), nullable=False)  # credit_card, pix, boleto
    payment_id = db.Column(db.String(100), nullable=True)  # ID do pagamento no gateway
    plan = db.Column(db.String(20), nullable=False)  # mensal, trimestral, anual
    status = db.Column(db.String(20), nullable=False)  # pending, approved, rejected, refunded
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento
    license_id = db.Column(db.Integer, db.ForeignKey('licenses.id'), nullable=True)
    license = db.relationship('License', backref=db.backref('payment', uselist=False))
    
    def __repr__(self):
        return f'<Payment {self.id} ${self.amount} {self.status}>'

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan = db.Column(db.String(20), nullable=False)  # mensal, trimestral, anual
    subscription_id = db.Column(db.String(100), nullable=False)  # ID da assinatura no gateway
    status = db.Column(db.String(20), nullable=False)  # active, paused, cancelled
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    next_billing_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Subscription {self.id} {self.plan} {self.status}>'

from datetime import datetime, timedelta
from app import db
import uuid

class License(db.Model):
    __tablename__ = 'licenses'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan = db.Column(db.String(20), nullable=False)  # mensal, trimestral, anual
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    last_check = db.Column(db.DateTime, nullable=True)
    is_cancelled = db.Column(db.Boolean, default=False)
    
    # Relacionamentos
    activations = db.relationship('Activation', backref='license', lazy=True)
    
    def is_active(self):
        """Verifica se a licença está ativa"""
        return not self.is_cancelled and self.expires_at > datetime.utcnow()
    
    def days_left(self):
        """Retorna o número de dias restantes na licença"""
        if not self.is_active():
            return 0
        
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)
    
    def record_check(self):
        """Registra uma verificação de licença"""
        self.last_check = datetime.utcnow()
        db.session.commit()
    
    def extend(self, days):
        """Estende a licença por um número específico de dias"""
        if self.expires_at < datetime.utcnow():
            # Se já expirou, começa do dia atual
            self.expires_at = datetime.utcnow() + timedelta(days=days)
        else:
            # Se ainda está ativa, adiciona dias à data de expiração atual
            self.expires_at = self.expires_at + timedelta(days=days)
        db.session.commit()
    
    def __repr__(self):
        return f'<License {self.key}>'

class Activation(db.Model):
    """Registra ativações da licença em computadores diferentes"""
    __tablename__ = 'activations'
    
    id = db.Column(db.Integer, primary_key=True)
    license_id = db.Column(db.Integer, db.ForeignKey('licenses.id'), nullable=False)
    hardware_id = db.Column(db.String(100), nullable=False)  # ID único do computador
    hostname = db.Column(db.String(100), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    first_activation = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Activation {self.hardware_id} for License {self.license_id}>'

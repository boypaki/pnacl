from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
import uuid

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relacionamentos
    licenses = db.relationship('License', backref='user', lazy=True)
    payments = db.relationship('Payment', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def has_active_license(self):
        """Verifica se o usuário tem licença ativa"""
        for license in self.licenses:
            if license.is_active():
                return True
        return False
    
    def get_active_license(self):
        """Retorna a licença ativa mais recente"""
        active_licenses = [lic for lic in self.licenses if lic.is_active()]
        if active_licenses:
            # Ordenar por data de expiração, pegar a que expira mais tarde
            return sorted(active_licenses, key=lambda x: x.expires_at, reverse=True)[0]
        return None
    
    def __repr__(self):
        return f'<User {self.email}>'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

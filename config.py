import os
from datetime import timedelta

class Config:
    # Configurações básicas
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chave-super-secreta-para-desenvolvimento'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload de arquivos
    UPLOAD_FOLDER = os.path.join('app', 'static', 'downloads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB máximo
    ALLOWED_EXTENSIONS = {'zip', 'exe', 'dmg', 'pkg', 'deb', 'rpm'}
    
    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'suporte@importador.com.br'
    
    # Pagamentos (Stripe)
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    
    # Configurações de Licença
    LICENSE_VALIDITY_DAYS = {
        'mensal': 30,
        'trimestral': 90,
        'anual': 365
    }
    
    # Configurações de sessão
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    
class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    
    # Use HTTPS em produção
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    
    # Use servidor de email em produção
    MAIL_USE_TLS = True

# Configuração a ser usada
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

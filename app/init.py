from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from config import config

# Inicialização de extensões
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
mail = Mail()
migrate = Migrate()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Inicializar extensões
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    
    # Garantir diretório de uploads
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Registrar blueprints
    from app.routes.main import main_blueprint
    from app.routes.auth import auth_blueprint
    from app.routes.downloads import downloads_blueprint
    from app.routes.payment import payment_blueprint
    from app.routes.admin import admin_blueprint
    from app.routes.api import api_blueprint
    
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(downloads_blueprint, url_prefix='/downloads')
    app.register_blueprint(payment_blueprint, url_prefix='/payment')
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    app.register_blueprint(api_blueprint, url_prefix='/api')
    
    # Criar banco de dados se não existir
    with app.app_context():
        db.create_all()
        
        # Criar usuário admin inicial, se não existir
        from app.models.users import User
        if not User.query.filter_by(email='admin@sistema.com').first():
            admin = User(
                name='Administrador',
                email='admin@sistema.com',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
    
    return app

from flask import Blueprint, render_template, request, redirect, url_for, current_app
from flask_login import current_user

from app.models.downloads import Download
from app.models.licenses import License

main_blueprint = Blueprint('main', __name__)

@main_blueprint.route('/')
def index():
    # Obter versões mais recentes para cada plataforma
    latest_versions = {
        'windows': Download.query.filter_by(platform='windows', is_latest=True).first(),
        'mac': Download.query.filter_by(platform='mac', is_latest=True).first(),
        'linux': Download.query.filter_by(platform='linux', is_latest=True).first()
    }
    
    return render_template('index.html', latest_versions=latest_versions)

@main_blueprint.route('/pricing')
def pricing():
    return render_template('pricing.html')

@main_blueprint.route('/features')
def features():
    return render_template('features.html')

@main_blueprint.route('/support')
def support():
    return render_template('support.html')

@main_blueprint.route('/dashboard')
def dashboard():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
        
    # Obter informações do usuário
    user_license = current_user.get_active_license()
    
    # Obter downloads recentes
    downloads = Download.query.filter_by(is_latest=True).all()
    
    return render_template('dashboard/index.html', 
                          license=user_license, 
                          downloads=downloads)

@main_blueprint.route('/contact', methods=['GET', 'POST'])
def contact():
    from app.utils.email_sender import send_contact_email
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # Enviar email
        send_contact_email(name, email, subject, message)
        
        return render_template('contact.html', success=True)
        
    return render_template('contact.html')

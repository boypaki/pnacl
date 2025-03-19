from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from datetime import datetime
import uuid

from app import db
from app.models.users import User
from app.models.licenses import License, Activation
from app.utils.license_manager import verify_license

api_blueprint = Blueprint('api', __name__)

# API para verificação de licença
@api_blueprint.route('/verify-license', methods=['POST'])
def verify_license_api():
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'Dados não fornecidos'
        }), 400
    
    license_key = data.get('license_key')
    hardware_id = data.get('hardware_id')
    hostname = data.get('hostname')
    
    if not license_key or not hardware_id:
        return jsonify({
            'success': False,
            'message': 'Dados incompletos'
        }), 400
    
    # Verificar licença
    result = verify_license(license_key, hardware_id, hostname, request.remote_addr)
    
    if result['success']:
        return jsonify({
            'success': True,
            'message': 'Licença válida',
            'data': {
                'expires_at': result['expires_at'].isoformat(),
                'days_left': result['days_left'],
                'plan': result['plan'],
                'user': result['user_name']
            }
        })
    else:
        return jsonify({
            'success': False,
            'message': result['message']
        }), 401

# API para obter lista de versões
@api_blueprint.route('/versions', methods=['GET'])
def get_versions():
    from app.models.downloads import Download
    
    # Obter parâmetro da plataforma
    platform = request.args.get('platform', 'all')
    
    if platform == 'all':
        downloads = Download.query.order_by(Download.upload_date.desc()).all()
    else:
        downloads = Download.query.filter_by(platform=platform).order_by(Download.upload_date.desc()).all()
    
    # Formatar resposta
    versions = []
    for download in downloads:
        versions.append({
            'id': download.id,
            'version': download.version,
            'platform': download.platform,
            'filename': download.filename,
            'size_bytes': download.size_bytes,
            'is_latest': download.is_latest,
            'description': download.description,
            'upload_date': download.upload_date.isoformat(),
            'download_url': f"/downloads/download/{download.id}"
        })
    
    return jsonify({
        'success': True,
        'versions': versions
    })

# API para registrar uso do aplicativo
@api_blueprint.route('/report-usage', methods=['POST'])
def report_usage():
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'Dados não fornecidos'}), 400
    
    license_key = data.get('license_key')
    hardware_id = data.get('hardware_id')
    usage_data = data.get('usage_data', {})
    
    if not license_key or not hardware_id:
        return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
    
    # Buscar licença
    license = License.query.filter_by(key=license_key).first()
    
    if not license:
        return jsonify({'success': False, 'message': 'Licença não encontrada'}), 404
    
    # Verificar se licença está ativa
    if not license.is_active():
        return jsonify({'success': False, 'message': 'Licença expirada'}), 401
    
    # Registrar uso
    license.record_check()
    
    # Verificar se esta ativação já existe
    activation = Activation.query.filter_by(license_id=license.id, hardware_id=hardware_id).first()
    
    if activation:
        # Atualizar last_seen
        activation.last_seen = datetime.utcnow()
        db.session.commit()
    
    # Registrar dados de uso (se implementado)
    # Esta funcionalidade poderia ser expandida para registrar estatísticas de uso
    
    return jsonify({
        'success': True,
        'message': 'Uso registrado com sucesso'
    })

# API para criação de conta via aplicativo
@api_blueprint.route('/register', methods=['POST'])
def register_api():
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'Dados não fornecidos'}), 400
    
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    
    if not name or not email or not password:
        return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
    
    # Verificar se email já existe
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email já registrado'}), 409
    
    # Criar usuário
    user = User(name=name, email=email)
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    # Enviar email de boas-vindas
    from app.utils.email_sender import send_welcome_email
    send_welcome_email(user)
    
    return jsonify({
        'success': True,
        'message': 'Conta criada com sucesso',
        'user_id': user.id
    })

# API para login via aplicativo
@api_blueprint.route('/login', methods=['POST'])
def login_api():
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'Dados não fornecidos'}), 400
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
    
    # Buscar usuário
    user = User.query.filter_by(email=email).first()
    
    # Verificar usuário e senha
    if not user or not user.check_password(password):
        return jsonify({'success': False, 'message': 'Email ou senha incorretos'}), 401
    
    # Verificar se conta está ativa
    if not user.is_active:
        return jsonify({'success': False, 'message': 'Conta inativa'}), 403
    
    # Atualizar data de último login
    user.last_login = db.func.now()
    db.session.commit()
    
    # Obter licenças do usuário
    licenses = []
    for license in user.licenses:
        if license.is_active():
            licenses.append({
                'key': license.key,
                'plan': license.plan,
                'expires_at': license.expires_at.isoformat(),
                'days_left': license.days_left()
            })
    
    return jsonify({
        'success': True,
        'message': 'Login realizado com sucesso',
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'licenses': licenses
        }
    })

from datetime import datetime
from app import db
from app.models.licenses import License, Activation

def verify_license(license_key, hardware_id, hostname=None, ip_address=None):
    """Verifica a validade de uma licença e registra sua ativação"""
    # Buscar licença
    license = License.query.filter_by(key=license_key).first()
    
    # Verificar se licença existe
    if not license:
        return {
            'success': False,
            'message': 'Licença não encontrada'
        }
    
    # Verificar se licença está cancelada
    if license.is_cancelled:
        return {
            'success': False,
            'message': 'Licença cancelada'
        }
    
    # Verificar se licença expirou
    if license.expires_at <= datetime.utcnow():
        return {
            'success': False,
            'message': 'Licença expirada',
            'expires_at': license.expires_at,
            'days_left': 0
        }
    
    # Registrar verificação
    license.record_check()
    
    # Verificar ativação
    activation = Activation.query.filter_by(
        license_id=license.id,
        hardware_id=hardware_id
    ).first()
    
    # Limite máximo de ativações (geralmente 3-5 por licença)
    max_activations = 3
    
    if not activation:
        # Contar ativações existentes
        active_count = Activation.query.filter_by(
            license_id=license.id,
            is_active=True
        ).count()
        
        if active_count >= max_activations:
            return {
                'success': False,
                'message': f'Limite de {max_activations} ativações atingido'
            }
        
        # Criar nova ativação
        activation = Activation(
            license_id=license.id,
            hardware_id=hardware_id,
            hostname=hostname,
            ip_address=ip_address
        )
        db.session.add(activation)
        db.session.commit()
    else:
        # Atualizar data de ativação
        activation.last_seen = datetime.utcnow()
        activation.hostname = hostname or activation.hostname
        activation.ip_address = ip_address or activation.ip_address
        db.session.commit()
    
    # Obter usuário
    user = license.user
    
    return {
        'success': True,
        'expires_at': license.expires_at,
        'days_left': license.days_left(),
        'plan': license.plan,
        'user_name': user.name
    }

def generate_license(user, plan, days):
    """Gera uma nova licença para o usuário"""
    # Calcular data de expiração
    expires_at = datetime.utcnow() + timedelta(days=days)
    
    # Criar licença
    license = License(
        user_id=user.id,
        plan=plan,
        expires_at=expires_at
    )
    
    db.session.add(license)
    db.session.commit()
    
    return license

def deactivate_hardware(license_id, hardware_id):
    """Desativa um hardware específico"""
    activation = Activation.query.filter_by(
        license_id=license_id,
        hardware_id=hardware_id
    ).first()
    
    if activation:
        activation.is_active = False
        db.session.commit()
        return True
        
    return False

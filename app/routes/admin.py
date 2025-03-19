from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from datetime import datetime

from app import db
from app.models.users import User
from app.models.licenses import License, Activation
from app.models.payments import Payment, Subscription
from app.models.downloads import Download, DownloadLog

admin_blueprint = Blueprint('admin', __name__)

# Verificador de permissão admin
def admin_required(func):
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return func(*args, **kwargs)
    decorated_view.__name__ = func.__name__
    return login_required(decorated_view)

@admin_blueprint.route('/')
@admin_required
def index():
    # Estatísticas
    stats = {
        'total_users': User.query.count(),
        'active_licenses': License.query.filter(License.expires_at > datetime.utcnow()).count(),
        'total_payments': Payment.query.count(),
        'total_downloads': sum([d.download_count for d in Download.query.all()])
    }
    
    # Gráficos de rendimento
    monthly_revenue = db.session.query(
        db.func.strftime('%Y-%m', Payment.created_at).label('month'),
        db.func.sum(Payment.amount).label('total')
    ).filter(Payment.status == 'approved').group_by(db.func.strftime('%Y-%m', Payment.created_at)).all()
    
    revenue_data = {
        'labels': [item[0] for item in monthly_revenue],
        'values': [float(item[1]) for item in monthly_revenue]
    }
    
    # Usuários recentes
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Pagamentos recentes
    recent_payments = Payment.query.order_by(Payment.created_at.desc()).limit(5).all()
    
    return render_template('admin/index.html', 
                          stats=stats, 
                          revenue_data=revenue_data, 
                          recent_users=recent_users,
                          recent_payments=recent_payments)

@admin_blueprint.route('/users')
@admin_required
def users():
    # Parâmetros de paginação e filtro
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    # Consulta base
    query = User.query
    
    # Aplicar filtro se fornecido
    if search:
        query = query.filter(
            (User.name.like(f'%{search}%')) | 
            (User.email.like(f'%{search}%'))
        )
    
    # Paginar resultados
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20)
    
    return render_template('admin/users.html', 
                          pagination=pagination,
                          search=search)

@admin_blueprint.route('/user/<int:user_id>')
@admin_required
def view_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Licenças do usuário
    licenses = License.query.filter_by(user_id=user.id).order_by(License.created_at.desc()).all()
    
    # Pagamentos do usuário
    payments = Payment.query.filter_by(user_id=user.id).order_by(Payment.created_at.desc()).all()
    
    # Assinaturas do usuário
    subscriptions = Subscription.query.filter_by(user_id=user.id).order_by(Subscription.created_at.desc()).all()
    
    # Ativações
    activations = Activation.query.join(License).filter(License.user_id == user.id).all()
    
    return render_template('admin/user_detail.html',
                          user=user,
                          licenses=licenses,
                          payments=payments,
                          subscriptions=subscriptions,
                          activations=activations)

@admin_blueprint.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        # Atualizar dados do usuário
        user.name = request.form.get('name')
        user.email = request.form.get('email')
        
        # Verificar se email já existe em outro usuário
        if User.query.filter(User.email == user.email, User.id != user.id).first():
            flash('Email já está em uso por outro usuário', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user.id))
        
        # Atualizar status
        user.is_active = 'is_active' in request.form
        user.is_admin = 'is_admin' in request.form
        
        # Atualizar senha, se fornecida
        new_password = request.form.get('new_password')
        if new_password:
            user.set_password(new_password)
        
        db.session.commit()
        flash('Usuário atualizado com sucesso', 'success')
        return redirect(url_for('admin.view_user', user_id=user.id))
    
    return render_template('admin/edit_user.html', user=user)

@admin_blueprint.route('/licenses')
@admin_required
def licenses():
    # Parâmetros de paginação e filtro
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    
    # Consulta base
    query = License.query.join(User)
    
    # Filtrar por status
    if status == 'active':
        query = query.filter(License.expires_at > datetime.utcnow(), License.is_cancelled == False)
    elif status == 'expired':
        query = query.filter(License.expires_at <= datetime.utcnow())
    elif status == 'cancelled':
        query = query.filter(License.is_cancelled == True)
    
    # Paginar resultados
    pagination = query.order_by(License.created_at.desc()).paginate(
        page=page, per_page=20)
    
    return render_template('admin/licenses.html', 
                          pagination=pagination,
                          status=status)

@admin_blueprint.route('/license/<int:license_id>')
@admin_required
def view_license(license_id):
    license = License.query.get_or_404(license_id)
    
    # Obter ativações desta licença
    activations = Activation.query.filter_by(license_id=license.id).all()
    
    return render_template('admin/license_detail.html',
                          license=license,
                          activations=activations)

@admin_blueprint.route('/license/<int:license_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_license(license_id):
    license = License.query.get_or_404(license_id)
    
    if request.method == 'POST':
        # Atualizar dados da licença
        license.plan = request.form.get('plan')
        
        # Atualizar data de expiração
        try:
            expires_date = request.form.get('expires_at')
            license.expires_at = datetime.strptime(expires_date, '%Y-%m-%d')
        except:
            flash('Formato de data inválido', 'danger')
            return redirect(url_for('admin.edit_license', license_id=license.id))
        
        # Atualizar status de cancelamento
        license.is_cancelled = 'is_cancelled' in request.form
        
        db.session.commit()
        flash('Licença atualizada com sucesso', 'success')
        return redirect(url_for('admin.view_license', license_id=license.id))
    
    return render_template('admin/edit_license.html', license=license)

@admin_blueprint.route('/payments')
@admin_required
def payments():
    # Parâmetros de paginação e filtro
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    
    # Consulta base
    query = Payment.query.join(User)
    
    # Filtrar por status
    if status != 'all':
        query = query.filter(Payment.status == status)
    
    # Paginar resultados
    pagination = query.order_by(Payment.created_at.desc()).paginate(
        page=page, per_page=20)
    
    return render_template('admin/payments.html', 
                          pagination=pagination,
                          status=status)

@admin_blueprint.route('/payment/<int:payment_id>')
@admin_required
def view_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    return render_template('admin/payment_detail.html', payment=payment)

@admin_blueprint.route('/subscriptions')
@admin_required
def subscriptions():
    # Parâmetros de paginação e filtro
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    
    # Consulta base
    query = Subscription.query.join(User)
    
    # Filtrar por status
    if status != 'all':
        query = query.filter(Subscription.status == status)
    
    # Paginar resultados
    pagination = query.order_by(Subscription.created_at.desc()).paginate(
        page=page, per_page=20)
    
    return render_template('admin/subscriptions.html', 
                          pagination=pagination,
                          status=status)

@admin_blueprint.route('/downloads/stats')
@admin_required
def downloads_stats():
    # Estatísticas gerais
    downloads = Download.query.all()
    
    # Estatísticas por plataforma
    platform_stats = db.session.query(
        Download.platform,
        db.func.sum(Download.download_count).label('total')
    ).group_by(Download.platform).all()
    
    # Estatísticas por versão
    version_stats = db.session.query(
        Download.version,
        db.func.sum(Download.download_count).label('total')
    ).group_by(Download.version).all()
    
    # Logs de download recentes
    recent_logs = DownloadLog.query.order_by(DownloadLog.timestamp.desc()).limit(50).all()
    
    return render_template('admin/download_stats.html',
                          downloads=downloads,
                          platform_stats=platform_stats,
                          version_stats=version_stats,
                          recent_logs=recent_logs)

from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user

from app import db
from app.models.payments import Payment, Subscription
from app.models.licenses import License
from app.utils.payment_gateway import process_payment, create_subscription, cancel_subscription

payment_blueprint = Blueprint('payment', __name__)

@payment_blueprint.route('/checkout/<plan>')
@login_required
def checkout(plan):
    # Verificar se plano é válido
    valid_plans = ['mensal', 'trimestral', 'anual']
    if plan not in valid_plans:
        abort(404)
    
    # Definir preços conforme o plano
    prices = {
        'mensal': 49.90,
        'trimestral': 129.90,
        'anual': 399.90
    }
    
    # Desconto para planos mais longos
    discounts = {
        'mensal': 0,
        'trimestral': 15,  # 15% de desconto
        'anual': 35        # 35% de desconto
    }
    
    # Calcular valores
    base_price = prices[plan]
    discount_percent = discounts[plan]
    discount_amount = (base_price * discount_percent) / 100
    final_price = base_price - discount_amount
    
    return render_template('payment/checkout.html', 
                          plan=plan,
                          base_price=base_price,
                          discount_percent=discount_percent,
                          discount_amount=discount_amount,
                          final_price=final_price,
                          stripe_key=current_app.config['STRIPE_PUBLISHABLE_KEY'])

@payment_blueprint.route('/process', methods=['POST'])
@login_required
def process():
    plan = request.form.get('plan')
    payment_method = request.form.get('payment_method')
    token = request.form.get('token')  # Token do cartão (Stripe)
    
    # Validar plano
    valid_plans = ['mensal', 'trimestral', 'anual']
    if plan not in valid_plans:
        flash('Plano inválido', 'danger')
        return redirect(url_for('payment.checkout', plan=plan))
    
    # Definir preços e dias conforme o plano
    prices = {
        'mensal': 49.90,
        'trimestral': 129.90,
        'anual': 399.90
    }
    
    # Desconto para planos mais longos
    discounts = {
        'mensal': 0,
        'trimestral': 15,  # 15% de desconto
        'anual': 35        # 35% de desconto
    }
    
    # Calcular valores
    base_price = prices[plan]
    discount_percent = discounts[plan]
    discount_amount = (base_price * discount_percent) / 100
    final_price = base_price - discount_amount
    
    # Processar pagamento
    result = process_payment(
        user=current_user,
        amount=final_price,
        payment_method=payment_method,
        token=token,
        plan=plan
    )
    
    if result['success']:
        payment_id = result['payment_id']
        
        # Criar registro de pagamento
        payment = Payment(
            user_id=current_user.id,
            amount=final_price,
            payment_method=payment_method,
            payment_id=payment_id,
            plan=plan,
            status='approved'
        )
        
        db.session.add(payment)
        
        # Calcular dias de validade conforme o plano
        days = current_app.config['LICENSE_VALIDITY_DAYS'][plan]
        
        # Verificar se usuário já tem licença
        existing_license = current_user.get_active_license()
        
        if existing_license:
            # Estender licença existente
            existing_license.extend(days)
            license = existing_license
        else:
            # Criar nova licença
            expires_at = datetime.utcnow() + timedelta(days=days)
            license = License(
                user_id=current_user.id,
                plan=plan,
                expires_at=expires_at
            )
            db.session.add(license)
        
        # Associar pagamento à licença
        payment.license_id = license.id
        
        db.session.commit()
        
        flash('Pagamento processado com sucesso! Sua licença foi ativada.', 'success')
        return redirect(url_for('main.dashboard'))
    
    else:
        flash(f'Erro no pagamento: {result["error"]}', 'danger')
        return redirect(url_for('payment.checkout', plan=plan))

@payment_blueprint.route('/subscribe/<plan>', methods=['POST'])
@login_required
def subscribe(plan):
    # Validar plano
    valid_plans = ['mensal', 'trimestral', 'anual']
    if plan not in valid_plans:
        flash('Plano inválido', 'danger')
        return redirect(url_for('payment.checkout', plan=plan))
    
    token = request.form.get('token')
    
    # Criar assinatura
    result = create_subscription(
        user=current_user,
        plan=plan,
        token=token
    )
    
    if result['success']:
        subscription_id = result['subscription_id']
        
        # Registrar assinatura
        subscription = Subscription(
            user_id=current_user.id,
            plan=plan,
            subscription_id=subscription_id,
            status='active',
            next_billing_date=result['next_billing_date']
        )
        
        db.session.add(subscription)
        
        # Calcular dias de validade conforme o plano
        days = current_app.config['LICENSE_VALIDITY_DAYS'][plan]
        
        # Criar licença
        expires_at = datetime.utcnow() + timedelta(days=days)
        license = License(
            user_id=current_user.id,
            plan=plan,
            expires_at=expires_at
        )
        
        db.session.add(license)
        db.session.commit()
        
        flash('Assinatura criada com sucesso! Sua licença foi ativada.', 'success')
        return redirect(url_for('main.dashboard'))
    
    else:
        flash(f'Erro ao criar assinatura: {result["error"]}', 'danger')
        return redirect(url_for('payment.checkout', plan=plan))
        
@payment_blueprint.route('/cancel-subscription/<int:subscription_id>', methods=['POST'])
@login_required
def cancel_subscription_route(subscription_id):
    # Obter assinatura
    subscription = Subscription.query.get_or_404(subscription_id)
    
    # Verificar se pertence ao usuário atual
    if subscription.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    # Cancelar assinatura no gateway
    result = cancel_subscription(subscription.subscription_id)
    
    if result['success']:
        # Atualizar status
        subscription.status = 'cancelled'
        db.session.commit()
        
        flash('Assinatura cancelada com sucesso.', 'success')
    else:
        flash(f'Erro ao cancelar assinatura: {result["error"]}', 'danger')
    
    return redirect(url_for('auth.profile'))

import stripe
from flask import current_app
from datetime import datetime, timedelta

def setup_stripe():
    """Configura API do Stripe"""
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

def process_payment(user, amount, payment_method, token, plan):
    """Processa pagamento único via Stripe"""
    setup_stripe()
    
    try:
        # Converter para centavos (Stripe usa a menor unidade monetária)
        amount_cents = int(amount * 100)
        
        # Criar cliente se não existir
        customer = get_or_create_customer(user, token)
        
        # Criar cobrança
        charge = stripe.Charge.create(
            amount=amount_cents,
            currency='brl',
            description=f'Licença de Software - Plano {plan.capitalize()}',
            customer=customer.id,
            metadata={
                'user_id': user.id,
                'user_email': user.email,
                'plan': plan
            }
        )
        
        return {
            'success': True,
            'payment_id': charge.id,
            'payment_status': charge.status
        }
        
    except stripe.error.CardError as e:
        # Erro no cartão
        return {
            'success': False,
            'error': e.user_message
        }
    except Exception as e:
        # Outros erros
        return {
            'success': False,
            'error': str(e)
        }

def create_subscription(user, plan, token):
    """Cria uma assinatura recorrente"""
    setup_stripe()
    
    # Mapear planos para IDs de preço do Stripe
    # Estes IDs seriam criados no painel do Stripe
    price_ids = {
        'mensal': 'price_123mensal',
        'trimestral': 'price_123trimestral',
        'anual': 'price_123anual'
    }
    
    try:
        # Criar cliente se não existir
        customer = get_or_create_customer(user, token)
        
        # Criar assinatura
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[
                {"price": price_ids[plan]},
            ],
            metadata={
                'user_id': user.id,
                'user_email': user.email,
                'plan': plan
            }
        )
        
        # Calcular próxima data de cobrança
        next_billing_date = datetime.fromtimestamp(subscription.current_period_end)
        
        return {
            'success': True,
            'subscription_id': subscription.id,
            'status': subscription.status,
            'next_billing_date': next_billing_date
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def cancel_subscription(subscription_id):
    """Cancela uma assinatura existente"""
    setup_stripe()
    
    try:
        # Cancelar assinatura no Stripe
        subscription = stripe.Subscription.retrieve(subscription_id)
        subscription = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True
        )
        
        return {
            'success': True
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_or_create_customer(user, token=None):
    """Obtém cliente existente ou cria um novo"""
    setup_stripe()
    
    # Buscar por clientes com o mesmo email
    customers = stripe.Customer.list(email=user.email)
    
    if customers and customers.data:
        customer = customers.data[0]
        
        # Se token fornecido, atualizar método de pagamento
        if token:
            stripe.Customer.modify(
                customer.id,
                source=token
            )
    else:
        # Criar novo cliente
        customer = stripe.Customer.create(
            email=user.email,
            name=user.name,
            source=token if token else None,
            metadata={
                'user_id': user.id
            }
        )
    
    return customer

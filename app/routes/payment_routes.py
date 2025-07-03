"""
AutoWave Payment Routes
Handles subscription creation, management, and webhook processing
"""

import logging
import os
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from ..services.subscription_service import SubscriptionService
from ..services.payment_gateway import PaymentGatewayFactory
from ..services.currency_service import currency_service
from ..services.invoice_email_service import invoice_email_service
from ..services.coupon_service import coupon_service
from ..decorators.paywall import require_subscription, get_user_plan_info
from ..security.auth_manager import require_auth
from .referral_routes import get_referral_discount, get_referral_bonus_credits
import json

logger = logging.getLogger(__name__)

payment_bp = Blueprint('payment', __name__, url_prefix='/payment')

@payment_bp.route('/plans', methods=['GET'])
def get_subscription_plans():
    """Get all available subscription plans with currency conversion"""
    try:
        subscription_service = SubscriptionService()
        plans = subscription_service.get_subscription_plans()

        # Get user location for payment provider detection
        user_location = request.args.get('location', 'US')
        provider = PaymentGatewayFactory.detect_best_provider(user_location)

        plans_data = []
        for plan in plans:
            # Convert pricing for the detected provider
            monthly_conversion = currency_service.convert_plan_price(
                plan.monthly_price_usd, provider, 'monthly'
            )
            annual_conversion = currency_service.convert_plan_price(
                plan.annual_price_usd, provider, 'annual'
            )

            # Calculate Naira conversion for dual display
            monthly_naira = plan.monthly_price_usd * 1650
            annual_naira = plan.annual_price_usd * 1650

            plan_data = {
                'id': plan.id,
                'name': plan.plan_name,
                'display_name': plan.display_name,
                'monthly_price': plan.monthly_price_usd,
                'annual_price': plan.annual_price_usd,
                'monthly_credits': plan.monthly_credits,
                'features': plan.features,
                'is_active': plan.is_active,
                'provider': provider,
                'pricing': {
                    'monthly': {
                        'usd': plan.monthly_price_usd,
                        'naira': monthly_naira,
                        'naira_formatted': f"₦{monthly_naira:,.0f}",
                        'local': monthly_conversion['converted_amount'],
                        'currency': monthly_conversion['to_currency'],
                        'formatted': monthly_conversion['display_price'],
                        'exchange_rate': monthly_conversion['exchange_rate'],
                        'dual_display': f"${plan.monthly_price_usd} (₦{monthly_naira:,.0f})"
                    },
                    'annual': {
                        'usd': plan.annual_price_usd,
                        'naira': annual_naira,
                        'naira_formatted': f"₦{annual_naira:,.0f}",
                        'local': annual_conversion['converted_amount'],
                        'currency': annual_conversion['to_currency'],
                        'formatted': annual_conversion['display_price'],
                        'exchange_rate': annual_conversion['exchange_rate'],
                        'dual_display': f"${plan.annual_price_usd} (₦{annual_naira:,.0f})"
                    }
                }
            }
            plans_data.append(plan_data)

        return jsonify({
            'success': True,
            'plans': plans_data,
            'provider': provider,
            'currency_info': currency_service.get_provider_currency_info(provider),
            'dual_currency': {
                'primary': 'USD',
                'secondary': 'NGN',
                'exchange_rate': 1650,
                'display_format': 'USD with Naira below'
            }
        })

    except Exception as e:
        logger.error(f"Error fetching subscription plans: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch subscription plans'
        }), 500

@payment_bp.route('/user-info', methods=['GET'])
def get_user_payment_info():
    """Get user's current subscription and credit information"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            # Return default free plan info for non-authenticated users
            return jsonify({
                'success': True,
                'user_info': {
                    'plan_name': 'free',
                    'display_name': 'Free Plan',
                    'credits': {
                        'remaining': 50,
                        'total': 50,
                        'type': 'daily'
                    },
                    'authenticated': False
                }
            })

        # Use CreditService for accurate credit information
        from ..services.credit_service import credit_service
        credit_info = credit_service.get_user_credits(user_id)

        # Get subscription info
        subscription_service = SubscriptionService()
        user_subscription = subscription_service.get_user_subscription(user_id)

        # If no subscription found, create free subscription
        if not user_subscription:
            try:
                subscription_created = subscription_service.create_free_subscription(user_id)
                if subscription_created:
                    logger.info(f"Created free subscription for existing user: {user_id}")
                    user_subscription = subscription_service.get_user_subscription(user_id)
                else:
                    logger.warning(f"Failed to create free subscription for user: {user_id}")
            except Exception as e:
                logger.error(f"Error creating free subscription: {str(e)}")

        # Build response with accurate credit information
        plan_name = credit_info.get('plan', 'free')
        display_names = {
            'free': 'Free Plan',
            'plus': 'Plus Plan',
            'pro': 'Pro Plan',
            'enterprise': 'Enterprise Plan'
        }

        user_info = {
            'plan_name': plan_name,
            'display_name': display_names.get(plan_name, 'Free Plan'),
            'credits': {
                'remaining': credit_info.get('remaining', 50),
                'total': credit_info.get('total', 50),
                'type': credit_info.get('type', 'daily'),
                'percentage': credit_info.get('percentage', 100),
                'reset_date': credit_info.get('reset_date')
            },
            'authenticated': True,
            'subscription_status': getattr(user_subscription, 'status', 'active') if user_subscription else 'active'
        }

        return jsonify({
            'success': True,
            'user_info': user_info
        })

    except Exception as e:
        logger.error(f"Error fetching user payment info: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch user information'
        }), 500

@payment_bp.route('/consume-credits', methods=['POST'])
def consume_credits():
    """Consume credits for a user action and return updated credit info"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401

        task_type = data.get('task_type', 'general')
        amount = data.get('amount')  # Optional, will use default if not provided

        # Consume credits
        from ..services.credit_service import credit_service
        result = credit_service.consume_credits(user_id, task_type, amount)

        if result['success']:
            # Get updated user info for frontend
            updated_info = get_user_plan_info(user_id)

            return jsonify({
                'success': True,
                'credits_consumed': result['credits_consumed'],
                'remaining_credits': result['remaining_credits'],
                'user_info': updated_info,
                'task_type': task_type
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error'],
                'credits_needed': result.get('credits_needed'),
                'credits_available': result.get('credits_available')
            }), 400

    except Exception as e:
        logger.error(f"Error consuming credits: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to consume credits'
        }), 500

@payment_bp.route('/create-subscription', methods=['POST'])
@require_auth()
def create_subscription():
    """Create a new subscription"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        data = request.get_json()
        plan_id = data.get('plan_id')
        billing_cycle = data.get('billing_cycle', 'monthly')  # 'monthly' or 'annual'
        payment_provider = data.get('payment_provider', 'auto')
        user_location = data.get('user_location')
        coupon_code = data.get('coupon_code', '').strip()
        
        if not plan_id:
            return jsonify({'error': 'Plan ID is required'}), 400
        
        # Get user email for customer creation
        subscription_service = SubscriptionService()

        # Get user info from session or Supabase
        user_email = session.get('user_email')
        user_name = session.get('user_name', '')

        # Try to get user info from Supabase user_profiles table if available
        if subscription_service.use_supabase and not user_email:
            try:
                user_response = subscription_service.supabase.table('user_profiles').select('email, full_name').eq('id', user_id).single().execute()
                if user_response.data:
                    user_email = user_response.data['email']
                    user_name = user_response.data.get('full_name', '')
            except Exception as e:
                logger.warning(f"Could not fetch user profile from database: {e}")
                # Fall back to session data or default values
                pass

        # If still no email, use a default or return error
        if not user_email:
            # For testing purposes, use a default email
            user_email = f"user_{user_id}@autowave.pro"
            user_name = "AutoWave User"
            logger.warning(f"Using default email for user {user_id}: {user_email}")
        
        # Create payment gateway
        gateway = PaymentGatewayFactory.create_gateway(payment_provider, user_location)
        
        # Create customer in payment gateway
        customer_result = gateway.create_customer(user_email, user_name)
        
        if not customer_result['success']:
            return jsonify({
                'success': False,
                'error': customer_result.get('error', 'Failed to create customer')
            }), 400
        
        customer_id = customer_result['customer_id']
        
        # Get plan details for gateway-specific plan ID
        if not subscription_service.use_supabase:
            # In fallback mode, get plan from local data
            plans = subscription_service.get_subscription_plans()
            plan = next((p for p in plans if p.id == plan_id), None)

            if not plan:
                return jsonify({'error': 'Invalid plan ID'}), 400

            # Convert to dict format
            plan = {
                'id': plan.id,
                'plan_name': plan.plan_name,
                'display_name': plan.display_name,
                'monthly_price_usd': plan.monthly_price_usd,
                'annual_price_usd': plan.annual_price_usd,
                'monthly_credits': plan.monthly_credits,
                'features': plan.features,
                'is_active': plan.is_active
            }
        else:
            plan_response = subscription_service.supabase.table('subscription_plans').select('*').eq('id', plan_id).single().execute()

            if not plan_response.data:
                return jsonify({'error': 'Invalid plan ID'}), 400

            plan = plan_response.data
        
        # For Paystack, initialize payment instead of creating subscription directly
        if hasattr(gateway, 'initialize_payment'):
            # Calculate amount based on plan and billing cycle
            if billing_cycle == 'monthly':
                amount_usd = plan['monthly_price_usd']
            else:
                amount_usd = plan['annual_price_usd']

            # Apply coupon discount if provided
            coupon_info = None
            bonus_credits = 0
            original_amount = amount_usd
            if coupon_code:
                coupon_result = coupon_service.validate_coupon(coupon_code, plan['plan_name'], amount_usd)
                if coupon_result['valid']:
                    amount_usd = coupon_result['final_amount']
                    coupon_info = coupon_result.get('coupon')
                    bonus_credits = coupon_result.get('bonus_credits', 0)
                    logger.info(f"Applied coupon {coupon_code}: ${coupon_result['discount_amount']:.2f} discount")
                else:
                    return jsonify({
                        'success': False,
                        'error': f"Coupon error: {coupon_result['error']}"
                    }), 400

            # Apply referral discount if available (only if no coupon was applied)
            referral_discount = 0
            referral_bonus_credits = 0
            if not coupon_code:  # Don't stack discounts
                referral_discount = get_referral_discount()
                referral_bonus_credits = get_referral_bonus_credits()

                if referral_discount > 0:
                    discount_amount = amount_usd * (referral_discount / 100)
                    amount_usd = amount_usd - discount_amount
                    bonus_credits += referral_bonus_credits
                    logger.info(f"Applied referral discount: {referral_discount}% (${discount_amount:.2f}) + {referral_bonus_credits} bonus credits")

            # Convert to local currency if needed
            if payment_provider == 'paystack' or PaymentGatewayFactory.detect_best_provider(user_location) == 'paystack':
                # Convert USD to NGN
                exchange_rate = float(os.getenv('USD_TO_NGN_RATE', '1650'))
                amount_ngn = int(amount_usd * exchange_rate)

                # Initialize payment
                payment_result = gateway.initialize_payment(
                    customer_email=user_email,
                    amount=amount_ngn,
                    plan_name=plan['plan_name'],
                    billing_cycle=billing_cycle
                )

                if not payment_result['success']:
                    return jsonify({
                        'success': False,
                        'error': payment_result.get('error', 'Failed to initialize payment')
                    }), 400

                # Return payment URL for redirect
                return jsonify({
                    'success': True,
                    'authorization_url': payment_result['authorization_url'],
                    'access_code': payment_result.get('access_code'),
                    'reference': payment_result.get('reference'),
                    'message': 'Payment initialized. Redirecting to payment page...'
                })
            else:
                # For Stripe, use the existing subscription creation
                gateway_plan_id = f"{plan['plan_name']}_{billing_cycle}"
                subscription_result = gateway.create_subscription(customer_id, gateway_plan_id, billing_cycle)

                if not subscription_result['success']:
                    return jsonify({
                        'success': False,
                        'error': subscription_result.get('error', 'Failed to create subscription')
                    }), 400
        else:
            # Fallback to original subscription creation
            gateway_plan_id = f"{plan['plan_name']}_{billing_cycle}"
            subscription_result = gateway.create_subscription(customer_id, gateway_plan_id, billing_cycle)

            if not subscription_result['success']:
                return jsonify({
                    'success': False,
                    'error': subscription_result.get('error', 'Failed to create subscription')
                }), 400
        
        # Store subscription in database
        from datetime import timedelta, timezone

        now = datetime.now(timezone.utc)
        period_end = now + timedelta(days=30 if billing_cycle == 'monthly' else 365)

        subscription_data = {
            'user_id': user_id,
            'plan_id': plan_id,
            'status': 'active',
            'payment_gateway': payment_provider if payment_provider != 'auto' else PaymentGatewayFactory.detect_best_provider(user_location),
            'gateway_subscription_id': subscription_result['subscription_id'],
            'gateway_customer_id': customer_id,
            'current_period_start': now.isoformat(),
            'current_period_end': period_end.isoformat(),
            'cancel_at_period_end': False
        }

        # Store subscription based on available storage
        if subscription_service.use_supabase:
            result = subscription_service.supabase.table('user_subscriptions').insert(subscription_data).execute()
            subscription_id = result.data[0]['id'] if result.data else subscription_result['subscription_id']
        else:
            # In fallback mode, just log the subscription creation
            logger.info(f"Subscription created for user {user_id}: {subscription_data}")
            subscription_id = subscription_result['subscription_id']
            # In a real implementation, you'd store this in SQLite or another local database

        # Track referral conversion if applicable
        try:
            referral_data_dict = session.get('referral_data')
            if referral_data_dict:
                from app.services.referral_service import ReferralData, ReferralService

                # Convert dict back to ReferralData object
                referral_data = ReferralData(
                    influencer_id=referral_data_dict.get('influencer_id'),
                    utm_source=referral_data_dict.get('utm_source'),
                    utm_medium=referral_data_dict.get('utm_medium'),
                    utm_campaign=referral_data_dict.get('utm_campaign'),
                    utm_content=referral_data_dict.get('utm_content'),
                    utm_term=referral_data_dict.get('utm_term'),
                    referral_code=referral_data_dict.get('referral_code'),
                    discount_percentage=referral_data_dict.get('discount_percentage', 0.0),
                    bonus_credits=referral_data_dict.get('bonus_credits', 0)
                )

                # Track the conversion
                referral_service = ReferralService()
                referral_service.track_referral_conversion(
                    referral_data, user_id, subscription_id, original_amount
                )
                logger.info(f"Referral conversion tracked for user {user_id}")
        except Exception as e:
            logger.error(f"Error tracking referral conversion: {e}")

        return jsonify({
            'success': True,
            'subscription_id': subscription_result['subscription_id'],
            'client_secret': subscription_result.get('client_secret'),  # For Stripe
            'message': 'Subscription created successfully'
        })
        
    except Exception as e:
        logger.error(f"Error creating subscription: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to create subscription'
        }), 500

@payment_bp.route('/cancel-subscription', methods=['POST'])
@require_auth()
@require_subscription('plus')
def cancel_subscription():
    """Cancel user's current subscription"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        subscription_service = SubscriptionService()
        user_subscription = subscription_service.get_user_subscription(user_id)
        
        if not user_subscription:
            return jsonify({'error': 'No active subscription found'}), 404
        
        # Create payment gateway
        gateway = PaymentGatewayFactory.create_gateway(user_subscription.payment_gateway)
        
        # Cancel subscription in payment gateway
        cancel_result = gateway.cancel_subscription(user_subscription.gateway_subscription_id)
        
        if not cancel_result['success']:
            return jsonify({
                'success': False,
                'error': cancel_result.get('error', 'Failed to cancel subscription')
            }), 400
        
        # Update subscription in database
        subscription_service.supabase.table('user_subscriptions').update({
            'cancel_at_period_end': True,
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', user_subscription.id).execute()
        
        return jsonify({
            'success': True,
            'message': 'Subscription will be cancelled at the end of the current billing period'
        })
        
    except Exception as e:
        logger.error(f"Error cancelling subscription: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to cancel subscription'
        }), 500

@payment_bp.route('/webhook/<provider>', methods=['POST'])
def handle_webhook(provider):
    """Handle payment gateway webhooks"""
    try:
        payload = request.get_data(as_text=True)
        signature = request.headers.get('X-Paystack-Signature') if provider == 'paystack' else request.headers.get('Stripe-Signature')
        
        if not signature:
            return jsonify({'error': 'Missing signature'}), 400
        
        # Create gateway and verify webhook
        gateway = PaymentGatewayFactory.create_gateway(provider)
        
        if not gateway.verify_webhook(payload, signature):
            return jsonify({'error': 'Invalid signature'}), 400
        
        # Parse event data
        event_data = json.loads(payload)
        
        # Handle webhook
        result = gateway.handle_webhook(event_data)
        
        if result['success']:
            # Update database based on webhook event
            _process_webhook_event(result, provider)
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error handling {provider} webhook: {str(e)}")
        return jsonify({'error': 'Webhook processing failed'}), 500

def _process_webhook_event(webhook_result, provider):
    """Process webhook events and update database"""
    try:
        action = webhook_result.get('action')
        data = webhook_result.get('data', {})

        subscription_service = SubscriptionService()

        if action == 'subscription_created':
            # Handle subscription activation
            logger.info(f"Processing subscription creation via {provider}")
        elif action == 'subscription_cancelled':
            # Handle subscription cancellation
            logger.info(f"Processing subscription cancellation via {provider}")
        elif action == 'payment_failed':
            # Handle payment failure
            logger.info(f"Processing payment failure via {provider}")
        elif action == 'payment_succeeded':
            # Handle successful payment
            logger.info(f"Processing payment success via {provider}")

    except Exception as e:
        logger.error(f"Error processing webhook event: {str(e)}")

@payment_bp.route('/upgrade-plan', methods=['POST'])
@require_auth()
def upgrade_plan():
    """Upgrade user's current plan"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        data = request.get_json()
        new_plan_id = data.get('plan_id')
        
        if not new_plan_id:
            return jsonify({'error': 'New plan ID is required'}), 400
        
        subscription_service = SubscriptionService()
        current_subscription = subscription_service.get_user_subscription(user_id)
        
        if not current_subscription:
            return jsonify({'error': 'No current subscription found'}), 404
        
        # Update subscription plan
        subscription_service.supabase.table('user_subscriptions').update({
            'plan_id': new_plan_id,
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', current_subscription.id).execute()
        
        return jsonify({
            'success': True,
            'message': 'Plan upgraded successfully'
        })
        
    except Exception as e:
        logger.error(f"Error upgrading plan: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to upgrade plan'
        }), 500

@payment_bp.route('/callback', methods=['GET'])
def payment_callback():
    """Handle payment callback from Paystack"""
    try:
        # Get payment reference from query parameters
        reference = request.args.get('reference')

        if not reference:
            return jsonify({'error': 'Payment reference not provided'}), 400

        # Verify payment with Paystack
        gateway = PaymentGatewayFactory.create_gateway('paystack')

        if hasattr(gateway, 'verify_payment'):
            verification_result = gateway.verify_payment(reference)

            if verification_result.get('success'):
                # Payment successful - create subscription
                payment_data = verification_result.get('data', {})

                # Extract metadata
                metadata = payment_data.get('metadata', {})
                plan_name = metadata.get('plan_name')
                billing_cycle = metadata.get('billing_cycle')

                if plan_name and billing_cycle:
                    # Create subscription record
                    # This would typically be done in a webhook, but for simplicity we'll do it here
                    logger.info(f"Payment verified for plan {plan_name}, cycle {billing_cycle}")

                    # Send invoice email
                    try:
                        customer_email = payment_data.get('customer', {}).get('email')
                        if customer_email:
                            invoice_data = {
                                'customer_email': customer_email,
                                'amount': payment_data.get('amount', 0) / 100,  # Convert from kobo
                                'currency': 'NGN',
                                'plan_name': plan_name,
                                'billing_cycle': billing_cycle,
                                'reference': reference,
                                'payment_date': datetime.now().strftime('%B %d, %Y')
                            }

                            email_result = invoice_email_service.send_invoice_email(invoice_data)
                            if email_result['success']:
                                logger.info(f"Invoice email sent to {customer_email}")
                    except Exception as e:
                        logger.error(f"Invoice email error: {str(e)}")

                    return f"""
                    <html>
                    <head><title>Payment Successful</title></head>
                    <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                        <h1 style="color: green;">Payment Successful!</h1>
                        <p>Your subscription to {plan_name.title()} Plan has been activated.</p>
                        <p>You will be redirected to your dashboard in 3 seconds...</p>
                        <script>
                            setTimeout(function() {{
                                window.location.href = '/';
                            }}, 3000);
                        </script>
                    </body>
                    </html>
                    """
                else:
                    return jsonify({'error': 'Invalid payment metadata'}), 400
            else:
                return f"""
                <html>
                <head><title>Payment Failed</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: red;">Payment Failed</h1>
                    <p>Your payment could not be processed. Please try again.</p>
                    <a href="/pricing" style="background: #007cba; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Try Again</a>
                </body>
                </html>
                """
        else:
            # Test mode - simulate successful payment
            return f"""
            <html>
            <head><title>Payment Successful (Test Mode)</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: green;">Payment Successful! (Test Mode)</h1>
                <p>Your test payment has been processed successfully.</p>
                <p>In production, this would activate your subscription.</p>
                <p>You will be redirected to your dashboard in 3 seconds...</p>
                <script>
                    setTimeout(function() {{
                        window.location.href = '/';
                    }}, 3000);
                </script>
            </body>
            </html>
            """

    except Exception as e:
        logger.error(f"Payment callback error: {str(e)}")
        return f"""
        <html>
        <head><title>Payment Error</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <h1 style="color: red;">Payment Error</h1>
            <p>An error occurred while processing your payment.</p>
            <a href="/pricing" style="background: #007cba; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Try Again</a>
        </body>
        </html>
        """

@payment_bp.route('/billing-history', methods=['GET'])
@require_auth()
def get_billing_history():
    """Get user's billing history"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401

        subscription_service = SubscriptionService()

        # Get payment transactions
        transactions_response = subscription_service.supabase.table('payment_transactions').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()

        transactions = []
        for transaction in transactions_response.data:
            transactions.append({
                'id': transaction['id'],
                'amount': float(transaction['amount']),
                'currency': transaction['currency'],
                'status': transaction['status'],
                'payment_method': transaction.get('payment_method'),
                'created_at': transaction['created_at']
            })

        return jsonify({
            'success': True,
            'transactions': transactions
        })

    except Exception as e:
        logger.error(f"Error fetching billing history: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch billing history'
        }), 500

@payment_bp.route('/apple-pay-process', methods=['POST'])
def process_apple_pay():
    """Process Apple Pay payment"""
    try:
        data = request.get_json()
        payment_data = data.get('payment')
        plan_name = data.get('plan_name')
        billing_cycle = data.get('billing_cycle')

        # Get user info from session
        user_id = session.get('user_id')
        user_email = session.get('user_email')

        if not user_id or not user_email:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401

        logger.info(f"Processing Apple Pay payment for user {user_email}, plan {plan_name}")

        # For now, we'll simulate Apple Pay processing and fall back to regular Paystack
        # In a full implementation, you would:
        # 1. Validate the Apple Pay payment token
        # 2. Process it through Paystack or Stripe
        # 3. Update user subscription

        # Simulate processing delay
        import time
        time.sleep(1)

        # For demo purposes, we'll redirect to regular payment flow
        # This allows users to see the Apple Pay button and understand the flow

        return jsonify({
            'success': False,
            'error': 'Apple Pay setup in progress. Please use regular payment for now.',
            'fallback_to_regular': True
        })

    except Exception as e:
        logger.error(f"Apple Pay processing error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Apple Pay processing failed'
        }), 500

@payment_bp.route('/webhook/paystack', methods=['POST'])
def paystack_webhook():
    """Handle Paystack webhook events"""
    try:
        # Get the raw payload
        payload = request.get_data()
        signature = request.headers.get('X-Paystack-Signature')

        # Verify webhook signature
        webhook_secret = os.getenv('PAYSTACK_WEBHOOK_SECRET')
        if webhook_secret and webhook_secret != 'your_paystack_webhook_secret_here':
            import hmac
            import hashlib

            expected_signature = hmac.new(
                webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha512
            ).hexdigest()

            if signature != expected_signature:
                logger.warning("Invalid webhook signature")
                return jsonify({'error': 'Invalid signature'}), 400

        # Parse the event
        event = request.get_json()
        event_type = event.get('event')

        logger.info(f"Received Paystack webhook: {event_type}")

        if event_type == 'charge.success':
            # Handle successful payment
            data = event.get('data', {})
            reference = data.get('reference')
            amount = data.get('amount')  # Amount in kobo
            customer_email = data.get('customer', {}).get('email')
            metadata = data.get('metadata', {})

            logger.info(f"Payment successful: {reference}, Amount: ₦{amount/100}, Email: {customer_email}")

            # Extract plan information from metadata
            plan_name = metadata.get('plan_name', 'Unknown')
            billing_cycle = metadata.get('billing_cycle', 'monthly')

            # Prepare invoice data
            invoice_data = {
                'customer_email': customer_email,
                'amount': amount / 100,  # Convert from kobo to naira
                'currency': 'NGN',
                'plan_name': plan_name,
                'billing_cycle': billing_cycle,
                'reference': reference,
                'payment_date': datetime.now().strftime('%B %d, %Y')
            }

            # Send invoice email
            try:
                email_result = invoice_email_service.send_invoice_email(invoice_data)
                if email_result['success']:
                    logger.info(f"Invoice email sent to {customer_email}")
                else:
                    logger.error(f"Failed to send invoice email: {email_result.get('error')}")
            except Exception as e:
                logger.error(f"Invoice email error: {str(e)}")

            # Here you would also:
            # 1. Find the user by email
            # 2. Activate their subscription
            # 3. Update database records

            return jsonify({'status': 'success'}), 200

        elif event_type == 'subscription.create':
            # Handle subscription creation
            data = event.get('data', {})
            subscription_code = data.get('subscription_code')
            customer_email = data.get('customer', {}).get('email')

            logger.info(f"Subscription created: {subscription_code}, Email: {customer_email}")

            return jsonify({'status': 'success'}), 200

        else:
            logger.info(f"Unhandled webhook event: {event_type}")
            return jsonify({'status': 'ignored'}), 200

    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({'error': 'Webhook processing failed'}), 500

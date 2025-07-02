"""
AutoWave Referral Routes
Handles influencer referral tracking, UTM parameters, and discount codes
"""

import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
from app.services.referral_service import ReferralService, ReferralData

logger = logging.getLogger(__name__)

# Create blueprint
referral_bp = Blueprint('referral', __name__, url_prefix='/referral')

# Initialize referral service
referral_service = ReferralService()

@referral_bp.route('/track', methods=['GET', 'POST'])
def track_referral():
    """
    Track referral from UTM parameters or referral code.
    This endpoint is called when users visit with referral links.
    """
    try:
        # Get UTM parameters from URL
        utm_params = {}
        utm_keys = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term']
        
        for key in utm_keys:
            value = request.args.get(key)
            if value:
                utm_params[key] = value
        
        # Get referral code if provided
        referral_code = request.args.get('ref') or request.args.get('referral_code')
        
        # Process referral data
        referral_data = referral_service.process_referral(utm_params, referral_code)
        
        # Store referral data in session
        if referral_data.influencer_id:
            session['referral_data'] = {
                'influencer_id': referral_data.influencer_id,
                'utm_source': referral_data.utm_source,
                'utm_medium': referral_data.utm_medium,
                'utm_campaign': referral_data.utm_campaign,
                'utm_content': referral_data.utm_content,
                'utm_term': referral_data.utm_term,
                'referral_code': referral_data.referral_code,
                'discount_percentage': referral_data.discount_percentage,
                'bonus_credits': referral_data.bonus_credits,
                'created_at': referral_data.created_at.isoformat() if referral_data.created_at else None
            }
            
            # Track the visit
            user_id = session.get('user_id')
            ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
            referral_service.track_referral_visit(referral_data, user_id, ip_address)
            
            logger.info(f"Referral tracked: {referral_data.utm_source or referral_data.referral_code}")
        
        # Return referral information
        return jsonify({
            'success': True,
            'referral_active': bool(referral_data.influencer_id),
            'discount_percentage': referral_data.discount_percentage,
            'bonus_credits': referral_data.bonus_credits,
            'influencer_name': referral_data.utm_source,
            'message': f"Welcome! You'll get {referral_data.discount_percentage}% off and {referral_data.bonus_credits} bonus credits!" if referral_data.influencer_id else "Welcome to AutoWave!"
        })
        
    except Exception as e:
        logger.error(f"Error tracking referral: {e}")
        return jsonify({'success': False, 'error': 'Failed to track referral'}), 500

@referral_bp.route('/get-discount', methods=['GET'])
def get_referral_discount():
    """Get discount information for a UTM source."""
    try:
        utm_source = request.args.get('utm_source', '').strip()

        if not utm_source:
            return jsonify({
                'success': False,
                'error': 'UTM source is required'
            }), 400

        # Get influencer by UTM source
        influencer = referral_service.get_influencer_by_utm_source(utm_source)

        if influencer and influencer.is_active:
            # Store referral data in session
            session['referral_data'] = {
                'utm_source': utm_source,
                'discount_percentage': influencer.discount_percentage,
                'bonus_credits': influencer.bonus_credits,
                'influencer_id': influencer.id,
                'partner_name': influencer.name,
                'created_at': datetime.utcnow().isoformat()
            }

            return jsonify({
                'success': True,
                'discount_percentage': influencer.discount_percentage,
                'bonus_credits': influencer.bonus_credits,
                'partner_name': influencer.name,
                'message': f'{influencer.discount_percentage}% discount + {influencer.bonus_credits} bonus credits via {influencer.name} partnership'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No active referral found for this source'
            }), 404

    except Exception as e:
        logger.error(f"Error getting referral discount: {e}")
        return jsonify({'success': False, 'error': 'Failed to get referral discount'}), 500

@referral_bp.route('/apply-code', methods=['POST'])
def apply_referral_code():
    """
    Apply a referral code manually.
    Used when users enter a code during signup or checkout.
    """
    try:
        data = request.get_json()
        referral_code = data.get('referral_code', '').strip().upper()
        
        if not referral_code:
            return jsonify({'success': False, 'error': 'Referral code is required'}), 400
        
        # Process referral code
        referral_data = referral_service.process_referral(referral_code=referral_code)
        
        if referral_data.influencer_id:
            # Store in session
            session['referral_data'] = {
                'influencer_id': referral_data.influencer_id,
                'referral_code': referral_data.referral_code,
                'discount_percentage': referral_data.discount_percentage,
                'bonus_credits': referral_data.bonus_credits,
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Track the visit
            user_id = session.get('user_id')
            ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
            referral_service.track_referral_visit(referral_data, user_id, ip_address)
            
            return jsonify({
                'success': True,
                'discount_percentage': referral_data.discount_percentage,
                'bonus_credits': referral_data.bonus_credits,
                'message': f"Referral code applied! You'll get {referral_data.discount_percentage}% off and {referral_data.bonus_credits} bonus credits!"
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid referral code'
            }), 400
            
    except Exception as e:
        logger.error(f"Error applying referral code: {e}")
        return jsonify({'success': False, 'error': 'Failed to apply referral code'}), 500

@referral_bp.route('/status', methods=['GET'])
def get_referral_status():
    """
    Get current referral status for the user.
    """
    try:
        referral_data = session.get('referral_data')
        
        if referral_data:
            return jsonify({
                'success': True,
                'has_referral': True,
                'discount_percentage': referral_data.get('discount_percentage', 0),
                'bonus_credits': referral_data.get('bonus_credits', 0),
                'referral_code': referral_data.get('referral_code'),
                'utm_source': referral_data.get('utm_source')
            })
        else:
            return jsonify({
                'success': True,
                'has_referral': False,
                'discount_percentage': 0,
                'bonus_credits': 0
            })
            
    except Exception as e:
        logger.error(f"Error getting referral status: {e}")
        return jsonify({'success': False, 'error': 'Failed to get referral status'}), 500

@referral_bp.route('/clear', methods=['POST'])
def clear_referral():
    """
    Clear referral data from session.
    """
    try:
        if 'referral_data' in session:
            del session['referral_data']
        
        return jsonify({'success': True, 'message': 'Referral data cleared'})
        
    except Exception as e:
        logger.error(f"Error clearing referral: {e}")
        return jsonify({'success': False, 'error': 'Failed to clear referral'}), 500

@referral_bp.route('/influencers', methods=['GET'])
def get_active_influencers():
    """
    Get list of active influencers (public information only).
    """
    try:
        if not referral_service.use_supabase:
            # Return fallback data
            return jsonify({
                'success': True,
                'influencers': [
                    {
                        'name': 'Matthew Berman',
                        'utm_source': 'MatthewBerman',
                        'referral_code': 'MATTHEW20',
                        'discount_percentage': 20.0,
                        'bonus_credits': 100
                    },
                    {
                        'name': 'AI Explained',
                        'utm_source': 'AIExplained',
                        'referral_code': 'AIEXPLAINED15',
                        'discount_percentage': 15.0,
                        'bonus_credits': 50
                    }
                ]
            })
        
        # Get from database
        result = referral_service.client.table('public_influencers').select('*').execute()
        
        return jsonify({
            'success': True,
            'influencers': result.data if result.data else []
        })
        
    except Exception as e:
        logger.error(f"Error getting influencers: {e}")
        return jsonify({'success': False, 'error': 'Failed to get influencers'}), 500

@referral_bp.route('/admin')
def admin_referrals():
    """Admin interface for managing referral links."""
    return render_template('admin_referrals.html')

@referral_bp.route('/partners', methods=['GET'])
def get_partners():
    """Get all referral partners."""
    try:
        if referral_service.use_supabase:
            result = referral_service.client.table('influencers').select('*').execute()
            partners = result.data if result.data else []
        else:
            # Use fallback data
            partners = [
                {
                    'id': 'partner-001',
                    'name': 'Tech Partner A',
                    'utm_source': 'TechPartnerA',
                    'discount_percentage': 20.0,
                    'bonus_credits': 100,
                    'commission_rate': 10.0,
                    'total_referrals': 0,
                    'is_active': True
                },
                {
                    'id': 'partner-002',
                    'name': 'AI Partner B',
                    'utm_source': 'AIPartnerB',
                    'discount_percentage': 15.0,
                    'bonus_credits': 50,
                    'commission_rate': 8.0,
                    'total_referrals': 0,
                    'is_active': True
                },
                {
                    'id': 'partner-003',
                    'name': 'Premium Partner C',
                    'utm_source': 'PremiumPartnerC',
                    'discount_percentage': 30.0,
                    'bonus_credits': 150,
                    'commission_rate': 12.0,
                    'total_referrals': 0,
                    'is_active': True
                }
            ]

        return jsonify({
            'success': True,
            'partners': partners
        })

    except Exception as e:
        logger.error(f"Error getting partners: {e}")
        return jsonify({'success': False, 'error': 'Failed to get partners'}), 500

@referral_bp.route('/create-partner', methods=['POST'])
def create_partner():
    """Create a new referral partner."""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['name', 'utm_source', 'discount_percentage', 'bonus_credits', 'commission_rate']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing field: {field}'}), 400

        # Generate partner ID
        partner_id = f"partner-{data['utm_source'].lower()}"
        email = f"{data['utm_source'].lower()}@autowave.pro"

        partner_data = {
            'id': partner_id,
            'name': data['name'],
            'email': email,
            'utm_source': data['utm_source'],
            'referral_code': data.get('referral_code', data['utm_source'].upper()),
            'discount_percentage': float(data['discount_percentage']),
            'bonus_credits': int(data['bonus_credits']),
            'commission_rate': float(data['commission_rate']),
            'is_active': True,
            'total_referrals': 0,
            'total_revenue': 0.0
        }

        if referral_service.use_supabase:
            # Insert into database
            result = referral_service.client.table('influencers').insert(partner_data).execute()
            if not result.data:
                return jsonify({'success': False, 'error': 'Failed to create partner'}), 500

        return jsonify({
            'success': True,
            'partner': partner_data,
            'referral_url': f"https://autowave.pro/?utm_source={data['utm_source']}&utm_medium={data.get('utm_medium', 'Youtube')}&utm_campaign=partnership"
        })

    except Exception as e:
        logger.error(f"Error creating partner: {e}")
        return jsonify({'success': False, 'error': 'Failed to create partner'}), 500

@referral_bp.route('/generate-link/<influencer_id>', methods=['GET'])
def generate_referral_link(influencer_id):
    """
    Generate a referral link for an influencer.
    """
    try:
        base_url = request.args.get('base_url', 'https://autowave.pro')
        referral_link = referral_service.generate_referral_link(influencer_id, base_url)
        
        return jsonify({
            'success': True,
            'referral_link': referral_link
        })
        
    except Exception as e:
        logger.error(f"Error generating referral link: {e}")
        return jsonify({'success': False, 'error': 'Failed to generate referral link'}), 500

@referral_bp.route('/dashboard/<influencer_id>', methods=['GET'])
def get_influencer_dashboard(influencer_id):
    """
    Get dashboard data for an influencer.
    """
    try:
        dashboard_data = referral_service.get_influencer_dashboard_data(influencer_id)
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Error getting influencer dashboard: {e}")
        return jsonify({'success': False, 'error': 'Failed to get dashboard data'}), 500

@referral_bp.route('/convert', methods=['POST'])
def track_conversion():
    """
    Track a referral conversion (internal endpoint).
    Called when a user with referral data makes a purchase.
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        subscription_id = data.get('subscription_id')
        amount = data.get('amount', 0.0)
        
        if not user_id or not subscription_id:
            return jsonify({'success': False, 'error': 'Missing required data'}), 400
        
        # Get referral data from session or database
        referral_data_dict = session.get('referral_data')
        
        if referral_data_dict:
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
            success = referral_service.track_referral_conversion(
                referral_data, user_id, subscription_id, amount
            )
            
            if success:
                # Mark user referral as converted
                if referral_service.use_supabase:
                    try:
                        referral_service.client.table('user_referrals').update({
                            'is_converted': True,
                            'converted_at': datetime.utcnow().isoformat()
                        }).eq('user_id', user_id).execute()
                    except Exception as e:
                        logger.warning(f"Could not update user referral status: {e}")
                
                return jsonify({
                    'success': True,
                    'message': 'Conversion tracked successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to track conversion'
                }), 500
        else:
            return jsonify({
                'success': True,
                'message': 'No referral data to track'
            })
            
    except Exception as e:
        logger.error(f"Error tracking conversion: {e}")
        return jsonify({'success': False, 'error': 'Failed to track conversion'}), 500

# Helper function to get referral discount for payment processing
def get_referral_discount():
    """
    Get current referral discount percentage from session.
    Used by payment routes to apply discounts.
    """
    try:
        referral_data = session.get('referral_data')
        if referral_data:
            return referral_data.get('discount_percentage', 0.0)
        return 0.0
    except Exception:
        return 0.0

# Helper function to get referral bonus credits
def get_referral_bonus_credits():
    """
    Get current referral bonus credits from session.
    Used when creating user accounts.
    """
    try:
        referral_data = session.get('referral_data')
        if referral_data:
            return referral_data.get('bonus_credits', 0)
        return 0
    except Exception:
        return 0

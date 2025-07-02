"""
AutoWave Currency Conversion Service
Handles multi-currency support for payment gateways
"""

import os
import logging
import requests
from typing import Dict, Any, Optional
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)

class CurrencyService:
    """Handles currency conversion for payment processing"""
    
    def __init__(self):
        self.base_currency = os.getenv('PAYMENT_CURRENCY', 'USD')
        self.exchange_rate_mode = os.getenv('EXCHANGE_RATE_MODE', 'fixed')
        self.usd_to_ngn_rate = float(os.getenv('USD_TO_NGN_RATE', '1650'))
        
        # Currency configurations for different payment providers
        self.provider_currencies = {
            'paystack': {
                'currency': os.getenv('PAYSTACK_CURRENCY', 'NGN'),
                'country': os.getenv('PAYSTACK_COUNTRY', 'NG'),
                'symbol': '₦',
                'decimal_places': 2
            },
            'stripe': {
                'currency': 'USD',
                'country': 'US',
                'symbol': '$',
                'decimal_places': 2
            }
        }
    
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """Get exchange rate between two currencies"""
        try:
            if from_currency == to_currency:
                return 1.0
            
            # Handle USD to NGN conversion
            if from_currency == 'USD' and to_currency == 'NGN':
                if self.exchange_rate_mode == 'live':
                    return self._get_live_exchange_rate('USD', 'NGN')
                else:
                    return self.usd_to_ngn_rate
            
            # Handle NGN to USD conversion
            if from_currency == 'NGN' and to_currency == 'USD':
                if self.exchange_rate_mode == 'live':
                    return 1 / self._get_live_exchange_rate('USD', 'NGN')
                else:
                    return 1 / self.usd_to_ngn_rate
            
            # For other currency pairs, use live rates if available
            if self.exchange_rate_mode == 'live':
                return self._get_live_exchange_rate(from_currency, to_currency)
            
            # Fallback to 1:1 for unsupported pairs
            logger.warning(f"No exchange rate available for {from_currency} to {to_currency}, using 1:1")
            return 1.0
            
        except Exception as e:
            logger.error(f"Error getting exchange rate: {str(e)}")
            # Fallback to fixed rate for USD/NGN
            if from_currency == 'USD' and to_currency == 'NGN':
                return self.usd_to_ngn_rate
            return 1.0
    
    def _get_live_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """Fetch live exchange rate from external API"""
        try:
            # Using a free exchange rate API (you can replace with your preferred service)
            url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                rate = data.get('rates', {}).get(to_currency)
                if rate:
                    return float(rate)
            
            # Fallback to fixed rate
            logger.warning(f"Failed to get live rate for {from_currency}/{to_currency}, using fixed rate")
            if from_currency == 'USD' and to_currency == 'NGN':
                return self.usd_to_ngn_rate
            return 1.0
            
        except Exception as e:
            logger.error(f"Error fetching live exchange rate: {str(e)}")
            return self.usd_to_ngn_rate if from_currency == 'USD' and to_currency == 'NGN' else 1.0
    
    def convert_amount(self, amount: float, from_currency: str, to_currency: str) -> Dict[str, Any]:
        """Convert amount from one currency to another"""
        try:
            if from_currency == to_currency:
                return {
                    'original_amount': amount,
                    'converted_amount': amount,
                    'from_currency': from_currency,
                    'to_currency': to_currency,
                    'exchange_rate': 1.0,
                    'formatted_amount': self._format_amount(amount, to_currency)
                }
            
            exchange_rate = self.get_exchange_rate(from_currency, to_currency)
            converted_amount = amount * exchange_rate
            
            # Round to appropriate decimal places
            decimal_places = self.provider_currencies.get(to_currency.lower(), {}).get('decimal_places', 2)
            converted_amount = float(Decimal(str(converted_amount)).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            ))
            
            return {
                'original_amount': amount,
                'converted_amount': converted_amount,
                'from_currency': from_currency,
                'to_currency': to_currency,
                'exchange_rate': exchange_rate,
                'formatted_amount': self._format_amount(converted_amount, to_currency)
            }
            
        except Exception as e:
            logger.error(f"Error converting amount: {str(e)}")
            return {
                'original_amount': amount,
                'converted_amount': amount,
                'from_currency': from_currency,
                'to_currency': to_currency,
                'exchange_rate': 1.0,
                'formatted_amount': self._format_amount(amount, from_currency),
                'error': str(e)
            }
    
    def _format_amount(self, amount: float, currency: str) -> str:
        """Format amount with appropriate currency symbol"""
        try:
            # Get currency info
            currency_info = None
            for provider, info in self.provider_currencies.items():
                if info['currency'] == currency.upper():
                    currency_info = info
                    break
            
            if not currency_info:
                return f"{amount:.2f} {currency}"
            
            symbol = currency_info.get('symbol', currency)
            decimal_places = currency_info.get('decimal_places', 2)
            
            # Format with appropriate decimal places
            if currency.upper() == 'NGN':
                # For Naira, format with commas for thousands
                return f"{symbol}{amount:,.{decimal_places}f}"
            else:
                return f"{symbol}{amount:.{decimal_places}f}"
                
        except Exception as e:
            logger.error(f"Error formatting amount: {str(e)}")
            return f"{amount:.2f} {currency}"
    
    def get_provider_currency_info(self, provider: str) -> Dict[str, Any]:
        """Get currency information for a payment provider"""
        return self.provider_currencies.get(provider.lower(), {
            'currency': 'USD',
            'country': 'US',
            'symbol': '$',
            'decimal_places': 2
        })
    
    def convert_plan_price(self, plan_price_usd: float, provider: str, billing_cycle: str = 'monthly') -> Dict[str, Any]:
        """Convert plan price to provider's currency"""
        try:
            provider_info = self.get_provider_currency_info(provider)
            target_currency = provider_info['currency']
            
            conversion_result = self.convert_amount(plan_price_usd, 'USD', target_currency)
            
            # Add provider-specific information
            conversion_result.update({
                'provider': provider,
                'billing_cycle': billing_cycle,
                'currency_info': provider_info,
                'display_price': conversion_result['formatted_amount']
            })
            
            return conversion_result
            
        except Exception as e:
            logger.error(f"Error converting plan price: {str(e)}")
            return {
                'original_amount': plan_price_usd,
                'converted_amount': plan_price_usd,
                'from_currency': 'USD',
                'to_currency': 'USD',
                'exchange_rate': 1.0,
                'formatted_amount': f"${plan_price_usd:.2f}",
                'provider': provider,
                'billing_cycle': billing_cycle,
                'error': str(e)
            }

# Global currency service instance
currency_service = CurrencyService()

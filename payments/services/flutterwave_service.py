"""
Flutterwave Payment Integration

Service for processing international payments via Flutterwave API
including cards, bank transfers, and other payment methods.
"""

import hashlib
import hmac
import json
import logging
import requests
import uuid
from decimal import Decimal
from django.conf import settings
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class FlutterwaveService:
    """
    Flutterwave payment processing service
    """
    
    def __init__(self):
        self.config = settings.PAYMENT_CONFIG['FLUTTERWAVE']
        self.base_url = 'https://api.flutterwave.com/v3' if self.config['ENVIRONMENT'] == 'live' else 'https://api.flutterwave.com/v3'
        
    def _get_headers(self) -> Dict[str, str]:
        """
        Get common headers for Flutterwave API requests
        """
        return {
            'Authorization': f'Bearer {self.config["SECRET_KEY"]}',
            'Content-Type': 'application/json',
        }
    
    def _generate_tx_ref(self) -> str:
        """
        Generate unique transaction reference
        """
        return f"bematore_{uuid.uuid4().hex[:12]}"
    
    def initiate_card_payment(self, amount: float, currency: str, email: str, 
                            phone_number: str, name: str, redirect_url: str,
                            tx_ref: Optional[str] = None) -> Dict:
        """
        Initiate card payment via Flutterwave Standard
        """
        try:
            if not tx_ref:
                tx_ref = self._generate_tx_ref()
                
            payment_url = f"{self.base_url}/payments"
            
            payload = {
                "tx_ref": tx_ref,
                "amount": str(amount),
                "currency": currency.upper(),
                "redirect_url": redirect_url,
                "payment_options": "card,banktransfer,ussd",
                "customer": {
                    "email": email,
                    "phonenumber": phone_number,
                    "name": name
                },
                "customizations": {
                    "title": "Bematore Payment",
                    "description": "Payment for Bematore services",
                    "logo": "https://bematore.com/logo.png"
                },
                "meta": {
                    "source": "bematore_payment_system",
                    "platform": "web"
                }
            }
            
            response = requests.post(
                payment_url, 
                json=payload, 
                headers=self._get_headers(),
                timeout=30
            )
            
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('status') == 'success':
                data = response_data.get('data', {})
                
                logger.info(f"Flutterwave payment initiated: {tx_ref}")
                
                return {
                    'success': True,
                    'tx_ref': tx_ref,
                    'payment_link': data.get('link'),
                    'hosted_link': data.get('link'),
                    'response_data': response_data
                }
            else:
                error_message = response_data.get('message', 'Payment initiation failed')
                logger.error(f"Flutterwave payment initiation failed: {error_message}")
                
                return {
                    'success': False,
                    'error_message': error_message,
                    'response_data': response_data
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Flutterwave API request failed: {e}")
            return {
                'success': False,
                'error_message': 'Network error occurred. Please try again.',
                'error_details': str(e)
            }
        except Exception as e:
            logger.error(f"Flutterwave payment initiation error: {e}")
            return {
                'success': False,
                'error_message': str(e)
            }
    
    def verify_payment(self, tx_ref: str) -> Dict:
        """
        Verify payment status using transaction reference
        """
        try:
            verify_url = f"{self.base_url}/transactions/verify_by_reference"
            
            params = {'tx_ref': tx_ref}
            
            response = requests.get(
                verify_url,
                params=params,
                headers=self._get_headers(),
                timeout=30
            )
            
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('status') == 'success':
                data = response_data.get('data', {})
                status = data.get('status', '').lower()
                
                # Map Flutterwave status to our status
                payment_status = self._map_payment_status(status)
                
                return {
                    'success': True,
                    'status': payment_status,
                    'flw_ref': data.get('flw_ref'),
                    'tx_ref': data.get('tx_ref'),
                    'amount': data.get('amount'),
                    'currency': data.get('currency'),
                    'charged_amount': data.get('charged_amount'),
                    'app_fee': data.get('app_fee'),
                    'merchant_fee': data.get('merchant_fee'),
                    'payment_type': data.get('payment_type'),
                    'created_at': data.get('created_at'),
                    'raw_response': response_data
                }
            else:
                error_message = response_data.get('message', 'Payment verification failed')
                logger.error(f"Flutterwave payment verification failed: {error_message}")
                
                return {
                    'success': False,
                    'error_message': error_message,
                    'response_data': response_data
                }
                
        except Exception as e:
            logger.error(f"Flutterwave payment verification error: {e}")
            return {
                'success': False,
                'error_message': str(e)
            }
    
    def process_webhook(self, webhook_data: Dict, signature: str) -> Dict:
        """
        Process Flutterwave webhook notification
        """
        try:
            # Verify webhook signature
            if not self._verify_webhook_signature(webhook_data, signature):
                logger.warning("Invalid Flutterwave webhook signature")
                return {
                    'success': False,
                    'error_message': 'Invalid webhook signature'
                }
            
            # Extract payment data
            data = webhook_data.get('data', {})
            tx_ref = data.get('tx_ref')
            status = data.get('status', '').lower()
            
            payment_status = self._map_payment_status(status)
            
            result = {
                'success': True,
                'tx_ref': tx_ref,
                'flw_ref': data.get('flw_ref'),
                'status': payment_status,
                'amount': data.get('amount'),
                'currency': data.get('currency'),
                'payment_type': data.get('payment_type'),
                'customer_email': data.get('customer', {}).get('email'),
                'customer_phone': data.get('customer', {}).get('phone_number'),
                'raw_webhook': webhook_data
            }
            
            logger.info(f"Processed Flutterwave webhook: {tx_ref} - {payment_status}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing Flutterwave webhook: {e}")
            return {
                'success': False,
                'error_message': str(e),
                'raw_webhook': webhook_data
            }
    
    def _verify_webhook_signature(self, webhook_data: Dict, signature: str) -> bool:
        """
        Verify Flutterwave webhook signature
        """
        try:
            if not signature or not self.config.get('WEBHOOK_SECRET'):
                return False
                
            # Create hash using webhook secret
            webhook_secret = self.config['WEBHOOK_SECRET']
            computed_signature = hmac.new(
                webhook_secret.encode('utf-8'),
                json.dumps(webhook_data, separators=(',', ':')).encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, computed_signature)
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    def _map_payment_status(self, flutterwave_status: str) -> str:
        """
        Map Flutterwave payment status to our internal status
        """
        status_mapping = {
            'successful': 'completed',
            'completed': 'completed',
            'pending': 'processing',
            'failed': 'failed',
            'cancelled': 'cancelled',
            'abandoned': 'cancelled'
        }
        
        return status_mapping.get(flutterwave_status.lower(), 'failed')
    
    def get_supported_countries(self) -> Dict:
        """
        Get list of countries supported by Flutterwave
        """
        try:
            countries_url = f"{self.base_url}/misc/countries"
            
            response = requests.get(
                countries_url,
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'success': False, 'error': 'Failed to fetch countries'}
                
        except Exception as e:
            logger.error(f"Error fetching supported countries: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_banks(self, country_code: str) -> Dict:
        """
        Get list of banks for a specific country
        """
        try:
            banks_url = f"{self.base_url}/banks/{country_code}"
            
            response = requests.get(
                banks_url,
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'success': False, 'error': 'Failed to fetch banks'}
                
        except Exception as e:
            logger.error(f"Error fetching banks: {e}")
            return {'success': False, 'error': str(e)}
    
    def charge_card_directly(self, card_data: Dict, amount: float, currency: str, 
                           email: str, tx_ref: Optional[str] = None) -> Dict:
        """
        Charge card directly using Flutterwave API
        """
        try:
            if not tx_ref:
                tx_ref = self._generate_tx_ref()
                
            charge_url = f"{self.base_url}/charges?type=card"
            
            payload = {
                "card_number": card_data['number'],
                "cvv": card_data['cvv'],
                "expiry_month": card_data['expiry_month'],
                "expiry_year": card_data['expiry_year'],
                "currency": currency.upper(),
                "amount": str(amount),
                "email": email,
                "tx_ref": tx_ref,
                "redirect_url": settings.FLUTTER_CONFIG['SUCCESS_URL']
            }
            
            response = requests.post(
                charge_url,
                json=payload,
                headers=self._get_headers(),
                timeout=30
            )
            
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('status') == 'success':
                return {
                    'success': True,
                    'tx_ref': tx_ref,
                    'requires_validation': response_data.get('meta', {}).get('authorization', {}).get('mode') == 'pin',
                    'response_data': response_data
                }
            else:
                return {
                    'success': False,
                    'error_message': response_data.get('message', 'Card charge failed'),
                    'response_data': response_data
                }
                
        except Exception as e:
            logger.error(f"Flutterwave card charge error: {e}")
            return {
                'success': False,
                'error_message': str(e)
            }
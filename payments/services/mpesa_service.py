"""
M-Pesa Daraja API Integration

Direct integration with Safaricom's M-Pesa Daraja API for processing
Kenyan mobile money payments.
"""

import base64
import json
import logging
import requests
from datetime import datetime, timedelta
from django.conf import settings
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class MpesaService:
    """
    M-Pesa Daraja API service for processing payments
    """
    
    def __init__(self):
        self.config = settings.PAYMENT_CONFIG['MPESA']
        self.base_url = 'https://api.safaricom.co.ke' if self.config['ENVIRONMENT'] == 'production' else 'https://sandbox.safaricom.co.ke'
        self.access_token = None
        self.token_expiry = None
    
    def _get_access_token(self) -> str:
        """
        Get OAuth access token from M-Pesa API
        """
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token
        
        auth_url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        
        # Create basic auth header
        auth_string = f"{self.config['CONSUMER_KEY']}:{self.config['CONSUMER_SECRET']}"
        auth_header = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(auth_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data['access_token']
            # Token expires in ~3600 seconds, refresh 100 seconds early
            self.token_expiry = datetime.now() + timedelta(seconds=3500)
            
            logger.info("Successfully obtained M-Pesa access token")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get M-Pesa access token: {e}")
            raise Exception(f"M-Pesa authentication failed: {e}")
        except KeyError as e:
            logger.error(f"Invalid M-Pesa token response: {e}")
            raise Exception("Invalid M-Pesa API response")
    
    def _generate_password(self) -> tuple:
        """
        Generate password and timestamp for STK push
        """
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_string = f"{self.config['BUSINESS_SHORTCODE']}{self.config['PASS_KEY']}{timestamp}"
        password = base64.b64encode(password_string.encode()).decode()
        return password, timestamp
    
    def _format_phone_number(self, phone: str) -> str:
        """
        Format phone number to M-Pesa format (254XXXXXXXXX)
        """
        # Remove any non-digit characters
        phone = ''.join(filter(str.isdigit, phone))
        
        # Handle different formats
        if phone.startswith('254'):
            return phone
        elif phone.startswith('0'):
            return '254' + phone[1:]
        elif len(phone) == 9:
            return '254' + phone
        else:
            raise ValueError(f"Invalid phone number format: {phone}")
    
    def initiate_stk_push(self, phone_number: str, amount: float, account_reference: str, 
                         transaction_desc: str) -> Dict:
        """
        Initiate STK Push payment request
        """
        try:
            access_token = self._get_access_token()
            password, timestamp = self._generate_password()
            formatted_phone = self._format_phone_number(phone_number)
            
            # Validate amount
            if amount < 1:
                raise ValueError("Amount must be at least KES 1")
            
            stk_push_url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "BusinessShortCode": self.config['BUSINESS_SHORTCODE'],
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount),  # M-Pesa expects integer
                "PartyA": formatted_phone,
                "PartyB": self.config['BUSINESS_SHORTCODE'],
                "PhoneNumber": formatted_phone,
                "CallBackURL": self.config['CALLBACK_URL'],
                "AccountReference": account_reference,
                "TransactionDesc": transaction_desc
            }
            
            logger.info(f"Initiating M-Pesa STK push for {formatted_phone}, amount: {amount}")
            logger.info(f"STK Push payload: {payload}")
            
            response = requests.post(stk_push_url, json=payload, headers=headers, timeout=30)
            logger.info(f"STK Push response status: {response.status_code}")
            logger.info(f"STK Push response body: {response.text}")
            
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('ResponseCode') == '0':
                logger.info(f"STK push initiated successfully: {response_data.get('CheckoutRequestID')}")
                return {
                    'success': True,
                    'checkout_request_id': response_data.get('CheckoutRequestID'),
                    'merchant_request_id': response_data.get('MerchantRequestID'),
                    'response_description': response_data.get('ResponseDescription'),
                    'customer_message': response_data.get('CustomerMessage')
                }
            else:
                error_code = response_data.get('ResponseCode')
                error_desc = response_data.get('ResponseDescription', 'STK Push failed')
                
                # Map error codes to user-friendly messages
                error_message = self._map_error_code(error_code, error_desc)
                
                logger.error(f"STK push failed: {error_code} - {error_desc}")
                return {
                    'success': False,
                    'error_code': error_code,
                    'error_message': error_message,
                    'raw_response': response_data
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"M-Pesa API request failed: {e}")
            return {
                'success': False,
                'error_message': 'Network error occurred. Please try again.',
                'error_details': str(e)
            }
        except Exception as e:
            logger.error(f"M-Pesa STK push error: {e}")
            return {
                'success': False,
                'error_message': str(e)
            }
    
    def query_stk_status(self, checkout_request_id: str) -> Dict:
        """
        Query the status of an STK push transaction
        """
        try:
            access_token = self._get_access_token()
            password, timestamp = self._generate_password()
            
            query_url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "BusinessShortCode": self.config['BUSINESS_SHORTCODE'],
                "Password": password,
                "Timestamp": timestamp,
                "CheckoutRequestID": checkout_request_id
            }
            
            response = requests.post(query_url, json=payload, headers=headers, timeout=30)
            response_data = response.json()
            
            if response.status_code == 200:
                result_code = response_data.get('ResultCode')
                result_desc = response_data.get('ResultDesc', '')
                
                return {
                    'success': True,
                    'result_code': result_code,
                    'result_desc': result_desc,
                    'status': self._map_result_code(result_code),
                    'raw_response': response_data
                }
            else:
                logger.error(f"STK query failed: {response_data}")
                return {
                    'success': False,
                    'error_message': 'Failed to query payment status',
                    'raw_response': response_data
                }
                
        except Exception as e:
            logger.error(f"M-Pesa STK query error: {e}")
            return {
                'success': False,
                'error_message': str(e)
            }
    
    def _map_error_code(self, error_code: str, default_message: str) -> str:
        """
        Map M-Pesa error codes to user-friendly messages
        """
        error_messages = {
            '1': 'Invalid phone number or account details',
            '2': 'Invalid amount. Minimum is KES 1',
            '4': 'Service temporarily unavailable',
            '26': 'Phone number not registered for M-Pesa',
            '1001': 'Invalid phone number format',
            '1032': 'Request cancelled by user',
            '2001': 'Transaction is being processed'
        }
        
        return error_messages.get(str(error_code), default_message)
    
    def _map_result_code(self, result_code: str) -> str:
        """
        Map M-Pesa result codes to payment status
        """
        status_mapping = {
            '0': 'completed',      # Success
            '1032': 'cancelled',   # User cancelled
            '1037': 'failed',      # Timeout
            '1025': 'failed',      # Insufficient balance
            '1001': 'failed',      # Invalid phone
            '1019': 'failed',      # Transaction limit exceeded
            '1026': 'failed',      # Wrong PIN
            '1036': 'failed',      # Not registered
            '1054': 'failed',      # Service unavailable
            '2001': 'processing',  # Still processing
        }
        
        return status_mapping.get(str(result_code), 'failed')
    
    def process_callback(self, callback_data: Dict) -> Dict:
        """
        Process M-Pesa callback data
        """
        try:
            stk_callback = callback_data.get('Body', {}).get('stkCallback', {})
            
            merchant_request_id = stk_callback.get('MerchantRequestID')
            checkout_request_id = stk_callback.get('CheckoutRequestID')
            result_code = stk_callback.get('ResultCode')
            result_desc = stk_callback.get('ResultDesc')
            
            callback_metadata = stk_callback.get('CallbackMetadata', {})
            metadata_items = callback_metadata.get('Item', [])
            
            # Extract payment details from metadata
            payment_details = {}
            for item in metadata_items:
                name = item.get('Name')
                value = item.get('Value')
                if name == 'Amount':
                    payment_details['amount'] = value
                elif name == 'MpesaReceiptNumber':
                    payment_details['mpesa_receipt'] = value
                elif name == 'TransactionDate':
                    payment_details['transaction_date'] = value
                elif name == 'PhoneNumber':
                    payment_details['phone_number'] = value
            
            return {
                'success': True,
                'merchant_request_id': merchant_request_id,
                'checkout_request_id': checkout_request_id,
                'result_code': result_code,
                'result_desc': result_desc,
                'status': self._map_result_code(result_code),
                'payment_details': payment_details,
                'raw_callback': callback_data
            }
            
        except Exception as e:
            logger.error(f"Error processing M-Pesa callback: {e}")
            return {
                'success': False,
                'error_message': str(e),
                'raw_callback': callback_data
            }
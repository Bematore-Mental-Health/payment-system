"""
Payment Callback Handlers

Views for handling payment callbacks from M-Pesa, Flutterwave,
and other payment providers.
"""

import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View

from payments.models import PaymentTransaction
from .models import CallbackLog
from payments.services.mpesa_service import MpesaService
from payments.services.flutterwave_service import FlutterwaveService
from authentication.authentication import record_payment_in_firebase, update_user_payment_status

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class MpesaCallbackView(View):
    """
    Handle M-Pesa STK Push callbacks
    """
    
    def post(self, request):
        """
        Process M-Pesa callback
        """
        try:
            callback_data = json.loads(request.body.decode('utf-8'))
            
            # Log the callback
            callback_record = CallbackLog.objects.create(
                provider='mpesa',
                transaction_id='unknown',  # Will be updated after processing
                raw_data=callback_data
            )
            
            # Process callback with M-Pesa service
            mpesa_service = MpesaService()
            result = mpesa_service.process_callback(callback_data)
            
            if result.get('success'):
                checkout_request_id = result.get('checkout_request_id')
                logger.info(f"M-PESA FLOW: ========== CALLBACK VIEW PROCESSING ==========")
                logger.info(f"M-PESA FLOW: Callback processing successful, looking for transaction with CheckoutRequestID: {checkout_request_id}")
                
                # Find transaction by checkout request ID
                try:
                    transaction = PaymentTransaction.objects.get(
                        mpesa_checkout_request_id=checkout_request_id
                    )
                    
                    logger.info(f"M-PESA FLOW: Found transaction: {transaction.transaction_id}")
                    logger.info(f"M-PESA FLOW: Current transaction status: {transaction.status}")
                    
                    # Update callback record with transaction ID
                    callback_record.transaction_id = transaction.transaction_id
                    callback_record.success = True
                    callback_record.save()
                    
                    # Update transaction status
                    old_status = transaction.status
                    new_status = result.get('status', 'failed')
                    transaction.status = new_status
                    
                    logger.info(f"M-PESA FLOW: Status update: {old_status} → {new_status}")
                    
                    # Add M-Pesa specific data
                    payment_details = result.get('payment_details', {})
                    logger.info(f"M-PESA FLOW: Payment details from callback:")
                    logger.info(f"M-PESA FLOW: {json.dumps(payment_details, indent=2)}")
                    
                    if payment_details.get('mpesa_receipt'):
                        transaction.mpesa_receipt = payment_details['mpesa_receipt']
                        logger.info(f"M-PESA FLOW: Added M-Pesa receipt: {payment_details['mpesa_receipt']}")
                    
                    transaction.save()
                    logger.info(f"M-PESA FLOW: Transaction saved with new status: {transaction.status}")
                    
                    # Handle successful payment
                    if transaction.status == 'completed' and old_status != 'completed':
                        logger.info(f"M-PESA FLOW: Payment completed! Triggering success handlers...")
                        self._handle_successful_payment(transaction, payment_details)
                    
                    logger.info(f"M-PESA FLOW: M-Pesa callback processed successfully: {transaction.transaction_id}")
                    
                except PaymentTransaction.DoesNotExist:
                    logger.error(f"M-PESA FLOW: Transaction not found for checkout request: {checkout_request_id}")
                    callback_record.success = False
                    callback_record.error_message = "Transaction not found"
                    callback_record.save()
            
            else:
                callback_record.success = False
                callback_record.error_message = result.get('error_message', 'Callback processing failed')
                callback_record.save()
                
                logger.error(f"M-Pesa callback processing failed: {result.get('error_message')}")
            
            # Always return success to M-Pesa to avoid retries
            return JsonResponse({
                'ResultCode': 0,
                'ResultDesc': 'Callback processed successfully'
            })
            
        except Exception as e:
            logger.error(f"M-Pesa callback error: {e}")
            return JsonResponse({
                'ResultCode': 1,
                'ResultDesc': 'Callback processing failed'
            })
    
    def _handle_successful_payment(self, transaction, payment_details):
        """
        Handle successful M-Pesa payment
        """
        try:
            # Update user payment status in Firebase
            payment_data = {
                'status': 'completed',
                'transactionId': transaction.transaction_id,
                'amount': float(transaction.amount),
                'currency': transaction.currency,
                'paymentMethod': transaction.payment_method
            }
            
            update_user_payment_status(transaction.user_uid, payment_data)
            
            # Update payment record in Firebase
            firebase_data = {
                'transactionId': transaction.transaction_id,
                'userId': transaction.user_uid,
                'email': transaction.email,
                'name': transaction.name,
                'paymentMethod': transaction.payment_method,
                'amount': float(transaction.amount),
                'currency': transaction.currency,
                'status': 'completed',
                'purpose': transaction.purpose,
                'phoneNumber': transaction.phone_number,
                'mpesaReceipt': transaction.mpesa_receipt,
                'transactionDate': payment_details.get('transaction_date')
            }
            record_payment_in_firebase(firebase_data)
            
            logger.info(f"M-Pesa payment completed successfully: {transaction.transaction_id}")
            
        except Exception as e:
            logger.error(f"Error handling successful M-Pesa payment: {e}")


@method_decorator(csrf_exempt, name='dispatch')
class FlutterwaveWebhookView(View):
    """
    Handle Flutterwave webhook notifications
    """
    
    def post(self, request):
        """
        Process Flutterwave webhook
        """
        try:
            webhook_data = json.loads(request.body.decode('utf-8'))
            signature = request.META.get('HTTP_VERIF_HASH', '')
            
            # Log the webhook
            tx_ref = webhook_data.get('data', {}).get('tx_ref', 'unknown')
            callback_record = CallbackLog.objects.create(
                provider='flutterwave',
                transaction_id=tx_ref,
                raw_data=webhook_data
            )
            
            # Process webhook with Flutterwave service
            flutterwave_service = FlutterwaveService()
            result = flutterwave_service.process_webhook(webhook_data, signature)
            
            if result.get('success'):
                tx_ref = result.get('tx_ref')
                
                try:
                    transaction = PaymentTransaction.objects.get(transaction_id=tx_ref)
                    
                    # Update callback record
                    callback_record.success = True
                    callback_record.save()
                    
                    # Update transaction
                    old_status = transaction.status
                    transaction.status = result.get('status', 'failed')
                    
                    if result.get('flw_ref'):
                        transaction.flutterwave_flw_ref = result['flw_ref']
                    
                    transaction.save()
                    
                    # Handle successful payment
                    if transaction.status == 'completed' and old_status != 'completed':
                        self._handle_successful_flutterwave_payment(transaction, result)
                    
                    logger.info(f"Flutterwave webhook processed successfully: {tx_ref}")
                    
                except PaymentTransaction.DoesNotExist:
                    logger.error(f"Transaction not found for tx_ref: {tx_ref}")
                    callback_record.success = False
                    callback_record.error_message = "Transaction not found"
                    callback_record.save()
            
            else:
                callback_record.success = False
                callback_record.error_message = result.get('error_message', 'Webhook processing failed')
                callback_record.save()
                
                logger.error(f"Flutterwave webhook processing failed: {result.get('error_message')}")
            
            return HttpResponse(status=200)
            
        except Exception as e:
            logger.error(f"Flutterwave webhook error: {e}")
            return HttpResponse(status=500)
    
    def _handle_successful_flutterwave_payment(self, transaction, webhook_result):
        """
        Handle successful Flutterwave payment
        """
        try:
            # Update user payment status in Firebase
            payment_data = {
                'status': 'completed',
                'transactionId': transaction.transaction_id,
                'amount': float(transaction.amount),
                'currency': transaction.currency,
                'paymentMethod': transaction.payment_method
            }
            
            update_user_payment_status(transaction.user_uid, payment_data)
            
            # Update payment record in Firebase
            firebase_data = {
                'transactionId': transaction.transaction_id,
                'userId': transaction.user_uid,
                'email': transaction.email,
                'name': transaction.name,
                'paymentMethod': transaction.payment_method,
                'amount': float(transaction.amount),
                'currency': transaction.currency,
                'status': 'completed',
                'purpose': transaction.purpose,
                'phoneNumber': transaction.phone_number,
                'flutterwaveReference': transaction.flutterwave_flw_ref,
                'paymentType': webhook_result.get('payment_type')
            }
            record_payment_in_firebase(firebase_data)
            
            logger.info(f"Flutterwave payment completed successfully: {transaction.transaction_id}")
            
        except Exception as e:
            logger.error(f"Error handling successful Flutterwave payment: {e}")


@csrf_exempt
@require_http_methods(["POST"])
def mpesa_result_callback(request):
    """
    Handle M-Pesa result callback (for C2B transactions)
    """
    try:
        callback_data = json.loads(request.body.decode('utf-8'))
        logger.info(f"M-Pesa result callback received: {callback_data}")
        
        # Process result callback if needed
        # This is mainly for logging and monitoring
        
        return JsonResponse({
            'ResultCode': 0,
            'ResultDesc': 'Result callback processed successfully'
        })
        
    except Exception as e:
        logger.error(f"M-Pesa result callback error: {e}")
        return JsonResponse({
            'ResultCode': 1,
            'ResultDesc': 'Result callback processing failed'
        })

"""
Payment Views and API Endpoints

Main views for handling payment processing, status checks, and 
redirects for the Bematore payment system.
"""

import json
import logging
import uuid
from decimal import Decimal
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import PaymentTransaction
from .services.mpesa_service import MpesaService
from .services.flutterwave_service import FlutterwaveService
from .services.currency_service import CurrencyService
from authentication.authentication import record_payment_in_firebase, update_user_payment_status

logger = logging.getLogger(__name__)


class PaymentFormView(View):
    """
    Display payment form for users to select payment method
    """
    
    def get(self, request):
        """
        Display payment form with transaction details
        """
        # Get transaction details from query parameters
        transaction_id = request.GET.get('transaction_id')
        user_uid = request.GET.get('user_uid')
        email = request.GET.get('email')
        name = request.GET.get('name')
        amount = request.GET.get('amount')
        currency = request.GET.get('currency', settings.PAYMENT_CONFIG['DISPLAY_FALLBACK_CURRENCY'])
        original_usd_amount = request.GET.get('original_usd_amount')
        raw_purpose = request.GET.get('purpose', 'Mental Health Service')
        
        # Format purpose for better display
        purpose = self._format_purpose_display(raw_purpose)
        
        # Validate required parameters
        if not all([transaction_id, user_uid, email, name, amount]):
            return render(request, 'payment_form.html', {
                'error': 'Missing required payment parameters'
            })
        
        try:
            amount = Decimal(amount)
        except (ValueError, TypeError):
            return render(request, 'payment_form.html', {
                'error': 'Invalid amount specified'
            })
        
        # Initialize currency service for conversion
        currency_service = CurrencyService()
        
        # Handle currency and amount conversion
        if original_usd_amount:
            # Flutter sent both original USD amount and converted local amount
            storage_amount = Decimal(original_usd_amount)  # Store USD amount for backend processing
            display_amount = float(amount)  # Display amount in user's currency
            display_currency = currency  # User's selected currency
        else:
            # Fallback to old logic if original_usd_amount not provided
            if currency.upper() == 'USD':
                # Amount is in USD, convert for display
                user_currency = currency_service.fallback_currency
                display_amount, display_currency = currency_service.get_display_amount(float(amount), user_currency)
                storage_amount = Decimal(amount)  # Store USD amount
            else:
                # Amount is in user's currency, convert to USD for storage
                display_amount = float(amount)
                display_currency = currency
                storage_amount = currency_service.convert_to_usd(float(amount), currency)
        
        # Get additional data from URL parameters if available
        phone_number = request.GET.get('phone_number', '')
        assessment_type = request.GET.get('assessment_type', '')
        assessment_score = request.GET.get('assessment_score', '')
        
        # Fetch Firebase user data to enhance the transaction
        firebase_user_data = None
        try:
            from authentication.authentication import get_firebase_user_data
            firebase_user_data = get_firebase_user_data(user_uid)
            if firebase_user_data:
                # Use Firebase data to fill missing fields
                if not name or name == 'User':
                    name = firebase_user_data.get('name') or firebase_user_data.get('displayName') or 'Bematore User'
                if not phone_number:
                    phone_number = firebase_user_data.get('phoneNumber') or firebase_user_data.get('phone_number') or ''
        except Exception as e:
            logger.warning(f"Could not fetch Firebase user data for {user_uid}: {e}")

        # Check if transaction already exists
        transaction, created = PaymentTransaction.objects.get_or_create(
            transaction_id=transaction_id,
            defaults={
                'user_uid': user_uid,
                'email': email,
                'name': name,
                'phone_number': phone_number,
                'amount': storage_amount,  # Store in USD
                'currency': currency_service.base_currency,  # Store as USD
                'purpose': purpose,
                'status': 'pending',
                'metadata': {
                    'display_amount': display_amount,
                    'display_currency': display_currency,
                    'original_amount': float(amount),
                    'original_currency': currency,
                    'assessment_type': assessment_type,
                    'assessment_score': assessment_score,
                    'firebase_user_data': firebase_user_data
                }
            }
        )
        
        # Automatically sync transaction to Firebase
        if transaction:
            try:
                firebase_payment_data = {
                    'transactionId': transaction.transaction_id,
                    'userId': transaction.user_uid,
                    'email': transaction.email,
                    'name': transaction.name,
                    'phoneNumber': transaction.phone_number,
                    'paymentMethod': 'pending',  # Will be updated when user selects method
                    'amount': float(transaction.amount),
                    'currency': transaction.currency,
                    'status': transaction.status,
                    'purpose': transaction.purpose,
                    'assessmentType': assessment_type,
                    'assessmentScore': assessment_score,
                    'initiatedAt': transaction.created_at.isoformat() if transaction.created_at else None
                }
                
                record_payment_in_firebase(firebase_payment_data)
                logger.info(f"Synced transaction {transaction_id} to Firebase")
                
            except Exception as e:
                logger.error(f"Failed to sync transaction {transaction_id} to Firebase: {e}")
        
        # If transaction exists and is not pending, redirect to status
        if not created and transaction.status != 'pending':
            return redirect('payments:payment_status', transaction_id=transaction_id)
        
        # App Store compliance: Check if request is from mobile app
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        is_ios = 'iphone' in user_agent or 'ipad' in user_agent or 'ios' in user_agent
        is_android = 'android' in user_agent
        is_mobile_app = is_ios or is_android
        
        # Calculate M-Pesa amount in KES for display
        mpesa_amount = currency_service.get_mpesa_amount(storage_amount)
        
        context = {
            'transaction_id': transaction_id,
            'user_uid': user_uid,
            'email': email,
            'name': name,
            'amount': display_amount,  # Display converted amount
            'currency': display_currency,  # Display local currency
            'storage_amount_usd': float(storage_amount),  # USD amount for backend
            'mpesa_amount': float(mpesa_amount),  # M-Pesa amount in KES
            'purpose': purpose,
            'is_ios': is_ios,
            'is_android': is_android,
            'is_mobile_app': is_mobile_app,
            'currency_service': currency_service,  # Pass service to template for formatting
        }
        
        return render(request, 'payment_form.html', context)
    
    def _format_purpose_display(self, raw_purpose):
        """
        Format purpose for better display in payment form
        
        Args:
            raw_purpose: Raw purpose from Flutter app
            
        Returns:
            Formatted purpose string
        """
        if not raw_purpose:
            return 'Mental Health Service'
        
        # Check if it's already formatted (contains "Assessment Result")
        if 'Assessment Result' in raw_purpose:
            return raw_purpose
        
        # Map disorder names for better display
        disorder_mapping = {
            'Depression': 'Depression Assessment Result',
            'Anxiety': 'Anxiety Assessment Result', 
            'PTSD': 'PTSD Assessment Result',
            'Insomnia': 'Insomnia Assessment Result',
            'Stress': 'Stress Assessment Result',
            'Bipolar Disorder': 'Bipolar Disorder Assessment Result', 
            'ADHD': 'ADHD Assessment Result',
            'OCD': 'OCD Assessment Result',
            'Burnout': 'Burnout Assessment Result',
            'Self-Esteem': 'Self-Esteem Assessment Result',
            'Relationship Issues': 'Relationship Assessment Result',
            'Binge Eating': 'Eating Disorder Assessment Result',
            'Female Sexual Function': 'Sexual Health Assessment Result',
            'Male Sexual Function': 'Sexual Health Assessment Result', 
            'Alcohol Use': 'Substance Use Assessment Result',
            'Workplace Bullying': 'Workplace Assessment Result',
        }
        
        # Check if it's a disorder name that needs formatting
        for disorder, formatted in disorder_mapping.items():
            if disorder.lower() in raw_purpose.lower():
                return formatted
        
        # Check for assessment tool codes
        tool_mapping = {
            'phq9': 'Depression Assessment Result',
            'gad7': 'Anxiety Assessment Result',
            'pcl5': 'PTSD Assessment Result', 
            'isi': 'Insomnia Assessment Result',
            'pss': 'Stress Assessment Result',
            'mdq': 'Bipolar Disorder Assessment Result',
            'asrs': 'ADHD Assessment Result',
            'ybocs': 'OCD Assessment Result',
            'mbi': 'Burnout Assessment Result',
            'rses': 'Self-Esteem Assessment Result',
            'das': 'Relationship Assessment Result',
            'bes': 'Eating Disorder Assessment Result',
            'fsfi': 'Sexual Health Assessment Result',
            'iief': 'Sexual Health Assessment Result',
            'audit': 'Substance Use Assessment Result',
            'wbi': 'Workplace Assessment Result',
        }
        
        # Check for tool codes
        for tool, formatted in tool_mapping.items():
            if tool.lower() in raw_purpose.lower():
                return formatted
        
        # Default formatting
        return f"{raw_purpose} Assessment Result" if 'Assessment' not in raw_purpose else raw_purpose
    
    def post(self, request):
        """
        Process payment method selection and initiate payment
        """
        try:
            # Get form data
            transaction_id = request.POST.get('transaction_id')
            payment_method = request.POST.get('payment_method')
            
            # Get transaction
            transaction = get_object_or_404(PaymentTransaction, transaction_id=transaction_id)
            
            if payment_method == 'mpesa':
                return self._process_mpesa_payment(request, transaction)
            elif payment_method == 'flutterwave':
                return self._process_flutterwave_payment(request, transaction)
            else:
                messages.error(request, 'Invalid payment method selected')
                return redirect('payments:payment_form')
                
        except Exception as e:
            logger.error(f"Payment processing error: {e}")
            messages.error(request, 'An error occurred while processing your payment')
            
            # Try to preserve transaction context for redirect
            try:
                transaction_id = request.POST.get('transaction_id')
                if transaction_id:
                    transaction = PaymentTransaction.objects.get(transaction_id=transaction_id)
                    # Redirect with proper parameters
                    params = {
                        'token': 'error_recovery',  # Special token for error recovery
                        'amount': str(transaction.amount),
                        'currency': transaction.currency,
                        'purpose': transaction.purpose
                    }
                    from urllib.parse import urlencode
                    return redirect(f'/payment?{urlencode(params)}')
            except:
                pass  # If we can't recover context, fall back to basic redirect
            
            return redirect('payments:payment_form')
    
    def _process_mpesa_payment(self, request, transaction):
        """
        Process M-Pesa payment
        """
        phone_number = request.POST.get('phone_number')
        
        if not phone_number:
            messages.error(request, 'Phone number is required for M-Pesa payment')
            return redirect('payments:payment_form')
        
        # Update transaction
        transaction.payment_method = 'mpesa'
        transaction.phone_number = phone_number
        transaction.save()
        
        # Get KES amount for M-Pesa (M-Pesa operates in KES only)
        currency_service = CurrencyService()
        kes_amount = currency_service.get_mpesa_amount(float(transaction.amount))
        
        # Initiate M-Pesa payment
        mpesa_service = MpesaService()
        result = mpesa_service.initiate_stk_push(
            phone_number=phone_number,
            amount=int(kes_amount),  # Use converted KES amount
            transaction_desc=f"Payment for {transaction.purpose}",
            account_reference=transaction.transaction_id
        )
        
        if result.get('success'):
            transaction.mpesa_checkout_request_id = result.get('checkout_request_id')
            transaction.save()
            
            # Record payment initiation in Firebase
            firebase_data = {
                'transactionId': transaction.transaction_id,
                'userId': transaction.user_uid,
                'email': transaction.email,
                'name': transaction.name,
                'paymentMethod': 'mpesa',
                'amount': float(transaction.amount),
                'currency': transaction.currency,
                'status': 'pending',
                'purpose': transaction.purpose,
                'phoneNumber': phone_number,
                'initiatedAt': transaction.created_at.isoformat()
            }
            record_payment_in_firebase(firebase_data)
            
            return redirect('payments:payment_status', transaction_id=transaction.transaction_id)
        else:
            transaction.status = 'failed'
            transaction.failure_reason = result.get('message', 'M-Pesa payment initiation failed')
            transaction.save()
            
            messages.error(request, f"M-Pesa payment failed: {result.get('message')}")
            return redirect('payments:payment_form')
    
    def _process_flutterwave_payment(self, request, transaction):
        """
        Process Flutterwave payment
        """
        # Update transaction
        transaction.payment_method = 'flutterwave'
        transaction.save()
        
        # Create Flutterwave payment
        flutterwave_service = FlutterwaveService()
        payment_data = {
            'tx_ref': transaction.transaction_id,
            'amount': str(transaction.amount),
            'currency': transaction.currency,
            'customer': {
                'email': transaction.email,
                'name': transaction.name
            },
            'redirect_url': request.build_absolute_uri(
                f'/payments/callback/flutterwave/{transaction.transaction_id}/'
            ),
            'customizations': {
                'title': 'Bematore Payment',
                'description': transaction.purpose,
                'logo': request.build_absolute_uri('/static/images/bematore-logo.png')
            }
        }
        
        result = flutterwave_service.create_payment(payment_data)
        
        if result.get('success'):
            transaction.flutterwave_flw_ref = result.get('reference')
            transaction.save()
            
            # Record payment initiation in Firebase
            firebase_data = {
                'transactionId': transaction.transaction_id,
                'userId': transaction.user_uid,
                'email': transaction.email,
                'name': transaction.name,
                'paymentMethod': 'flutterwave',
                'amount': float(transaction.amount),
                'currency': transaction.currency,
                'status': 'pending',
                'purpose': transaction.purpose,
                'flutterwaveReference': result.get('reference'),
                'initiatedAt': transaction.created_at.isoformat()
            }
            record_payment_in_firebase(firebase_data)
            
            # Redirect to Flutterwave
            return redirect(result.get('payment_link'))
        else:
            transaction.status = 'failed'
            transaction.failure_reason = result.get('message', 'Flutterwave payment initiation failed')
            transaction.save()
            
            messages.error(request, f"Payment setup failed: {result.get('message')}")
            return redirect('payments:payment_form')


class PaymentStatusView(View):
    """
    Display payment status and handle completion
    """
    
    def get(self, request, transaction_id):
        """
        Display payment status
        """
        transaction = get_object_or_404(PaymentTransaction, transaction_id=transaction_id)
        
        context = {
            'transaction': transaction,
            'user_token': request.GET.get('token', ''),  # For status API calls
        }
        
        # Add Flutterwave link if needed
        if transaction.payment_method == 'flutterwave' and transaction.status == 'pending':
            if transaction.flutterwave_flw_ref:
                # Could reconstruct payment link if needed
                context['flutterwave_link'] = '#'
        
        return render(request, 'payment_status.html', context)


class PaymentInitiationView(APIView):
    """
    API endpoint to initiate payment process
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Extract payment data
            data = request.data
            display_amount = float(data.get('amount', 0))
            display_currency = data.get('currency', 'USD').upper()
            payment_method = data.get('payment_method', '').lower()
            purpose = data.get('purpose', 'assessment')
            
            # Initialize currency service for consistent handling
            currency_service = CurrencyService()
            
            # Convert to USD for storage (consistent with Flutter app)
            usd_amount = currency_service.normalize_amount_for_storage(display_amount, display_currency)
            
            # User information from Firebase auth
            user = request.user
            email = user.email
            name = user.name or 'Bematore User'
            phone_number = data.get('phone_number', user.phone_number or '')
            
            # Validate input (validate against USD amount for consistency)
            min_usd = settings.PAYMENT_CONFIG['MINIMUM_AMOUNT']
            max_usd = settings.PAYMENT_CONFIG['MAXIMUM_AMOUNT']
            
            if float(usd_amount) < min_usd:
                return Response({
                    'error': f'Minimum amount is ${min_usd:.2f} USD'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if float(usd_amount) > max_usd:
                return Response({
                    'error': f'Maximum amount is ${max_usd:.2f} USD'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate transaction ID
            transaction_id = str(uuid.uuid4())
            
            # Create payment transaction record (store in USD, display currency for reference)
            payment_transaction = PaymentTransaction.objects.create(
                transaction_id=transaction_id,
                user_uid=user.uid,
                email=email,
                name=name,
                phone_number=phone_number,
                payment_method=payment_method,
                amount=usd_amount,  # Store in USD
                currency='USD',  # Base currency for storage
                purpose=purpose,
                status='pending'
            )
            
            # Store original display currency and amount in metadata for reference
            payment_transaction.metadata = {
                'display_amount': display_amount,
                'display_currency': display_currency,
                'conversion_rate': currency_service.get_exchange_rate(display_currency, 'USD')
            }
            
            # Process payment based on method
            result = self._process_payment(payment_transaction, data)
            
            if result.get('success'):
                # Update transaction with provider-specific data
                self._update_transaction_with_provider_data(payment_transaction, result, payment_method)
                
                # Record in Firebase (store in USD consistent with Flutter app)
                firebase_data = {
                    'transactionId': transaction_id,
                    'userId': user.uid,
                    'email': email,
                    'name': name,
                    'paymentMethod': payment_method,
                    'amount': float(usd_amount),  # Store USD amount
                    'currency': 'USD',  # Base currency
                    'displayAmount': display_amount,  # Original display amount
                    'displayCurrency': display_currency,  # Original display currency
                    'status': 'pending',
                    'purpose': purpose,
                    'phoneNumber': phone_number
                }
                record_payment_in_firebase(firebase_data)
                
                response_data = {
                    'success': True,
                    'transaction_id': transaction_id,
                    'payment_method': payment_method,
                    'amount': float(usd_amount),  # USD amount
                    'currency': 'USD',  # Base currency
                    'display_amount': display_amount,  # For frontend display
                    'display_currency': display_currency
                }
                
                # Add method-specific response data
                if payment_method == 'mpesa':
                    response_data.update({
                        'checkout_request_id': result.get('checkout_request_id'),
                        'customer_message': result.get('customer_message')
                    })
                elif payment_method == 'flutterwave':
                    response_data.update({
                        'payment_link': result.get('payment_link'),
                        'hosted_link': result.get('hosted_link')
                    })
                
                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                payment_transaction.status = 'failed'
                payment_transaction.failure_reason = result.get('error_message', 'Payment initiation failed')
                payment_transaction.save()
                
                return Response({
                    'error': result.get('error_message', 'Payment initiation failed'),
                    'transaction_id': transaction_id
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Payment initiation error: {e}")
            return Response({
                'error': 'Internal server error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _process_payment(self, transaction, data):
        """
        Process payment based on payment method with proper currency handling
        """
        payment_method = transaction.payment_method
        currency_service = CurrencyService()
        
        if payment_method == 'mpesa':
            # M-Pesa always operates in KES regardless of storage currency
            kes_amount = currency_service.get_mpesa_amount(float(transaction.amount))
            
            mpesa_service = MpesaService()
            return mpesa_service.initiate_stk_push(
                phone_number=transaction.phone_number,
                amount=float(kes_amount),  # Convert USD to KES for M-Pesa
                account_reference=transaction.transaction_id,
                transaction_desc=f"Bematore {transaction.purpose} payment"
            )
        
        elif payment_method == 'flutterwave':
            # For Flutterwave, determine appropriate currency
            display_currency = transaction.metadata.get('display_currency', 'USD')
            display_amount = transaction.metadata.get('display_amount', float(transaction.amount))
            
            # Use display currency and amount for Flutterwave (better user experience)
            flutterwave_service = FlutterwaveService()
            redirect_url = f"https://payments.bematore.com/payment/callback/flutterwave/{transaction.transaction_id}/"
            
            return flutterwave_service.initiate_card_payment(
                amount=display_amount,  # Use original display amount
                currency=display_currency,  # Use original display currency
                email=transaction.email,
                phone_number=transaction.phone_number,
                name=transaction.name,
                redirect_url=redirect_url,
                tx_ref=transaction.transaction_id
            )
        
        else:
            return {
                'success': False,
                'error_message': f'Unsupported payment method: {payment_method}'
            }
    
    def _update_transaction_with_provider_data(self, transaction, result, payment_method):
        """
        Update transaction with provider-specific data
        """
        if payment_method == 'mpesa':
            transaction.mpesa_checkout_request_id = result.get('checkout_request_id', '')
        elif payment_method == 'flutterwave':
            transaction.flutterwave_tx_ref = result.get('tx_ref', '')
        
        transaction.save()


class PaymentStatusAPIView(APIView):
    """
    API endpoint to check payment status
    """
    # Remove authentication requirement to allow Flutter app to check status with transaction_id
    permission_classes = []
    
    def get(self, request, transaction_id):
        try:
            # Get transaction (don't require user_uid match to allow direct URL access)
            transaction = PaymentTransaction.objects.get(transaction_id=transaction_id)
            
            # Check if payment is still pending and needs status update
            if transaction.is_pending:
                self._update_payment_status(transaction)
                # Refresh from database to get updated status
                transaction.refresh_from_db()
            
            # Prepare response data
            response_data = {
                'transaction_id': transaction.transaction_id,
                'status': transaction.status,
                'amount': float(transaction.amount),
                'currency': transaction.currency,
                'payment_method': transaction.payment_method,
                'purpose': transaction.purpose,
                'created_at': transaction.created_at.isoformat() if transaction.created_at else None,
                'completed_at': transaction.completed_at.isoformat() if transaction.completed_at else None,
                'failure_reason': transaction.failure_reason,
                'user_uid': transaction.user_uid,
                'email': transaction.email,
                'name': transaction.name
            }
            
            # Include metadata if available
            if transaction.metadata:
                response_data['metadata'] = transaction.metadata
            
            return Response(response_data)
            
        except PaymentTransaction.DoesNotExist:
            return Response({
                'error': 'Payment transaction not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Payment status check error: {e}")
            return Response({
                'error': 'Internal server error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _update_payment_status(self, transaction):
        """
        Update payment status by querying payment provider
        """
        try:
            if transaction.payment_method == 'mpesa' and transaction.mpesa_checkout_request_id:
                mpesa_service = MpesaService()
                result = mpesa_service.query_stk_status(transaction.mpesa_checkout_request_id)
                
                if result.get('success'):
                    new_status = result.get('status', 'failed')
                    if new_status != transaction.status:
                        transaction.status = new_status
                        transaction.save()
                        
                        # Update Firebase if completed
                        if new_status == 'completed':
                            self._handle_successful_payment(transaction)
            
            elif transaction.payment_method == 'flutterwave':
                flutterwave_service = FlutterwaveService()
                result = flutterwave_service.verify_payment(transaction.transaction_id)
                
                if result.get('success'):
                    new_status = result.get('status', 'failed')
                    if new_status != transaction.status:
                        transaction.status = new_status
                        if result.get('flw_ref'):
                            transaction.flutterwave_flw_ref = result['flw_ref']
                        transaction.save()
                        
                        # Update Firebase if completed
                        if new_status == 'completed':
                            self._handle_successful_payment(transaction)
                            
        except Exception as e:
            logger.error(f"Error updating payment status: {e}")
    
    def _handle_successful_payment(self, transaction):
        """
        Handle successful payment completion and sync to Firebase
        """
        try:
            # Update transaction completion timestamp
            if not transaction.completed_at:
                transaction.completed_at = timezone.now()
                transaction.save()
            
            # Update user payment status in Firebase
            payment_data = {
                'status': 'completed',
                'transactionId': transaction.transaction_id,
                'amount': float(transaction.amount),
                'currency': transaction.currency,
                'paymentMethod': transaction.payment_method
            }
            
            update_user_payment_status(transaction.user_uid, payment_data)
            
            # Update complete payment record in Firebase
            firebase_data = {
                'transactionId': transaction.transaction_id,
                'userId': transaction.user_uid,
                'email': transaction.email,
                'name': transaction.name,
                'phoneNumber': transaction.phone_number,
                'paymentMethod': transaction.payment_method,
                'amount': float(transaction.amount),
                'currency': transaction.currency,
                'status': 'completed',
                'purpose': transaction.purpose,
                'mpesaReceipt': transaction.mpesa_receipt,
                'flutterwaveReference': transaction.flutterwave_flw_ref,
                'completedAt': transaction.completed_at.isoformat() if transaction.completed_at else None,
                'createdAt': transaction.created_at.isoformat() if transaction.created_at else None,
            }
            
            # Include metadata if available
            if transaction.metadata:
                firebase_data.update(transaction.metadata)
            
            record_payment_in_firebase(firebase_data)
            logger.info(f"Successfully synced completed payment {transaction.transaction_id} to Firebase")
            
        except Exception as e:
            logger.error(f"Error handling successful payment {transaction.transaction_id}: {e}")


@csrf_exempt
def simple_status_check(request, transaction_id):
    """
    Simple payment status check endpoint for Flutter app (no auth required)
    """
    try:
        transaction = PaymentTransaction.objects.get(transaction_id=transaction_id)
        
        # Update status if pending
        if transaction.is_pending:
            # Quick status update logic
            try:
                if transaction.payment_method == 'mpesa' and transaction.mpesa_checkout_request_id:
                    mpesa_service = MpesaService()
                    result = mpesa_service.query_stk_status(transaction.mpesa_checkout_request_id)
                    if result.get('success'):
                        new_status = result.get('status', 'failed')
                        if new_status != transaction.status:
                            transaction.status = new_status
                            if result.get('receipt'):
                                transaction.mpesa_receipt = result['receipt']
                            transaction.save()
                            
                            # Sync to Firebase if completed
                            if new_status == 'completed':
                                try:
                                    firebase_data = {
                                        'transactionId': transaction.transaction_id,
                                        'userId': transaction.user_uid,
                                        'email': transaction.email,
                                        'status': 'completed',
                                        'paymentMethod': transaction.payment_method,
                                        'amount': float(transaction.amount),
                                        'currency': transaction.currency,
                                        'purpose': transaction.purpose,
                                        'mpesaReceipt': transaction.mpesa_receipt,
                                        'completedAt': timezone.now().isoformat()
                                    }
                                    record_payment_in_firebase(firebase_data)
                                    update_user_payment_status(transaction.user_uid, {
                                        'status': 'completed',
                                        'transactionId': transaction.transaction_id
                                    })
                                except Exception as e:
                                    logger.error(f"Firebase sync error: {e}")
                
                elif transaction.payment_method == 'flutterwave':
                    flutterwave_service = FlutterwaveService()
                    result = flutterwave_service.verify_payment(transaction.transaction_id)
                    if result.get('success'):
                        new_status = result.get('status', 'failed')
                        if new_status != transaction.status:
                            transaction.status = new_status
                            if result.get('flw_ref'):
                                transaction.flutterwave_flw_ref = result['flw_ref']
                            transaction.save()
                            
                            # Sync to Firebase if completed
                            if new_status == 'completed':
                                try:
                                    firebase_data = {
                                        'transactionId': transaction.transaction_id,
                                        'userId': transaction.user_uid,
                                        'email': transaction.email,
                                        'status': 'completed',
                                        'paymentMethod': transaction.payment_method,
                                        'amount': float(transaction.amount),
                                        'currency': transaction.currency,
                                        'purpose': transaction.purpose,
                                        'flutterwaveReference': transaction.flutterwave_flw_ref,
                                        'completedAt': timezone.now().isoformat()
                                    }
                                    record_payment_in_firebase(firebase_data)
                                    update_user_payment_status(transaction.user_uid, {
                                        'status': 'completed',
                                        'transactionId': transaction.transaction_id
                                    })
                                except Exception as e:
                                    logger.error(f"Firebase sync error: {e}")
                                    
            except Exception as e:
                logger.error(f"Status update error: {e}")
        
        # Return status
        return JsonResponse({
            'success': True,
            'transaction_id': transaction.transaction_id,
            'status': transaction.status,
            'amount': float(transaction.amount),
            'currency': transaction.currency,
            'payment_method': transaction.payment_method,
            'purpose': transaction.purpose,
            'user_uid': transaction.user_uid,
            'email': transaction.email,
            'name': transaction.name,
            'created_at': transaction.created_at.isoformat() if transaction.created_at else None,
            'completed_at': transaction.completed_at.isoformat() if transaction.completed_at else None,
            'failure_reason': transaction.failure_reason
        })
        
    except PaymentTransaction.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Transaction not found'
        }, status=404)
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


class PaymentWebView(View):
    """
    Web view for payment processing (accessed from Flutter app)
    """
    
    def get(self, request):
        """
        Display payment form
        """
        # Get parameters from URL
        token = request.GET.get('token')
        amount = request.GET.get('amount', '2.0')
        currency = request.GET.get('currency', 'USD')
        purpose = request.GET.get('purpose', 'assessment')
        
        if not token:
            return render(request, 'payments/error.html', {
                'error': 'Authentication required',
                'redirect_url': settings.FLUTTER_CONFIG['APP_URL']
            })
        
        # Handle error recovery token
        if token == 'error_recovery':
            # Allow the form to render with the provided parameters
            pass
        
        context = {
            'amount': amount,
            'currency': currency,
            'purpose': purpose,
            'mpesa_enabled': bool(settings.PAYMENT_CONFIG['MPESA']['CONSUMER_KEY']),
            'flutterwave_enabled': bool(settings.PAYMENT_CONFIG['FLUTTERWAVE']['PUBLIC_KEY']),
            'user': request.user if hasattr(request, 'user') else None
        }
        
        return render(request, 'payments/payment_form.html', context)


class PaymentCallbackView(View):
    """
    Handle payment callbacks and redirects
    """
    
    def get(self, request, provider, transaction_id):
        """
        Handle GET callback (usually for successful payments)
        """
        try:
            transaction = PaymentTransaction.objects.get(transaction_id=transaction_id)
            
            if provider == 'flutterwave':
                # Verify Flutterwave payment
                flutterwave_service = FlutterwaveService()
                result = flutterwave_service.verify_payment(transaction_id)
                
                if result.get('success') and result.get('status') == 'completed':
                    transaction.status = 'completed'
                    if result.get('flw_ref'):
                        transaction.flutterwave_flw_ref = result['flw_ref']
                    transaction.save()
                    
                    # Handle successful payment
                    PaymentStatusView()._handle_successful_payment(transaction)
                    
                    # Redirect to Flutter app success page
                    return redirect(f"{settings.FLUTTER_CONFIG['SUCCESS_URL']}?transaction_id={transaction_id}")
                else:
                    transaction.status = 'failed'
                    transaction.failure_reason = result.get('error_message', 'Payment verification failed')
                    transaction.save()
                    
                    return redirect(f"{settings.FLUTTER_CONFIG['FAILURE_URL']}?transaction_id={transaction_id}")
            
            return redirect(f"{settings.FLUTTER_CONFIG['FAILURE_URL']}?transaction_id={transaction_id}")
            
        except PaymentTransaction.DoesNotExist:
            return redirect(f"{settings.FLUTTER_CONFIG['FAILURE_URL']}?error=transaction_not_found")
        except Exception as e:
            logger.error(f"Payment callback error: {e}")
            return redirect(f"{settings.FLUTTER_CONFIG['FAILURE_URL']}?error=callback_failed")

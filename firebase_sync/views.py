"""
Firebase Sync Views

Views for synchronizing data between Django and Firebase.
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from payments.models import PaymentTransaction
from authentication.authentication import get_firebase_user_data, record_payment_in_firebase, update_user_payment_status

logger = logging.getLogger(__name__)


class SyncPaymentView(APIView):
    """
    Manually sync payment data to Firebase
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, transaction_id):
        """
        Sync payment transaction to Firebase
        """
        try:
            transaction = PaymentTransaction.objects.get(
                transaction_id=transaction_id,
                user_uid=request.user.uid
            )
            
            # Prepare Firebase data
            firebase_data = {
                'transactionId': transaction.transaction_id,
                'userId': transaction.user_uid,
                'email': transaction.email,
                'name': transaction.name,
                'paymentMethod': transaction.payment_method,
                'amount': float(transaction.amount),
                'currency': transaction.currency,
                'status': transaction.status,
                'purpose': transaction.purpose,
                'phoneNumber': transaction.phone_number,
                'mpesaReceipt': transaction.mpesa_receipt,
                'flutterwaveReference': transaction.flutterwave_flw_ref,
                'failureReason': transaction.failure_reason
            }
            
            # Record in Firebase
            success = record_payment_in_firebase(firebase_data)
            
            if success:
                # Update user payment status if completed
                if transaction.status == 'completed':
                    payment_data = {
                        'status': 'completed',
                        'transactionId': transaction.transaction_id,
                        'amount': float(transaction.amount),
                        'currency': transaction.currency,
                        'paymentMethod': transaction.payment_method
                    }
                    update_user_payment_status(transaction.user_uid, payment_data)
                
                return Response({
                    'success': True,
                    'message': 'Payment synced to Firebase successfully'
                })
            else:
                return Response({
                    'error': 'Failed to sync payment to Firebase'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except PaymentTransaction.DoesNotExist:
            return Response({
                'error': 'Payment transaction not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Payment sync error: {e}")
            return Response({
                'error': 'Internal server error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserDataView(APIView):
    """
    Get user data from Firebase
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, uid):
        """
        Get user data from Firebase by UID
        """
        try:
            # Ensure user can only access their own data
            if request.user.uid != uid:
                return Response({
                    'error': 'Access denied'
                }, status=status.HTTP_403_FORBIDDEN)
            
            user_data = get_firebase_user_data(uid)
            
            if user_data:
                return Response({
                    'success': True,
                    'user_data': user_data
                })
            else:
                return Response({
                    'error': 'User data not found'
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            logger.error(f"User data fetch error: {e}")
            return Response({
                'error': 'Failed to fetch user data'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

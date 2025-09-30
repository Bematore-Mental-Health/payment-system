"""
Firebase Authentication for Django REST Framework

This module provides Firebase token verification and user authentication
for the payment system, integrating with the existing Firebase setup
from the Flutter application.
"""

import json
import logging
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from firebase_admin import auth, firestore
from firebase_admin.exceptions import FirebaseError

logger = logging.getLogger(__name__)


class FirebaseUser:
    """
    Firebase user object that mimics Django User interface
    """
    def __init__(self, firebase_user_data):
        self.uid = firebase_user_data.get('uid')
        self.email = firebase_user_data.get('email')
        self.name = firebase_user_data.get('name', firebase_user_data.get('display_name', ''))
        self.phone_number = firebase_user_data.get('phone_number')
        self.email_verified = firebase_user_data.get('email_verified', False)
        self.is_authenticated = True
        self.is_anonymous = False
        
        # Additional user data from Firestore
        self.firebase_data = firebase_user_data
        
    @property
    def username(self):
        return self.email or self.uid
        
    @property
    def is_active(self):
        return True
        
    def __str__(self):
        return f"FirebaseUser({self.email or self.uid})"


class FirebaseAuthentication(BaseAuthentication):
    """
    Firebase token authentication for Django REST Framework
    """
    
    def authenticate(self, request):
        """
        Authenticate the request using Firebase ID token
        """
        # Get token from Authorization header or firebase-token header
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        firebase_token = request.META.get('HTTP_FIREBASE_TOKEN')
        
        token = None
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        elif firebase_token:
            token = firebase_token
        
        if not token:
            return None
            
        try:
            # Verify the Firebase ID token
            decoded_token = auth.verify_id_token(token)
            uid = decoded_token['uid']
            
            # Get additional user data from Firestore
            db = firestore.client()
            user_doc = db.collection('users').document(uid).get()
            
            firebase_user_data = {
                'uid': uid,
                'email': decoded_token.get('email'),
                'name': decoded_token.get('name'),
                'phone_number': decoded_token.get('phone_number'),
                'email_verified': decoded_token.get('email_verified', False),
            }
            
            # Merge with Firestore user data if available
            if user_doc.exists:
                firestore_data = user_doc.to_dict()
                firebase_user_data.update(firestore_data)
                
            firebase_user = FirebaseUser(firebase_user_data)
            
            logger.info(f"Authenticated Firebase user: {firebase_user.uid}")
            return (firebase_user, token)
            
        except auth.InvalidIdTokenError:
            logger.warning("Invalid Firebase ID token")
            raise AuthenticationFailed('Invalid Firebase token')
        except auth.ExpiredIdTokenError:
            logger.warning("Expired Firebase ID token")
            raise AuthenticationFailed('Expired Firebase token')
        except FirebaseError as e:
            logger.error(f"Firebase authentication error: {e}")
            raise AuthenticationFailed('Firebase authentication failed')
        except Exception as e:
            logger.error(f"Unexpected authentication error: {e}")
            raise AuthenticationFailed('Authentication failed')
    
    def authenticate_header(self, request):
        """
        Return the authentication header to use
        """
        return 'Bearer'


def get_firebase_user_data(uid):
    """
    Get complete user data from Firebase (Auth + Firestore)
    """
    try:
        # Get auth user
        auth_user = auth.get_user(uid)
        
        # Get Firestore user data
        db = firestore.client()
        user_doc = db.collection('users').document(uid).get()
        
        user_data = {
            'uid': uid,
            'email': auth_user.email,
            'name': auth_user.display_name,
            'phone_number': auth_user.phone_number,
            'email_verified': auth_user.email_verified,
            'created_at': auth_user.user_metadata.creation_timestamp,
        }
        
        if user_doc.exists:
            firestore_data = user_doc.to_dict()
            user_data.update(firestore_data)
            
        return user_data
        
    except Exception as e:
        logger.error(f"Error getting Firebase user data: {e}")
        return None


def update_user_payment_status(uid, payment_data):
    """
    Update user's payment status in Firebase Firestore
    """
    try:
        db = firestore.client()
        user_ref = db.collection('users').document(uid)
        
        update_data = {
            'hasPaid': payment_data.get('status') == 'completed',
            'lastPaymentDate': firestore.SERVER_TIMESTAMP,
            'paymentStatus': 'active' if payment_data.get('status') == 'completed' else 'inactive',
            'updatedAt': firestore.SERVER_TIMESTAMP,
        }
        
        user_ref.update(update_data)
        logger.info(f"Updated payment status for user {uid}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating user payment status: {e}")
        return False


def record_payment_in_firebase(payment_data):
    """
    Record payment transaction in Firebase payments collection
    """
    try:
        db = firestore.client()
        payments_ref = db.collection('payments')
        
        # Use transaction ID as document ID to prevent duplicates
        doc_ref = payments_ref.document(payment_data['transactionId'])
        
        payment_record = {
            'userId': payment_data.get('userId'),
            'email': payment_data.get('email'),
            'name': payment_data.get('name'),
            'paymentMethod': payment_data.get('paymentMethod'),
            'amount': payment_data.get('amount'),
            'currency': payment_data.get('currency'),
            'status': payment_data.get('status'),
            'transactionId': payment_data.get('transactionId'),
            'phoneNumber': payment_data.get('phoneNumber'),
            'mpesaReceipt': payment_data.get('mpesaReceipt'),
            'stripeChargeId': payment_data.get('stripeChargeId'),
            'flutterwaveReference': payment_data.get('flutterwaveReference'),
            'purpose': payment_data.get('purpose', 'assessment'),
            'failureReason': payment_data.get('failureReason'),
            'createdAt': firestore.SERVER_TIMESTAMP,
            'updatedAt': firestore.SERVER_TIMESTAMP,
        }
        
        doc_ref.set(payment_record, merge=True)
        logger.info(f"Recorded payment in Firebase: {payment_data['transactionId']}")
        return True
        
    except Exception as e:
        logger.error(f"Error recording payment in Firebase: {e}")
        return False
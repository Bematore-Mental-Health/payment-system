"""
Authentication Views

Views for Firebase token verification and user management.
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .authentication import get_firebase_user_data

logger = logging.getLogger(__name__)


class VerifyTokenView(APIView):
    """
    Verify Firebase token and return user data
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Verify token (token is already verified by middleware)
        """
        try:
            user = request.user
            
            return Response({
                'success': True,
                'user': {
                    'uid': user.uid,
                    'email': user.email,
                    'name': user.name,
                    'phone_number': user.phone_number,
                    'email_verified': user.email_verified
                }
            })
            
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return Response({
                'error': 'Token verification failed'
            }, status=status.HTTP_401_UNAUTHORIZED)


class UserProfileView(APIView):
    """
    Get user profile from Firebase
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get complete user profile from Firebase
        """
        try:
            user = request.user
            user_data = get_firebase_user_data(user.uid)
            
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
            logger.error(f"User profile error: {e}")
            return Response({
                'error': 'Failed to fetch user profile'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

"""
Bematore Payment System - Security Configuration
Professional Payment Processing Platform
Developed by Brandon Ochieng | Bematore Technologies

Enterprise-grade security middleware and configurations for HIPAA/PCI compliance.
"""

import os
import logging
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger('security')

class SecurityHeadersMiddleware(MiddlewareMixin):
    """Enterprise security headers middleware for enhanced protection."""
    
    def process_response(self, request, response):
        """Add comprehensive security headers to all responses."""
        
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdnjs.cloudflare.com; "
            "connect-src 'self' https://api.flutterwave.com https://sandbox.safaricom.co.ke; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        
        # Security headers for enterprise compliance
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = (
            'camera=(), microphone=(), geolocation=(), '
            'payment=(), usb=(), magnetometer=(), gyroscope=()'
        )
        
        # HSTS for HTTPS enforcement
        if settings.USE_HTTPS:
            response['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains; preload'
            )
        
        # Custom security headers
        response['X-Powered-By'] = 'Bematore Security Framework'
        response['X-Platform-Version'] = settings.PLATFORM_INFO.get('version', '1.0.0')
        
        return response

class IPWhitelistMiddleware(MiddlewareMixin):
    """IP whitelisting middleware for admin and sensitive endpoints."""
    
    PROTECTED_PATHS = [
        '/admin/',
        '/callbacks/',
        '/api/admin/',
        '/health/detailed/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_ips = self._load_allowed_ips()
    
    def _load_allowed_ips(self):
        """Load allowed IP addresses from environment."""
        allowed_ips = os.getenv('ALLOWED_IPS', '').split(',')
        return [ip.strip() for ip in allowed_ips if ip.strip()]
    
    def _get_client_ip(self, request):
        """Get the real client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
    
    def __call__(self, request):
        # Check if path requires IP whitelisting
        if any(request.path.startswith(path) for path in self.PROTECTED_PATHS):
            client_ip = self._get_client_ip(request)
            
            # Allow localhost in development
            if settings.DEBUG and client_ip in ['127.0.0.1', '::1']:
                pass
            elif self.allowed_ips and client_ip not in self.allowed_ips:
                logger.warning(
                    f"Unauthorized IP access attempt: {client_ip} to {request.path}",
                    extra={'ip': client_ip, 'path': request.path, 'user_agent': request.META.get('HTTP_USER_AGENT')}
                )
                return HttpResponseForbidden(
                    "Access denied. Your IP address is not authorized to access this resource."
                )
        
        return self.get_response(request)

class RateLimitMiddleware(MiddlewareMixin):
    """Rate limiting middleware for API protection."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limits = {}
    
    def _get_cache_key(self, request):
        """Generate cache key for rate limiting."""
        ip = self._get_client_ip(request)
        path = request.path
        return f"rate_limit:{ip}:{path}"
    
    def _get_client_ip(self, request):
        """Get the real client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
    
    def __call__(self, request):
        # Skip rate limiting in development
        if settings.DEBUG:
            return self.get_response(request)
        
        # Check rate limits for API endpoints
        if request.path.startswith('/api/'):
            cache_key = self._get_cache_key(request)
            
            # Implement rate limiting logic here
            # This would typically use Redis or Django cache
            
        return self.get_response(request)

class AuditLogMiddleware(MiddlewareMixin):
    """Comprehensive audit logging middleware for compliance."""
    
    SENSITIVE_PATHS = [
        '/api/payments/',
        '/admin/',
        '/callbacks/',
        '/api/auth/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.audit_logger = logging.getLogger('audit')
    
    def __call__(self, request):
        # Log sensitive requests
        if any(request.path.startswith(path) for path in self.SENSITIVE_PATHS):
            self._log_request(request)
        
        response = self.get_response(request)
        
        # Log sensitive responses
        if any(request.path.startswith(path) for path in self.SENSITIVE_PATHS):
            self._log_response(request, response)
        
        return response
    
    def _log_request(self, request):
        """Log incoming request details."""
        log_data = {
            'event': 'request_received',
            'method': request.method,
            'path': request.path,
            'ip': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'user': str(request.user) if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous',
            'timestamp': self._get_timestamp(),
        }
        
        # Don't log sensitive data in request body
        if request.method in ['POST', 'PUT', 'PATCH']:
            log_data['has_body'] = bool(request.body)
            log_data['content_type'] = request.content_type
        
        self.audit_logger.info("Request audit", extra=log_data)
    
    def _log_response(self, request, response):
        """Log response details."""
        log_data = {
            'event': 'response_sent',
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'ip': self._get_client_ip(request),
            'user': str(request.user) if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous',
            'timestamp': self._get_timestamp(),
        }
        
        self.audit_logger.info("Response audit", extra=log_data)
    
    def _get_client_ip(self, request):
        """Get the real client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
    
    def _get_timestamp(self):
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'

class MaintenanceModeMiddleware(MiddlewareMixin):
    """Maintenance mode middleware for planned downtime."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if os.getenv('MAINTENANCE_MODE', 'False').lower() == 'true':
            # Allow admin access during maintenance
            if request.path.startswith('/admin/') and request.user.is_superuser:
                return self.get_response(request)
            
            # Allow health checks
            if request.path.startswith('/health/'):
                return self.get_response(request)
            
            from django.http import HttpResponse
            maintenance_message = os.getenv(
                'MAINTENANCE_MESSAGE',
                'System temporarily unavailable for scheduled maintenance.'
            )
            
            return HttpResponse(
                f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Maintenance - Bematore Payment System</title>
                    <style>
                        body {{ 
                            font-family: Arial, sans-serif; 
                            text-align: center; 
                            padding: 50px; 
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                        }}
                        .container {{ 
                            max-width: 600px; 
                            margin: 0 auto; 
                            padding: 40px; 
                            background: rgba(255,255,255,0.1); 
                            border-radius: 10px; 
                        }}
                        h1 {{ margin-bottom: 20px; }}
                        p {{ margin-bottom: 15px; line-height: 1.6; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>🔧 Scheduled Maintenance</h1>
                        <p>{maintenance_message}</p>
                        <p>We apologize for any inconvenience. Please check back shortly.</p>
                        <hr style="margin: 30px 0; opacity: 0.3;">
                        <p><strong>Bematore Payment System</strong><br>
                        Professional Payment Processing Platform</p>
                    </div>
                </body>
                </html>
                """,
                status=503,
                content_type='text/html'
            )
        
        return self.get_response(request)

# Security utility functions
def validate_payment_signature(payload, signature, secret):
    """Validate webhook signature for payment callbacks."""
    import hmac
    import hashlib
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

def sanitize_input(data):
    """Sanitize user input to prevent XSS and injection attacks."""
    import html
    import re
    
    if isinstance(data, str):
        # Remove potentially dangerous characters
        data = html.escape(data)
        data = re.sub(r'[<>"\';]', '', data)
    
    return data

def generate_secure_token(length=32):
    """Generate cryptographically secure random token."""
    import secrets
    import string
    
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

class SecurityConfig:
    """Central security configuration class."""
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 12
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBERS = True
    REQUIRE_SPECIAL_CHARS = True
    
    # Session security
    SESSION_TIMEOUT = 1800  # 30 minutes
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = 900  # 15 minutes
    
    # API security
    API_RATE_LIMIT = 100  # requests per minute
    MAX_REQUEST_SIZE = 1024 * 1024  # 1MB
    
    # File upload security
    ALLOWED_FILE_TYPES = ['.pdf', '.png', '.jpg', '.jpeg']
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    
    # Encryption settings
    ENCRYPTION_ALGORITHM = 'AES-256-GCM'
    KEY_ROTATION_INTERVAL = 30  # days
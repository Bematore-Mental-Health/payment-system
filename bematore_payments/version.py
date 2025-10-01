"""
Bematore Payment System Version Management
Professional Payment Processing Platform
Developed by Brandon Ochieng | Mental Health Technology Solutions
"""

__version__ = "1.0.0"
__version_info__ = (1, 0, 0)
__author__ = "Brandon Ochieng"
__email__ = "brandoncohieng72@gmail.com"
__description__ = "Professional Payment Processing Platform for Bematore Technologies"
__license__ = "Proprietary"
__copyright__ = "Copyright 2025 Bematore Technologies"

# Release Information
RELEASE_NAME = "Genesis"
RELEASE_DATE = "2025-10-01"
BUILD_NUMBER = "1000"

# Platform Information
PLATFORM_NAME = "Bematore Payment System"
PLATFORM_TAGLINE = "Professional Payment Processing Platform"
DEVELOPER = "Brandon Ochieng"
ORGANIZATION = "Bematore Technologies"

# Feature Flags
FEATURES = {
    'mpesa_integration': True,
    'flutterwave_integration': False,  # Under development
    'paypal_integration': False,       # Under development
    'firebase_sync': True,
    'currency_conversion': True,
    'comprehensive_logging': True,
    'enterprise_security': True,
}

# System Configuration
SYSTEM_CONFIG = {
    'max_transaction_amount': 1000000,  # KES
    'session_timeout': 1800,  # 30 minutes
    'max_retry_attempts': 3,
    'callback_timeout': 300,  # 5 minutes
}

def get_version():
    """Get the current version string."""
    return __version__

def get_version_info():
    """Get detailed version information."""
    return {
        'version': __version__,
        'version_info': __version_info__,
        'release_name': RELEASE_NAME,
        'release_date': RELEASE_DATE,
        'build_number': BUILD_NUMBER,
        'author': __author__,
        'organization': ORGANIZATION,
    }
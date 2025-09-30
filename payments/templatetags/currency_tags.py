"""
Custom template tags for payment system
"""

from django import template
from decimal import Decimal
from ..services.currency_service import CurrencyService

register = template.Library()

@register.filter
def format_currency(amount, currency_code):
    """
    Format amount with appropriate currency symbol and formatting
    
    Usage: {{ amount|format_currency:currency_code }}
    """
    try:
        currency_service = CurrencyService()
        return currency_service.format_currency(float(amount), currency_code)
    except (ValueError, TypeError):
        return f"{currency_code} {amount}"

@register.filter
def currency_symbol(currency_code):
    """
    Get currency symbol for a currency code
    
    Usage: {{ currency_code|currency_symbol }}
    """
    symbols = {
        'USD': '$',
        'KES': 'KSh',
        'EUR': '€',
        'GBP': '£',
        'JPY': '¥',
        'NGN': '₦',
        'ZAR': 'R',
        'GHS': '₵',
    }
    return symbols.get(currency_code.upper(), currency_code)
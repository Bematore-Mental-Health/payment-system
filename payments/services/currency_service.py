"""
Currency Conversion Service

Handles currency conversion to maintain consistency with Flutter app.
All amounts are stored in USD (base currency) and converted for display.
"""

import logging
from decimal import Decimal
from typing import Dict, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class CurrencyService:
    """
    Currency conversion service consistent with Flutter app behavior
    """
    
    def __init__(self):
        self.base_currency = settings.PAYMENT_CONFIG['DEFAULT_CURRENCY']  # USD
        self.exchange_rates = settings.PAYMENT_CONFIG['EXCHANGE_RATES']
        self.fallback_currency = settings.PAYMENT_CONFIG['DISPLAY_FALLBACK_CURRENCY']  # KES
    
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """
        Get exchange rate between two currencies
        
        Args:
            from_currency: Source currency code (e.g., 'USD')
            to_currency: Target currency code (e.g., 'KES')
            
        Returns:
            Exchange rate as float
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        if from_currency == to_currency:
            return 1.0
        
        # If converting from USD (base currency)
        if from_currency == self.base_currency:
            return self.exchange_rates.get(to_currency, 1.0)
        
        # If converting to USD (base currency)
        if to_currency == self.base_currency:
            from_rate = self.exchange_rates.get(from_currency, 1.0)
            return 1.0 / from_rate if from_rate != 0 else 1.0
        
        # Converting between two non-USD currencies
        # Convert through USD: from -> USD -> to
        from_to_usd_rate = 1.0 / self.exchange_rates.get(from_currency, 1.0)
        usd_to_target_rate = self.exchange_rates.get(to_currency, 1.0)
        
        return from_to_usd_rate * usd_to_target_rate
    
    def convert_amount(self, amount: float, from_currency: str, to_currency: str) -> Decimal:
        """
        Convert amount between currencies
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Converted amount as Decimal
        """
        try:
            rate = self.get_exchange_rate(from_currency, to_currency)
            converted = Decimal(str(amount)) * Decimal(str(rate))
            return converted.quantize(Decimal('0.01'))  # Round to 2 decimal places
        except Exception as e:
            logger.error(f"Currency conversion error: {e}")
            return Decimal(str(amount))  # Return original amount on error
    
    def convert_to_usd(self, amount: float, from_currency: str) -> Decimal:
        """
        Convert any currency amount to USD (base currency)
        Consistent with Flutter app storage behavior
        
        Args:
            amount: Amount in source currency
            from_currency: Source currency code
            
        Returns:
            Amount in USD as Decimal
        """
        return self.convert_amount(amount, from_currency, self.base_currency)
    
    def convert_from_usd(self, usd_amount: float, to_currency: str) -> Decimal:
        """
        Convert USD amount to target currency for display
        Consistent with Flutter app display behavior
        
        Args:
            usd_amount: Amount in USD
            to_currency: Target currency code
            
        Returns:
            Amount in target currency as Decimal
        """
        return self.convert_amount(usd_amount, self.base_currency, to_currency)
    
    def format_currency(self, amount: float, currency: str) -> str:
        """
        Format amount for display with appropriate currency symbol
        
        Args:
            amount: Amount to format
            currency: Currency code
            
        Returns:
            Formatted currency string
        """
        currency = currency.upper()
        
        # Currency symbols mapping
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
        
        symbol = symbols.get(currency, currency)
        
        # Format based on currency
        if currency in ['KES', 'NGN', 'JPY']:
            # Currencies without decimal places for large amounts
            if amount >= 1000:
                return f"{symbol} {amount:,.0f}"
            else:
                return f"{symbol} {amount:.2f}"
        else:
            # Standard decimal formatting
            return f"{symbol} {amount:.2f}"
    
    def get_mpesa_amount(self, usd_amount: float) -> Decimal:
        """
        Get KES amount for M-Pesa payments
        M-Pesa always operates in KES regardless of user location
        
        Args:
            usd_amount: Amount in USD
            
        Returns:
            Amount in KES as Decimal
        """
        return self.convert_from_usd(usd_amount, 'KES')
    
    def normalize_amount_for_storage(self, amount: float, currency: str) -> Decimal:
        """
        Normalize amount to USD for consistent storage
        Mirrors Flutter app behavior of storing all amounts in USD
        
        Args:
            amount: Amount in source currency
            currency: Source currency code
            
        Returns:
            Amount in USD for storage
        """
        return self.convert_to_usd(amount, currency)
    
    def get_display_amount(self, usd_amount: float, display_currency: str = None) -> tuple:
        """
        Get amount and currency for display
        
        Args:
            usd_amount: Stored USD amount
            display_currency: Preferred display currency (optional)
            
        Returns:
            Tuple of (display_amount, currency_code)
        """
        if not display_currency:
            display_currency = self.fallback_currency
        
        display_amount = self.convert_from_usd(usd_amount, display_currency)
        return float(display_amount), display_currency
    
    def validate_currency_code(self, currency: str) -> bool:
        """
        Validate if currency code is supported
        
        Args:
            currency: Currency code to validate
            
        Returns:
            True if currency is supported
        """
        return currency.upper() in self.exchange_rates
    
    def get_supported_currencies(self) -> list:
        """
        Get list of supported currency codes
        
        Returns:
            List of supported currency codes
        """
        return list(self.exchange_rates.keys())
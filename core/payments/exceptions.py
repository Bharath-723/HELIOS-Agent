"""
core/payments/exceptions.py — Custom Exceptions for HELIOS Payment Subsystem
================================================================================
Isolated exceptions for payment operations, transaction guards, and verifications.
"""

class PaymentException(Exception):
    """Base exception for all payment-related errors."""
    pass


class PaymentSecurityException(PaymentException):
    """Raised when a security policy or signature check fails."""
    pass


class PaymentConfigurationException(PaymentException):
    """Raised when payment configuration or credentials are invalid."""
    pass


class PaymentAuthorizationException(PaymentException):
    """Raised when an operation requires explicit user authorization."""
    pass


class PaymentVerificationException(PaymentException):
    """Raised when signature verification or order/payment verification fails."""
    pass


class PaymentOrderException(PaymentException):
    """Raised when Razorpay order creation or retrieval fails."""
    pass


class PaymentIdempotencyException(PaymentException):
    """Raised when an idempotent duplicate conflict is detected."""
    pass


class PaymentLimitExceededException(PaymentException):
    """Raised when a payment amount exceeds maximum allowed safety threshold."""
    pass

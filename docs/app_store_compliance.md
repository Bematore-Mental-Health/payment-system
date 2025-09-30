# App Store Compliance Guide

This document outlines the compliance measures implemented for both Apple App Store and Google Play Store to ensure approval and ongoing compliance.

## Apple App Store Compliance

### Guideline 3.1.1 - In-App Purchase
**Issue**: Apps may not include buttons, external links, or other calls to action that direct customers to purchasing mechanisms other than in-app purchase.

**Our Solution**:
1. **External Payment System**: All payments are processed through our external payment system at `payments.bematore.com`
2. **Compliance Notice**: iOS users see a mandatory notice explaining the external payment redirect
3. **User Agent Detection**: System automatically detects iOS devices and shows appropriate messaging
4. **Clear Communication**: Users are informed that external payments may have different terms and protections

### Implementation Details
- **Location**: `payments/views.py` - iOS detection logic
- **Template**: `templates/payment_form.html` - Compliance notice display
- **Styling**: `static/css/payment-styles.css` - Apple-specific styling

## Google Play Store Compliance

### Play Billing Policy
**Requirements**: Apps selling digital goods must use Google Play Billing, but apps selling physical goods or services can use alternative payment methods.

**Our Solution**:
1. **Physical Service Classification**: Mental health services are classified as physical/real-world services
2. **External Payment Allowed**: Our services qualify for external payment processing
3. **Transparent Communication**: Android users receive clear information about the external payment system
4. **Service-Based Pricing**: All payments are for actual therapeutic services, not digital goods

### Implementation Details
- **Location**: `payments/views.py` - Android detection logic
- **Template**: `templates/payment_form.html` - Android-specific messaging
- **Styling**: `static/css/payment-styles.css` - Green-themed Android styling

## Technical Implementation

### User Agent Detection
```python
user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
is_ios = 'iphone' in user_agent or 'ipad' in user_agent or 'ios' in user_agent
is_android = 'android' in user_agent
is_mobile_app = is_ios or is_android
```

### Compliance Messages

#### iOS Users (Apple Compliance)
> "You are being redirected to an external payment system. This payment is processed outside of the app and may have different terms, privacy policies, and user protections than in-app purchases."

#### Android Users (Google Play Compliance)
> "This payment is processed through our secure external payment system to ensure the best rates and payment options for your mental health services."

## Domain Configuration

### Production Environment
- **Domain**: `payments.bematore.com`
- **SSL**: Required for all payment processing
- **CORS**: Configured for app domains (`bematore.com`, `app.bematore.com`)

### Security Measures
1. **HTTPS Only**: All payment processing over secure connections
2. **CORS Restrictions**: Limited to approved domains
3. **Firebase Integration**: Secure user authentication and data sync
4. **PCI Compliance**: Through Flutterwave and M-Pesa integrations

## Service Classification

### Mental Health Services
Our services are classified as **physical services** rather than digital goods:

1. **Therapy Sessions**: Real-world therapeutic consultations
2. **Mental Health Assessments**: Professional evaluations
3. **Counseling Services**: Personal development and mental wellness
4. **Professional Consultations**: Licensed therapist interactions

This classification allows us to use external payment systems on both platforms.

## Compliance Checklist

### Apple App Store
- [x] External payment system implemented
- [x] iOS compliance notice displayed
- [x] No in-app purchase buttons or references
- [x] Clear external redirect communication
- [x] Proper user protection disclosure

### Google Play Store
- [x] Physical service classification established
- [x] External payment system for services (not digital goods)
- [x] Android-specific messaging implemented
- [x] Transparent payment process communication
- [x] No violation of Play Billing policy

## Testing Requirements

### iOS Testing
1. Test on iPhone/iPad devices
2. Verify compliance notice appears
3. Confirm external redirect works
4. Validate user experience flow

### Android Testing
1. Test on Android devices
2. Verify Android-specific messaging
3. Confirm payment flow completion
4. Validate service-based payment processing

## Maintenance

### Regular Reviews
1. **Monthly**: Review app store policy updates
2. **Quarterly**: Audit compliance implementation
3. **Before Updates**: Verify continued compliance
4. **Policy Changes**: Update messaging and flow as needed

### Documentation Updates
- Keep compliance notices current with policy changes
- Update technical implementation as platforms evolve
- Maintain clear separation between digital goods and services

## Contact Information

For compliance questions or updates:
- **Technical Lead**: [Your contact]
- **Legal Counsel**: [Legal contact if applicable]
- **App Store Relations**: [Store contact if applicable]

---

**Last Updated**: September 30, 2025
**Next Review**: October 30, 2025
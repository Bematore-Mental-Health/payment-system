# Bematore Payment System

> **Professional Payment Processing Platform**  
> Developed by **Brandon Ochieng** | Mental Health Technology Solutions

[![Django](https://img.shields.io/badge/Django-4.2+-092E20?style=flat&logo=django&logoColor=white)](https://djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1?style=flat&logo=mysql&logoColor=white)](https://mysql.com/)
[![Firebase](https://img.shields.io/badge/Firebase-Admin-FFCA28?style=flat&logo=firebase&logoColor=black)](https://firebase.google.com/)
[![REST API](https://img.shields.io/badge/REST-API-FF6B35?style=flat)](https://restfulapi.net/)

## � Project Overview

The Bematore Payment System is a robust, enterprise-grade payment processing platform specifically designed for the mental health sector. Built as an external payment gateway, it ensures compliance with Apple App Store guidelines while providing seamless integration with mobile applications through Firebase authentication and real-time data synchronization.

### Key Highlights
- **External Payment Processing**: Compliant with app store payment policies
- **Multi-Gateway Integration**: M-Pesa, Flutterwave, PayPal support
- **Firebase Integration**: Real-time user authentication and data sync
- **Global Currency Support**: 50+ currencies with automatic conversion
- **Enterprise Security**: PCI-compliant payment handling
- **Scalable Architecture**: Built for high-volume transaction processing

## 🏗️ System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Flutter App   │────│  Payment System  │────│  Payment Gateways   │
│  (Mobile/Web)   │    │   Django API     │    │  M-Pesa/Flutter     │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
         │                        │                         │
         │                        │                         │
         └────────────────────────┼─────────────────────────┘
                                  │
                        ┌─────────▼─────────┐
                        │   Firebase        │
                        │  Authentication   │
                        │  & Data Storage   │
                        └───────────────────┘
```

## 🚀 Core Features

### Payment Processing
- **Multi-Gateway Support**: Integrated M-Pesa, Flutterwave, and PayPal
- **Currency Management**: Real-time exchange rates for 50+ currencies
- **Transaction Security**: End-to-end encryption and PCI compliance
- **Callback Handling**: Automated payment status updates

### Authentication & Security
- **Firebase Authentication**: Seamless token-based verification
- **CORS Configuration**: Secure cross-origin request handling
- **SSL/TLS Support**: Production-ready security configurations
- **Rate Limiting**: Built-in protection against abuse

### Data Management
- **Firebase Sync**: Real-time user and payment data synchronization
- **MySQL Database**: Reliable local caching and transaction logging
- **RESTful API**: Clean, documented API endpoints
- **Audit Trails**: Comprehensive payment and user activity logging

## 📊 API Documentation

### Version Information
- **API Version**: v1.0
- **Django Version**: 4.2.7
- **DRF Version**: 3.14.0
- **Python Version**: 3.11+

### Core Endpoints

| Endpoint | Method | Description | Authentication |
|----------|--------|-------------|----------------|
| `/api/v1/payments/` | POST | Initialize payment | Firebase Token |
| `/api/v1/payments/{id}/` | GET | Get payment status | Firebase Token |
| `/api/v1/callbacks/mpesa/` | POST | M-Pesa callback | Webhook |
| `/api/v1/callbacks/flutterwave/` | POST | Flutterwave callback | Webhook |
| `/api/v1/currencies/` | GET | List supported currencies | Firebase Token |
| `/api/v1/exchange-rates/` | GET | Current exchange rates | Firebase Token |

### Payment Flow
1. **Authentication**: Verify Firebase token from mobile app
2. **User Context**: Load user profile and payment history
3. **Payment Initialization**: Create payment session with selected gateway
4. **Processing**: Handle payment through M-Pesa/Flutterwave/PayPal
5. **Callback Processing**: Receive and validate payment status
6. **Firebase Update**: Sync payment status to user profile
7. **Redirect**: Return user to mobile app with results

## 🛠️ Technology Stack

### Backend Framework
- **Django 4.2+**: Web framework with ORM and admin interface
- **Django REST Framework 3.14+**: API development and serialization
- **Firebase Admin SDK 6.2+**: Server-side Firebase integration

### Database & Storage
- **MySQL 8.0+**: Primary database for transactions and caching
- **Firebase Firestore**: Real-time user data and payment records
- **Redis** (Optional): Caching and session management

### Payment Integrations
- **M-Pesa Daraja API**: Direct integration for Kenyan mobile payments
- **Flutterwave API**: International card and bank transfers
- **PayPal REST API**: Alternative payment method

### Security & Authentication
- **Firebase Authentication**: Token-based user verification
- **CORS Middleware**: Cross-origin request security
- **WhiteNoise**: Static file serving with compression
- **SSL/TLS**: Production-ready HTTPS configuration

## 🔧 Installation & Setup

### Prerequisites
- Python 3.11+
- MySQL 8.0+
- Firebase Project with Admin SDK
- Payment gateway credentials (M-Pesa, Flutterwave, PayPal)

### Local Development
```bash
# Clone repository
git clone https://github.com/bematore/payment-system.git
cd payment-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Database setup
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Production Deployment (cPanel)
```bash
# Upload files to cPanel
# Configure database in cPanel MySQL
# Update .env with production values
# Set up static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate
```

## 📝 Configuration

### Environment Variables
Key configuration variables for production deployment:

```env
# Django Core
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=payments.bematore.com,www.bematore.com

# Database Configuration
DB_NAME=bematore_payments
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306

# Firebase Configuration
FIREBASE_PROJECT_ID=bematore-public-app-d47e5
FIREBASE_PRIVATE_KEY_PATH=firebase-adminsdk.json

# Payment Gateway Configuration
MPESA_CONSUMER_KEY=your_mpesa_consumer_key
MPESA_CONSUMER_SECRET=your_mpesa_consumer_secret
FLUTTERWAVE_SECRET_KEY=your_flutterwave_secret
```

## 🧪 Testing

```bash
# Run unit tests
python manage.py test

# Run specific app tests
python manage.py test payments
python manage.py test authentication

# Coverage report
coverage run --source='.' manage.py test
coverage report
```

## 📦 Deployment

### Production Checklist
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Static files collected
- [ ] SSL certificate installed
- [ ] Payment gateway webhooks configured
- [ ] Firebase service account setup
- [ ] Monitoring and logging enabled

### Performance Optimization
- Database indexing for payment queries
- Redis caching for exchange rates
- CDN integration for static files
- Database connection pooling
- Celery for background tasks

## 🤝 Contributing

This project follows professional development standards:

1. **Code Style**: Black formatting, PEP 8 compliance
2. **Testing**: Comprehensive unit and integration tests
3. **Documentation**: Inline comments and API documentation
4. **Security**: Regular dependency updates and security audits

## 📞 Support & Contact

**Developer**: Brandon Ochieng  
**Email**: brandon@bematore.com  
**Company**: Bematore Mental Health Solutions  
**Website**: https://bematore.com  

For technical support or feature requests, please contact the development team through official channels.

## 📄 License

This project is proprietary software developed for Bematore Mental Health Platform. All rights reserved.

---

*Built with ❤️ for Bematore by [Brandon Ochieng](https://github.com/OchiengBrandon)*
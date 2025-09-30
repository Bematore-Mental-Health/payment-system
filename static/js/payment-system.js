/**
 * Bematore Payment System - Modern JavaScript
 * Enhanced interactions for app-like experience
 */

class PaymentSystem {
    constructor() {
        this.currentMethod = null;
        this.isProcessing = false;
        this.init();
    }

    init() {
        this.bindEvents();
        this.setupAnimations();
        this.initializeTooltips();
    }

    bindEvents() {
        // Payment method selection
        document.querySelectorAll('.payment-method').forEach(method => {
            method.addEventListener('click', (e) => this.selectPaymentMethod(e));
        });

        // Form submission
        const form = document.getElementById('paymentForm');
        if (form) {
            form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }

        // Phone number formatting for M-Pesa
        const phoneInput = document.getElementById('phoneNumber');
        if (phoneInput) {
            phoneInput.addEventListener('input', (e) => this.formatPhoneNumber(e));
            phoneInput.addEventListener('blur', (e) => this.validatePhoneNumber(e));
        }

        // Status checking
        const checkStatusBtn = document.getElementById('checkStatusBtn');
        if (checkStatusBtn) {
            checkStatusBtn.addEventListener('click', () => this.checkPaymentStatus());
        }

        // Auto-refresh for pending payments
        if (window.paymentStatus === 'pending') {
            this.startStatusPolling();
        }

        // Keyboard navigation
        document.addEventListener('keydown', (e) => this.handleKeyboardNav(e));

        // Open in browser button
        const openInBrowserBtn = document.getElementById('openInBrowserBtn');
        if (openInBrowserBtn) {
            openInBrowserBtn.addEventListener('click', () => this.openInBrowser());
        }
    }

    selectPaymentMethod(event) {
        const method = event.currentTarget;
        const methodType = method.dataset.method;

        // Remove selection from all methods
        document.querySelectorAll('.payment-method').forEach(m => {
            m.classList.remove('selected');
            m.setAttribute('aria-selected', 'false');
        });

        // Select current method
        method.classList.add('selected');
        method.setAttribute('aria-selected', 'true');

        // Update hidden input
        const paymentMethodInput = document.getElementById('paymentMethod');
        if (paymentMethodInput) {
            paymentMethodInput.value = methodType;
        }

        // Show/hide relevant fields with animation
        this.showPaymentFields(methodType);

        // Update button state
        this.updatePayButton(methodType);

        // Haptic feedback simulation
        this.triggerHapticFeedback();

        this.currentMethod = methodType;
    }

    showPaymentFields(methodType) {
        const allFields = document.querySelectorAll('.payment-fields');
        
        // Hide all fields first
        allFields.forEach(field => {
            field.classList.remove('show');
            field.style.display = 'none';
        });

        // Show relevant fields with animation
        const targetField = document.getElementById(`${methodType}Fields`);
        if (targetField) {
            setTimeout(() => {
                targetField.style.display = 'block';
                targetField.classList.add('show');
            }, 150);
        }
    }

    updatePayButton(methodType) {
        const button = document.getElementById('payButton');
        const buttonText = document.getElementById('buttonText');
        
        if (!button || !buttonText) return;

        button.disabled = false;
        button.classList.remove('btn-secondary');
        button.classList.add('btn-primary');

        const buttonTexts = {
            mpesa: '💳 Pay with M-Pesa',
            flutterwave: '💳 Continue to Card Payment'
        };

        buttonText.textContent = buttonTexts[methodType] || 'Continue Payment';

        // Add subtle animation
        button.style.transform = 'scale(0.98)';
        setTimeout(() => {
            button.style.transform = 'scale(1)';
        }, 100);
    }

    formatPhoneNumber(event) {
        let value = event.target.value.replace(/\D/g, '');
        
        // Store original input for validation
        let originalValue = value;
        
        // Handle Kenyan phone number formats
        if (value.length > 0) {
            // Convert 07xxxxxxxx to 254xxxxxxxx for storage
            if (value.startsWith('0') && value.length <= 10) {
                // Keep original display but store converted version
                originalValue = value;
                value = '254' + value.substring(1);
            } else if (value.startsWith('7') && value.length <= 9) {
                // 7xxxxxxxx -> 254xxxxxxxx
                originalValue = '0' + value;
                value = '254' + value;
            } else if (value.startsWith('254')) {
                // Already in international format
                originalValue = '0' + value.substring(3);
            }
        }

        // Limit length
        if (originalValue.startsWith('0') && originalValue.length > 10) {
            originalValue = originalValue.substring(0, 10);
        } else if (value.startsWith('254') && value.length > 12) {
            value = value.substring(0, 12);
        }

        // Display the original format (0xxxxxxxxx) for better UX
        let displayValue = originalValue;
        if (displayValue.length >= 4) {
            displayValue = displayValue.substring(0, 4) + ' ' + displayValue.substring(4);
            if (displayValue.length >= 9) {
                displayValue = displayValue.substring(0, 9) + ' ' + displayValue.substring(9);
            }
        }

        event.target.value = displayValue;
        event.target.dataset.raw = value; // Store international format for validation
        event.target.dataset.display = originalValue; // Store local format for display
    }

    validatePhoneNumber(event) {
        const input = event.target;
        const rawValue = input.dataset.raw || input.value.replace(/\D/g, '');
        const displayValue = input.dataset.display || input.value.replace(/\D/g, '');
        
        // Validate both local format (07xxxxxxxx) and international format (254xxxxxxxx)
        const localFormat = /^0[17][0-9]{8}$/.test(displayValue); // 0712345678 or 0112345678
        const internationalFormat = /^254[17][0-9]{8}$/.test(rawValue); // 254712345678 or 254112345678
        
        const isValid = localFormat || internationalFormat;

        if (rawValue && !isValid) {
            input.classList.add('error');
            this.showFieldError(input, 'Please enter a valid M-Pesa number (e.g., 0712345678)');
        } else {
            input.classList.remove('error');
            this.hideFieldError(input);
        }

        return isValid;
    }

    showFieldError(field, message) {
        let errorDiv = field.parentNode.querySelector('.field-error');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'field-error';
            field.parentNode.appendChild(errorDiv);
        }
        errorDiv.textContent = message;
        errorDiv.style.color = 'var(--error-color)';
        errorDiv.style.fontSize = 'var(--font-size-xs)';
        errorDiv.style.marginTop = 'var(--space-xs)';
    }

    hideFieldError(field) {
        const errorDiv = field.parentNode.querySelector('.field-error');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    async handleFormSubmit(event) {
        event.preventDefault();

        if (this.isProcessing) return;

        const form = event.target;
        const formData = new FormData(form);

        // Validate form
        if (!this.validateForm(formData)) {
            return;
        }

        this.isProcessing = true;
        this.showProcessingState();

        try {
            // Submit form
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                }
            });

            if (response.redirected) {
                // Handle redirect
                window.location.href = response.url;
            } else {
                const result = await response.text();
                // Handle JSON response or error
                this.handleFormResponse(result);
            }
        } catch (error) {
            console.error('Payment submission error:', error);
            this.showError('Network error. Please check your connection and try again.');
        } finally {
            this.isProcessing = false;
            this.hideProcessingState();
        }
    }

    validateForm(formData) {
        const method = formData.get('payment_method');
        
        if (!method) {
            this.showError('Please select a payment method');
            return false;
        }

        if (method === 'mpesa') {
            const phoneInput = document.getElementById('phoneNumber');
            if (!this.validatePhoneNumber({target: phoneInput})) {
                phoneInput.focus();
                return false;
            }
            
            // Set the raw phone number value
            const rawPhone = phoneInput.dataset.raw;
            formData.set('phone_number', rawPhone);
        }

        return true;
    }

    showProcessingState() {
        const button = document.getElementById('payButton');
        const buttonText = document.getElementById('buttonText');
        const spinner = document.getElementById('loadingSpinner');

        if (button) button.disabled = true;
        if (buttonText) buttonText.textContent = 'Processing...';
        if (spinner) spinner.style.display = 'inline-block';

        // Disable form
        document.querySelectorAll('.payment-method, input, select').forEach(el => {
            el.disabled = true;
        });
    }

    hideProcessingState() {
        const button = document.getElementById('payButton');
        const buttonText = document.getElementById('buttonText');
        const spinner = document.getElementById('loadingSpinner');

        if (button) button.disabled = false;
        if (buttonText) buttonText.textContent = this.getButtonText();
        if (spinner) spinner.style.display = 'none';

        // Re-enable form
        document.querySelectorAll('.payment-method, input, select').forEach(el => {
            el.disabled = false;
        });
    }

    getButtonText() {
        const buttonTexts = {
            mpesa: '💳 Pay with M-Pesa',
            flutterwave: '💳 Continue to Card Payment'
        };
        return buttonTexts[this.currentMethod] || 'Select Payment Method';
    }

    async checkPaymentStatus() {
        const button = document.getElementById('checkStatusBtn');
        const originalText = button.textContent;
        
        button.disabled = true;
        button.innerHTML = '<span class="loading-spinner"></span> Checking...';

        try {
            const transactionId = window.transactionId;
            const token = window.userToken;
            
            const response = await fetch(`/payments/api/status/${encodeURIComponent(transactionId)}/`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();
            
            if (data.status === 'completed' || data.status === 'failed') {
                location.reload();
            } else {
                this.showTemporaryMessage('Payment still processing...', 'info');
            }
        } catch (error) {
            console.error('Status check error:', error);
            this.showTemporaryMessage('Unable to check status. Please try again.', 'error');
        } finally {
            button.disabled = false;
            button.textContent = originalText;
        }
    }

    startStatusPolling() {
        // Poll every 30 seconds
        setInterval(() => {
            if (!document.hidden) {
                this.checkPaymentStatus();
            }
        }, 30000);

        // Check when page becomes visible
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                setTimeout(() => this.checkPaymentStatus(), 1000);
            }
        });
    }

    showError(message) {
        this.showAlert(message, 'error');
    }

    showSuccess(message) {
        this.showAlert(message, 'success');
    }

    showAlert(message, type = 'info') {
        const existingAlert = document.querySelector('.alert-toast');
        if (existingAlert) {
            existingAlert.remove();
        }

        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-toast`;
        alert.innerHTML = `
            <div class="alert-content">
                <div class="alert-title">${this.getAlertTitle(type)}</div>
                ${message}
            </div>
        `;
        alert.style.position = 'fixed';
        alert.style.top = '20px';
        alert.style.right = '20px';
        alert.style.zIndex = '9999';
        alert.style.maxWidth = '400px';
        alert.style.animation = 'slideInRight 0.3s ease-out';

        document.body.appendChild(alert);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            alert.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    }

    showTemporaryMessage(message, type = 'info') {
        this.showAlert(message, type);
    }

    getAlertTitle(type) {
        const titles = {
            error: 'Error',
            success: 'Success',
            warning: 'Warning',
            info: 'Information'
        };
        return titles[type] || 'Notice';
    }

    triggerHapticFeedback() {
        // Simulate haptic feedback with vibration API
        if ('vibrate' in navigator) {
            navigator.vibrate(50);
        }
    }

    setupAnimations() {
        // Add entrance animations
        const elements = document.querySelectorAll('.payment-card > *');
        elements.forEach((el, index) => {
            el.style.animation = `fadeInUp 0.5s ease-out ${index * 0.1}s both`;
        });

        // Add CSS for animations
        const style = document.createElement('style');
        style.textContent = `
            @keyframes fadeInUp {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            @keyframes slideOutRight {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }
            
            .form-control.error {
                border-color: var(--error-color) !important;
                box-shadow: 0 0 0 3px rgba(229, 62, 62, 0.1) !important;
            }
        `;
        document.head.appendChild(style);
    }

    initializeTooltips() {
        // Simple tooltip system
        document.querySelectorAll('[data-tooltip]').forEach(element => {
            element.addEventListener('mouseenter', (e) => {
                const tooltip = document.createElement('div');
                tooltip.className = 'tooltip';
                tooltip.textContent = e.target.dataset.tooltip;
                tooltip.style.cssText = `
                    position: absolute;
                    background: rgba(0, 0, 0, 0.8);
                    color: white;
                    padding: 8px 12px;
                    border-radius: 4px;
                    font-size: 12px;
                    z-index: 10000;
                    pointer-events: none;
                    white-space: nowrap;
                `;
                document.body.appendChild(tooltip);

                const rect = e.target.getBoundingClientRect();
                tooltip.style.left = rect.left + rect.width / 2 - tooltip.offsetWidth / 2 + 'px';
                tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';

                e.target.tooltip = tooltip;
            });

            element.addEventListener('mouseleave', (e) => {
                if (e.target.tooltip) {
                    e.target.tooltip.remove();
                    e.target.tooltip = null;
                }
            });
        });
    }

    handleKeyboardNav(event) {
        // Handle keyboard navigation for accessibility
        const focusableElements = document.querySelectorAll(
            'button, input, select, .payment-method[tabindex="0"]'
        );
        
        if (event.key === 'Tab') {
            // Custom tab handling if needed
        } else if (event.key === 'Enter' || event.key === ' ') {
            const focused = document.activeElement;
            if (focused.classList.contains('payment-method')) {
                event.preventDefault();
                focused.click();
            }
        }
    }

    // Utility function for returning to app
    returnToApp() {
        // Try Flutter WebView communication first
        if (window.flutter_inappwebview) {
            window.flutter_inappwebview.callHandler('paymentComplete', {
                transaction_id: window.transactionId,
                status: window.paymentStatus
            });
            return;
        }

        // Try React Native WebView
        if (window.ReactNativeWebView) {
            window.ReactNativeWebView.postMessage(JSON.stringify({
                type: 'payment_complete',
                transaction_id: window.transactionId,
                status: window.paymentStatus
            }));
            return;
        }

        // Fallback to deep link
        const appLink = `bematore://payment/complete?transaction_id=${window.transactionId}&status=${window.paymentStatus}`;
        window.location.href = appLink;
        
        // If deep link doesn't work, try to close window
        setTimeout(() => {
            try {
                window.close();
            } catch (e) {
                console.log('Unable to close window automatically');
            }
        }, 1000);
    }

    openInBrowser() {
        // Get current URL
        const currentUrl = window.location.href;
        
        // Try to open in external browser
        if (window.open) {
            // Open in new window/tab
            const newWindow = window.open(currentUrl, '_blank');
            
            if (newWindow) {
                // Show success message
                this.showAlert('Opening in browser...', 'success');
                
                // Optional: Close the current window after a delay
                setTimeout(() => {
                    try {
                        window.close();
                    } catch (e) {
                        console.log('Unable to close current window');
                    }
                }, 2000);
            } else {
                // Fallback: show instructions
                this.showAlert('Please copy this URL and open it in your browser: ' + currentUrl, 'info');
            }
        } else {
            // Fallback for environments without window.open
            navigator.clipboard.writeText(currentUrl).then(() => {
                this.showAlert('URL copied to clipboard! Paste it in your browser.', 'success');
            }).catch(() => {
                this.showAlert('Please copy this URL and open it in your browser: ' + currentUrl, 'info');
            });
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.paymentSystem = new PaymentSystem();
});

// Global functions for template use
window.returnToApp = () => window.paymentSystem?.returnToApp();
window.checkPaymentStatus = () => window.paymentSystem?.checkPaymentStatus();
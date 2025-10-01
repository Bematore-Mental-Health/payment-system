/*
 * Bematore Payment System - Enterprise JavaScript
 * Professional Payment Processing Platform
 * Version: 1.0.0
 * Author: Brandon Ochieng
 * Company: Bematore Technologies
 */

document.addEventListener('DOMContentLoaded', function() {
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            // Only prevent default for internal anchor links, not for mailto: or external links
            if (href.startsWith('#') && href.length > 1) {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });

    // Navbar scroll effect
    window.addEventListener('scroll', function() {
        const navbar = document.querySelector('.navbar-enterprise');
        if (navbar) {
            if (window.scrollY > 50) {
                navbar.style.background = 'rgba(30, 41, 59, 0.98)';
                navbar.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.1)';
            } else {
                navbar.style.background = 'rgba(30, 41, 59, 0.95)';
                navbar.style.boxShadow = 'none';
            }
        }
    });

    // Ensure mailto links work properly
    document.querySelectorAll('a[href^="mailto:"]').forEach(link => {
        link.addEventListener('click', function(e) {
            // Allow the mailto link to work normally
            console.log('Opening email client for:', this.href);
            
            // Additional fallback for browsers that might have issues
            if (!window.location.href.startsWith('file://')) {
                // Only for web environments, not local files
                try {
                    window.location.href = this.href;
                } catch (error) {
                    console.error('Error opening email client:', error);
                    // Fallback: copy email to clipboard
                    const email = this.href.replace('mailto:', '').split('?')[0];
                    navigator.clipboard.writeText(email).then(() => {
                        alert('Email address copied to clipboard: ' + email);
                    }).catch(() => {
                        alert('Please contact: ' + email);
                    });
                }
            }
        });
    });

    // Add loading effect
    window.addEventListener('load', function() {
        const loadingIndicator = document.querySelector('.loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
    });

    // Feature card animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observe feature cards for animation
    document.querySelectorAll('.feature-card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });

    // Console message for developers
    console.log('%cBematore Payment System', 'color: #667eea; font-size: 20px; font-weight: bold;');
    console.log('%cProfessional Payment Processing Platform', 'color: #764ba2; font-size: 14px;');
    console.log('%cDeveloped by Brandon Ochieng | Bematore Technologies', 'color: #6b7280; font-size: 12px;');
    console.log('%cVersion: 1.0.0', 'color: #10b981; font-size: 12px;');
    console.log('%cGitHub: https://github.com/OchiengBrandon', 'color: #6b7280; font-size: 10px;');
});

// Enhanced email functionality
function openEmailClient(email, subject = '', body = '') {
    const mailtoUrl = `mailto:${email}${subject ? `?subject=${encodeURIComponent(subject)}` : ''}${body ? `&body=${encodeURIComponent(body)}` : ''}`;
    
    try {
        window.location.href = mailtoUrl;
        console.log('Email client opened successfully');
    } catch (error) {
        console.error('Error opening email client:', error);
        // Fallback to clipboard
        navigator.clipboard.writeText(email).then(() => {
            alert(`Email address copied to clipboard: ${email}`);
        }).catch(() => {
            alert(`Please contact us at: ${email}`);
        });
    }
}

// Performance monitoring
window.addEventListener('load', function() {
    if (window.performance && window.performance.timing) {
        const loadTime = window.performance.timing.loadEventEnd - window.performance.timing.navigationStart;
        console.log(`%cPage loaded in ${loadTime}ms`, 'color: #10b981; font-size: 10px;');
    }
});
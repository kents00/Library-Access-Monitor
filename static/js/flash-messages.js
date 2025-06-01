/**
 * Enhanced Flash Messages Utility
 * This file provides comprehensive setup for Notiflix notifications
 * with validation, error handling, and advanced features.
 */

// Global configuration object for customization
const FlashMessageConfig = {
    // Default notification settings
    notify: {
        position: 'right-top',
        timeout: 5000,
        distance: '10px',
        opacity: 1,
        borderRadius: '8px',
        width: '320px',
        closeButton: true,
        clickToClose: true,
        pauseOnHover: true,
        showOnlyTheLastOne: false,
        fontFamily: 'Quicksand',
        fontSize: '13px',
        cssAnimationStyle: 'zoom',
        cssAnimationDuration: 400,
        messageMaxLength: 110,
        backOverlay: false,
        plainText: true,
        useIcon: true,
        useFontAwesome: false,
        fontAwesomeIconStyle: 'basic',
        fontAwesomeIconSize: '16px',
    },

    // Loading spinner settings
    loading: {
        svgColor: '#0D6EFD',
        messageFontSize: '1rem',
        backgroundColor: 'rgba(0,0,0,0.8)',
        svgSize: '80px',
        messageColor: '#ddd',
        messageMaxLength: 34,
        clickToClose: false,
        customSvgUrl: null,
        customSvgCode: null,
    },

    // Confirm dialog settings
    confirm: {
        titleColor: '#0D6EFD',
        okButtonBackground: '#0D6EFD',
        cancelButtonBackground: '#6C757D',
        okButtonColor: '#fff',
        cancelButtonColor: '#fff',
        width: '300px',
        borderRadius: '8px',
        backOverlay: true,
        backOverlayColor: 'rgba(0,0,0,0.5)',
        rtl: false,
        fontFamily: 'Quicksand',
        cssAnimation: true,
        cssAnimationDuration: 300,
        cssAnimationStyle: 'fade',
        plainText: true,
        titleMaxLength: 34,
        messageMaxLength: 110,
    },

    // Report dialog settings
    report: {
        titleColor: '#0D6EFD',
        okButtonBackground: '#0D6EFD',
        okButtonColor: '#fff',
        width: '320px',
        borderRadius: '8px',
        backOverlay: true,
        backOverlayColor: 'rgba(0,0,0,0.5)',
        rtl: false,
        fontFamily: 'Quicksand',
        cssAnimation: true,
        cssAnimationDuration: 300,
        cssAnimationStyle: 'fade',
        plainText: true,
        titleMaxLength: 34,
        messageMaxLength: 400,
    },

    // Custom validation settings
    validation: {
        enableRealTimeValidation: true,
        showValidationErrors: true,
        validationErrorTimeout: 3000,
        highlightInvalidFields: true,
        invalidFieldClass: 'is-invalid',
        validFieldClass: 'is-valid',
    },

    // Error handling settings
    errorHandling: {
        logToConsole: true,
        showNetworkErrors: true,
        showValidationErrors: true,
        retryFailedRequests: false,
        maxRetries: 3,
        retryDelay: 1000,
        globalErrorHandler: true,
    }
};

// Initialize Notiflix with enhanced configuration
function initializeNotiflix() {
    try {
        // Initialize Notify
        Notiflix.Notify.init(FlashMessageConfig.notify);

        // Initialize Loading
        Notiflix.Loading.init(FlashMessageConfig.loading);

        // Initialize Confirm
        Notiflix.Confirm.init(FlashMessageConfig.confirm);

        // Initialize Report
        Notiflix.Report.init(FlashMessageConfig.report);

        console.log('✅ Notiflix initialized successfully with enhanced configuration');
    } catch (error) {
        console.error('❌ Error initializing Notiflix:', error);
        // Fallback to basic alert for critical errors
        if (typeof alert !== 'undefined') {
            alert('Error initializing notification system. Please refresh the page.');
        }
    }
}

/**
 * Enhanced flash message processing with validation and error handling
 */
function processFlashMessages() {
    try {
        let messagesProcessed = 0;

        // Method 1: Process flash messages from hidden container
        const flashContainer = document.getElementById('flash-messages-container');
        if (flashContainer) {
            const messages = flashContainer.querySelectorAll('.flash-message');
            messages.forEach(function (messageEl) {
                const category = messageEl.getAttribute('data-category') || 'info';
                const message = messageEl.textContent?.trim();

                if (message && validateMessage(message, category)) {
                    showNotification(category, message);
                    messagesProcessed++;
                }
            });
        }

        // Method 2: Process standard Bootstrap alerts
        const alertElements = document.querySelectorAll('.alert');
        alertElements.forEach(function (alert) {
            let category = 'info';
            if (alert.classList.contains('alert-warning')) category = 'warning';
            if (alert.classList.contains('alert-danger')) category = 'failure';
            if (alert.classList.contains('alert-success')) category = 'success';
            if (alert.classList.contains('alert-primary')) category = 'info';

            const message = alert.textContent?.trim();
            if (message && validateMessage(message, category)) {
                showNotification(category, message);
                alert.style.display = 'none';
                messagesProcessed++;
            }
        });

        // Method 3: Process backend errors
        const errorElement = document.getElementById('backend-error');
        if (errorElement) {
            const error = errorElement.value;
            if (error && error !== 'None' && error !== '' && validateMessage(error, 'error')) {
                showNotification('failure', error);
                messagesProcessed++;
            }
        }

        // Method 4: Process validation errors from forms
        processValidationErrors();

        // Method 5: Process URL parameters for messages
        processUrlMessages();

        if (FlashMessageConfig.errorHandling.logToConsole) {
            console.log(`📄 Processed ${messagesProcessed} flash messages`);
        }

    } catch (error) {
        console.error('❌ Error processing flash messages:', error);
        if (FlashMessageConfig.errorHandling.showNetworkErrors) {
            showNotification('failure', 'Error loading notifications. Please refresh the page.');
        }
    }
}

/**
 * Validate message content and category
 */
function validateMessage(message, category) {
    if (!message || typeof message !== 'string') {
        if (FlashMessageConfig.errorHandling.logToConsole) {
            console.warn('⚠️ Invalid message content:', message);
        }
        return false;
    }

    const trimmedMessage = message.trim();
    if (trimmedMessage.length === 0) {
        return false;
    }

    if (trimmedMessage.length > FlashMessageConfig.notify.messageMaxLength) {
        if (FlashMessageConfig.errorHandling.logToConsole) {
            console.warn(`⚠️ Message too long (${trimmedMessage.length} chars):`, trimmedMessage);
        }
        // Truncate message but still show it
        return true;
    }

    const validCategories = ['success', 'error', 'danger', 'failure', 'warning', 'info'];
    if (!validCategories.includes(category)) {
        if (FlashMessageConfig.errorHandling.logToConsole) {
            console.warn('⚠️ Invalid category:', category);
        }
        // Still process with default category
        return true;
    }

    return true;
}

/**
 * Process validation errors from forms
 */
function processValidationErrors() {
    if (!FlashMessageConfig.validation.showValidationErrors) return;

    // Check for HTML5 validation errors
    const invalidInputs = document.querySelectorAll(':invalid');
    invalidInputs.forEach(input => {
        if (input.validationMessage && FlashMessageConfig.validation.highlightInvalidFields) {
            input.classList.add(FlashMessageConfig.validation.invalidFieldClass);
            input.classList.remove(FlashMessageConfig.validation.validFieldClass);
        }
    });

    // Check for custom validation attributes
    const elementsWithErrors = document.querySelectorAll('[data-validation-error]');
    elementsWithErrors.forEach(element => {
        const errorMessage = element.getAttribute('data-validation-error');
        if (errorMessage && errorMessage.trim()) {
            showNotification('warning', errorMessage);
            element.removeAttribute('data-validation-error'); // Remove after showing
        }
    });
}

/**
 * Process messages from URL parameters
 */
function processUrlMessages() {
    try {
        const urlParams = new URLSearchParams(window.location.search);
        const message = urlParams.get('message');
        const type = urlParams.get('type') || 'info';

        if (message) {
            showNotification(type, decodeURIComponent(message));

            // Clean URL by removing message parameters
            const url = new URL(window.location);
            url.searchParams.delete('message');
            url.searchParams.delete('type');
            window.history.replaceState({}, document.title, url.toString());
        }
    } catch (error) {
        console.error('❌ Error processing URL messages:', error);
    }
}

/**
 * Enhanced notification display with additional parameters
 */
function showNotification(category, message, options = {}) {
    try {
        // Validate and sanitize inputs
        if (!validateMessage(message, category)) {
            return false;
        }

        // Merge with default options
        const defaultOptions = {
            timeout: FlashMessageConfig.notify.timeout,
            clickToClose: FlashMessageConfig.notify.clickToClose,
            pauseOnHover: FlashMessageConfig.notify.pauseOnHover,
        };

        const finalOptions = { ...defaultOptions, ...options };

        // Truncate message if too long
        let displayMessage = message;
        if (message.length > FlashMessageConfig.notify.messageMaxLength) {
            displayMessage = message.substring(0, FlashMessageConfig.notify.messageMaxLength - 3) + '...';
        }

        // Show notification based on category
        switch (category.toLowerCase()) {
            case 'success':
                Notiflix.Notify.success(displayMessage, finalOptions);
                break;
            case 'error':
            case 'danger':
            case 'failure':
                Notiflix.Notify.failure(displayMessage, finalOptions);
                break;
            case 'warning':
            case 'warn':
                Notiflix.Notify.warning(displayMessage, finalOptions);
                break;
            case 'info':
            case 'information':
            default:
                Notiflix.Notify.info(displayMessage, finalOptions);
                break;
        }

        if (FlashMessageConfig.errorHandling.logToConsole) {
            console.log(`📢 Notification shown [${category}]:`, displayMessage);
        }

        return true;
    } catch (error) {
        console.error('❌ Error showing notification:', error);
        // Fallback to browser alert
        if (typeof alert !== 'undefined') {
            alert(`${category.toUpperCase()}: ${message}`);
        }
        return false;
    }
}

/**
 * Enhanced loading indicator with options
 */
function showLoading(message = 'Loading...', options = {}) {
    try {
        const defaultOptions = {
            svgColor: FlashMessageConfig.loading.svgColor,
            backgroundColor: FlashMessageConfig.loading.backgroundColor,
            clickToClose: FlashMessageConfig.loading.clickToClose,
        };

        const finalOptions = { ...defaultOptions, ...options };

        // Apply custom options
        if (Object.keys(finalOptions).length > 3) {
            Notiflix.Loading.init(finalOptions);
        }

        Notiflix.Loading.pulse(message);

        if (FlashMessageConfig.errorHandling.logToConsole) {
            console.log('⏳ Loading shown:', message);
        }

        return true;
    } catch (error) {
        console.error('❌ Error showing loading:', error);
        return false;
    }
}

/**
 * Enhanced hide loading with error handling
 */
function hideLoading() {
    try {
        Notiflix.Loading.remove();

        if (FlashMessageConfig.errorHandling.logToConsole) {
            console.log('✅ Loading hidden');
        }

        return true;
    } catch (error) {
        console.error('❌ Error hiding loading:', error);
        return false;
    }
}

/**
 * Enhanced confirm dialog with validation
 */
function showConfirm(title, message, onConfirm, onCancel, options = {}) {
    try {
        if (!title || !message) {
            console.error('❌ Title and message are required for confirm dialog');
            return false;
        }

        const defaultOptions = {
            titleColor: FlashMessageConfig.confirm.titleColor,
            okButtonBackground: FlashMessageConfig.confirm.okButtonBackground,
            cancelButtonBackground: FlashMessageConfig.confirm.cancelButtonBackground,
            width: FlashMessageConfig.confirm.width,
            borderRadius: FlashMessageConfig.confirm.borderRadius,
        };

        const finalOptions = { ...defaultOptions, ...options };

        Notiflix.Confirm.show(
            title,
            message,
            'Yes',
            'No',
            function okCallback() {
                if (typeof onConfirm === 'function') {
                    onConfirm();
                } else {
                    console.warn('⚠️ onConfirm callback is not a function');
                }
            },
            function cancelCallback() {
                if (typeof onCancel === 'function') {
                    onCancel();
                } else {
                    console.log('📝 Confirm dialog cancelled');
                }
            },
            finalOptions
        );

        return true;
    } catch (error) {
        console.error('❌ Error showing confirm dialog:', error);
        return false;
    }
}

/**
 * Enhanced report dialog for detailed messages
 */
function showReport(type, title, message, buttonText = 'Okay', options = {}) {
    try {
        if (!title || !message) {
            console.error('❌ Title and message are required for report dialog');
            return false;
        }

        const defaultOptions = {
            titleColor: FlashMessageConfig.report.titleColor,
            okButtonBackground: FlashMessageConfig.report.okButtonBackground,
            width: FlashMessageConfig.report.width,
            borderRadius: FlashMessageConfig.report.borderRadius,
        };

        const finalOptions = { ...defaultOptions, ...options };

        switch (type.toLowerCase()) {
            case 'success':
                Notiflix.Report.success(title, message, buttonText, null, finalOptions);
                break;
            case 'failure':
            case 'error':
                Notiflix.Report.failure(title, message, buttonText, null, finalOptions);
                break;
            case 'warning':
                Notiflix.Report.warning(title, message, buttonText, null, finalOptions);
                break;
            case 'info':
            default:
                Notiflix.Report.info(title, message, buttonText, null, finalOptions);
                break;
        }

        return true;
    } catch (error) {
        console.error('❌ Error showing report dialog:', error);
        return false;
    }
}

/**
 * Form validation enhancement
 */
function enhanceFormValidation() {
    if (!FlashMessageConfig.validation.enableRealTimeValidation) return;

    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        if (form.hasAttribute('data-validation-enhanced')) return;

        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            // Real-time validation
            input.addEventListener('blur', function () {
                validateField(this);
            });

            input.addEventListener('input', function () {
                if (this.classList.contains(FlashMessageConfig.validation.invalidFieldClass)) {
                    validateField(this);
                }
            });
        });

        // Form submission validation
        form.addEventListener('submit', function (e) {
            if (!validateForm(this)) {
                e.preventDefault();
                showNotification('warning', 'Please fix validation errors before submitting.');
                return false;
            }
        });

        form.setAttribute('data-validation-enhanced', 'true');
    });
}

/**
 * Validate individual form field
 */
function validateField(field) {
    const isValid = field.checkValidity();

    if (isValid) {
        field.classList.remove(FlashMessageConfig.validation.invalidFieldClass);
        field.classList.add(FlashMessageConfig.validation.validFieldClass);
    } else {
        field.classList.add(FlashMessageConfig.validation.invalidFieldClass);
        field.classList.remove(FlashMessageConfig.validation.validFieldClass);

        if (FlashMessageConfig.validation.showValidationErrors && field.validationMessage) {
            setTimeout(() => {
                showNotification('warning', field.validationMessage, {
                    timeout: FlashMessageConfig.validation.validationErrorTimeout
                });
            }, 100);
        }
    }

    return isValid;
}

/**
 * Validate entire form
 */
function validateForm(form) {
    const inputs = form.querySelectorAll('input, select, textarea');
    let isFormValid = true;
    let firstInvalidField = null;

    inputs.forEach(input => {
        if (!validateField(input)) {
            isFormValid = false;
            if (!firstInvalidField) {
                firstInvalidField = input;
            }
        }
    });

    // Focus on first invalid field
    if (firstInvalidField) {
        firstInvalidField.focus();
        firstInvalidField.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    return isFormValid;
}

/**
 * Global error handler for unhandled errors
 */
function setupGlobalErrorHandler() {
    if (!FlashMessageConfig.errorHandling.globalErrorHandler) return;

    window.addEventListener('error', function (event) {
        console.error('💥 Global error caught:', event.error);

        if (FlashMessageConfig.errorHandling.showNetworkErrors) {
            showNotification('failure', 'An unexpected error occurred. Please try again.');
        }
    });

    window.addEventListener('unhandledrejection', function (event) {
        console.error('💥 Unhandled promise rejection:', event.reason);

        if (FlashMessageConfig.errorHandling.showNetworkErrors) {
            showNotification('failure', 'A network error occurred. Please check your connection.');
        }
    });
}

/**
 * Network error handler for fetch requests
 */
function handleNetworkError(error, context = '') {
    console.error(`🌐 Network error${context ? ' in ' + context : ''}:`, error);

    if (FlashMessageConfig.errorHandling.showNetworkErrors) {
        let message = 'Network error occurred.';

        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            message = 'Unable to connect to server. Please check your internet connection.';
        } else if (error.message) {
            message = error.message;
        }

        showNotification('failure', message);
    }
}

/**
 * Initialize all flash message functionality
 */
function initializeFlashMessages() {
    try {
        // Initialize Notiflix
        initializeNotiflix();

        // Process existing flash messages
        processFlashMessages();

        // Enhance form validation
        enhanceFormValidation();

        // Setup global error handling
        setupGlobalErrorHandler();

        // Setup form loading indicators
        setupFormLoadingIndicators();

        console.log('🚀 Flash message system fully initialized');

    } catch (error) {
        console.error('💥 Critical error initializing flash messages:', error);
    }
}

/**
 * Setup automatic loading indicators for forms
 */
function setupFormLoadingIndicators() {
    document.querySelectorAll('form').forEach(form => {
        if (form.hasAttribute('data-loading-enhanced')) return;

        form.addEventListener('submit', function (e) {
            // Don't show loading for forms with data-no-loading attribute or export forms
            if (!this.hasAttribute('data-no-loading') && !e.submitter?.name?.includes('export')) {
                setTimeout(() => {
                    showLoading('Processing...');
                }, 100);
            }
        });

        form.setAttribute('data-loading-enhanced', 'true');
    });
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
    // Small delay to ensure all elements are ready
    setTimeout(initializeFlashMessages, 100);
});

// Export functions for global use
window.FlashMessages = {
    showNotification,
    showLoading,
    hideLoading,
    showConfirm,
    showReport,
    validateForm,
    validateField,
    handleNetworkError,
    handleExportSuccess,
    handleExportError,
    config: FlashMessageConfig
};

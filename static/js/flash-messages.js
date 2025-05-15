/**
 * Flash Messages Utility
 * This file provides standardized setup for Notiflix notifications
 * to handle flash messages in Flask applications.
 */

// Configure Notiflix with default settings
Notiflix.Notify.init({
    position: 'right-top',
    timeout: 5000,
    distance: '10px',
    opacity: 1,
    borderRadius: '5px',
    width: '280px',
    closeButton: true,
    clickToClose: true,
    // Add other default settings as needed
});

// Loading spinner configuration
Notiflix.Loading.init({
    svgColor: '#0D6EFD',
    messageFontSize: '1rem',
    backgroundColor: 'rgba(0,0,0,0.8)',
});

// Confirm dialogs configuration
Notiflix.Confirm.init({
    titleColor: '#0D6EFD',
    okButtonBackground: '#0D6EFD',
    cancelButtonBackground: '#6C757D',
});

/**
 * Process flash messages from the Flask app
 * This function should be called on DOMContentLoaded
 */
function processFlashMessages() {
    // Method 1: Process flash messages from hidden container
    const flashContainer = document.getElementById('flash-messages-container');
    if (flashContainer) {
        const messages = flashContainer.querySelectorAll('.flash-message');
        messages.forEach(function (messageEl) {
            const category = messageEl.getAttribute('data-category') || 'info';
            const message = messageEl.textContent;

            showNotification(category, message);
        });
    }

    // Method 2: Look for standard Bootstrap alerts and convert to Notiflix
    const alertElements = document.querySelectorAll('.alert');
    alertElements.forEach(function (alert) {
        let category = 'info';
        if (alert.classList.contains('alert-warning')) category = 'warning';
        if (alert.classList.contains('alert-danger')) category = 'failure';
        if (alert.classList.contains('alert-success')) category = 'success';

        const message = alert.textContent.trim();
        if (message) {
            showNotification(category, message);
            alert.style.display = 'none'; // Hide the original alert
        }
    });

    // Process error passed from backend
    const errorElement = document.getElementById('backend-error');
    if (errorElement) {
        const error = errorElement.value;
        if (error && error !== 'None' && error !== '') {
            showNotification('failure', error);
        }
    }
}

/**
 * Show a notification using Notiflix
 * @param {string} category - The type of notification: success, failure, warning, info
 * @param {string} message - The message to display
 */
function showNotification(category, message) {
    switch (category) {
        case 'success':
            Notiflix.Notify.success(message);
            break;
        case 'error':
        case 'danger':
        case 'failure':
            Notiflix.Notify.failure(message);
            break;
        case 'warning':
            Notiflix.Notify.warning(message);
            break;
        default:
            Notiflix.Notify.info(message);
    }
}

/**
 * Show a loading indicator
 * @param {string} message - Optional message to display
 */
function showLoading(message = 'Loading...') {
    Notiflix.Loading.pulse(message);
}

/**
 * Remove the loading indicator
 */
function hideLoading() {
    Notiflix.Loading.remove();
}

// Initialize flash messages processing on page load
document.addEventListener('DOMContentLoaded', function () {
    processFlashMessages();

    // Add loading indicator to all forms by default
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function (e) {
            // Don't show loading for forms with data-no-loading attribute
            if (!this.hasAttribute('data-no-loading')) {
                showLoading('Processing...');
            }
        });
    });
});

/**
 * Common JS functionality for the Library Attendance System
 */

document.addEventListener('DOMContentLoaded', function () {
    // Initialize all interactive elements
    initializeSearchFunctionality();
    initializeFormValidation();
    initializeDynamicElements();
});

/**
 * Initialize search functionality across the application
 */
function initializeSearchFunctionality() {
    // Get search input - check if element exists first
    const searchInput = document.getElementById('searchInput');

    if (searchInput) {
        searchInput.addEventListener('input', function () {
            const searchTerm = this.value.toLowerCase();
            const tableId = this.getAttribute('data-table') || 'studentTable';
            const tableBody = document.querySelector(`#${tableId} tbody`);

            if (!tableBody) return;

            const rows = tableBody.querySelectorAll('tr:not(#noUsersFound)');
            let visibleCount = 0;

            rows.forEach(function (row) {
                if (row.textContent.toLowerCase().includes(searchTerm)) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });

            const noResultsRow = document.getElementById('noUsersFound');
            if (noResultsRow) {
                noResultsRow.style.display = visibleCount > 0 ? 'none' : '';
            }
        });
    }
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    // Select all forms that need validation
    const forms = document.querySelectorAll('.needs-validation');

    // Loop over them and prevent submission
    Array.from(forms).forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }

            form.classList.add('was-validated');
        }, false);
    });
}

/**
 * Initialize dynamic elements like tooltips, popovers, etc.
 */
function initializeDynamicElements() {
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    }

    // Initialize image preview functionality
    const imageInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
    imageInputs.forEach(input => {
        input.addEventListener('change', function (event) {
            const previewId = this.getAttribute('data-preview') || 'profileImagePreview';
            const previewElement = document.getElementById(previewId);

            if (previewElement && event.target.files && event.target.files[0]) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    previewElement.src = e.target.result;
                };
                reader.readAsDataURL(event.target.files[0]);
            }
        });
    });
}

/**
 * Show a notification to the user
 * @param {string} message - Message to display
 * @param {string} type - Type of notification (success, error, warning, info)
 */
function showNotification(message, type = 'info') {
    // Check if Notiflix is available
    if (typeof Notiflix !== 'undefined' && Notiflix.Notify) {
        Notiflix.Notify[type](message);
    } else {
        // Fallback to alert
        alert(message);
    }
}

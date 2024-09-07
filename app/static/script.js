// Automatically submit the form when the Enter key is pressed
document.getElementById('id').addEventListener('keypress', function (event) {
    if (event.key === 'Enter') {
        event.preventDefault();  // Prevent the default form submission
        document.getElementById('loginForm').submit();  // Submit the form
    }
});

// Optional: submit form when the submit button is clicked (already happens by default)
document.getElementById('submitBtn').addEventListener('click', function (event) {
    document.getElementById('loginForm').submit();
});
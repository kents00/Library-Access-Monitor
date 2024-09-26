function getLocalTime() {
    // Get the current date and time
    var localDate = new Date();
    // Convert to ISO string to send to server (if needed)
    return localDate.toISOString();
}

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

$(document).ready(function() {
    // Handle CSV export button click
    $('#export-csv').click(function() {
        const filter = $('#filter').val();
        const localTime = new Date().toISOString();  // Get current local time in ISO format

        // Make an AJAX request to export CSV
        $.post("{{ url_for('export_csv') }}", {
            filter: filter,
            local_time: localTime
        })
        .done(function(response) {
            // Create a link to download the CSV
            const blob = new Blob([response], { type: 'text/csv' });
            const link = document.createElement('a');
            link.href = window.URL.createObjectURL(blob);
            link.download = 'attendance_data.csv';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        })
        .fail(function() {
            alert('Error exporting CSV. Please try again.');
        });
    });

    // Handle form submission
    $('#filter-form').submit(function(event) {
        event.preventDefault();  // Prevent default form submission

        const filter = $('#filter').val();
        const localTime = new Date().toISOString();  // Get current local time in ISO format

        $.post($(this).attr('action'), {
            filter: filter,
            local_time: localTime
        })
        .done(function(data) {
            // Update the analytics section with new data
            $('#analytics-section').html(data);
        })
        .fail(function() {
            alert('Error loading analytics. Please try again.');
        });
    });
});
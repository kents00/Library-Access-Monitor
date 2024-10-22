document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('userSearch');
    const userTable = document.getElementById('userTable');
    const tableRows = userTable.getElementsByTagName('tr');

    searchInput.addEventListener('keyup', function () {
        const filter = searchInput.value.toLowerCase();

        for (let i = 1; i < tableRows.length; i++) {
            const cells = tableRows[i].getElementsByTagName('td');
            let rowVisible = false;


            for (let j = 1; j < cells.length; j++) {
                if (cells[j].textContent.toLowerCase().includes(filter)) {
                    rowVisible = true;
                    break;
                }
            }

            tableRows[i].style.display = rowVisible ? '' : 'none';
        }
    });
});

function exportCSV() {
    window.location.href = '/export/csv';
}

function exportPDF() {
    window.location.href = '/export/pdf';
}





let studentToDelete = null;

// Function to store the student ID to be deleted
function setStudentToDelete(studentId) {
    studentToDelete = studentId;
    document.getElementById('deleteStudentId').value = studentToDelete;
}

// Function to handle edit action
function editStudent(studentId) {
    // Redirect to the Flask route for editing the student
    window.location.href = `/admin/edit_student/${studentId}`;
}

// Function to filter students based on search input
function searchStudents() {
    const input = document.getElementById('searchStudent').value.toLowerCase();
    const studentItems = document.querySelectorAll('.student-item');

    studentItems.forEach(function (item) {
        const name = item.querySelector('.student-name').textContent.toLowerCase();
        const id = item.querySelector('.student-id').textContent.toLowerCase();

        if (name.includes(input) || id.includes(input)) {
            item.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
}
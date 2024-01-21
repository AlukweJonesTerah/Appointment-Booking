document.getElementById('scheduleButton').addEventListener('click', function() {
    scheduleAppointment();
});


function scheduleAppointment(){
    // Show laoding spinner
    document.getElementById('loadingSpinner').style.display = 'block';

    // Fetch selected date and time, then send a POST request to the backend
    const date = document.getElementById('date').value;
    const time = document.getElementById('time').value;
    const title = document.getElementById('title').value;
    const location = document.getElementById('location').value;
    const description = document.getElementById('description').value;

    fetch('/schedule', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({date, time, title, location, description}),
    })
    .then(response => response.json())
    .then(data => {
        // Hide loading spinner on success
        document.getElementById('loadingSpinner').style.display = 'none';
        // Display success message
        alert(data.message);
    })
    .catch(error => {
        // Hide loading spinner on error
        document.getElementById('loadingSpinner').style.display = 'none';
        console.error('Error:', error)
    });
}
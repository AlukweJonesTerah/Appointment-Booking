
document.addEventListener('DOMContentLoaded', function() {
    const registrationForm = document.getElementById('registration-form');
    const registrationMessages = document.getElementById('registration-messages');

    registrationForm.addEventListener('submit', async function(event) {
        event.preventDefault();

        const formData = new FormData(registrationForm);
        // Include the CSRF token manually
        formData.append("csrf_token", "{{ form.csrf_token._value() }}");


        fetch('/register', {
            method: 'POST',
            body: JSON.stringify(Object.fromEntries(formData)),
        })
        .then(response => {
            if (response.ok) {
                // Registration successful
                 alert(data.message);
                return response.json();
            } else {
                // Registration failed
                return response.json().then(errors => Promise.reject(errors));
            }
        })
        .then(data => {
            // Handle success
            alert(data.message);
            displayMessage('success', data.message);
        })
        .catch(errors => {
            // Handle errors
            displayMessage('error', 'Registration failed. Please check the form and try again.');
            // Optionally, display specific error messages from 'errors' object
            // for (const fieldName in errors.errors) {
            //     console.error(errors.errors[fieldName].join(', '));
            // }
            console.error('Error:', error)
        });
    });
    function displayMessage(type, message) {
        registrationMessages.innerHTML = `<div class="${type}-message">${message}</div>`;
    }
});

//{{form.csrf_token}}
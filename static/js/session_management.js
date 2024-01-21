// Periodically send a heartbeat or ping to the server to indicate that the user is still active.
jQuery(document).ready(function($) {
    function sendHeartbeat() {
        fetch('/heartbeat', {
            method: 'POST',
            credentials: 'same-origin',  // Include credentials in the request
        })
        .then(response => response.json())
        .then(data => {
            // Handle success based on the server's response
            if (data.status === 'success') {
                console.log('Heartbeat successful');
            } else {
                console.error('Heartbeat failed:', data.message);
            }
        })
        .catch(error => {
            console.error('Heartbeat failed:', error);
        });
    }

    // Trigger heartbeat every 5 seconds
    setInterval(sendHeartbeat, 5000); // 5 * 60 * 1000 = 5 mins

    // Handle window unload event when the user is navigating away from the page or closing the browser tab/window
    window.addEventListener('beforeunload', function() {
        // Notify the server about the user leaving using navigator.sendBeacon
        navigator.sendBeacon('/leave-site');

        // Make an additional synchronous AJAX request to get a response (if needed)
        fetch('/leave-site', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),  // Include your CSRF token retrieval logic
            },
            credentials: 'same-origin',  // Include credentials in the request
        })
        .then(response => response.json())
        .then(data => {
            // Handle success based on the server's response
            if (data.status === 'success') {
                console.log('Leave site notification successful');
            } else {
                console.error('Leave site notification failed:', data.message);
            }
        })
        .catch(error => {
            console.error('Leaving site notification failed:', error);
        });
    });

    // Function to retrieve the CSRF token (replace with your actual logic)
    function getCSRFToken() {
        // Implement your CSRF token retrieval logic
        // For example, if you're using a meta tag to store the token:
        return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    }
});

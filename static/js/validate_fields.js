// Field validator
$(document).ready(function() {
    $('#first_name').on('blur', function(){
        var first_nameValue = $(this).val();
        validateField('first_name', first_nameValue, '#first_name-validation-message');
        function validateField(field, value, messageDivId) {
            $.ajax({
                url: '/validation/first_name',  // Update the URL path
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ [field]: value }),
                success: function(response) {
                    // Handle success response (e.g., show success message)
                    alert(response.message);
                    $(messageDivId).text(response.message).removeClass('error').addClass('success');
                    console.log(response.message);
                },
                error: function(error) {
                    // Handle error response (e.g., show error message)
                    alert(error.responseJSON.message);
                    $(messageDivId).text(error.responseJSON.message).removeClass('success').addClass('error');
                    console.error(error.responseJSON.message);
                }
            });
        }
    });
});



$(document).ready(function() {
    $('#last_name').on('blur', function(){
        var last_nameValue = $(this).val();
        validateField('last_name', last_nameValue, '#last_name-validation-message');
        function validateField(field, value, messageDivId) {
            $.ajax({
                url: '/validation/last_name',  // Update the URL path
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ [field]: value }),
                success: function(response) {
                    // Handle success response (e.g., show success message)
                    alert(response.message);
                    $(messageDivId).text(response.message).removeClass('error').addClass('success');
                    console.log(response.message);
                },
                error: function(error) {
                    // Handle error response (e.g., show error message)
                    alert(error.responseJSON.message);
                    $(messageDivId).text(error.responseJSON.message).removeClass('success').addClass('error');
                    console.error(error.responseJSON.message);
                }
            });
        }
    });
});

$(document).ready(function() {
    $('#phone_number').on('blur', function(){
        var phone_numberValue = $(this).val();
        validateField('phone_number', phone_numberValue, '#phone_number-validation-message')
        function validateField(field, value, messageDivId) {
            $.ajax({
                url: '/validation/phone_number',  // Update the URL path
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ [field]: value }),
                success: function(response) {
                    // Handle success response (e.g., show success message)
                    alert(response.message);
                    $(messageDivId).text(response.message).removeClass('error').addClass('success');
                    console.log(response.message);
                },
                error: function(error) {
                    // Handle error response (e.g., show error message)
                    alert(error.responseJSON.message);
                    $(messageDivId).text(error.responseJSON.message).removeClass('success').addClass('error');
                    console.error(error.responseJSON.message);
                }
            });
        }
    });
});

$(document).ready(function() {
    $('#email').on('blur', function() {
        var emailValue = $(this).val();
        validateField('email', emailValue, '#email-validation-message');
        function validateField(field, value, messageDivId) {
            $.ajax({
                url: '/validation/email',  // Update the URL path
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ [field]: value }),
                success: function(response) {
                    // Handle success response (e.g., show success message)
                    alert(response.message);
                    $(messageDivId).text(response.message).removeClass('error').addClass('success');
                    console.log(response.message);
                },
                error: function(error) {
                    // Handle error response (e.g., show error message)
                    alert(error.responseJSON.message);
                    $(messageDivId).text(error.responseJSON.message).removeClass('success').addClass('error');
                    console.error(error.responseJSON.message);
                }
            });
        }
    });
});

$(document).ready(function() {
     $('#username').on('blur', function() {
        var usernameValue = $(this).val();
        validateField('username', usernameValue, '#username-validation-message');
        function validateField(field, value, messageDivId) {
            $.ajax({
                url: '/validation/username',  // Update the URL path
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ [field]: value }),
                success: function(response) {
                    // Handle success response (e.g., show success message)
                    alert(response.message);
                    $(messageDivId).text(response.message).removeClass('error').addClass('success');
                    console.log(response.message);
                },
                error: function(error) {
                    // Handle error response (e.g., show error message)
                    alert(error.responseJSON.message);
                    $(messageDivId).text(error.responseJSON.message).removeClass('success').addClass('error');
                    console.error(error.responseJSON.message);
                }
            });
        }
    });
});

$(document).ready(function() {
     $('#password').on('blur', function() {
        var passwordValue = $(this).val();
        validateField('password', passwordValue, '#password-validation-message');
        function validateField(field, value, messageDivId) {
            $.ajax({
                url: '/validation/password',  // Update the URL path
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ [field]: value }),
                success: function(response) {
                    // Handle success response (e.g., show success message)
                    alert(response.message);
                    $(messageDivId).text(response.message).removeClass('error').addClass('success');
                    console.log(response.message);
                },
                error: function(error) {
                    // Handle error response (e.g., show error message)
                    alert(error.responseJSON.message);
                    $(messageDivId).text(error.responseJSON.message).removeClass('success').addClass('error');
                    console.error(error.responseJSON.message);
                }
            });
        }
    });
});
    // Add more fields as needed...

//$(document).ready(function() {
//    function validateField(field, value, messageDivId) {
//        $.ajax({
//            url: '/validate/' + field,
//            method: 'POST',
//            contentType: 'application/json',
//            data: JSON.stringify({ [field]: value }),
//            success: function(response) {
//                // Handle success response (e.g., show success message)
//                alert(response.message);
//                $(messageDivId).text(response.message).removeClass('error').addClass('success');
//                console.log(response.message);
//            },
//            error: function(error) {
//                // Handle error response (e.g., show error message)
//                alert(error.responseJSON.message);
//                $(messageDivId).text(error.responseJSON.message).removeClass('success').addClass('error');
//                console.error(error.responseJSON.message);
//            }
//        });
//    }
//});

 $(document).ready(function() {
        $('#myForm input').on('input', function() {
            var fieldName = $(this).attr('name');
            var formData = {};
            formData[fieldName] = $(this).val();

            $.ajax({
                type: 'POST',
                url: '/process_field',
                data: formData,
                success: function(response) {
                    $('#result').html(response);
                }
            });
        });
    });
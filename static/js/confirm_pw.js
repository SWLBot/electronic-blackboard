$(document).ready(function(){
    $('#confirm-password').on('keyup', function () {
        if ($(this).val() == $('#password').val()) {
            $('#message').html('matching').css('color', 'green');
            $('#submit').removeAttr('disabled');
        } else {
            $('#message').html('not matching').css('color', 'red');
            $('#submit').attr('disabled','disabled');
        }
    });
    $('#password').on('keyup', function () {
        if ($(this).val() == $('#confirm-password').val()) {
            $('#message').html('matching').css('color', 'green');
            $('#submit').removeAttr('disabled');
        } else {
            $('#message').html('not matching').css('color', 'red');
            $('#submit').attr('disabled','disabled');
        }
    });
});
var last_schedule_id = "no_id";

$(window).on('load',function(){
    window.setInterval(load_schedule, 1000);
});

function load_schedule(){
    $.ajaxSetup({
        beforeSend: function (jqXHR, settings){
            type = settings.type
            if (type != 'GET' && type != 'HEAD' && type != 'OPTIONS'){
                var pattern = /(.+; *)?_xsrf *= *([^;" ]+)/;
                var xsrf = pattern.exec( document .cookie);
                // check xsrf //
                if (xsrf){
                    jqXHR.setRequestHeader('X-Xsrftoken', xsrf[2]);
                }
            }
        }
    });

    $.ajax({
        url: '/db_schedule',
        type: 'GET',
        contentType : 'application/text',
        // ajax success //
        success: function(jsonRes){
            $('div.container').html(jsonRes)
            setImageInfo()
            setup_textwindow()
        },
        // ajax error //
        error: function (xhr, textStatus, error) {
            console.log("load_schedule error");
            console.log(xhr.statusText);
            console.log(textStatus);
            console.log(error);
        }
    });
}

function setImageInfo(){
    $('img#pic').height(screen.height * 0.98);
    $('img#pic').css('maxWidth',($(window).width() * 0.85 | 0 ));
}

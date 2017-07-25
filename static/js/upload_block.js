    function default_date(year,month,day) {
        var today = new Date();
        today.setDate(today.getDate()+day);
        today.setMonth(today.getMonth()+month);
        today.setFullYear(today.getFullYear()+year);
        var date_str = today.toISOString().substring(0, 10);
        return date_str;
    }
    $(window).on('load',function(){
        window.document.getElementById("img_end_date").value=default_date(0,0,7);
        window.document.getElementById("award_end_date").value=default_date(0,1,0);
        window.document.getElementById("activity_end_date").value=default_date(0,0,14);
        window.document.getElementById("img_start_date").value=default_date(0,0,0);
        window.document.getElementById("award_start_date").value=default_date(0,0,0);
        window.document.getElementById("activity_start_date").value=default_date(0,0,0);
        $('span#year').text($('select#year').val());
        $('span#month').text($('select#month').val());
        $('#upload_image').click(function(){
            if($('.text_block').css('display') !== "none"){
                $('.text_block').toggle();
            }
            if($('.activity_block').css('display') !== "none"){
                $('.activity_block').toggle();
            }
            $('.image_block').toggle();
        });
        $('#upload_text').click(function(){
            if($('.image_block').css('display') !== "none"){
                $('.image_block').toggle();
            }
            if($('.activity_block').css('display') !== "none"){
                $('.activity_block').toggle();
            }
            $('.text_block').toggle();
        });
        $('#upload_activity').click(function(){
            if($('.image_block').css('display') !== "none"){
                $('.imgae_block').toggle();
            }
            if($('.text_block').css('display') !== "none"){
                $('.text_block').toggle();
            }
            $('.activity_block').toggle();
        });
    });

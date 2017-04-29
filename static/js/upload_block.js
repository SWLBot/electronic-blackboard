    $(window).on('load',function(){
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
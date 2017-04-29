var last_schedule_id = "no_id"
function load_schedule()
{
	$.ajaxSetup({
	    beforeSend: function (jqXHR, settings)  {
		type = settings.type
		if (type != 'GET' && type != 'HEAD' && type != 'OPTIONS' ) {
		     var pattern = /(.+; *)?_xsrf *= *([^;" ]+)/ ;
		     var xsrf = pattern.exec( document .cookie);
		     if (xsrf) {
			jqXHR.setRequestHeader( 'X-Xsrftoken' , xsrf[ 2 ]);
		    }
		}
	}});
	
	$.ajax({
		url: '/db_schedule',
		type: 'GET',
		contentType : 'application/text',
		success: function (jsonRes) 
		{
            if(jsonRes.result == "fail"){console.log("fail");}
            else if(last_schedule_id == jsonRes.schedule_id){console.log("same");}
            else if(jsonRes.file_type == "text"){
                console.log("text");
                last_schedule_id = jsonRes.schedule_id;
                $('img').css('display','none');
                $('footer').css('display','inline');
                $('div.title2').css('display','inline');
                if ( 'con' in jsonRes.file_text){
                    $('span#con').html(jsonRes.file_text.con);
                }else{
                    if (jsonRes.type_name === "獲獎公告"){
                        $('span#con').html("賀！");
                    }else{
                        $('span#con').html("活動公告");
                    }
                }
                $('#title1').html(jsonRes.file_text.title1);
                $('#title2').html(jsonRes.file_text.title2);
                $('#description').html(jsonRes.file_text.description);
                if(jsonRes.type_name === "獲獎公告"){
                    console.log('reward');
                    if ('background_color' in jsonRes.file_text){
                        $('div.header').css('background-color',jsonRes.file_text.background_color);
                        $('div.bar').css('background-color',jsonRes.file_text.background_color);
                    }else{
                        $('div.header').css('background-color','#CE0000');
                        $('div.bar').css('background-color','#CE0000');
                    }
                    $('div#footer').css('display','inline');
                    $('div.congratulation').html(jsonRes.file_text.year+"年"+jsonRes.file_text.month+"月 資訊學院全體師生慶賀");
                }else{
                    if ('background_color' in jsonRes.file_text){
                        $('div.header').css('background-color',jsonRes.file_text.background_color);
                    }else{
                        $('div.header').css('background-color','#FF8000');
                    }
                    $('div#footer').css('display','none');
                }
            }else{
                console.log("image");
                last_schedule_id = jsonRes.schedule_id;
                $('div.title2').css('display','none');
                $('img').css('display','inline');
                $('img').attr('src',"/static/"+jsonRes.file);
                var width = $('img').width();
                var height = $('img').height();
                $('img').height(screen.height * 0.98);
                $('img').css('maxWidth',($(window).width() * 0.85 | 0 ) + "px");
            }
		},
		error: function (xhr, textStatus, error) 
		{
			console.log(xhr.statusText);
			console.log(textStatus);
			console.log(error);
			console.log("load_schedule error");
		}
	});

}

function timer()
{
    load_schedule()
}


$(window).on('load',function(){
    window.setInterval(timer,1000);
});

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
            if(jsonRes.result == "fail"){
                console.log("fail");
                console.log(jsonRes);
            }
            else if(last_schedule_id == jsonRes.schedule_id){console.log("same");}
            else if(jsonRes.file_type == "text"){
                $('footer').css('display','none');
                $('div.title2').css('display','none');
                $('img#pic').css('display','none');
                $('div.like_count').css('display','none');
                $('div#user_pref').css('display','inline');
                $('img#qrcode1').css('display','inline');
                $('img#qrcode2').css('display','inline');
                $('img#event_qrcode').css('display','none');
                
                console.log("text");
                if ('preference' in jsonRes.file_text){
                    console.log(jsonRes);
                    if(jsonRes.file_text.preference === 1){
                        var weekday=new Array(7);
                        weekday[0]="Mon.";
                        weekday[1]="Tue.";
                        weekday[2]="Wed.";
                        weekday[3]="Thu.";
                        weekday[4]="Fri.";
                        weekday[5]="Sat.";
                        weekday[6]="Sun.";
                        var datetime = new Date(Date.parse(jsonRes.file_text.date));
                        console.log(datetime);
                        var weekday = weekday[datetime.getDay()];
                        var year = datetime.getFullYear();
                        var month = datetime.getMonth() + 1;
                        var date = datetime.getDate();
                        console.log("Month",month);
                        console.log("Year",year);
                        console.log("Date",date);
                        $('div#week b').text(weekday);
                        $('div#year b').text(year);
                        $('div#date b').text(String(month)+'.'+String(date));
                        $('div#name b').text(jsonRes.file_text.nickname);
                        $('div#star b').text(jsonRes.file_text.constellation.name);
                        $('div#overall b').text(jsonRes.file_text.constellation.value[0]);
                        $('div#love b').text(jsonRes.file_text.constellation.value[1]);
                        $('div#career b').text(jsonRes.file_text.constellation.value[2]);
                        $('div#wealth b').text(jsonRes.file_text.constellation.value[3]);
                        if( jsonRes.file_text.news.length > 0){
                            console.log("print!!!");
                            $('img#qrcode1').attr('src',String(jsonRes.file_text.news[0].QR));
                            $('div#newsTitle1').text(jsonRes.file_text.news[0].title);
                            $('img#qrcode2').attr('src',String(jsonRes.file_text.news[1].QR));
                            $('div#newsTitle2').text(jsonRes.file_text.news[1].title);
                        }
                    }
                }else{
                    last_schedule_id = jsonRes.schedule_id;
                    $('div#user_pref').css('display','none');
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
                }
                if ('event_id' in jsonRes.file_text){
                    $('img#event_qrcode').attr('src',String(jsonRes.file_text.event_id));
                    $('img#event_qrcode').css('display','inline');
                }
            }else{
                console.log("image");
                console.log(jsonRes);
                last_schedule_id = jsonRes.schedule_id;
                $('div.title2').css('display','none');
                $('div#user_pref').css('display','none');
                $('img#pic').css('display','inline');
                $('img#like').css('display','inline');
                $('div.like_count').css('display','inline');
                $('p#like_count').css('display','inline');
                if('like_count' in jsonRes){
                    $('p#like_count').text(jsonRes.like_count);
                }
                $('img#pic').attr('src',"/static/"+jsonRes.file);
                $('img#like').attr('src',"/static/img/Like.png");
                var width = $('img#pic').width();
                var height = $('img#pic').height();
                $('img#pic').height(screen.height * 0.98);
                $('img#pic').css('maxWidth',($(window).width() * 0.85 | 0 ) + "px");
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

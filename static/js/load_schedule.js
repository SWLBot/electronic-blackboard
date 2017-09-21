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
            // case1 - fail //
            if(jsonRes.result == "fail"){
                console.log("fail");
                console.log(jsonRes);
            }
            // case2 - same //
            else if(last_schedule_id == jsonRes.schedule_id){
                console.log("same");
            }
            // case3 - text //
            else if(jsonRes.file_type == "text"){
                console.log("text");
                last_schedule_id = jsonRes.schedule_id;
                resetTextDisplay();
                // 1. preference //
                if ('preference' in jsonRes.file_text){
                    setPreferenceDisplay();
                    if(jsonRes.file_text.preference === 1){
                        setDateInfo();
                        setConstellationInfo(jsonRes);
                        if( jsonRes.file_text.news.length > 0){
                            $('img#qrcode1').attr('src',String(jsonRes.file_text.news[0].QR));
                            $('div#newsTitle1').text(jsonRes.file_text.news[0].title);
                            $('img#qrcode2').attr('src',String(jsonRes.file_text.news[1].QR));
                            $('div#newsTitle2').text(jsonRes.file_text.news[1].title);
                        }
                    }
                }
                // 2. forum news //
                else if('text_type' in jsonRes.file_text && jsonRes.file_text.text_type=='news'){
                    setNewsDisplay();
                    setNewsInfo(jsonRes);
                }
                // 3. other announcement //
                else{
                    setAnnouncementDisplay();
                    setConInfo(jsonRes);
                    setAnnouncementInfo(jsonRes);
                    setAnnouncementStyle(jsonRes);
                }

                if ('event_id' in jsonRes.file_text){
                    $('img#event_qrcode').css('display','inline');
                    $('img#event_qrcode').attr('src',String(jsonRes.file_text.event_id));
                }
            }
            // case4 - image //
            else if(jsonRes.file_type == "image"){
                console.log("text");
                last_schedule_id = jsonRes.schedule_id;
                setImageDisplay();
                setImageInfo(jsonRes);
            }
            // else handling //
            else{

            }
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

// text //
function resetTextDisplay(){
    $('img#pic').css('display','none');
    $('div.like_count').css('display','none');
    $('div.title2').css('display','none');
    $('img#event_qrcode').css('display','none');
    $('footer').css('display','none');
    $('div#user_pref').css('display','none');
    $('div#news').css('display','none');
    $('img#qrcode1').css('display','none');
    $('img#qrcode2').css('display','none');
}

function setDateInfo(jsonRes){
    var datetime = new Date(Date.parse(jsonRes.file_text.date));
    var weekday = getWeekday(datetime);
    var year = datetime.getFullYear();
    var month = datetime.getMonth() + 1;
    var date = datetime.getDate();
    $('div#week b').text(weekday);
    $('div#year b').text(year);
    $('div#date b').text(String(month)+'.'+String(date));
}

function getWeekday(datetime){
    var week = ["Mon.", "Tue.", "Wed.", "Thu.", "Fri.", "Sat.", "Sun."];
    return week[datetime.getDay()];
}

function setPreferenceDisplay(){
    $('div#user_pref').css('display','inline');
    $('img#qrcode1').css('display','inline');
    $('img#qrcode2').css('display','inline');
}

function setConstellationInfo(jsonRes){
    $('div#name b').text(jsonRes.file_text.nickname);
    $('div#star b').text(jsonRes.file_text.constellation.name);
    $('div#overall b').text(jsonRes.file_text.constellation.value[0]);
    $('div#love b').text(jsonRes.file_text.constellation.value[1]);
    $('div#career b').text(jsonRes.file_text.constellation.value[2]);
    $('div#wealth b').text(jsonRes.file_text.constellation.value[3]);
}

function setNewsDisplay(){
    $('div#news').css('display','inline');
}

function setNewsInfo(jsonRes){
    $('div#forum-1').text(jsonRes.file_text.forum_name1);
    $('p#title-1').text(jsonRes.file_text.title1);
    $('img#qrcode-1').attr('src',String(jsonRes.file_text.QR1));
    $('div#forum-2').text(jsonRes.file_text.forum_name2);
    $('p#title-2').text(jsonRes.file_text.title2);
    $('img#qrcode-2').attr('src',String(jsonRes.file_text.QR2));
}

function setAnnouncementDisplay(jsonRes){
    $('div.title2').css('display','inline');
    if(jsonRes.type_name === "獲獎公告"){
        $('footer').css('display','inline');
    }
    else{
        $('footer').css('display','none')
    }
}

function setConInfo(jsonRes){
    if ( 'con' in jsonRes.file_text){
        $('span#con').html(jsonRes.file_text.con);
    }
    else{
        if (jsonRes.type_name === "獲獎公告"){
            $('span#con').html("賀！");
        }
        else{
            $('span#con').html("活動公告");
        }
    }
}

function setAnnouncementInfo(jsonRes){
    $('#title1').html(jsonRes.file_text.title1);
    $('#title2').html(jsonRes.file_text.title2);
    if('location' in jsonRes.file_text && jsonRes.file_text.location != ''){
        $('#location').html('地點： ' + jsonRes.file_text.location)
    }
    else{
        $('#location').html('')
    }
    if('detailtime' in jsonRes.file_text && jsonRes.file_text.detailtime != ''){
        $('#detailtime').html('時間： ' + jsonRes.file_text.detailtime
    }
    else{
        $('#detailtime').html('')
    }
    $('#description').html(jsonRes.file_text.description);
    if(jsonRes.type_name === "獲獎公告"){
        if ('background_color' in jsonRes.file_text){
            $('div.header').css('background-color',jsonRes.file_text.background_color);
            $('div.bar').css('background-color',jsonRes.file_text.background_color);
        }
        else{
            $('div.header').css('background-color','#CE0000');
            $('div.bar').css('background-color','#CE0000');
        }
        $('div.congratulation').html(jsonRes.file_text.year+"年"+jsonRes.file_text.month+"月 資訊學院全體師生慶賀");
    }
    else{
        if ('background_color' in jsonRes.file_text){
            $('div.header').css('background-color',jsonRes.file_text.background_color);
        }
        else{
            $('div.header').css('background-color','#FF8000');
        }
    }
}

// image //
function setImageDisplay(){
    $('div.title2').css('display','none');
    $('div#user_pref').css('display','none');
    $('div#news').css('display','none');
    $('img#pic').css('display','inline');
    $('img#like').css('display','inline');
    $('div.like_count').css('display','inline');
    $('p#like_count').css('display','inline');
}

function setImageInfo(jsonRes){
    $('img#pic').attr('src',"/static/" + jsonRes.file);
    $('img#pic').height(screen.height * 0.98);
    $('img#pic').css('maxWidth',($(window).width() * 0.85 | 0 ));
    $('img#like').attr('src',"/static/img/Like.png");
    if('like_count' in jsonRes){
        $('p#like_count').text(jsonRes.like_count);
    }
}
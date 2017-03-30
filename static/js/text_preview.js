$('input,textarea').on('keyup',function(){
    var id = $(this).attr('id');
    if( $('div#'+id).length ){
        var str = $(this).val().replace(/ /g,'&nbsp').replace(/\n/g,'<br>');
        $('div#'+id).html(str);
    }
});
$('input').keyup(function(){
    var id = $(this).attr('id');
    if( $('span#'+id).length ){
        var str = $(this).val().replace(/ /g,'&nbsp').replace(/\n/g,'<br>');
        $('span#'+id).html(str);
    }
}).keyup();
$('select').change(function(){
    var id = $(this).attr('id');
    if( $('span#'+id).length ){
        $('span#'+id).text($(this).val());
    }
});

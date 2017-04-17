function deal_space(){
    document.getElementById("con").value = document.getElementById("con").value.replace(/ /g,'&nbsp').replace(/\n/g,'<br>');
    document.getElementById("con2").value = document.getElementById("con2").value.replace(/ /g,'&nbsp').replace(/\n/g,'<br>');
    document.getElementById("person_name").value = document.getElementById("person_name").value.replace(/ /g,'&nbsp').replace(/\n/g,'<br>');
    document.getElementById("reward").value = document.getElementById("reward").value.replace(/ /g,'&nbsp').replace(/\n/g,'<br>');
    document.getElementById("description").value = document.getElementById("description").value.replace(/ /g,'&nbsp').replace(/\n/g,'<br>');
    document.getElementById("person_name2").value = document.getElementById("person_name2").value.replace(/ /g,'&nbsp').replace(/\n/g,'<br>');
    document.getElementById("reward2").value = document.getElementById("reward2").value.replace(/ /g,'&nbsp').replace(/\n/g,'<br>');
    document.getElementById("description2").value = document.getElementById("description2").value.replace(/ /g,'&nbsp').replace(/\n/g,'<br>');      
}
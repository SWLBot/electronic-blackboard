function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function formatParams( params ){
    return "?" + Object
        .keys(params)
        .map(function(key){
            return key+"="+encodeURIComponent(params[key])
        })
        .join("&")
}

function show_display(type='image'){
    var http = new XMLHttpRequest();
    http.open('GET','/display'+formatParams({type:type}), true);
    http.onreadystatechange = function(){
        if(this.readyState === 4 && this.status === 200){
            display_data(this.response)
        }
    }
    http.send();
}

function create_editButton(type,id){
    var editButton = document.createElement('a');
    editButton.innerHTML = 'Edit';
    editButton.classList.add('btn','btn-link');
    if(type==='image'){
        editButton.setAttribute('href','/edit?img_id='+id);
    }else if(type==='text'){
        editButton.setAttribute('href','/edit?text_id='+id);
    }
    return editButton;
}

function create_deleteButton(id){
    var deleteButton = document.createElement('a');
    deleteButton.innerHTML = 'Delete';
    deleteButton.classList.add('btn','btn-link');
    deleteButton.setAttribute('href','/delete?target_id='+id);
    deleteButton.setAttribute('onclick','return deleteConfirm()');
    return deleteButton
}

function insert_imgs(imgs,data_types){
    var img_table = document.getElementById('img_table')
    while(img_table.rows.length > 1){
        img_table.deleteRow(-1);
    }
    for(let obj of imgs){
        var row = img_table.insertRow();
        for (let type of data_types){
            if(type[0] === obj['type_id']){
                var target_type = type
            }
        }
        var preview_img = document.createElement('img');
        preview_img.setAttribute('src',obj['img_url']);
        preview_img.setAttribute('width','240');
        preview_img.setAttribute('height','180');

        var editButton = create_editButton(type='image',obj['img_id']);
        var deleteButton = create_deleteButton(obj['img_id']);

        row.insertCell().innerHTML = obj['img_id'];
        row.insertCell().innerHTML = target_type[1];
        row.insertCell().innerHTML = obj['img_upload_time'];
        row.insertCell().innerHTML = obj['img_start_date'];
        row.insertCell().innerHTML = obj['img_end_date'];
        row.insertCell().innerHTML = obj['img_start_time'];
        row.insertCell().innerHTML = obj['img_end_time'];
        row.insertCell().innerHTML = obj['img_display_count'];
        row.insertCell().innerHTML = obj['img_display_time'];
        row.insertCell().appendChild(preview_img);
        var editCell = row.insertCell();
        editCell.appendChild(editButton);
        editCell.appendChild(deleteButton);
    }
}

function insert_texts(texts,data_types){
    text_table = document.getElementById('text_table');
    while(text_table.rows.length > 1){
        text_table.deleteRow(-1);
    }
    for(let text of texts){
        var row = text_table.insertRow();
        for (let type of data_types){
            if(type[0] === text[1]){
                var target_type = type
            }
        }
        
        var editButton = create_editButton(type='text',text[0]);
        var deleteButton = create_deleteButton(text[0]);

        row.insertCell().innerHTML = text[0];
        if (typeof target_type != 'undefined'){
            row.insertCell().innerHTML = target_type[1];
        }else{
            row.insertCell().innerHTML = '';
        }
        row.insertCell().innerHTML = text[2];
        row.insertCell().innerHTML = text[3];
        row.insertCell().innerHTML = text[4];
        row.insertCell().innerHTML = text[5];
        row.insertCell().innerHTML = text[6];
        row.insertCell().innerHTML = text[7];
        row.insertCell().innerHTML = text[8];
        var editCell = row.insertCell();
        editCell.appendChild(editButton);
        editCell.appendChild(deleteButton);
    }
}

function display_data(response){
    response = JSON.parse(response)
    if(response.type === 'image'){
        insert_imgs(response.data,response.data_types)
    }else if(response.type === 'text'){
        insert_texts(response.data,response.data_types)
    }
}

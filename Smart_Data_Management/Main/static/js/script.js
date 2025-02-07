function get_select(){
    let column = document.getElementById('column');
    return column?column.value:column;
}

function dontAskWhy(){

    const dont = document.querySelector(".dont-ask-why-this");
    if(dont!=undefined){
        dont.style.width = document.querySelector('.tableView').scrollWidth + 'px';
    }
}

function add_csrf(){
    document.body.addEventListener('htmx:configRequest', function (event) {
        event.detail.headers['X-CSRFToken'] = document.getElementsByName('csrfmiddlewaretoken').value;
    });
    }

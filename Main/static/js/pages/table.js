const a = document.querySelector(".table-view");
const searchText = document.querySelector("input#search");
const columns = document.querySelector("select#column");

const htmxSuggest = document.querySelector(".here-cause-htmx");
const htmxForm = document.querySelector(".htmx-form");
var firstTime = true;

function centerDiv(){
    var b = document.querySelector(".loading");
    let left = a.scrollLeft + ((a.offsetWidth - b.offsetWidth) / 2);
    b.style.left = left + 'px';
}

document.addEventListener("DOMContentLoaded", centerDiv);
a.addEventListener("scroll", centerDiv);
window.onresize = centerDiv;

document.addEventListener("htmx:confirm", function(event){
    if(event.detail.elt === htmxForm){
        event.preventDefault(); 
        if((columns.value !== '' && searchText.value !== '') || (searchText.value === '' && columns.value === '')){
            event.detail.issueRequest();
        }
    }
});

function fancy_function_doing_everything_for_table_i_dont_know_why_i_am_writing_the_name_this_long_but_oh_well(){

    searchText.addEventListener("input", 
        () => {
            document.querySelector("select#status").dispatchEvent(new Event("input"));
        }
    );
}

function setObserver(){
    $('select#column').select2();

    const observer = new MutationObserver((mutations) => {

        for(const mutation of mutations){
            if(mutation.type == 'attributes' && mutation.attributeName == 'title'){
                if(firstTime){
                    firstTime = !firstTime;
                } else {
                    document.querySelector("select#status").dispatchEvent(new Event("input"));
                }
            }
        }
    });

    observer.observe(
    document.querySelector("select#column+span"), {
        attributes: true,
        childList: true,
        subtree: true
    });
}

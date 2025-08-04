const a = document.querySelector(".table-view");

function centerDiv(){
    var b = document.querySelectorAll(".loading");

    for(let node of b){
        let left = a.scrollLeft + ((a.offsetWidth - node.offsetWidth) / 2);
        node.style.left = left + 'px';
    }
}

document.addEventListener("DOMContentLoaded", centerDiv);
a.addEventListener("scroll", centerDiv);
window.onresize = centerDiv;
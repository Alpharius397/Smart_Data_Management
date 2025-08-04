function getTaskHeight(){
    const tabs = document.querySelectorAll(".task-info");

    for(let tab of tabs){
        let height = 0;
        for(let child of tab.childNodes){

            if(child.offsetHeight){
                height = Math.max(height, child.offsetHeight + 10);
            }
            
        }
        tab.style.setProperty('--tab-height', height + 'px');
    }
}

window.onresize = getTaskHeight;
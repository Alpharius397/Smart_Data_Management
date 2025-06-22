function setObserver(){
    $('.schema-field select').select2();

    const observer = new MutationObserver((mutations) => {

        for(const mutation of mutations){
            if(mutation.type == 'attributes' && mutation.attributeName == 'title'){
                document.querySelector("select").dispatchEvent(new Event("input"));
            }
        }
    });

    observer.observe(
    document.querySelector("select+span"), {
        attributes: true,
        childList: true,
        subtree: true
    });
}

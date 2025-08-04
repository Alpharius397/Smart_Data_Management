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

/**
 * 
 * @param {String} ws_conn 
 */
function beginWebSocket(ws_conn){
    const fancy = document.querySelector("#fancy-thing");

    fancy.innerHTML = `<div class="htmx-ws-connection-here" hx-ext="ws" ws-connect="${ws_conn}"></div>`;
    htmx.process(fancy)

    setTimeout(() => {
        let a = document.querySelector(".htmx-ws-connection-here");

        if(a !== null) htmx.trigger(a, 'htmx:beforeCleanupElement');
    }, 1000*5);
}

function endWebSocket(){
    let a = document.querySelector(".htmx-ws-connection-here");
    console.warn("stop");
    htmx.trigger(a, 'htmx:beforeCleanupElement');
}
/**
 * 
 * @param {String} value 
 * @returns {String | null}
 */

function get_select(value){
    let column = document.querySelector(value);
    if(column !== null) return column.value;
    return null;
}

function get_header(){
    const hamBurger = document.querySelector(".hamburger");
    const headerLeft = document.querySelector(".header-left")?.cloneNode(true);
    const headerRight = document.querySelector(".header-right")?.cloneNode(true);
    const hamBurgerOption = document.querySelector(".header-option");

    hamBurgerOption.appendChild(headerLeft);
    hamBurgerOption.appendChild(headerRight);

    hamBurger.addEventListener("click", function(){

        if(hamBurgerOption.classList.contains("close")){
            hamBurgerOption.classList.remove("close");
        } else {
            hamBurgerOption.classList.add("close");
        }
    });
}

get_header();

function dontAskWhy(){

    const dont = document.querySelector(".dont-ask-why-this");
    if(dont!=undefined){
        dont.style.width = document.querySelector('.tableView').scrollWidth + 'px';
    }
}

function add_csrf(){
    document.body.addEventListener('htmx:configRequest', function (event) {
        event.detail.headers['X-CSRFToken'] = document.getElementsByName('csrfmiddlewaretoken')?.[0].value;
    });
}

/**
 * 
 * @param {HTMLElement} form 
 * @returns {Map}
 */

function formValue(formID){
    const NODE = document.getElementById(formID);
    let children = NODE.childNodes;
    let memo = {};
    
    for(let i of children){
        if(i.name!="" && i.name!=undefined){
            memo[i.name] = i.value;
        }
    }

    return memo;
}

/**
 * @param {String} url_to_redirect
 * @returns {void}
 */
function redirect(url_to_redirect){
    window.location.href = url_to_redirect;
}

/**
 * @param {String} url_to_go
 * @returns {void}
 */
function confirmPrompt(url_to_go) {
    let confirmConfirm = confirm("Are you sure you want to proceed?");

    if(confirmConfirm==true) redirect(url_to_go);
}
const dialogBox = document.querySelector("dialog");
const dialogTitle = document.querySelector(".dialog-title");
const dialogMessage = document.querySelector(".dialog-message");

let dialogClose = document.querySelector(".dialog-close");
let dialogYes = document.querySelector(".dialog-yes");
let dialogNo = document.querySelector(".dialog-no");

let offsetX = 0;
let offsetY = 0;
let isDragging = false;

/**
 * @param {string} title
 */
function setTitle(title) {
    dialogTitle.textContent = title;
}

/**
 * @param {string} message
 */
function setMessage(message) {
    dialogMessage.textContent = message;
}

/**
 * @param {(event: Event) => void | () => void} callBack
 * @param {boolean} closeAfter
 */
function setClose(callBack = ()=>{}, closeAfter = true) {
    const funcClosure = function (event = null) {
        callBack(event);
        if (closeAfter) __closeBox();
    };
    const clonedNode = dialogClose.cloneNode(true);
    dialogClose.parentElement.replaceChild(clonedNode, dialogClose);
    dialogClose = clonedNode;
    dialogClose.addEventListener("click", funcClosure);
}

/**
 * @param {(event: Event) => void | () => void} callBack
 * @param {boolean} closeAfter
 */
function setYes(callBack = ()=>{}, closeAfter = true) {
    const funcClosure = function (event = null) {
        callBack(event);
        if (closeAfter) __closeBox();
    };

    const clonedNode = dialogYes.cloneNode(true);
    dialogYes.parentElement.replaceChild(clonedNode, dialogYes);
    dialogYes = clonedNode;
    dialogYes.addEventListener("click", funcClosure);
}

/**
 * @param {(event: Event) => void | () => void} callBack
 * @param {boolean} closeAfter
 */
function setNo(callBack = ()=>{}, closeAfter = true) {
    const funcClosure = function (event = null) {
        callBack(event);
        if (closeAfter) __closeBox();
    };
    const clonedNode = dialogNo.cloneNode(true);
    dialogNo.parentElement.replaceChild(clonedNode, dialogNo);
    dialogNo = clonedNode;
    dialogNo.addEventListener("click", funcClosure);
}

/**
 * Opens the dialog and enables dragging
 */
function dialogBoxOpen() {
    dialogBox.showModal();
    dialogBox.addEventListener("click", dialogBoxClose);
    dialogBox.addEventListener("mousedown", dialogBoxDragStart);
    document.addEventListener("mousemove", dialogBoxDragGoing);
    dialogBox.addEventListener("mouseup", dialogBoxDragEnd);
}

function __closeBox() {
    dialogBox.close();
    dialogBox.removeEventListener("click", dialogBoxClose);
    dialogBox.removeEventListener("mousedown", dialogBoxDragStart);
    document.removeEventListener("mousemove", dialogBoxDragGoing);
    dialogBox.removeEventListener("mouseup", dialogBoxDragEnd);
}

/**
 * @param {Event} event
 */
function dialogBoxClose(event) {
    if (event.target === dialogBox) {
        __closeBox();
    }
}

/**
 * @param {MouseEvent} event
 */
function dialogBoxDragStart(event) {
    isDragging = true;
    offsetX = event.clientX - dialogBox.offsetLeft;
    offsetY = event.clientY - dialogBox.offsetTop;
}

/**
 * @param {MouseEvent} event
 */
function dialogBoxDragGoing(event) {
    if (isDragging) {
        dialogBox.style.left = `${event.clientX - offsetX}px`;
        dialogBox.style.top = `${event.clientY - offsetY}px`;
        dialogBox.style.position = "fixed";
    }
}

function dialogBoxDragEnd() {
    isDragging = false;
}

/**
 * 
 * @param {String} selector
 * @param {String} classOne
 * @param {String} classTwo
 */
function addClass(selector, classOne, classTwo){
    const elem = document.querySelector(selector);

    if(elem==null) return false;

    if(elem.classList.contains(classOne)){
        elem.classList.replace(classOne, classTwo);
    } else {
        elem.classList.replace(classTwo, classOne);
    }

    return true;
}
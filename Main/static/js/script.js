/**
 *
 * @param {String} value
 * @returns {String | null}
 */

function get_select(value) {
  let column = document.querySelector(value);
  if (column !== null) return column.value;
  return null;
}
const hamBurgerOption = document.querySelector(".header-option");
const hamBurgerIcon = document.querySelector(".hamburger");
const header = document.querySelector("header");

function get_header() {

  let childCount = hamBurgerOption.childElementCount;

  hamBurgerOption.style.setProperty("--height", 60*(childCount) + 'px');

  switch(childCount){
    case 1: hamBurgerOption.style.justifyContent = 'center'; break;
    default : hamBurgerOption.style.justifyContent = 'space-evenly';
  }
  console.log(childCount)

}

hamBurgerIcon.addEventListener("click", function(event) {
  hamBurgerIcon.classList.toggle("open");
  hamBurgerOption.classList.toggle("close");
  event.stopPropagation();
});

document.addEventListener("click", function(event) {

  if((event.target !== hamBurgerOption) && (event.target !== hamBurgerIcon)) {
    if(hamBurgerIcon !== null && hamBurgerIcon.classList.contains("open")){
      hamBurgerIcon.click();
    }
  }
});

function add_csrf() {
  document.body.addEventListener("htmx:configRequest", function(event) {
    event.detail.headers["X-CSRFToken"] = document.getElementsByName(
      "csrfmiddlewaretoken",
    )?.[0].value;
  });
}

/**
 * 
 * @param {Event} event 
 * @param {string} id 
 * @returns 
 */
function formCheck(event, id){
  const form = document.querySelector(id);
  
  console.log(form)

  if(form.checkValidity() === false){
    form.reportValidity(); 
    event.stopImmediatePropagation(); 
  }
}

/**
 *
 * @param {HTMLElement} form
 * @returns {Map}
 */

function formValue(formID) {
  const NODE = document.getElementById(formID);
  let children = NODE.childNodes;
  let memo = {};

  for (let i of children) {
    if (i.name != "" && i.name != undefined) {
      memo[i.name] = i.value;
    }
  }

  return memo;
}

/**
 * @param {String} url_to_redirect
 * @returns {void}
 */
function redirect(url_to_redirect) {
  window.location.href = url_to_redirect;
}

/**
 * @param {Event} event
 * @returns {void}
 */
function confirmPrompt(event) {
  let confirmConfirm = confirm("Are you sure you want to proceed?");

  if (confirmConfirm != true) event.stopImmediatePropagation();
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
  dialogMessage.innerHTML = message;
  dialogBox.style.width = Math.max(dialogBox.offsetWidth, dialogMessage.offsetWidth) + 'px';
  console.info(Math.max(dialogBox.offsetWidth, dialogMessage.offsetWidth))
}

/**
 * @param {(event: Event) => void | () => void} callBack
 * @param {boolean} closeAfter
 */
function setClose(callBack, closeAfter = true) {
  const funcClosure = function(event = null) {
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
 * @param {string} title
 */
function setYes(callBack, closeAfter = true, title = 'Yes') {
  const funcClosure = function(event = null) {
    callBack(event);
    if (closeAfter) __closeBox();
  };

  const clonedNode = dialogYes.cloneNode(true);
  dialogYes.parentElement.replaceChild(clonedNode, dialogYes);
  dialogYes = clonedNode;
  dialogYes.textContent = title; 
  dialogYes.addEventListener("click", funcClosure);
}

/**
 * @param {(event: Event) => void | () => void} callBack
 * @param {boolean} closeAfter
 * @param {string} title
 */
function setNo(callBack, closeAfter = true, title = 'No') {
  const funcClosure = function(event = null) {
    callBack(event);
    if (closeAfter) __closeBox();
  };
  const clonedNode = dialogNo.cloneNode(true);
  dialogNo.parentElement.replaceChild(clonedNode, dialogNo);
  dialogNo = clonedNode;
  dialogNo.textContent = title; 
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
 * @param {MouseEvent} event
 */
function dialogBoxClose(event) {
  console.log(event.offsetX)
  if (event.target === dialogBox && ((event.offsetX > (dialogBox.offsetWidth + 10)) ||  (event.offsetY > (dialogBox.offsetHeight + 10)) || (event.offsetX < (-10)) || (event.offsetY > (dialogBox.offsetHeight + 10)))) {
    __closeBox();
  }
}

/**
 * @param {MouseEvent} event
 */
function dialogBoxDragStart(event) {

  if(event.target.closest('dialog') && event.target !== dialogBox){
    isDragging = true;
    offsetX = event.clientX - dialogBox.offsetLeft;
    offsetY = event.clientY - dialogBox.offsetTop;
  }
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
 */
function addClass(selector, classOne) {
  const elem = document.querySelector(selector);

  if (elem == null) return false;

  elem.classList.toggle(classOne);

  return true;
}

function handleSize() {
  if (window.innerWidth <= 600) {
    get_header();
  }
}
get_header()
window.onresize = handleSize;

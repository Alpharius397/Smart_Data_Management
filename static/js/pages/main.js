const hamBurgerOption = document.querySelector(".header-option"); // On all pages so no worries
const hamBurgerIcon = document.querySelector(".hamburger"); // On all pages so no worries

function get_header() {

  if(hamBurgerOption == null ) return
  let childCount = hamBurgerOption.childElementCount;

  hamBurgerOption.style.setProperty("--height", 60*(childCount) + 'px');

  switch(childCount){
    case 1: hamBurgerOption.style.justifyContent = 'center'; break;
    default : hamBurgerOption.style.justifyContent = 'space-evenly';
  }
}

hamBurgerIcon?.addEventListener("click", function(event) {
  hamBurgerIcon?.classList.toggle("open");
  hamBurgerOption?.classList.toggle("close");
  event.stopPropagation();
});

document.addEventListener("click", function(event) {

  if((event.target !== hamBurgerOption) && (event.target !== hamBurgerIcon)) {
    if(hamBurgerIcon !== null && hamBurgerIcon?.classList.contains("open")){
      hamBurgerIcon?.click();
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
  
  if((form != null) && (form.checkValidity() === false)){
    form.reportValidity(); 
    event.stopImmediatePropagation(); 
  }
}

/**
 * @param {String} url_to_redirect
 * @returns {void}
 */
function redirect(url_to_redirect) {
  window.location.href = url_to_redirect;
}

var SkipThis = {
  flag: false,
  
  setFlag: function(value){
    
    if(typeof(value) !== 'boolean') {
      console.warn("Invalid value, required boolean")
      return false;
    } else {
      this.flag = value;

      return true;
    }
  }
}

/**
 * @param {Event} event
 * @returns {void}
 */
function confirmPrompt(event) {
  
  if(!SkipThis.flag){
    event.preventDefault();

    swal(
      {title:"Are you sure?",text:"Are you sure about this action",icon:"warning",buttons:true,dangerMode:true}
    ).then((confirmConfirm) => {
      if (confirmConfirm === true){ 
        SkipThis.setFlag(true);
        event.target.click();
      }
    })

  } else {
    SkipThis.setFlag(false);
  }
}

/**
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

/**
 * @param {string} className 
 * @param {string} message 
 * @returns
 */
function makeLi(className, message){
  let a = document.createElement('li');
  a.className=className;
  a.innerHTML = message
  return a;
}

/**
 * @param {string} className 
 * @param {string} message 
 * @returns
 */
function makeUl(className = "messages"){
  let a = document.createElement('ul');
  a.className=className;
  return a;
}

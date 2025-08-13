const resendBtn = document.getElementById("resend-otp-btn");

function startCooldown() {
  resendBtn.disabled = true;
  let cooldown = 30;
  let interval = setInterval(() => {
    cooldown--;
    resendBtn.innerText = `Resend OTP (${cooldown}s)`;
    if (cooldown <= 0) {
      clearInterval(interval);
      resendBtn.disabled = false;
      resendBtn.innerText = "Resend OTP";
      cooldown = 5;
    }
  }, 1000);
}

document.addEventListener("DOMContentLoaded", startCooldown);

document.addEventListener("htmx:afterRequest", (evt) => {
  if (evt.detail.elt.id === "resend-otp-btn") {
    startCooldown();
  }
});

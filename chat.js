// static/js/chat.js
document.addEventListener("DOMContentLoaded", () => {
  const ta = document.querySelector("textarea[name='prompt']");
  if (!ta) return;
  ta.focus();
  ta.addEventListener("input", () => {
    ta.style.height = "auto";
    ta.style.height = ta.scrollHeight + "px";
  });
});

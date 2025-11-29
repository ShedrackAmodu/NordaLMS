// sidebar navigation bar
function toggleSidebar() {
  document.getElementById("side-nav").classList.toggle("toggle-active");
  document.getElementById("main").classList.toggle("toggle-active");
  document.getElementById("top-navbar").classList.toggle("toggle-active");
  document.querySelector(".manage-wrap").classList.toggle("toggle-active");
}

// theme toggle
function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute('data-theme');
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
  const icons = document.querySelectorAll('.theme-toggle i');
  const buttons = document.querySelectorAll('.theme-toggle');

  document.documentElement.setAttribute('data-theme', newTheme);
  localStorage.setItem('theme', newTheme);

  if (newTheme === 'dark') {
    icons.forEach(icon => {
      icon.classList.remove('fa-moon');
      icon.classList.add('fa-sun');
    });
    buttons.forEach(button => {
      button.classList.remove('btn-light');
      button.classList.add('btn-outline-light');
    });
  } else {
    icons.forEach(icon => {
      icon.classList.remove('fa-sun');
      icon.classList.add('fa-moon');
    });
    buttons.forEach(button => {
      button.classList.remove('btn-outline-light');
      button.classList.add('btn-light');
    });
  }
}

// Initialize theme on page load
document.addEventListener('DOMContentLoaded', function() {
  const savedTheme = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);
  const icons = document.querySelectorAll('.theme-toggle i');
  const buttons = document.querySelectorAll('.theme-toggle');
  if (savedTheme === 'dark') {
    icons.forEach(icon => {
      icon.classList.remove('fa-moon');
      icon.classList.add('fa-sun');
    });
    buttons.forEach(button => {
      button.classList.remove('btn-light');
      button.classList.add('btn-outline-light');
    });
  } else {
    icons.forEach(icon => {
      icon.classList.remove('fa-sun');
      icon.classList.add('fa-moon');
    });
    buttons.forEach(button => {
      button.classList.remove('btn-outline-light');
      button.classList.add('btn-light');
    });
  }
});

// #################################
// popup

var c = 0;
function pop() {
  if (c == 0) {
    document.getElementById("popup-box").style.display = "block";
    c = 1;
  } else {
    document.getElementById("popup-box").style.display = "none";
    c = 0;
  }
}

// ##################################

// Example starter JavaScript for disabling form submissions if there are invalid fields
// Fetch all the forms we want to apply custom Bootstrap validation styles to
var forms = document.getElementsByClassName("needs-validation");

// Loop over them and prevent submission
Array.prototype.filter.call(forms, function (form) {
  form.addEventListener(
    "submit",
    function (event) {
      if (form.checkValidity() === false) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add("was-validated");
    },
    false
  );
});
// ##################################

// extend and collapse
function showCourses(btn) {
  var btn = $(btn);

  if (collapsed) {
    btn.html('Collapse <i class="fas fa-angle-up"></i>');
    $(".hide").css("max-height", "unset");
    $(".white-shadow").css({ background: "unset", "z-index": "0" });
  } else {
    btn.html('Expand <i class="fas fa-angle-down"></i>');
    $(".hide").css("max-height", "150");
    $(".white-shadow").css({
      background: "linear-gradient(transparent 50%, rgba(255,255,255,.8) 80%)",
      "z-index": "2",
    });
  }
  collapsed = !collapsed;
}

// Toast notification function
function showToast(title, message, type = 'info') {
  const toastElement = document.getElementById('liveToast');
  const toastTitle = document.getElementById('toastTitle');
  const toastBody = document.getElementById('toastBody');

  // Set icon based on type
  let iconClass = 'fas fa-info-circle text-primary';
  if (type === 'success') iconClass = 'fas fa-check-circle text-success';
  if (type === 'warning') iconClass = 'fas fa-exclamation-triangle text-warning';
  if (type === 'danger') iconClass = 'fas fa-times-circle text-danger';

  toastTitle.innerHTML = `<i class="${iconClass} me-2"></i>${title}`;
  toastBody.textContent = message;

  const toast = new bootstrap.Toast(toastElement);
  toast.show();
}

$(document).ready(function () {
  $("#primary-search").focus(function () {
    $("#top-navbar").attr("class", "dim");
    $("#side-nav").css("pointer-events", "none");
    $("#main-content").css("pointer-events", "none");
  });
  $("#primary-search").focusout(function () {
    $("#top-navbar").removeAttr("class");
    $("#side-nav").css("pointer-events", "auto");
    $("#main-content").css("pointer-events", "auto");
  });
});

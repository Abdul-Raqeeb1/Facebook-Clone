/*
  js/app.js
  - Enables login button when inputs are non-empty
  - Handles opening/closing of signup modal with accessible attributes
  - Basic focus management for modal
*/

document.addEventListener('DOMContentLoaded', function () {
  const email = document.getElementById('email');
  const password = document.getElementById('password');
  const loginBtn = document.getElementById('login-button');

  function updateLoginState() {
    const enabled = email.value.trim() !== '' && password.value.trim() !== '';
    loginBtn.disabled = !enabled;
    loginBtn.setAttribute('aria-disabled', String(!enabled));
  }

  // Function to show error messages
  function showError(field, show) {
    const errorElement = document.getElementById(`${field.id}-error`);
    const formGroup = field.closest('.form-group');
    if (show) {
      formGroup.classList.add('has-error');
      errorElement.style.display = 'block';
    } else {
      formGroup.classList.remove('has-error');
      errorElement.style.display = 'none';
    }
  }

  // Clear error messages on input
  [email, password].forEach((el) => {
    el && el.addEventListener('input', () => {
      showError(el, false);
      updateLoginState();
    });
  });

  // Handle login form submission
  const form = document.getElementById('login-form');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (!loginBtn.disabled) {
        // Clear any existing error messages
        showError(email, false);
        showError(password, false);
        
        loginBtn.textContent = 'Logging in...';
        
        const formData = new FormData(form);
        fetch(form.action || window.location.href, {
          method: 'POST',
          body: formData,
          headers: {
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
          }
        })
        .then(response => {
          if (response.redirected) {
            // If the response is a redirect, it means login was successful
            window.location.href = response.url;
          } else {
            return response.text();
          }
        })
        .then(html => {
          if (html) {  // Only process html if it exists (not redirected)
            loginBtn.textContent = 'Log In';
            if (html.includes('Invalid email or password')) {
              showError(email, true);
              showError(password, true);
              password.value = '';  // Clear only password field
            }
          }
        })
        .catch(error => {
          loginBtn.textContent = 'Log In';
          showError(email, true);
          showError(password, true);
        });
      }
    });
  }

  /* Modal behavior */
  const openBtn = document.getElementById('open-signup');
  const modal = document.getElementById('signup-modal');
  const overlay = modal?.querySelector('.modal__overlay');
  const closeBtn = modal?.querySelector('[data-dismiss="modal"]');
  const firstInput = modal?.querySelector('input');

  function openModal() {
    if (!modal) return;
    modal.setAttribute('aria-hidden', 'false');
    openBtn.setAttribute('aria-expanded', 'true');
    // store last focused
    modal.__lastFocus = document.activeElement;
    // focus first input
    setTimeout(() => { firstInput?.focus(); }, 120);
  }

  function closeModal() {
    if (!modal) return;
    modal.setAttribute('aria-hidden', 'true');
    openBtn.setAttribute('aria-expanded', 'false');
    // return focus
    modal.__lastFocus?.focus?.();
  }

  openBtn?.addEventListener('click', openModal);
  closeBtn?.addEventListener('click', closeModal);
  overlay?.addEventListener('click', closeModal);

  // Close on Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal && modal.getAttribute('aria-hidden') === 'false') {
      closeModal();
    }
  });

  // Basic signup form placeholder handling
  const signupForm = document.getElementById('signup-form');
  if (signupForm) {
    signupForm.addEventListener('submit', function (e) {
      e.preventDefault();
      const submit = document.getElementById('signup-submit');
      submit.disabled = true;
      submit.textContent = 'Creating...';
      setTimeout(() => {
        submit.disabled = false;submit.textContent = 'Sign Up';
        closeModal();
        alert('Demo: Account created (no backend)');
      }, 1000);
    });
  }

});

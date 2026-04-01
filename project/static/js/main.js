// ============================================================
// RetailAI — Main JavaScript
// ============================================================

// ---- TOAST ----
function showToast(message, type = 'info') {
  const icons = { success: 'fa-check-circle', error: 'fa-times-circle', warning: 'fa-exclamation-triangle', info: 'fa-info-circle' };
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <i class="fas ${icons[type] || icons.info} toast-icon"></i>
    <span class="toast-msg">${message}</span>
    <button class="toast-close" onclick="removeToast(this.parentElement)"><i class="fas fa-times"></i></button>
  `;
  container.appendChild(toast);
  setTimeout(() => removeToast(toast), 4500);
}
function removeToast(toast) {
  toast.classList.add('removing');
  setTimeout(() => toast.remove(), 300);
}

// ---- LOADING ----
function showLoading(text = 'Processing...') {
  let el = document.getElementById('loadingOverlay');
  if (!el) {
    el = document.createElement('div');
    el.id = 'loadingOverlay';
    el.className = 'loading-overlay';
    el.innerHTML = `<div class="spinner"></div><div class="loading-text">${text}</div>`;
    document.body.appendChild(el);
  } else {
    el.querySelector('.loading-text').textContent = text;
    el.style.display = 'flex';
  }
}
function hideLoading() {
  const el = document.getElementById('loadingOverlay');
  if (el) el.style.display = 'none';
}

// ---- NAVBAR ----
window.addEventListener('scroll', () => {
  const nb = document.getElementById('navbar');
  if (nb) nb.classList.toggle('scrolled', window.scrollY > 20);
});
document.getElementById('navToggle')?.addEventListener('click', () => {
  document.getElementById('navMenu')?.classList.toggle('open');
});
document.getElementById('userBtn')?.addEventListener('click', (e) => {
  e.stopPropagation();
  document.getElementById('userDropdown')?.classList.toggle('show');
});
document.addEventListener('click', () => {
  document.getElementById('userDropdown')?.classList.remove('show');
});

// ---- TABS ----
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const tabId = btn.dataset.tab;
    const parent = btn.closest('.tabs-wrapper') || document;
    parent.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    parent.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(tabId)?.classList.add('active');
  });
});

// ---- INTERSECTION OBSERVER (fade-up) ----
const observer = new IntersectionObserver((entries) => {
  entries.forEach(e => { if (e.isIntersecting) { e.target.style.animationPlayState = 'running'; } });
}, { threshold: 0.1 });
document.querySelectorAll('.fade-up').forEach(el => {
  el.style.animationPlayState = 'paused';
  observer.observe(el);
});

// ---- COUNTER ANIMATION ----
function animateCounter(el, target, duration = 1500) {
  let start = 0;
  const step = (timestamp) => {
    if (!start) start = timestamp;
    const progress = Math.min((timestamp - start) / duration, 1);
    el.textContent = Math.floor(progress * target).toLocaleString();
    if (progress < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}
document.querySelectorAll('[data-counter]').forEach(el => {
  const obs = new IntersectionObserver(entries => {
    if (entries[0].isIntersecting) { animateCounter(el, parseInt(el.dataset.counter)); obs.disconnect(); }
  });
  obs.observe(el);
});

// ---- SIDEBAR TOGGLE (mobile) ----
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebar = document.querySelector('.sidebar');
sidebarToggle?.addEventListener('click', () => sidebar?.classList.toggle('open'));

// ---- PASSWORD TOGGLE ----
document.querySelectorAll('.toggle-password').forEach(btn => {
  btn.addEventListener('click', () => {
    const input = btn.previousElementSibling || document.getElementById(btn.dataset.target);
    if (!input) return;
    const isPass = input.type === 'password';
    input.type = isPass ? 'text' : 'password';
    btn.querySelector('i').className = `fas ${isPass ? 'fa-eye-slash' : 'fa-eye'}`;
  });
});

// ---- PASSWORD STRENGTH ----
const pwInput = document.getElementById('password');
const strengthFill = document.getElementById('strengthFill');
const strengthText = document.getElementById('strengthText');
if (pwInput && strengthFill) {
  pwInput.addEventListener('input', () => {
    const v = pwInput.value;
    let score = 0;
    if (v.length >= 8) score++;
    if (/[A-Z]/.test(v)) score++;
    if (/[0-9]/.test(v)) score++;
    if (/[^A-Za-z0-9]/.test(v)) score++;
    const levels = [
      { width: '0%', color: 'transparent', text: '' },
      { width: '25%', color: '#ef4444', text: 'Weak' },
      { width: '50%', color: '#f59e0b', text: 'Fair' },
      { width: '75%', color: '#06b6d4', text: 'Good' },
      { width: '100%', color: '#10b981', text: 'Strong' },
    ];
    const l = levels[score] || levels[0];
    strengthFill.style.width = l.width;
    strengthFill.style.background = l.color;
    if (strengthText) { strengthText.textContent = l.text; strengthText.style.color = l.color; }
  });
}

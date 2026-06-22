const API_BASE = '/api';

function escapeHtml(value = '') {
  return String(value).replace(/[&<>"']/g, (char) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;',
  }[char]));
}

function ensureToastContainer() {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  return container;
}

function showToast(message, type = 'success') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  ensureToastContainer().appendChild(toast);
  setTimeout(() => toast.remove(), 4200);
}

function setFormMessage(form, message, type = 'info') {
  let status = form.querySelector('.form-status');
  if (!status) {
    status = document.createElement('p');
    status.className = 'form-status';
    form.appendChild(status);
  }
  status.className = `form-status ${type}`;
  status.textContent = message;
}

function clearFormMessage(form) {
  const status = form.querySelector('.form-status');
  if (status) status.remove();
}

function setLoading(form, isLoading, label = 'Working...') {
  const button = form.querySelector('button[type="submit"]');
  if (!button) return;

  if (isLoading) {
    button.dataset.originalText = button.textContent;
    button.textContent = label;
    button.disabled = true;
    form.classList.add('is-loading');
    return;
  }

  button.textContent = button.dataset.originalText || button.textContent;
  button.disabled = false;
  form.classList.remove('is-loading');
}

async function apiFetch(url, options = {}) {
  const res = await fetch(url, {
    credentials: 'include',
    ...options,
  });

  if (!res.ok) {
    let message = 'Request failed';
    try {
      const data = await res.json();
      message = data.detail || message;
    } catch (error) {
      message = res.statusText || message;
    }
    throw new Error(message);
  }

  if (res.status === 204) return null;
  return res.json();
}

async function fetchCurrentOwner() {
  try {
    return await apiFetch(`${API_BASE}/me`);
  } catch (error) {
    return null;
  }
}

async function updateAuthUI() {
  const nav = document.getElementById('nav-auth');
  if (!nav) return;

  const owner = await fetchCurrentOwner();
  if (owner) {
    nav.innerHTML = `
      <span class="nav-owner">${escapeHtml(owner.restaurant_name)}</span>
      <a href="/frontend/dashboard.html">Dashboard</a>
      <button onclick="logout()" class="link-button">Logout</button>
    `;
    return;
  }

  nav.innerHTML = `
    <a href="/frontend/login.html">Login</a>
    <a class="button small" href="/frontend/signup.html">Sign up</a>
  `;
}

async function logout() {
  try {
    await fetch(`${API_BASE}/logout`, { method: 'POST', credentials: 'include' });
  } finally {
    window.location.href = '/';
  }
}

function publicMenuUrl(menu) {
  return `${window.location.origin}/m/${menu.slug}`;
}

document.addEventListener('DOMContentLoaded', updateAuthUI);

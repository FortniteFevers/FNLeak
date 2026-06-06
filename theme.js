// Apply theme immediately to prevent flash
(function () {
  const saved = localStorage.getItem('wc2026-theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
})();

function toggleTheme() {
  const curr = document.documentElement.getAttribute('data-theme');
  const next = curr === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('wc2026-theme', next);
  updateThemeBtn();
  window.dispatchEvent(new CustomEvent('themechange', { detail: next }));
}

function updateThemeBtn() {
  const btn = document.getElementById('themeToggle');
  if (!btn) return;
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  btn.textContent = isDark ? '☀️' : '🌙';
  btn.title = isDark ? 'Switch to light mode' : 'Switch to dark mode';
}

function toggleMobileNav() {
  const backdrop = document.getElementById('mobileMenuBackdrop');
  const modal = document.getElementById('mobileMenuModal');
  const isOpen = backdrop?.classList.contains('open');

  if (isOpen) {
    backdrop?.classList.remove('open');
    modal?.classList.remove('open');
  } else {
    backdrop?.classList.add('open');
    modal?.classList.add('open');
  }
}

function closeMobileMenu() {
  const backdrop = document.getElementById('mobileMenuBackdrop');
  const modal = document.getElementById('mobileMenuModal');
  backdrop?.classList.remove('open');
  modal?.classList.remove('open');
}

document.addEventListener('DOMContentLoaded', () => {
  updateThemeBtn();
  // Close mobile nav on link click
  document.querySelectorAll('nav a').forEach(a => {
    a.addEventListener('click', () => {
      document.querySelector('nav ul')?.classList.remove('open');
    });
  });
});

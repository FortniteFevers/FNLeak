// Shared utility functions
// Most functionality is inline in HTML for simplicity and to avoid dependencies

// Set active nav link
document.addEventListener('DOMContentLoaded', () => {
  const currentLocation = location.pathname.split('/').pop() || 'index.html';
  const navLinks = document.querySelectorAll('nav a');
  navLinks.forEach(link => {
    const href = link.getAttribute('href');
    if (href === currentLocation || (currentLocation === '' && href === 'index.html')) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });
});

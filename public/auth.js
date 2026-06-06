const CLERK_PUBLISHABLE_KEY = 'pk_test_ZGlzdGluY3QtbG9uZ2hvcm4tODAuY2xlcmsuYWNjb3VudHMuZGV2JA';

(function initClerkAuth() {
  const controls = document.getElementById('authControls');
  const userButton = document.getElementById('userButton');
  const signInBtn = document.getElementById('signInBtn');
  const signUpBtn = document.getElementById('signUpBtn');

  if (!controls || !userButton || !signInBtn || !signUpBtn) return;

  function showSignedOut() {
    controls.classList.remove('signed-in');
    controls.classList.add('signed-out');
  }

  function showSignedIn() {
    controls.classList.remove('signed-out');
    controls.classList.add('signed-in');
  }

  function loadClerkScript() {
    return new Promise((resolve, reject) => {
      if (window.Clerk) {
        resolve(window.Clerk);
        return;
      }

      const script = document.createElement('script');
      script.async = true;
      script.crossOrigin = 'anonymous';
      script.dataset.clerkPublishableKey = CLERK_PUBLISHABLE_KEY;
      script.src = 'https://distinct-longhorn-80.clerk.accounts.dev/npm/@clerk/clerk-js@latest/dist/clerk.browser.js';
      script.onload = () => resolve(window.Clerk);
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }

  async function start() {
    try {
      const clerk = await loadClerkScript();
      await clerk.load();

      signInBtn.addEventListener('click', () => clerk.openSignIn());
      signUpBtn.addEventListener('click', () => clerk.openSignUp());

      if (clerk.user) {
        showSignedIn();
        clerk.mountUserButton(userButton);
      } else {
        showSignedOut();
      }

      clerk.addListener(({ user }) => {
        if (user) {
          showSignedIn();
          clerk.mountUserButton(userButton);
        } else {
          userButton.innerHTML = '';
          showSignedOut();
        }
      });
    } catch (error) {
      console.warn('Clerk auth failed to load:', error);
      showSignedOut();
    }
  }

  start();
})();

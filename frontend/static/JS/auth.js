import { signIn, signUp, signOut } from './api-call.js';
import { SIGNIN_URL, SIGNUP_URL, SIGNOUT_URL } from './constants.js';
import { checkAuthState, tokenIsValid } from './auth-helper-fun.js';

document.addEventListener('DOMContentLoaded', () => {
    // Initial check to set the correct UI state on page load
    checkAuthState();

    // Helper utility to safely reset message elements
    const resetMessage = (element) => {
        if (!element) return;
        element.innerText = "";
        element.style.color = "black";
    };

    // === SIGNIN FORM SECTION ===
    const signinForm = document.getElementById('signin-form');
    if (signinForm) {
        const signinBtn = signinForm.querySelector('button[type="submit"]');
        const signinMessage = document.getElementById('signin-message');

        signinForm.addEventListener('submit', async (event) => {
            event.preventDefault(); // Prevent page reload

            const username = document.getElementById('signin-username').value.trim();
            const password = document.getElementById('signin-password').value;

            resetMessage(signinMessage);

            try {
                // Disable button to prevent double-clicks
                if (signinBtn) signinBtn.disabled = true;

                const response = await signIn(username, password, SIGNIN_URL);

                if (response.success) {
                    signinMessage.style.color = "green";
                    signinMessage.innerText = response.message;

                    // Securely store tokens if they exist in the envelope
                    if (response.content?.access_token && response.content?.refresh_token) {
                        localStorage.setItem('access_token', response.content.access_token);
                        localStorage.setItem('refresh_token', response.content.refresh_token);
                    }

                    // Redirect to dashboard after a brief delay
                    setTimeout(() => { window.location.href = '/'; }, 1000);
                } else {
                    signinMessage.style.color = "red";
                    signinMessage.innerText = response.message;
                    if (signinBtn) signinBtn.disabled = false; // Re-enable on failure
                }
            } catch (error) {
                signinMessage.style.color = "darkred";
                signinMessage.innerText = "Unable to connect to the authentication server. Please try again later.";
                console.error("Network Error Details:", error);
                if (signinBtn) signinBtn.disabled = false; // Re-enable on network error
            }
        });
    }

    // === SIGNUP FORM SECTION ===
    const signupForm = document.getElementById('signup-form');
    if (signupForm) {
        const signupBtn = signupForm.querySelector('button[type="submit"]');
        const signupMessage = document.getElementById('signup-message');

        signupForm.addEventListener('submit', async (event) => {
            event.preventDefault(); // Prevent page reload

            const username = document.getElementById('signup-username').value.trim();
            const email = document.getElementById('signup-email').value;
            const password = document.getElementById('signup-password').value;
            const confirmPassword = document.getElementById('signup-confirm-password').value;

            resetMessage(signupMessage);

            // Local validation rule check
            if (password !== confirmPassword) {
                signupMessage.style.color = "red";
                signupMessage.innerText = "Passwords do not match!";
                return;
            }

            try {
                // Disable button to prevent double-clicks
                if (signupBtn) signupBtn.disabled = true;

                const response = await signUp(username, password, email, SIGNUP_URL);

                if (response.success) {
                    signupMessage.style.color = "green";
                    signupMessage.innerText = response.message;

                    // Swap modals after a short delay
                    setTimeout(() => {
                        const closeSignupBtn = document.getElementById('closeSignup');
                        if (closeSignupBtn) closeSignupBtn.click();

                        const openSigninBtn = document.getElementById('openSigninBtn');
                        if (openSigninBtn) openSigninBtn.click();
                    }, 1500);
                } else {
                    signupMessage.style.color = "red";
                    signupMessage.innerText = response.message;
                    if (signupBtn) signupBtn.disabled = false; // Re-enable on failure
                }
            } catch (error) {
                signupMessage.style.color = "darkred";
                signupMessage.innerText = "System error: Unable to complete your registration right now.";
                console.error("Signup network error details:", error);
                if (signupBtn) signupBtn.disabled = false; // Re-enable on network error
            }
        });
    }

    // === LOGOUT SECTION ===
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async () => {
            const validToken = await tokenIsValid();

            if (validToken) {
                const accessToken = localStorage.getItem('access_token');

                try {
                    // Sync logout status with backend
                    const response = await signOut(accessToken, SIGNOUT_URL);

                    if (response.success) {
                        console.log("Server session cleared cleanly.");
                    } else {
                        console.warn("Server-side signout returned an error envelope:", response.message);
                    }
                } catch (error) { // Fixed capitalized standard error object naming here
                    console.error("Network failure during server signout sync:", error);
                }
            }

            // Always clear local tokens regardless of API success/failure
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');

            // Redirect to home page
            window.location.href = '/';
        });
    }
});
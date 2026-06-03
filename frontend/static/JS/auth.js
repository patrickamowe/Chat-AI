import { signIn, signUp } from './api-call.js';
import { SIGNIN_URL, SIGNUP_URL } from './constants.js';

document.addEventListener('DOMContentLoaded', () => {
    const signinForm = document.getElementById('signin-form');
    const signupForm = document.getElementById('signup-form');

    
    if (signinForm) {
        signinForm.addEventListener('submit', async (event) => {
            event.preventDefault(); // Prevent page reload on form submission

            const username = document.getElementById('signin-username').value.trim();
            const password = document.getElementById('signin-password').value;
            const signinMessage = document.getElementById('signin-message');

            // Reset UI states
            signinMessage.innerText = "";
            signinMessage.style.color = "black";

            try {
                const response = await signIn(username, password, SIGNIN_URL);

                if (response.success) {
                    // --- SUCCESS FLOW (UserLoginSuccessEnvelope) ---
                    signinMessage.style.color = "green";
                    signinMessage.innerText = response.message;

                    // Securely store fresh rotating tokens
                    localStorage.setItem('access_token', response.content.access_token);
                    localStorage.setItem('refresh_token', response.content.refresh_token);
                    
                    // Redirect to home dashboard after a brief delay
                    setTimeout(() => { window.location.href = '/'; }, 1000);

                } else {
                    // --- CONTROLLED FAILURE FLOW (APIFailureEnvelope) ---
                    signinMessage.style.color = "red";
                    signinMessage.innerText = response.message;
                }
                
            } catch (error) {
                // --- UNCONTROLLED NETWORK FAILURE FLOW ---
                signinMessage.style.color = "darkred";
                signinMessage.innerText = "Unable to connect to the authentication server. Please try again later.";
                console.error("Network Error Details:", error);
            }
        });
    }

    
    if (signupForm) {
        signupForm.addEventListener('submit', async (event) => {
            event.preventDefault(); // Prevent page reload on form submission

            const username = document.getElementById('signup-username').value.trim();
            const email = document.getElementById('signup-email').value;
            const password = document.getElementById('signup-password').value;
            const confirmPassword = document.getElementById('signup-confirm-password').value;
            const signupMessage = document.getElementById('signup-message');

            // Reset UI states
            signupMessage.innerText = "";
            signupMessage.style.color = "black";

            // Local validation rule check
            if (password !== confirmPassword) {
                signupMessage.style.color = "red";
                signupMessage.innerText = "Passwords do not match!";
                return;
            }

            try {
                const response = await signUp(username, password, email, SIGNUP_URL);

                if (response.success) {
                    // --- SUCCESS FLOW (UserRegistrationSuccessEnvelope) ---
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
                    // --- CONTROLLED FAILURE FLOW (APIFailureEnvelope) ---
                    // FIXED: Changed data.message to response.message
                    signupMessage.style.color = "red";
                    signupMessage.innerText = response.message; 
                }

            } catch (error) {
                // --- UNCONTROLLED NETWORK FAILURE FLOW ---
                signupMessage.style.color = "darkred";
                signupMessage.innerText = "System error: Unable to complete your registration right now.";
                console.error("Signup network error details:", error);
            }
        });
    }
});
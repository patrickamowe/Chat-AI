import { signIn, signUp, signOut} from './api-call.js';
import { SIGNIN_URL, SIGNUP_URL, SIGNOUT_URL } from './constants.js';
import { checkAuthState , tokenIsValid} from './helper-fun.js';


document.addEventListener('DOMContentLoaded', () => {
    // Initial check to set the correct UI state on page load
    checkAuthState();

    const signinForm = document.getElementById('signin-form');
    const signupForm = document.getElementById('signup-form');
    const logoutBtn = document.getElementById('logout-btn');

    
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

                    // Securely store tokens in localStorage for session management
                    // store only if the response contains the expected tokens
                    if (
                        response.content 
                        && response.content.access_token 
                        && response.content.refresh_token
                    ) {

                        localStorage.setItem('access_token', response.content.access_token);
                        localStorage.setItem('refresh_token', response.content.refresh_token);
                        
                    }

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

    if (logoutBtn) {
        logoutBtn.addEventListener('click', async () => {
            // Make API call to invalidate the refresh token and access token on the server 
            const validToken = await tokenIsValid();
            
            if (validToken) {
                const accessToken = localStorage.getItem('access_token');
                
                try {
                    // Make API call to invalidate the refresh token and access token on the server
                    const response = await signOut(accessToken, SIGNOUT_URL);
                    
                    if (response.success) {
                        console.log("Server session cleared cleanly.");
                    } else {
                        console.warn("Server-side signout returned an error envelope:", response.message);
                    }
                } catch (Error) {
                    // Log the error but continue logging the user out locally anyway
                    console.error("Network failure during server signout sync:", Error);
                }
            }

            // Always clear tokens from localStorage to log the user out on the client side
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            
            // Redirect to home page after logout
            window.location.href = '/';
        });
    }
});
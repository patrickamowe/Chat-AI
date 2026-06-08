// auth-state.js
import { VALIDATE_TOKEN_URL, REFRESH_TOKEN_URL, USER_INFO_URL } from './constants.js';
import { validateAccessToken, refreshToken, getUserInfo } from './api-call.js';


function updateUIState(isLoggedIn) {
    // This function updates the UI based on 
    // the user's authentication state.
    
    const body = document.body;
    if (isLoggedIn) {
        body.classList.add('user-logged-in');
        body.classList.remove('user-logged-out');
    } else {
        body.classList.add('user-logged-out');
        body.classList.remove('user-logged-in');
    }
}

async function tokenIsValid() {
    // This function validates the current access token with the backend.
    // If the access token is expired, it attempts to refresh it using the refresh token.
    // Returns true if the token is valid (or successfully refreshed), false otherwise.

    const accessToken = localStorage.getItem('access_token');
    const refreshTokenStr = localStorage.getItem('refresh_token');

    if (accessToken) {
        const accessResponse = await validateAccessToken(accessToken, VALIDATE_TOKEN_URL);

        if (!accessResponse.success) {
            // Access token is invalid or expired. Try refreshing it.
            if (refreshTokenStr) {
                const refreshResponse = await refreshToken(refreshTokenStr, REFRESH_TOKEN_URL);
                
                if (refreshResponse.success) {
                    // Successfully refreshed the access token. Update storage and return valid.
                    localStorage.setItem('access_token', refreshResponse.content.access_token);
                    return true;
                } else {
                    // Refresh token is also invalid or expired. Clear storage and return invalid.
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    return false;
                }
            } else {
                // No refresh token available. Clear access token and return invalid.
                localStorage.removeItem('access_token');
                return false;
            }
        }

        // Access token is valid.
        return true;
    }

    // No access token found. User is not authenticated.
    return false;
}

async function checkAuthState() {
    // This function checks the user's authentication state 
    // and updates the UI accordingly.

    const isLoggedIn = await tokenIsValid();
    updateUIState(isLoggedIn);

}

async function userDetails() {
    // This function fetches user details from the backend 
    // and returns the user information if the user is authenticated, or null if not.

    const isLoggedIn = await tokenIsValid();
    if (isLoggedIn) {
        const accessToken = localStorage.getItem('access_token');
        const response = await getUserInfo(accessToken, USER_INFO_URL);

        if (response.success) {
            // Extract user information and set the variables
                const userName = response.content.username;
                const firstLetter = userName.charAt(0).toUpperCase();
                const email = response.content.email;
                
            return {
                username: userName,
                firstLetter: firstLetter,
                email: email
            };
        } else {
            console.error("Failed to fetch user info:", response.message);
            return null;
        }

    } else {
        console.warn("User is not authenticated. Cannot fetch user details.");
        return null;
    }
}

export { checkAuthState, tokenIsValid, userDetails };
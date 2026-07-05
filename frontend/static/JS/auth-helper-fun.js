import { refreshToken, validateAccessToken } from "./api-call.js";
import { REFRESH_TOKEN_URL, VALIDATE_TOKEN_URL } from "./constants.js";

/**
 * Checks if the user is logged in and returns their temporary login key if they are.
 *
 * @returns {Promise<string|null>} The secret login key if logged in, or null if not.
 */
async function getAuthenticatedToken() {
    const isLoggedIn = await tokenIsValid();
    if (!isLoggedIn) return null;
    return localStorage.getItem('access_token');
}

/**
 * Updates the appearance of the page based on whether the user is logged in or out.
 *
 * @param {boolean} isLoggedIn - True if the user is logged in, false if they are logged out.
 * @returns {void} This function updates the page styles directly and does not return a value.
 */
function updateUIState(isLoggedIn) {
    const body = document.body;
    body.classList.toggle('user-logged-in', isLoggedIn);
    body.classList.toggle('user-logged-out', !isLoggedIn);
}

/**
 * Checks if the user's login keys are still valid, and automatically attempts to renew them if needed.
 *
 * @returns {Promise<boolean>} True if the user has a working login session, false if they are logged out.
 */
async function tokenIsValid() {
    const accessToken = localStorage.getItem('access_token');
    const refreshTokenStr = localStorage.getItem('refresh_token');

    // 1. If an access key exists, check if it is still active and valid
    if (accessToken) {
        const accessResponse = await validateAccessToken(accessToken, VALIDATE_TOKEN_URL);
        if (accessResponse.success) return true;
    }

    // 2. If the access key is missing or expired, try using the refresh key to get a new one
    if (refreshTokenStr) {
        const refreshResponse = await refreshToken(refreshTokenStr, REFRESH_TOKEN_URL);

        if (refreshResponse.success) {
            localStorage.setItem('access_token', refreshResponse.content.access_token);
            return true;
        }
    }

    // 3. If both keys fail or do not exist, clear the browser storage entirely
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    return false;
}

/**
 * Verifies the user's current login status and updates the look of the webpage to match.
 *
 * @returns {Promise<void>} Resolves once the login status is confirmed and the webpage interface updates.
 */
async function checkAuthState() {
    const isLoggedIn = await tokenIsValid();
    updateUIState(isLoggedIn);
}

export {
    checkAuthState,
    tokenIsValid,
    updateUIState,
    getAuthenticatedToken,
};
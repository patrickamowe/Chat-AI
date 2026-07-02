import { refreshToken, validateAccessToken } from "./api-call.js";
import { REFRESH_TOKEN_URL, VALIDATE_TOKEN_URL } from "./constants.js";

function updateUIState(isLoggedIn) {
    const body = document.body;
    body.classList.toggle('user-logged-in', isLoggedIn);
    body.classList.toggle('user-logged-out', !isLoggedIn);
}

async function tokenIsValid() {
    const accessToken = localStorage.getItem('access_token');
    const refreshTokenStr = localStorage.getItem('refresh_token');

    // 1. If an access token exists, try to validate it
    if (accessToken) {
        const accessResponse = await validateAccessToken(accessToken, VALIDATE_TOKEN_URL);
        if (accessResponse.success) return true;
    }

    // 2. If access token is missing or invalid, try using the refresh token
    if (refreshTokenStr) {
        const refreshResponse = await refreshToken(refreshTokenStr, REFRESH_TOKEN_URL);

        if (refreshResponse.success) {
            localStorage.setItem('access_token', refreshResponse.content.access_token);
            return true;
        }
    }

    // 3. If both tokens failed or are missing, clear storage and log out
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    return false;
}

async function checkAuthState() {
    const isLoggedIn = await tokenIsValid();
    updateUIState(isLoggedIn);
}

export {
    checkAuthState,
    tokenIsValid,
    updateUIState
};
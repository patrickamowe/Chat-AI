import {refreshToken, validateAccessToken} from "./api-call.js";
import {REFRESH_TOKEN_URL, VALIDATE_TOKEN_URL} from "./constants.js";

function updateUIState(isLoggedIn) {
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
    const accessToken = localStorage.getItem('access_token');
    const refreshTokenStr = localStorage.getItem('refresh_token');

    if (accessToken) {
        const accessResponse = await validateAccessToken(accessToken, VALIDATE_TOKEN_URL);

        if (!accessResponse.success) {
            if (refreshTokenStr) {
                const refreshResponse = await refreshToken(refreshTokenStr, REFRESH_TOKEN_URL);

                if (refreshResponse.success) {
                    localStorage.setItem('access_token', refreshResponse.content.access_token);
                    return true;
                } else {
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    return false;
                }
            } else {
                localStorage.removeItem('access_token');
                return false;
            }
        }
        return true;
    }
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
}
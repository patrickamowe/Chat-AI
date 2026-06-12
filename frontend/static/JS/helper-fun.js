import {
    VALIDATE_TOKEN_URL,
    REFRESH_TOKEN_URL,
    USER_INFO_URL,
    CONVERSATIONS_URL,
    CONVERSATION_URL,
    MESSAGE_URL
} from './constants.js';
import {
    chat,
    validateAccessToken,
    refreshToken,
    getUserInfo,
    getConversations,
    getConversation,
    deleteConversations,
    deleteConversation
} from './api-call.js';


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

async function userDetails() {
    const isLoggedIn = await tokenIsValid();
    if (isLoggedIn) {
        const accessToken = localStorage.getItem('access_token');
        const response = await getUserInfo(accessToken, USER_INFO_URL);

        if (response.success) {
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

async function userChat(query, conversation_id = null, ) {
    const isLoggedIn = await tokenIsValid();
    const accessToken = localStorage.getItem("access_token")
    let response;

    if (isLoggedIn) {
        response = await chat(query, MESSAGE_URL, accessToken, conversation_id);
    } else {
        response = await chat(query, MESSAGE_URL, accessToken);
    }

    if (response && response.success) {
        return response.content;
    } else {
        console.error("Failed to get user chat:", response?.message || "Unknown API error");
        return null;
    }
}

async function getUserConversations() {
    const isLoggedIn = await tokenIsValid();
    if (isLoggedIn) {
        const accessToken = localStorage.getItem("access_token");
        const response = await getConversations(accessToken, CONVERSATIONS_URL);

        if (response.success) {
            return response.content;
        } else {
            console.error("Failure to fetch user conversations:", response.message);
            return null;
        }
    } else {
        console.warn("User is not authenticated. Cannot fetch user conversations.");
        return null;
    }
}

async function deleteUserConversations() {
    const isLoggedIn = await tokenIsValid();
    if (isLoggedIn) {
        const accessToken = localStorage.getItem("access_token");
        const response = await deleteConversations(accessToken, CONVERSATIONS_URL);

        if (response.success) {
            return response.message;
        } else {
            console.error("Failure to delete user conversations:", response.message);
            return null;
        }
    } else {
        console.warn("User is not authenticated. Cannot delete user conversations.");
        return null;
    }
}

async function getUserConversation(conversation_id) {
    const isLoggedIn = await tokenIsValid();
    if (isLoggedIn) {
        const accessToken = localStorage.getItem("access_token");
        const URL = `${CONVERSATION_URL}/${conversation_id}`;
        const response = await getConversation(conversation_id, accessToken, URL);

        if (response.success) {
            return response.content;
        } else {
            console.error("Failure to fetch user conversation:", response.message);
            return null;
        }
    } else {
        console.warn("User is not authenticated. Cannot fetch user conversation.");
        return null;
    }
}

async function deleteUserConversation(conversation_id) {
    const isLoggedIn = await tokenIsValid();
    if (isLoggedIn) {
        const accessToken = localStorage.getItem("access_token");
        const URL = `${CONVERSATION_URL}/${conversation_id}`;
        const response = await deleteConversation(conversation_id, accessToken, URL);

        if (response.success) {
            return response.message;
        } else {
            console.error("Failure to delete user conversation:", response.message);
            return null;
        }
    } else {
        console.warn("User is not authenticated. Cannot delete user conversation.");
        return null;
    }
}

export {
    checkAuthState,
    tokenIsValid,
    userDetails,
    getUserConversations,
    deleteUserConversations,
    getUserConversation,
    deleteUserConversation,
    userChat
};
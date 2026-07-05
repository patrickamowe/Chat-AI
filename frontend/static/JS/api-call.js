/**
 * Logs a user into their account.
 *
 * @param {string} username - The user's account username.
 * @param {string} password - The user's account password.
 * @param {string} url - The web address to send the login request to.
 * @returns {Promise<object>} The server response containing login tokens or error messages.
 */
async function signIn(username, password, url) {
    const data = {
        username: username,
        password: password
    };

    const request = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });

    return await request.json();
}

/**
 * Logs a user out of their account and deactivates their current temporary access key.
 *
 * @param {string} access_token - The current secret key validating the user's session.
 * @param {string} url - The web address to send the logout request to.
 * @returns {Promise<object>} The server confirmation message.
 */
async function signOut(access_token, url) {
    const request = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${access_token}`
        }
    });

    return await request.json();
}

/**
 * Gets account information for the user, such as their username and email.
 *
 * @param {string} access_token - The current secret key validating the user's session.
 * @param {string} url - The web address to request the profile information from.
 * @returns {Promise<object>} The user's account information profile.
 */
async function getUserInfo(access_token, url) {
    const request = await fetch(url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${access_token}`
        }
    });

    return await request.json();
}

/**
 * Updates the user's profile information with a new username or email address.
 *
 * @param {string} username - The updated username.
 * @param {string} email - The updated email address.
 * @param {string} access_token - The current secret key validating the user's session.
 * @param {string} url - The web address to send the updated information to.
 * @returns {Promise<object>} The updated account profile details from the server.
 */
async function updateUserInfo(username, email, access_token, url){
    const data = {
        username: username,
        email: email,
    }

    const request = await fetch(url, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${access_token}`
        },
        body: JSON.stringify(data)
    });

    return await request.json()
}

/**
 * Permanently deletes the user's account from the system.
 *
 * @param {string} access_token - The current secret key validating the user's session.
 * @param {string} url - The web address to send the account closure request to.
 * @returns {Promise<object>} The server confirmation message of the permanent closure.
 */
async function deleteUserAcc(access_token, url) {
    const request = await fetch(url, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${access_token}`
        }
    });

    return await request.json()
}

/**
 * Changes the user's account password to a new one.
 *
 * @param {string} password - The user's current password.
 * @param {string} new_password - The brand new password to save.
 * @param {string} access_token - The current secret key validating the user's session.
 * @param {string} url - The web address to send the password update request to.
 * @returns {Promise<object>} The server confirmation status.
 */
async function changeUserPassword(password, new_password, access_token, url){
    const data = {
        password: password,
        new_password: new_password
    }

    const request = await fetch(url, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${access_token}`
        },
        body: JSON.stringify(data)
    });

    return await request.json()
}

/**
 * Creates a brand new user account in the system.
 *
 * @param {string} username - The desired unique username.
 * @param {string} password - The new account password.
 * @param {string} email - The user's email address.
 * @param {string} url - The web address to send the sign-up request to.
 * @returns {Promise<object>} The newly created user account details.
 */
async function signUp(username, password, email, url) {
    const data = {
        username: username,
        password: password,
        email: email
    };

    const request = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });

    return await request.json();
}

/**
 * Requests a fresh access key using a long-lasting refresh key when the current session expires.
 *
 * @param {string} refresh_token - The special background key used to maintain login states.
 * @param {string} url - The web address to swap the tokens at.
 * @returns {Promise<object>} The new short-term access key details.
 */
async function refreshToken(refresh_token, url) {
    const data = {
        refresh_token: refresh_token
    };

    const request = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });

    return await request.json();
}

/**
 * Checks with the server to confirm if the user's current session key is valid and working.
 *
 * @param {string} access_token - The current secret key validating the user's session.
 * @param {string} url - The web address to test the key's validity.
 * @returns {Promise<object>} True or false confirmation data from the server.
 */
async function validateAccessToken(access_token, url) {
    const data = {
        access_token: access_token
    };

    const request = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    });

    return await request.json();
}

/**
 * Sends a message prompt to the Gemini AI and returns its text reply.
 *
 * @param {string} query - The question or prompt typed by the user.
 * @param {string} url - The web address of the AI message handling endpoint.
 * @param {string|null} [access_token=null] - The current secret key validating the user's session.
 * @param {string|null} [conversation_id=null] - The ID of an ongoing chat thread, if continuing a conversation.
 * @returns {Promise<object>} The server response containing the AI's answer.
 */
async function chat(query, url, access_token=null, conversation_id=null) {
    let data;

    if (conversation_id) {
        data = {
            user_prompt: query,
            conversation_id: conversation_id
        };
    } else {
        data = {
            user_prompt: query
        }
    }

    const request = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${access_token}`
        },
        body: JSON.stringify(data)
    });

    return await request.json();
}

/**
 * Gets all stored chat messages for one specific conversation thread.
 *
 * @param {string} access_token - The current secret key validating the user's session.
 * @param {string} url - The web address containing this specific chat thread's history.
 * @returns {Promise<object>} An object containing the list of past text messages.
 */
async function getConversation(access_token, url) {
    const request = await fetch(url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${access_token}`
        },
    });

    return await request.json();
}

/**
 * Deletes a single conversation thread from the user's history list.
 *
 * @param {string} access_token - The current secret key validating the user's session.
 * @param {string} url - The web address linked to this specific conversation thread.
 * @returns {Promise<object>} The server confirmation status message.
 */
async function deleteConversation(access_token, url) {
    const request = await fetch(url, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${access_token}`
        },
    });

    return await request.json();
}

/**
 * Changes the visible title name of a single conversation thread.
 *
 * @param {string} title - The brand new display name for the conversation thread.
 * @param {string} access_token - The current secret key validating the user's session.
 * @param {string} url - The web address linked to this specific conversation thread.
 * @returns {Promise<object>} The server confirmation status message.
 */
async function renameConversation(title, access_token, url) {
    const data = {title: title}

    const request = await fetch(url, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${access_token}`
        },
        body: JSON.stringify(data)
    });

    return await request.json();
}

/**
 * Gets a basic list overview of all past chat conversations belonging to the user.
 *
 * @param {string} access_token - The current secret key validating the user's session.
 * @param {string} url - The web address hosting the total conversation list index.
 * @returns {Promise<object>} A list containing titles and metadata for past user logs.
 */
async function getConversations(access_token, url) {
    const request = await fetch(url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${access_token}`
        }
    });

    return await request.json();
}

/**
 * Clears and deletes every conversation thread belonging to the user all at once.
 *
 * @param {string} access_token - The current secret key validating the user's session.
 * @param {string} url - The web address hosting the total conversation list index.
 * @returns {Promise<object>} The server confirmation status message.
 */
async function deleteConversations(access_token, url) {
    const request = await fetch(url, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${access_token}`
        }
    });

    return await request.json();
}

export {
    signIn,
    signOut,
    getUserInfo,
    signUp,
    refreshToken,
    validateAccessToken,
    chat,
    getConversations,
    deleteConversations,
    getConversation,
    deleteConversation,
    changeUserPassword,
    updateUserInfo,
    deleteUserAcc,
    renameConversation
};
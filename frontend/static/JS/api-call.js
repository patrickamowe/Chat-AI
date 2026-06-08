async function signIn(username, password, url) {
    // This function is used by the frontend to log 
    // the user into their account.

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

    const response = await request.json();

    return response;
}


async function signOut(access_token, url) {
    // This function is used by the frontend to log the user out of 
    // their account. It invalidates the user's current access token.

    const request = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${access_token}`
        }
    });

    // Parse our uniform backend envelope
    const response = await request.json();

    return response;
}


async function getUserInfo(access_token, url) {
    // This function is used by the frontend to get the current user's 
    // information, such as their username and email.

    const request = await fetch(url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${access_token}`
        }
    });

    const response = await request.json();

    return response;
}

async function signUp(username, password, email, url) {
    // This function is used by the frontend to create
    // a new user account. It sends the user's

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

    const response = await request.json();

    return response;
}

async function refreshToken(refresh_token, url) {
    // This function is used by the frontend to get a fresh access 
    // token when the current one expires, using the refresh token

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

    const response = await request.json();

    return response;
}

async function validateAccessToken(access_token, url) {
    // This function is used by the frontend to check if 
    // the user's current access token is still valid

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

    const response = await request.json();

    return response;
}

async function chat(message, access_token, url) {

    const data = {
        message: message
    };

    const request = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${access_token}`
        },
        body: JSON.stringify(data)
    });

    const response = await request.json();

    return response;

}

async function getConversation(conversation_id, access_token, url) {
    // This function is used by the frontend to get a specific user conversation.

    const data = {
        conversation_id: conversation_id
    };

    const request = await fetch(url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${access_token}`
        },
        body: JSON.stringify(data)
    });

    const response = await request.json();

    return response;
}

async function deleteConversation(conversation_id, access_token, url) {
    // This function is used by the frontend to delete a specific user conversation.

    const data = {
        conversation_id: conversation_id
    };

    const request = await fetch(url, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${access_token}`
        }
    });

    const response = await request.json();

    return response;
}

async function getConversations(access_token, url) {
    // This function is used by the frontend to get all the user conversations.

    const request = await fetch(url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${access_token}`
        }
    });

    const response = await request.json();

    return response;
}

async function deleteConversations(access_token, url) {
    // This function is used by the frontend to delete all the user conversations.

    const request = await fetch(url, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${access_token}`
        }
    });

    const response = await request.json();

    return response;
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
};

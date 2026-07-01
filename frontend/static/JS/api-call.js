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

    return await request.json();
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
    return await request.json();
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

    return await request.json();
}

async function updateUserInfo(username, email, access_token, url){
    // The function is use by the frontend to
    // update user info.

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

async function deleteUserAcc(access_token, url) {
    // The function is use by the frontend to
    // permanently delete user account

    const request = await fetch(url, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${access_token}`
        }
    });

    return await request.json()
}

async function changeUserPassword(password, new_password, access_token, url){
    //The function is use by the frontend to
    // change user password.

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

    return await request.json();
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

    return await request.json();
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

    return await request.json();
}

async function chat(query, url, access_token, conversation_id=null) {
    // This function is use by the frontend to get the
    // Gemini response
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

async function getConversation(conversation_id, access_token, url) {
    // This function is used by the frontend to get a specific user conversation.

    const request = await fetch(url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${access_token}`
        },
    });

    return await request.json();
}

async function deleteConversation(conversation_id, access_token, url) {
    // This function is used by the frontend to delete a specific user conversation.

    const request = await fetch(url, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${access_token}`
        },
    });

    return await request.json();
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

    return await request.json();
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
    deleteUserAcc
};

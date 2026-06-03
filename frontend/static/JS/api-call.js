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

    const response = await request.json();

    return response;
}


async function signOut(access_token, url) {
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


async function getUserInfo(access_token, user_id, url) {

    // Append the user_id to the URL
    url = `${url}/${user_id}`;

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

    

export { signIn, signOut, getUserInfo, signUp, refreshToken };

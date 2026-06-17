import {getUserInfo} from "./api-call.js";
import {USER_INFO_URL} from "./constants.js";
import {tokenIsValid} from "./auth-helper-fun.js";

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

export {
    userDetails
}
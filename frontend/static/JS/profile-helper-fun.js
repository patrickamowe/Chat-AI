import {getUserInfo, updateUserInfo, changeUserPassword, deleteUserAcc} from "./api-call.js";
import {USER_INFO_URL, CHANGE_PASSWORD_URL} from "./constants.js";
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

async function updateUserDetails(username, email){
    const isLoggedIn = await tokenIsValid();
    if (isLoggedIn) {
        const accessToken = localStorage.getItem('access_token');
        const response = await updateUserInfo(username, email, accessToken, USER_INFO_URL);

        if (response.success) {
            return {status: true, message:response.message};
        } else {
            console.error("Failed to update user info:", response.message);
            return {status: false , message:response.message};
        }
    } else {
        console.warn("User is not authenticated. Cannot update user details.");
        return {
            status:false,
            message: "User is not authenticated. Cannot update user details."
        };
    }
}

async function changePassword(password, new_password) {
    const isLoggedIn = await tokenIsValid();
    if (isLoggedIn) {
        const accessToken = localStorage.getItem('access_token');
        const response = await changeUserPassword(password, new_password, accessToken, CHANGE_PASSWORD_URL)

        if (response.success) {
           return {status: true, message:response.message};
        } else {
            console.error("Failed to change user password:", response.message);
            return {status: false , message:response.message};
        }
    } else {
        console.warn("User is not authenticated. Cannot change user password.");
        return {
            status:false,
            message: "User is not authenticated. Cannot change user password."
        };
    }
}

async function deleteAcc() {
    const isLoggedIn = await tokenIsValid();

    if (isLoggedIn) {
        const accessToken = localStorage.getItem('access_token');
        const response = await deleteUserAcc(accessToken, USER_INFO_URL);

        if (response.success) {
            return {status: true, message:response.message};
        } else {
             console.error("Failed to delete user account:", response.message);
            return {status: false , message:response.message};
        }
    } else {
        console.warn("User is not authenticated. Cannot delete user account.");
        return {
            status:false,
            message: "User is not authenticated. Cannot delete user account."
        };
    }
}

export {
    userDetails,
    updateUserDetails,
    changePassword,
    deleteAcc
}
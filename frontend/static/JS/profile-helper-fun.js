import { getUserInfo, updateUserInfo, changeUserPassword, deleteUserAcc } from "./api-call.js";
import { USER_INFO_URL, CHANGE_PASSWORD_URL } from "./constants.js";
import { tokenIsValid } from "./auth-helper-fun.js";

// Helper function to handle boilerplate auth checks and token retrieval
async function getAuthenticatedToken() {
    const isLoggedIn = await tokenIsValid();
    if (!isLoggedIn) return null;
    return localStorage.getItem('access_token');
}

async function userDetails() {
    const accessToken = await getAuthenticatedToken();
    if (!accessToken) {
        console.warn("User is not authenticated. Cannot fetch user details.");
        return null;
    }

    try {
        const response = await getUserInfo(accessToken, USER_INFO_URL);

        if (response?.success) {
            const userName = response.content.username;
            return {
                username: userName,
                firstLetter: userName.charAt(0).toUpperCase(),
                email: response.content.email
            };
        }

        console.error("Failed to fetch user info:", response?.message);
        return null;
    } catch (error) {
        console.error("Network error while fetching user info:", error);
        return null;
    }
}

async function updateUserDetails(username, email) {
    const accessToken = await getAuthenticatedToken();
    if (!accessToken) {
        return { status: false, message: "User is not authenticated. Cannot update user details." };
    }

    try {
        const response = await updateUserInfo(username, email, accessToken, USER_INFO_URL);

        if (response?.success) {
            return { status: true, message: response.message };
        }

        console.error("Failed to update user info:", response?.message);
        return { status: false, message: response?.message };
    } catch (error) {
        console.error("Network error while updating user info:", error);
        return { status: false, message: "A network error occurred. Please try again." };
    }
}

async function changePassword(password, new_password) {
    const accessToken = await getAuthenticatedToken();
    if (!accessToken) {
        return { status: false, message: "User is not authenticated. Cannot change user password." };
    }

    try {
        const response = await changeUserPassword(password, new_password, accessToken, CHANGE_PASSWORD_URL);

        if (response?.success) {
            return { status: true, message: response.message };
        }

        console.error("Failed to change user password:", response?.message);
        return { status: false, message: response?.message };
    } catch (error) {
        console.error("Network error while changing password:", error);
        return { status: false, message: "A network error occurred. Please try again." };
    }
}

async function deleteAcc() {
    const accessToken = await getAuthenticatedToken();
    if (!accessToken) {
        return { status: false, message: "User is not authenticated. Cannot delete user account." };
    }

    try {
        const response = await deleteUserAcc(accessToken, USER_INFO_URL);

        if (response?.success) {
            return { status: true, message: response.message };
        }

        console.error("Failed to delete user account:", response?.message);
        return { status: false, message: response?.message };
    } catch (error) {
        console.error("Network error while deleting account:", error);
        return { status: false, message: "A network error occurred. Please try again." };
    }
}

export {
    userDetails,
    updateUserDetails,
    changePassword,
    deleteAcc
};
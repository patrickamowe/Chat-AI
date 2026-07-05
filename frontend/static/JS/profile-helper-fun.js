import { getUserInfo, updateUserInfo, changeUserPassword, deleteUserAcc } from "./api-call.js";
import { USER_INFO_URL, CHANGE_PASSWORD_URL } from "./constants.js";
import { getAuthenticatedToken } from "./auth-helper-fun.js";



/**
 * Gets the current logged-in user's profile details and formats their name.
 *
 * @returns {Promise<object|null>} An object with the username, first letter capitalized, and email, or null if it fails.
 */
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

/**
 * Updates the user's account name and email address on the server.
 *
 * @param {string} username - The new username to set.
 * @param {string} email - The new email address to set.
 * @returns {Promise<object>} An object showing whether the update succeeded and a message string.
 */
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

/**
 * Submits a request to change the user's password.
 *
 * @param {string} password - The current account password.
 * @param {string} new_password - The brand new password to save.
 * @returns {Promise<object>} An object showing whether the change succeeded and a message string.
 */
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

/**
 * Requests the permanent removal of the current user's account.
 *
 * @returns {Promise<object>} An object showing whether the deletion succeeded and a message string.
 */
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
import { userDetails, changePassword, updateUserDetails, deleteAcc } from './profile-helper-fun.js';

// --- 1. DOM Elements ---
const userUsername = document.getElementById("user-username");
const userEmail = document.getElementById("user-email");
const profileIcon = document.getElementById("navbar-profile-icon");
const profileAvatar = document.querySelector(".avatar"); // Using querySelector for a single element

const profileUsernameInput = document.getElementById("profile-username");
const profileEmailInput = document.getElementById("profile-email");

const editProfileForm = document.getElementById('edit-profile-form');
const editProfileMessage = document.getElementById('edit-profile-message');

const changePasswordForm = document.getElementById('change-password-form');
const changePasswordMessage = document.getElementById('change-password-message');

const deleteAccBtn = document.getElementById("delete-account-btn");

// --- 2. Initialize Profile Data ---
async function initProfile() {
    const userDetailsInfo = await userDetails();

    if (userDetailsInfo && userDetailsInfo.username && userDetailsInfo.email) {
        // Update display text
        if (userUsername) userUsername.innerText = userDetailsInfo.username;
        if (userEmail) userEmail.innerText = userDetailsInfo.email;

        // Update profile icons/avatars
        const firstLetter = userDetailsInfo.firstLetter || userDetailsInfo.username.charAt(0).toUpperCase();
        if (profileIcon) profileIcon.innerText = firstLetter;
        if (profileAvatar) profileAvatar.innerText = firstLetter;

        // Fill form inputs
        if (profileUsernameInput) profileUsernameInput.value = userDetailsInfo.username;
        if (profileEmailInput) profileEmailInput.value = userDetailsInfo.email;
    } else {
        console.error("User information is missing. Cannot display profile details.");
    }
}

// --- 3. Event Listeners ---

// Edit Profile Form
if (editProfileForm) {
    editProfileForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const username = profileUsernameInput.value;
        const email = profileEmailInput.value;

        const response = await updateUserDetails(username, email);

        if (response.status) {
            editProfileMessage.style.color = "green";
            editProfileMessage.innerText = response.message;

            // Give the user 1.5 seconds to read the success message before reloading
            setTimeout(() => window.location.reload(), 1500);
        } else {
            editProfileMessage.style.color = "red";
            editProfileMessage.innerText = response.message;
        }
    });
}

// Change Password Form
if (changePasswordForm) {
    changePasswordForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const password = document.getElementById('user-password').value;
        const new_password = document.getElementById('user-new-password').value;

        const response = await changePassword(password, new_password);

        if (response.status) {
            changePasswordMessage.style.color = "green";
            changePasswordMessage.innerText = response.message;

            // Clear inputs and wait briefly before reloading
            changePasswordForm.reset();
            setTimeout(() => window.location.reload(), 1500);
        } else {
            changePasswordMessage.style.color = "red";
            changePasswordMessage.innerText = response.message;
        }
    });
}

// Delete Account Action
if (deleteAccBtn) {
    deleteAccBtn.addEventListener('click', async () => {
        const confirmed = window.confirm("Are you absolutely sure you want to delete your account? This action cannot be undone.");

        if (!confirmed) return; // Exit if user clicks "Cancel"

        const response = await deleteAcc();
        if (response.status) {
            window.alert(response.message);
            setTimeout(() => { window.location.href = '/'; }, 1000);
        } else {
            window.alert(response.message);
            window.location.reload();
        }
    });
}

// Run initializer
initProfile();
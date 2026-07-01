import { userDetails, changePassword, updateUserDetails, deleteAcc} from './profile-helper-fun.js';

// Fetch user details and update the profile page
// with the user's username, email, and profile icon (first letter of username)
const userUsername = document.getElementById("user-username");
const userEmail = document.getElementById("user-email");
const profileIcon = document.getElementById("navbar-profile-icon");
const profileAvatar = document.getElementsByClassName("avatar")[0];
const userDetailsInfo = await userDetails();

if (
    userDetailsInfo 
    && userDetailsInfo.username 
    && userDetailsInfo.email 
    && userDetailsInfo.firstLetter
) {
    // Display the user's username and email on the profile page
    userUsername.innerText = userDetailsInfo.username;
    userEmail.innerText = userDetailsInfo.email;

    // Set the profile icon and avatar to the first letter of the username
    profileIcon.innerText = userDetailsInfo.firstLetter;
    profileAvatar.innerText = userDetailsInfo.firstLetter;

} else {
    console.error("User information is missing. Cannot display profile details.");
}

// Fill the Edit profile username and email input.
const profileUsernameInput = document.getElementById("profile-username");
const profileEmailInput = document.getElementById("profile-email");

if (profileEmailInput && profileUsernameInput) {
    if (userDetailsInfo
    && userDetailsInfo.username
    && userDetailsInfo.email
    ) {
        profileUsernameInput.value = userDetailsInfo.username
        profileEmailInput.value = userDetailsInfo.email
    } else {
         console.error("User information is missing. Cannot get user profile details.");
    }
}

// Edit user profile info e.g username and email
const editProfileForm = document.getElementById('edit-profile-form');
const editProfileMessage = document.getElementById('edit-profile-message')
if (editProfileForm) {
    editProfileForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevent page reload on form submission

        const username = document.getElementById("profile-username").value;
        const email = document.getElementById("profile-email").value;

        const response = await updateUserDetails(username, email);

        if (response.status){
            editProfileMessage.style.color = "green";
            editProfileMessage.innerText = response.message;

            // reload the current page
            window.location.reload();
        } else {
            editProfileMessage.style.color = "red";
            editProfileMessage.innerText = response.message;
        }
    });
}

//
const changePasswordForm = document.getElementById('change-password-form');
const changePasswordMessage = document.getElementById('change-password-message');
if (changePasswordForm) {
    changePasswordForm.addEventListener('submit', async (event) => {
        event.preventDefault() // Prevent page reload on form submission

        const password = document.getElementById('user-password').value;
        const new_password = document.getElementById('user-new-password').value;

        const response = await changePassword(password, new_password);

        if (response.status){
            changePasswordMessage.style.color = "green";
            changePasswordMessage.innerText = response.message;

            // reload the current page
            window.location.reload();
        } else {
            changePasswordMessage.style.color = "red";
            changePasswordMessage.innerText = response.message;
        }
    });
}

//
const deleteAccBtn = document.getElementById("delete-account-btn");
if (deleteAccBtn) {
    deleteAccBtn.addEventListener('click', async (event) => {
        window.alert("About to delete user Account. Cannot undo this action.");

        const response = await deleteAcc();
        if (response.status) {
            window.alert(response.message);

            // Redirect to home page after a brief delay
            setTimeout(() => { window.location.href = '/'; }, 1000);
        } else {
            // Alert fail message and reload the profile page
            window.alert(response.message);
            window.location.reload();
        }


    });
}
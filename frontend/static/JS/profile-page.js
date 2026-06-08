import { userDetails} from './helper-fun.js';

const userUsername = document.getElementById("user-username");
const userEmail = document.getElementById("user-email");
const profileIcon = document.getElementById("navbar-profile-icon");
const profileAvatar = document.getElementsByClassName("avatar")[0];

// Fetch user details and update the profile page
// with the user's username, email, and profile icon (first letter of username)

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

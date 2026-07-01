// Get DOM elements
const editProfileModal = document.getElementById('editProfileModal');
const changePasswordModal = document.getElementById('changePasswordModal');

const openEditProfileBtn = document.getElementById('edit-profile-btn');
const openChangePasswordBtn = document.getElementById('change-password-btn');

const closeEditProfile = document.getElementById('closeEditProfile');
const closeChangePassword = document.getElementById('closeChangePassword');

// Open Modals
openEditProfileBtn.onclick = () => editProfileModal.style.display = 'flex';
openChangePasswordBtn.onclick = () => changePasswordModal.style.display = 'flex';

// Close Modals using the 'X' button
closeEditProfile.onclick = () => editProfileModal.style.display = 'none';
closeChangePassword.onclick = () => changePasswordModal.style.display = 'none';

// Close Modals if user clicks anywhere outside the white box
window.onclick = (event) => {
    if (event.target === editProfileModal) editProfileModal.style.display = 'none';
    if (event.target === changePasswordModal) changePasswordModal.style.display = 'none';
}

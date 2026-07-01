// Get DOM elements
const signinModal = document.getElementById('signinModal');
const signupModal = document.getElementById('signupModal');

const openSigninBtn = document.getElementById('openSigninBtn');
const openSignupBtn = document.getElementById('openSignupBtn');
const loginBtn = document.getElementById('login-btn');

const closeSignin = document.getElementById('closeSignin');
const closeSignup = document.getElementById('closeSignup');

// Open Modals
openSigninBtn.onclick = () => signinModal.style.display = 'flex';
openSignupBtn.onclick = () => signupModal.style.display = 'flex';
loginBtn.onclick = () => signinModal.style.display = 'flex';

// Close Modals using the 'X' button
closeSignin.onclick = () => signinModal.style.display = 'none';
closeSignup.onclick = () => signupModal.style.display = 'none';

// Close Modals if user clicks anywhere outside the white box
window.onclick = (event) => {
    if (event.target === signinModal) signinModal.style.display = 'none';
    if (event.target === signupModal) signupModal.style.display = 'none';
}

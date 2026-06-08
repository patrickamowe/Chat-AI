import { userDetails} from './helper-fun.js';

// sidebar
const sidebarToggle = document.getElementById('sidebar-toggle');
const sidebar = document.getElementById('sidebar');


if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', (e) => {
        e.stopPropagation(); // Prevents instant closing
        sidebar.classList.toggle('show-sidebar');
    });

    // Close sidebar when clicking anywhere on the main chat interface
    document.getElementById('main-chat-area').addEventListener('click', () => {
        sidebar.classList.remove('show-sidebar');
    });
}else {
    console.warn("Sidebar toggle button or sidebar element not found. Sidebar functionality will not work.");
}
// end of sidebar

// profile icon
const userDetailsInfo = await userDetails();

// Check if userDetailsInfo and its firstLetter property 
// are available before trying to update the profile icon
if (userDetailsInfo && userDetailsInfo.firstLetter) {
    const profileIcon = document.getElementById('profile-icon');
    profileIcon.innerText = userDetailsInfo.firstLetter;
} else {
    console.warn("First letter of username is not available. Profile icon will not be displayed.");
}

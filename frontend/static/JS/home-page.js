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
}
// end of sidebar
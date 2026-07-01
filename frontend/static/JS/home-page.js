import {
    getUserConversations,
    appendHistoryItemToSidebar,
    handleQuerySubmission,
    loadActiveMessages
} from './home-helper-fun.js';
import { userDetails } from "./profile-helper-fun.js";

// =========================================================================
// GLOBAL APPLICATION STATE DEFINITIONS
// =========================================================================
// Pull from sessionStorage so state is isolated strictly to THIS tab
let currentConversationId = sessionStorage.getItem('active_conversation_id') || null;

/**
 * Main application initializer orchestration loop binding listeners
 * as soon as safe structural rendering events finalize inside DOM lifecycle.
 */
document.addEventListener('DOMContentLoaded', async () => {

    // === REUSABLE/SHARED ELEMENT LOCATORS ===
    const chatInterface = document.getElementById('chat-interface');
    const messageStream = document.getElementById('message-stream');
    let ulConversations = document.getElementById("user-conversations");
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');

    // === SIDEBAR TOGGLE SECTION ===
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const mainChatArea = document.getElementById('main-chat-area');
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            sidebar.classList.toggle('show-sidebar');
        });

        mainChatArea?.addEventListener('click', () => {
            sidebar.classList.remove('show-sidebar');
        });
    } else {
        console.warn("Sidebar toggle button or sidebar element not found inside current view.");
    }

    // === USER PROFILE ICON SECTION ===
    const profileIcon = document.getElementById('profile-icon');
    if (profileIcon) {
        try {
            const info = await userDetails();
            if (info?.firstLetter) {
                profileIcon.innerText = info.firstLetter;
            } else {
                console.warn("User profile details are inactive (Guest state).");
            }
        } catch (err) {
            console.error("Failed fetching user profile details :", err);
        }
    }

    // === CHAT HISTORY SELECTION SECTION ===
    if (ulConversations) {
        try {
            const history = await getUserConversations();
            if (history && Array.isArray(history)) {
                ulConversations.innerHTML = '';
                history.forEach(convo => appendHistoryItemToSidebar(ulConversations, convo));
            }
        } catch (err) {
            console.error("Failed fetching chat history logs:", err);
        }

        // If a conversation ID survived a refresh inside this specific tab, autoload it
        if (currentConversationId) {
            chatInterface?.classList.add('chat-active');
            await loadActiveMessages(currentConversationId, messageStream);
        }

        // Capture targeting clicks using optimized operational event delegation
        ulConversations.addEventListener('click', async (e) => {
            const targetItem = e.target.closest('.chat-history-item');
            if (targetItem) {
                const conversationId = targetItem.getAttribute('item-id');
                if (!conversationId) return;

                currentConversationId = conversationId;
                // Save to sessionStorage to prevent leaking to other tabs
                sessionStorage.setItem('active_conversation_id', conversationId);

                chatInterface?.classList.add('chat-active');
                await loadActiveMessages(conversationId, messageStream);
            }
        });
    } else {
        console.warn("User conversations container not found inside current view.");
    }

    // === CHAT INPUT & SUBMISSION ENGINE SECTION ===
    if (chatInput || sendBtn) {
        const executeSubmission = async () => {
            const newId = await handleQuerySubmission({
                chatInput,
                chatInterface,
                messageStream,
                ulConversations,
                currentConversationId
            });

            if (newId) {
                currentConversationId = newId;
                // Save newly started thread ID to sessionStorage
                sessionStorage.setItem('active_conversation_id', newId);
            }
        };

        if (sendBtn) {
            sendBtn.style.cursor = 'pointer';
            sendBtn.addEventListener('click', executeSubmission);
        }

        chatInput?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                executeSubmission();
            }
        });

        chatInput?.addEventListener('input', () => {
            chatInput.style.height = 'auto';
            chatInput.style.height = (chatInput.scrollHeight) + 'px';
        });
    }

    // === NEW CHAT CONTROL SECTION ===
    const newChatBtn = document.getElementById('new-chat-btn');
    if (newChatBtn) {
        newChatBtn.addEventListener('click', () => {
            currentConversationId = null;
            // Safely drop the session token when starting completely fresh
            sessionStorage.removeItem('active_conversation_id');

            chatInterface?.classList.remove('chat-active');
            if (messageStream) messageStream.innerHTML = '';

            if (chatInput) {
                chatInput.value = '';
                chatInput.style.height = '24px';
            }
        });
    }
});
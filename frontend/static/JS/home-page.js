import {
    getUserConversations,
    getUserConversation,
    appendMessageBubble,
    scrollToBottom,
    appendHistoryItemToSidebar,
    handleQuerySubmission
} from './home-helper-fun.js';
import { userDetails } from "./profile-helper-fun.js";

// =========================================================================
// GLOBAL APPLICATION STATE DEFINITIONS
// =========================================================================
let currentConversationId = null;

/**
 * Main application initializer orchestration loop binding listeners
 * as soon as safe structural rendering events finalize inside DOM lifecycle.
 */
document.addEventListener('DOMContentLoaded', async () => {

    // === REUSABLE/SHARED ELEMENT LOCATORS ===
    const chatInterface = document.getElementById('chat-interface');
    const messageStream = document.getElementById('message-stream');
    const ulConversations = document.getElementById("user-conversations");
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');

    // === SIDEBAR TOGGLE SECTION ===
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const mainChatArea = document.getElementById('main-chat-area');
    if (sidebarToggle && sidebar) {
        // Intercept viewport interaction requests to trigger sliding mobile panels
        sidebarToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            sidebar.classList.toggle('show-sidebar');
        });

        // Safely close context drawer if user interacts outside structural margins
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
                console.warn("User profile details are inactive (App serving in standard Guest variant state).");
            }
        } catch (err) {
            console.error("Failed fetching user profile details :", err);
        }
    } else {
        console.warn("Profile icon element not found inside current view.");
    }

    // === CHAT HISTORY SELECTION SECTION ===
    if (ulConversations) {
        try {
            // Direct background sync pipeline downloading records history logs
            const history = await getUserConversations();
            if (history && Array.isArray(history)) {
                ulConversations.innerHTML = '';
                history.forEach(convo => appendHistoryItemToSidebar(ulConversations, convo));
            }
        } catch (err) {
            console.error("Failed fetching chat history logs:", err);
        }

        // Capture targeting clicks using optimized operational event delegation
        ulConversations.addEventListener('click', async (e) => {
            const targetItem = e.target.closest('.chat-history-item');
            if (targetItem) {
                const conversationId = targetItem.getAttribute('item-id');
                if (!conversationId) return;

                currentConversationId = conversationId;
                chatInterface?.classList.add('chat-active');

                if (messageStream) messageStream.innerHTML = '';

                try {
                    const responseData = await getUserConversation(conversationId);
                    const messageList = Array.isArray(responseData) ? responseData : (responseData?.content || []);

                    // Distribute chronological dialogue rows smoothly within interactive stream viewport
                    messageList.forEach(msg => {
                        if (msg.user_prompt) {
                            appendMessageBubble(messageStream, 'user', msg.user_prompt);
                        }
                        if (msg.AI_response) {
                            appendMessageBubble(messageStream, 'assistant', msg.AI_response);
                        }
                    });

                    scrollToBottom(messageStream);
                } catch (err) {
                    console.error("Could not download old structural message logs context:", err);
                    appendMessageBubble(messageStream, 'assistant', "Error: Failed downloading chat context logs.");
                }
            }
        });
    } else {
        console.warn("User conversations container not found inside current view.");
    }

    // === CHAT INPUT & SUBMISSION ENGINE SECTION ===
    if (chatInput || sendBtn) {

        // Helper package to run inside execution bindings
        const executeSubmission = async () => {
            const newId = await handleQuerySubmission({
                chatInput,
                chatInterface,
                messageStream,
                ulConversations,
                currentConversationId
            });
            // If the query setup initiated a completely new thread, sync state records
            if (newId) {
                currentConversationId = newId;
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

        // Dynamic processing listener to stretch or scale tracking heights as lines extend
        chatInput?.addEventListener('input', () => {
            chatInput.style.height = 'auto';
            chatInput.style.height = (chatInput.scrollHeight) + 'px';
        });
    } else {
        console.warn("Chat input or send button elements not found inside current view.");
    }

    // === NEW CHAT CONTROL SECTION ===
    const newChatBtn = document.getElementById('new-chat-btn');
    if (newChatBtn) {
        newChatBtn.addEventListener('click', () => {
            currentConversationId = null;
            chatInterface?.classList.remove('chat-active');
            if (messageStream) messageStream.innerHTML = '';

            if (chatInput) {
                chatInput.value = '';
                chatInput.style.height = '24px'; // Resets structural baseline heights back to single row specs
            }
        });
    } else {
        console.warn("New chat button element not found inside current view.");
    }
});
import {
    getUserConversations,
    appendHistoryItemToSidebar,
    handleQuerySubmission,
    loadActiveMessages,
    deleteUserConversations
} from './home-helper-fun.js';
import { userDetails } from "./profile-helper-fun.js";

// =========================================================================
// GLOBAL APPLICATION STATE DEFINITIONS
// =========================================================================
let currentConversationId = sessionStorage.getItem('active_conversation_id') || null;

/**
 * Main application initializer orchestration loop binding listeners
 * as soon as safe structural rendering events finalize inside DOM lifecycle.
 */
document.addEventListener('DOMContentLoaded', () => {
    // 1. Locate shared/global element nodes
    const elements = {
        chatInterface: document.getElementById('chat-interface'),
        messageStream: document.getElementById('message-stream'),
        ulConversations: document.getElementById("user-conversations"),
        chatInput: document.getElementById('chat-input'),
        sendBtn: document.getElementById('send-btn'),
        sidebarToggle: document.getElementById('sidebar-toggle'),
        sidebar: document.getElementById('sidebar'),
        mainChatArea: document.getElementById('main-chat-area'),
        profileIcon: document.getElementById('profile-icon'),
        dropdownContainer: document.getElementById('app-logo'),
        arrowToggle: document.getElementById('dropdown-toggle'),
        currentBrand: document.getElementById('current-brand'),
        newChatBtn: document.getElementById('new-chat-btn'),
        appWrapper: document.getElementById('app-wrapper'),
        clearAllBtn: document.getElementById('clear-all-chats-btn')
    };

    // 2. Initialize feature domains independently
    initSidebar(elements);
    initUserProfile(elements);
    initChatHistory(elements);
    initModelDropdown(elements);
    initChatSubmission(elements);
    initNewChatEngine(elements);
    initClearAllEngine(elements);
});

// =========================================================================
// FEATURE ISOLATION MODULES
// =========================================================================

/**
 * Injects a temporary processing indicator into the stream
 */
function showLoadingIndicator(messageStream) {
    // Remove any existing one just in case
    document.getElementById('ai-loading-row')?.remove();

    const loadingRow = document.createElement('div');
    loadingRow.className = 'message-row assistant-msg';
    loadingRow.id = 'ai-loading-row';
    loadingRow.innerHTML = `
        <div class="msg-bubble">
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    messageStream.appendChild(loadingRow);
    messageStream.scrollTop = messageStream.scrollHeight; // Auto scroll down
}

/**
 * Removes the processing indicator when response data arrives
 */
function hideLoadingIndicator() {
    document.getElementById('ai-loading-row')?.remove();
}

/**
 * Handles toggling behavior for the responsive application sidebar
 */
function initSidebar({ sidebarToggle, sidebar, mainChatArea }) {
    if (!sidebarToggle || !sidebar) {
        console.warn("Sidebar toggle button or sidebar element not found inside current view.");
        return;
    }

    sidebarToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        sidebar.classList.toggle('show-sidebar');
    });

    mainChatArea?.addEventListener('click', () => {
        sidebar.classList.remove('show-sidebar');
    });
}

/**
 * Fetches and injects user profile styling/data asynchronously
 */
async function initUserProfile({ profileIcon }) {
    if (!profileIcon) return;

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

/**
 * Manages loading past threads and listening for history swaps via event delegation
 */
async function initChatHistory({ ulConversations, chatInterface, messageStream }) {
    if (!ulConversations) {
        console.warn("User conversations container not found inside current view.");
        return;
    }

    // Load initial historical list items
    try {
        const history = await getUserConversations();
        if (history && Array.isArray(history)) {
            ulConversations.innerHTML = '';
            history.forEach(convo => appendHistoryItemToSidebar(ulConversations, convo));
        }
    } catch (err) {
        console.error("Failed fetching chat history logs:", err);
    }

    // Autoload active session conversation if tab was refreshed
    if (currentConversationId) {
        chatInterface?.classList.add('chat-active');
        await loadActiveMessages(currentConversationId, messageStream);
    }

    // Event delegation handling chat swaps
    ulConversations.addEventListener('click', async (e) => {
        const targetItem = e.target.closest('.chat-history-item');
        if (!targetItem) return;

        const conversationId = targetItem.getAttribute('item-id');
        if (!conversationId) return;

        currentConversationId = conversationId;
        sessionStorage.setItem('active_conversation_id', conversationId);

        chatInterface?.classList.add('chat-active');
        await loadActiveMessages(conversationId, messageStream);
    });

    // UPDATED: Click user message bubble to reveal full text toggle
    messageStream?.addEventListener('click', (e) => {
        const userBubble = e.target.closest('.user-msg .msg-bubble');
        if (userBubble) {
            userBubble.classList.toggle('expanded');
        }
    });
}

/**
 * Controls the custom AI Model configuration dropdown menu & dynamic themes
 */
function initModelDropdown({ dropdownContainer, arrowToggle, currentBrand, appWrapper }) {
    if (!dropdownContainer || !arrowToggle || !currentBrand) return;

    const menuItems = dropdownContainer.querySelectorAll('.dropdown-menu li');
    const savedModel = sessionStorage.getItem('selectedModel');

    // Restore cached selection state
    if (savedModel) {
        const activeItem = dropdownContainer.querySelector(`.dropdown-menu li[data-value="${savedModel}"]`);
        if (activeItem) {
            currentBrand.textContent = activeItem.textContent;
            menuItems.forEach(i => i.classList.remove('active'));
            activeItem.classList.add('active');

            // Apply theme toggle condition on reload
            if (savedModel === 'gemini' && appWrapper) {
                appWrapper.classList.add('gemini-mode');
            }
        }
    }

    // Open/Close toggle
    arrowToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdownContainer.classList.toggle('open');
    });

    // Handle updates
    menuItems.forEach(item => {
        item.addEventListener('click', () => {
            const selectedValue = item.getAttribute('data-value');
            currentBrand.textContent = item.textContent;

            menuItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');

            sessionStorage.setItem('selectedModel', selectedValue);
            dropdownContainer.classList.remove('open');

            // Handle switching the Gemini UI Glow styles dynamically
            if (appWrapper) {
                if (selectedValue === 'gemini') {
                    appWrapper.classList.add('gemini-mode');
                } else {
                    appWrapper.classList.remove('gemini-mode');
                }
            }
        });
    });

    // Close menu when clicking outside
    document.addEventListener('click', () => {
        dropdownContainer.classList.remove('open');
    });
}

/**
 * Standardizes messaging pipeline bindings and auto-expanding key tracking
 */
function initChatSubmission({ chatInput, sendBtn, chatInterface, messageStream, ulConversations }) {
    if (!chatInput && !sendBtn) return;

    const executeSubmission = async () => {
        const handleSubmissionPromise = handleQuerySubmission({
            chatInput,
            chatInterface,
            messageStream,
            ulConversations,
            currentConversationId
        });

        // Show your loading dots exactly when text processing initializes
        if (messageStream) {
            showLoadingIndicator(messageStream);
        }

        const newId = await handleSubmissionPromise;

        // Erase loading animations immediately when handleQuerySubmission yields execution
        hideLoadingIndicator();

        if (newId) {
            currentConversationId = newId;
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
        chatInput.style.height = `${chatInput.scrollHeight}px`;
    });
}

/**
 * Binds clean setup handlers targeting fresh workspace actions
 */
function initNewChatEngine({ newChatBtn, chatInterface, messageStream, chatInput }) {
    if (!newChatBtn) return;

    newChatBtn.addEventListener('click', () => {
        currentConversationId = null;
        sessionStorage.removeItem('active_conversation_id');

        chatInterface?.classList.remove('chat-active');
        if (messageStream) messageStream.innerHTML = '';

        if (chatInput) {
            chatInput.value = '';
            chatInput.style.height = '24px';
        }
    });
}

/**
 * Attaches structural pipeline actions to purge the entire conversation tree context
 */
function initClearAllEngine({ clearAllBtn, ulConversations, chatInterface, messageStream, chatInput }) {
    if (!clearAllBtn) return;

    // We can import deleteUserConversations dynamically or declare it at the top of home-page.js
    clearAllBtn.addEventListener('click', async (e) => {
        e.stopPropagation();

        if (!confirm("Are you sure you want to permanently clear ALL your conversation history? This cannot be undone.")) {
            return;
        }

        try {
            const successMessage = await deleteUserConversations();

            if (successMessage) {
                // 1. Wipe layout interface states clean
                sessionStorage.removeItem('active_conversation_id');
                if (ulConversations) ulConversations.innerHTML = '';
                if (messageStream) messageStream.innerHTML = '';

                chatInterface?.classList.remove('chat-active');
                if (chatInput) {
                    chatInput.value = '';
                    chatInput.style.height = '24px';
                }

                window.alert(successMessage || "All chats have been cleared.");
                window.location.reload(); // Hard reload layout frame cleanly
            } else {
                window.alert("Failed to clear chat history logs.");
            }
        } catch (err) {
            console.error("Failed running global clear process handler:", err);
            window.alert("An error occurred while clearing your history.");
        }
    });
}
import {
    getUserConversations,
    getUserConversation,
    userChat
} from './home-helper-fun.js';
import {userDetails} from "./profile-helper-fun";

// =========================================================================
// GLOBAL APPLICATION STATE DEFINITIONS
// =========================================================================
let currentConversationId = null;

/**
 * Main application initializer orchestration loop binding listeners
 * as soon as safe structural rendering events finalize inside DOM lifecycle.
 */
document.addEventListener('DOMContentLoaded', async () => {
    sidebarToggle();
    await userProfile();
    await chatHistory();
    chatInput();
    newChat();
});

// =========================================================================
// SIDEBAR TOGGLE COMPONENT
// =========================================================================
function sidebarToggle() {
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
}

// =========================================================================
// PROFILE ICON COMPONENT
// =========================================================================
async function userProfile() {
    try {
        const info = await userDetails();
        const profileIcon = document.getElementById('profile-icon');

        if (info?.firstLetter && profileIcon) {
            profileIcon.innerText = info.firstLetter;
        } else {
            console.warn("User profile details are inactive (App serving in standard Guest variant state).");
        }
    } catch (err) {
        console.error("Failed fetching user validation profiles setup architecture:", err);
    }
}

// =========================================================================
// GET CONVERSATIONS & HISTORY SELECTION COMPONENT
// =========================================================================
async function chatHistory() {
    const ulConversations = document.getElementById("user-conversations");
    if (!ulConversations) return;

    // Direct background sync pipeline downloading records history logs
    const history = await getUserConversations();
    if (history && Array.isArray(history)) {
        ulConversations.innerHTML = '';
        history.forEach(convo => appendHistoryItemToSidebar(ulConversations, convo));
    }

    // Capture targeting clicks using optimized operational event delegation
    ulConversations.addEventListener('click', async (e) => {
        const targetItem = e.target.closest('.chat-history-item');
        if (targetItem) {
            await switchActiveConversation(targetItem.getAttribute('item-id'));
        }
    });
}

async function switchActiveConversation(conversationId) {
    if (!conversationId) return;
    currentConversationId = conversationId;

    const chatInterface = document.getElementById('chat-interface');
    chatInterface?.classList.add('chat-active');

    const messageStream = document.getElementById('message-stream');
    if (messageStream) messageStream.innerHTML = '';

    try {
        const responseData = await getUserConversation(conversationId);

        // Safety Unpack: Handles raw arrays or data wrapped inside a .content property envelope
        const messageList = Array.isArray(responseData) ? responseData : (responseData?.content || []);

        // Distribute chronological dialogue rows smoothly within interactive stream viewport
        messageList.forEach(msg => {
            // 1. Render User Message Bubble
            if (msg.user_prompt) {
                appendMessageBubble(messageStream, 'user', msg.user_prompt);
            }
            // 2. Render AI Response Message Bubble
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

function appendHistoryItemToSidebar(container, convo) {
    const li = document.createElement('li');
    li.classList.add('chat-history-item');
    li.setAttribute('item-id', convo.id);
    li.textContent = convo.title || `Conversation #${convo.id}`;
    container.insertBefore(li, container.firstChild);
}

// =========================================================================
// CHAT INPUT & SUBMISSION ENGINE COMPONENT
// =========================================================================
function chatInput() {
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');

    if (sendBtn) {
        sendBtn.style.cursor = 'pointer';
        sendBtn.addEventListener('click', () => submitUserQuery(chatInput));
    }

    chatInput?.addEventListener('keydown', (e) => {
        // Route validation: Lone "Enter" key forces dispatch, "Shift + Enter" skips to add a new line break
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            submitUserQuery(chatInput);
        }
    });

    // Dynamic processing listener to stretch or scale tracking heights as lines extend
    chatInput?.addEventListener('input', () => {
        chatInput.style.height = 'auto';
        chatInput.style.height = (chatInput.scrollHeight) + 'px';
    });
}

async function submitUserQuery(chatInput) {
    if (!chatInput) return;
    const queryText = chatInput.value.trim();
    if (!queryText) return;

    const chatInterface = document.getElementById('chat-interface');
    chatInterface?.classList.add('chat-active');

    const messageStream = document.getElementById('message-stream');
    appendMessageBubble(messageStream, 'user', queryText);

    // Instantly wipe query data input cache buffers and snap input node dimensions back to layout defaults
    chatInput.value = '';
    chatInput.style.height = '24px';

    scrollToBottom(messageStream);

    try {
        const response = await userChat(queryText, currentConversationId);

        if (!response) {
            appendMessageBubble(messageStream, 'assistant', "System Error: Failed to receive response from server.");
            return;
        }

        const reply = response.AI_response || (typeof response === 'string' ? response : "");
        const nextId = response.conversation_id;
        console.log(nextId, currentConversationId)

        appendMessageBubble(messageStream, 'assistant', reply);

        // Track and auto-append item inside navigation historical indexes for completely new threads
        if (!currentConversationId && nextId) {
            currentConversationId = nextId;
            const ulConversations = document.getElementById("user-conversations");
            if (ulConversations) {
                appendHistoryItemToSidebar(ulConversations, {
                    id: nextId,
                    title: response.title
                });
            }
        }
    } catch (err) {
        console.error("Query dispatch transmission pipeline trace failed:", err);
        appendMessageBubble(messageStream, 'assistant', "System Error: Failed to fetch backend answer.");
    } finally {
        scrollToBottom(messageStream);
    }
}

// =========================================================================
// NEW CHAT COMPONENT
// =========================================================================
function newChat() {
    const newChatBtn = document.getElementById('new-chat-btn');

    newChatBtn?.addEventListener('click', () => {
        // Reset state context tracking markers
        currentConversationId = null;

        const chatInterface = document.getElementById('chat-interface');
        chatInterface?.classList.remove('chat-active');

        const messageStream = document.getElementById('message-stream');
        if (messageStream) messageStream.innerHTML = '';

        const chatInput = document.getElementById('chat-input');
        if (chatInput) {
            chatInput.value = '';
            chatInput.style.height = '24px'; // Resets structural baseline heights back to single row specs
        }
    });
}

// =========================================================================
// LAYOUT RENDERING UTILITIES (Shared internally across module functions)
// =========================================================================
function appendMessageBubble(stream, role, text) {
    if (!stream) return;

    const row = document.createElement('div');
    row.classList.add('message-row', role === 'user' ? 'user-msg' : 'assistant-msg');

    let formattedText = text;

    // If it's an assistant message and the markdown library loaded successfully
    if (role === 'assistant' && typeof marked !== 'undefined') {
        // Convert Markdown string to HTML elements safely
        formattedText = marked.parse(text);
    } else {
        // Safe escaping fallback for user messages to prevent HTML injection/XSS
        const tempDiv = document.createElement('div');
        tempDiv.textContent = text;
        formattedText = tempDiv.innerHTML;
    }

    row.innerHTML = `<div class="msg-bubble">${formattedText}</div>`;
    stream.appendChild(row);
}

function scrollToBottom(stream) {
    if (stream) stream.scrollTop = stream.scrollHeight;
}
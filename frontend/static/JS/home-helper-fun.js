import {
    CONVERSATIONS_URL,
    CONVERSATION_URL,
    MESSAGE_URL,
} from './constants.js';
import {
    chat,
    getConversations,
    getConversation,
    deleteConversations,
    deleteConversation
} from './api-call.js';
import { tokenIsValid } from "./auth-helper-fun.js";

/**
 * Sends a user query payload down to the backend communication network.
 */
async function userChat(userPrompt, conversationId = null) {
    const isLoggedIn = await tokenIsValid();
    const accessToken = localStorage.getItem("access_token");
    let response;

    if (isLoggedIn) {
        response = await chat(userPrompt, MESSAGE_URL, accessToken, conversationId);
    } else {
        response = await chat(userPrompt, MESSAGE_URL, accessToken);
    }

    if (response && response.success) {
        return response.content;
    } else {
        console.error("Failed to get user chat:", response?.message || "Unknown API error");
        return null;
    }
}

/**
 * Downloads a structured historical index containing all past conversation meta records.
 */
async function getUserConversations() {
    const isLoggedIn = await tokenIsValid();
    if (isLoggedIn) {
        const accessToken = localStorage.getItem("access_token");
        const response = await getConversations(accessToken, CONVERSATIONS_URL);

        if (response.success) {
            return response.content;
        } else {
            console.error("Failure to fetch user conversations:", response.message);
            return null;
        }
    } else {
        console.warn("User is not authenticated. Cannot fetch user conversations.");
        return null;
    }
}

/**
 * Requests global server-side removal of all conversational indices.
 */
async function deleteUserConversations() {
    const isLoggedIn = await tokenIsValid();
    if (isLoggedIn) {
        const accessToken = localStorage.getItem("access_token");
        const response = await deleteConversations(accessToken, CONVERSATIONS_URL);

        if (response.success) {
            return response.message;
        } else {
            console.error("Failure to delete user conversations:", response.message);
            return null;
        }
    } else {
        console.warn("User is not authenticated. Cannot delete user conversations.");
        return null;
    }
}

/**
 * Fetches the entire full-length message history stream log.
 */
async function getUserConversation(conversationId) {
    const isLoggedIn = await tokenIsValid();
    if (isLoggedIn) {
        const accessToken = localStorage.getItem("access_token");
        const URL = `${CONVERSATION_URL}/${conversationId}`;
        const response = await getConversation(conversationId, accessToken, URL);

        if (response.success) {
            return response.content;
        } else {
            console.error("Failure to fetch user conversation:", response.message);
            return null;
        }
    } else {
        console.warn("User is not authenticated. Cannot fetch user conversation.");
        return null;
    }
}

/**
 * Targets and purges a single conversation container from remote cloud database nodes.
 */
async function deleteUserConversation(conversationId) {
    const isLoggedIn = await tokenIsValid();
    if (isLoggedIn) {
        const accessToken = localStorage.getItem("access_token");
        const URL = `${CONVERSATION_URL}/${conversationId}`;
        const response = await deleteConversation(conversationId, accessToken, URL);

        if (response.success) {
            return response.message;
        } else {
            console.error("Failure to delete user conversation:", response.message);
            return null;
        }
    } else {
        console.warn("User is not authenticated. Cannot delete user conversation.");
        return null;
    }
}

/**
 * UI UTILITY: Generates and appends standard dialog bubbles inside the chat window viewport.
 * Features an interactive progressive word-by-word typewriter rendering algorithm for incoming assistant responses.
 * @function appendMessageBubble
 * @param {HTMLElement} stream - The scrolling message stream panel node.
 * @param {'user'|'assistant'} role - Identity flag determining structural style configurations.
 * @param {string} text - Message context payload being forced down visual trees.
 * @param {boolean} [shouldStream=false] - When true, forces the text to type out smoothly word-by-word.
 */
function appendMessageBubble(stream, role, text, shouldStream = false) {
    if (!stream) return;

    const row = document.createElement('div');
    row.classList.add('message-row', role === 'user' ? 'user-msg' : 'assistant-msg');

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    row.appendChild(bubble);
    stream.appendChild(row);

    // XSS Sanitization helper for raw user blocks
    const escapeHTML = (rawStr) => {
        const tempDiv = document.createElement('div');
        tempDiv.textContent = rawStr;
        return tempDiv.innerHTML;
    };

    if (role === 'user') {
        bubble.innerHTML = escapeHTML(text);
        scrollToBottom(stream);
        return;
    }

    // Process Assistant Text
    if (shouldStream) {
        const words = text.split(' ');
        let index = 0;
        let currentTextAccumulator = '';

        function streamNextWord() {
            if (index < words.length) {
                currentTextAccumulator += (index === 0 ? '' : ' ') + words[index];
                index++;

                // Dynamically compile markdown layouts down the DOM tree
                if (typeof marked !== 'undefined') {
                    bubble.innerHTML = marked.parse(currentTextAccumulator);
                } else {
                    bubble.innerHTML = currentTextAccumulator;
                }

                scrollToBottom(stream);
                setTimeout(streamNextWord, 35); // Smooth layout streaming cadence delay
            }
        }
        streamNextWord();
    } else {
        if (typeof marked !== 'undefined') {
            bubble.innerHTML = marked.parse(text);
        } else {
            bubble.innerHTML = text;
        }
        scrollToBottom(stream);
    }
}

/**
 * UI UTILITY: Force scrolls the active message pool target into instant user visibility.
 */
function scrollToBottom(stream) {
    if (stream) stream.scrollTop = stream.scrollHeight;
}

/**
 * CORE LOGIC: Orchestrates submission stream pipelines, updating structural layouts.
 */
async function handleQuerySubmission({
    chatInput,
    chatInterface,
    messageStream,
    ulConversations,
    currentConversationId
}) {
    const queryText = chatInput.value.trim();
    if (!queryText) return null;

    chatInterface?.classList.add('chat-active');
    appendMessageBubble(messageStream, 'user', queryText);

    chatInput.value = '';
    chatInput.style.height = '24px';

    scrollToBottom(messageStream);

    try {
        const response = await userChat(queryText, currentConversationId);

        if (!response) {
            appendMessageBubble(messageStream, 'assistant', "System Error: Failed to receive response from server.");
            return null;
        }

        const reply = response.AI_response || response.content?.AI_response || (typeof response === 'string' ? response : "");
        const nextId = response.conversation_id || response.content?.conversation_id;
        const conversationTitle = response.conversation_title || response.content?.title || `Conversation #${nextId}`;

        // Set shouldStream flag to TRUE so fresh replies feel alive
        appendMessageBubble(messageStream, 'assistant', reply, true);

        const isNewThread = !currentConversationId || currentConversationId === "null";

        if (isNewThread && nextId) {
            if (ulConversations) {
                appendHistoryItemToSidebar(ulConversations, {
                    id: nextId,
                    title: conversationTitle
                });
            } else {
                console.warn("Could not append item because ulConversations element reference is missing.");
            }
            return nextId;
        }
    } catch (err) {
        console.error("Query dispatch transmission pipeline trace failed:", err);
        appendMessageBubble(messageStream, 'assistant', "System Error: Failed to fetch backend answer.");
    } finally {
        scrollToBottom(messageStream);
    }

    return null;
}

/**
 * Downloads a historic log slice and drops message rows down the UI viewport.
 */
async function loadActiveMessages(conversationId, messageStream) {
    if (!messageStream) return;
    messageStream.innerHTML = '';

    try {
        const responseData = await getUserConversation(conversationId);
        const messageList = Array.isArray(responseData) ? responseData : (responseData?.content || []);

        messageList.forEach(msg => {
            if (msg.user_prompt) {
                appendMessageBubble(messageStream, 'user', msg.user_prompt, false);
            }
            if (msg.AI_response) {
                appendMessageBubble(messageStream, 'assistant', msg.AI_response, false);
            }
        });

        scrollToBottom(messageStream);
    } catch (err) {
        console.error("Could not download old structural message logs context:", err);
        appendMessageBubble(messageStream, 'assistant', "Error: Failed downloading chat context logs.");
    }
}

/**
 * SIDEBAR UTILITY: Formats and shifts a historical list item directly into tracking sidebar slots.
 */
function appendHistoryItemToSidebar(container, convo) {
    const li = document.createElement('li');
    li.classList.add('chat-history-item');
    li.setAttribute('item-id', convo.id);

    const textSpan = document.createElement('span');
    textSpan.classList.add('chat-history-text');
    textSpan.textContent = convo.title || `Conversation #${convo.id}`;
    li.appendChild(textSpan);

    const menuWrapper = document.createElement('div');
    menuWrapper.classList.add('history-menu-wrapper');

    const menuBtn = document.createElement('button');
    menuBtn.classList.add('history-menu-btn');
    menuBtn.innerHTML = '&#8942;';
    menuWrapper.appendChild(menuBtn);

    const dropdown = document.createElement('div');
    dropdown.classList.add('history-dropdown');
    dropdown.style.display = 'none';

    const actions = [
        { label: 'Rename', class: 'action-rename', fn: () => renameConvo(convo.id) },
        { label: 'Share', class: 'action-share', fn: () => shareConvo(convo.id) },
        { label: 'Delete', class: 'action-delete', fn: async () => await deleteConvo(convo.id) }
    ];

    actions.forEach(action => {
        const option = document.createElement('div');
        option.classList.add('dropdown-item', action.class);
        option.textContent = action.label;
        option.addEventListener('click', (e) => {
            e.stopPropagation();
            action.fn();
            dropdown.style.display = 'none';
        });
        dropdown.appendChild(option);
    });

    menuWrapper.appendChild(dropdown);
    li.appendChild(menuWrapper);

    menuBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        document.querySelectorAll('.history-dropdown').forEach(d => {
            if (d !== dropdown) d.style.display = 'none';
        });
        const isHidden = dropdown.style.display === 'none';
        dropdown.style.display = isHidden ? 'block' : 'none';
    });

    document.addEventListener('click', () => {
        dropdown.style.display = 'none';
    });

    container.insertBefore(li, container.firstChild);
}

// --- Placeholder Handler Functions ---
function renameConvo(id) {
    const newName = prompt("Enter new conversation name:");
    if (newName) console.log(`Renaming convo ${id} to: ${newName}`);
}

function shareConvo(id) {
    console.log(`Sharing convo ${id}`);
}

async function deleteConvo(id) {
    if (!confirm("Are you sure you want to delete this conversation?")) return;

    const response = await deleteUserConversation(id);
    if (response) {
        const currentConversationId = sessionStorage.getItem('active_conversation_id');
        if (currentConversationId && currentConversationId === id.toString()) {
            sessionStorage.removeItem('active_conversation_id');
        }
        window.alert(response);
        window.location.reload();
    } else {
        window.alert("Failed to delete the conversation.");
    }
}

export {
    getUserConversations,
    appendHistoryItemToSidebar,
    handleQuerySubmission,
    loadActiveMessages,
    deleteUserConversations
};
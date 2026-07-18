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
    deleteConversation,
    renameConversation
} from './api-call.js';
import { getAuthenticatedToken } from "./auth-helper-fun.js";

/**
 * Sends a chat message to the server and returns the AI's response.
 *
 * @param {string} userPrompt - The message text sent by the user.
 * @param {string|null} conversationId - The ID of the current chat thread, if it exists.
 * @returns {Promise<object|null>} The server response data, or null if the request fails.
 */
async function userChat(userPrompt, conversationId = null) {
    const accessToken = await getAuthenticatedToken();
    let response;

    try {
        if (!accessToken) {
            console.warn("User is not authenticated. Sending chat message as guest user.");
            response = await chat(userPrompt, MESSAGE_URL);
        } else if (conversationId) {
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
    } catch (error) {
        console.error("Network error while sending chat message:", error);
        return null;
    }
}

/**
 * Gets a list of all past conversations for the logged-in user.
 *
 * @returns {Promise<array|null>} An array containing past conversation records, or null if something goes wrong.
 */
async function getUserConversations() {
    const accessToken = await getAuthenticatedToken();
    if (!accessToken) {
        console.warn("User is not authenticated. Cannot fetch user conversations.");
        return null;
    }

    try {
        const response = await getConversations(accessToken, CONVERSATIONS_URL);

        if (response.success) {
            return response.content;
        } else {
            console.error("Failure to fetch user conversations:", response.message);
            return null;
        }
    } catch (error) {
        console.error("Network error while fetching user conversations:", error);
        return null;
    }
}

/**
 * Deletes all conversations for the logged-in user.
 *
 * @returns {Promise<string|null>} A success status message from the server, or null if the deletion fails.
 */
async function deleteUserConversations() {
    const accessToken = await getAuthenticatedToken();
    if (!accessToken) {
        console.warn("User is not authenticated. Cannot delete user conversations.");
        return null;
    }

    try {
        const response = await deleteConversations(accessToken, CONVERSATIONS_URL);

        if (response.success) {
            return response.message;
        } else {
            console.error("Failure to delete user conversations:", response.message);
            return null;
        }
    } catch (error) {
        console.error("Network error while deleting user conversations:", error);
        return null;
    }
}

/**
 * Changes the title of a specific conversation.
 *
 * @param {string} conversationId - The unique ID of the conversation to rename.
 * @param {string} title - The new name for the conversation.
 * @returns {Promise<string|null>} A success status message from the server, or null if the rename fails.
 */
async function renameUserConversation(conversationId, title) {
    const accessToken = await getAuthenticatedToken();
    if (!accessToken) {
        console.warn("User is not authenticated. Cannot rename user conversation.");
        return null;
    }

    try {
        const URL = `${CONVERSATION_URL}/${conversationId}`;
        const response = await renameConversation(title, accessToken, URL);

        if (response.success) {
            return response.message;
        } else {
            console.error("Failure to rename user conversation:", response.message);
            return null;
        }
    } catch (error) {
        console.error("Network error while renaming user conversation:", error);
        return null;
    }
}

/**
 * Gets the full history of messages for a single conversation.
 *
 * @param {string} conversationId - The unique ID of the conversation to fetch.
 * @returns {Promise<array|null>} An array of messages from the conversation history, or null if it fails.
 */
async function getUserConversation(conversationId) {
    const accessToken = await getAuthenticatedToken();
    if (!accessToken) {
        console.warn("User is not authenticated. Cannot fetch user conversation.");
        return null;
    }

    try {
        const URL = `${CONVERSATION_URL}/${conversationId}`;
        const response = await getConversation(accessToken, URL);

        if (response.success) {
            return response.content;
        } else {
            console.error("Failure to fetch user conversation:", response.message);
            return null;
        }
    } catch (error) {
        console.error("Network error while fetching user conversation:", error);
        return null;
    }
}

/**
 * Deletes a single conversation from the server.
 *
 * @param {string} conversationId - The unique ID of the conversation to delete.
 * @returns {Promise<string|null>} A success status message from the server, or null if the deletion fails.
 */
async function deleteUserConversation(conversationId) {
    const accessToken = await getAuthenticatedToken();
    if (!accessToken) {
        console.warn("User is not authenticated. Cannot delete user conversation.");
        return null;
    }

    try {
        const URL = `${CONVERSATION_URL}/${conversationId}`;
        const response = await deleteConversation(accessToken, URL);

        if (response.success) {
            return response.message;
        } else {
            console.error("Failure to delete user conversation:", response.message);
            return null;
        }
    } catch (error) {
        console.error("Network error while deleting user conversation:", error);
        return null;
    }
}

/**
 * Adds a message bubble (user or AI) into the chat area, with an optional word-by-word typewriter effect.
 *
 * @param {HTMLElement} stream - The HTML container element where messages are displayed.
 * @param {'user'|'assistant'} role - Tells the UI who sent the message to apply the correct styling.
 * @param {string} text - The actual message text to show.
 * @param {boolean} [shouldStream=false] - When true, forces the AI text to type out smoothly word-by-word.
 * @returns {void} This function updates the UI directly and does not return a value.
 */
function appendMessageBubble(stream, role, text, shouldStream = false) {
    if (!stream) return;

    const row = document.createElement('div');
    row.classList.add('message-row', role === 'user' ? 'user-msg' : 'assistant-msg');

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    row.appendChild(bubble);
    stream.appendChild(row);

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

    if (shouldStream) {
        const words = text.split(' ');
        let index = 0;
        let currentTextAccumulator = '';

        function streamNextWord() {
            if (index < words.length) {
                currentTextAccumulator += (index === 0 ? '' : ' ') + words[index];
                index++;

                if (typeof marked !== 'undefined') {
                    bubble.innerHTML = marked.parse(currentTextAccumulator);
                } else {
                    bubble.innerHTML = currentTextAccumulator;
                }

                scrollToBottom(stream);
                setTimeout(streamNextWord, 35);
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
 * Automatically scrolls the chat container down so the latest message is visible.
 *
 * @param {HTMLElement} stream - The HTML container element to scroll.
 * @returns {void} This function updates the UI directly and does not return a value.
 */
function scrollToBottom(stream) {
    if (stream) stream.scrollTop = stream.scrollHeight;
}

/**
 * Handles what happens when a user submits a new chat message, managing inputs, bubbles, and responses.
 *
 * @param {object} options - An object containing HTML element references and the current state.
 * @param {HTMLInputElement} options.chatInput - The input field text box.
 * @param {HTMLElement} options.chatInterface - The main chat wrapper element.
 * @param {HTMLElement} options.messageStream - The chat message history container.
 * @param {HTMLElement} options.ulConversations - The sidebar history list element.
 * @param {string|null} options.currentConversationId - The ID of the conversation currently open.
 * @returns {Promise<string|null>} The ID of the conversation thread (useful if a new thread started), or null.
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
 * Clears the chat window and loads every old message from a saved conversation history.
 *
 * @param {string} conversationId - The ID of the historical chat thread to display.
 * @param {HTMLElement} messageStream - The HTML container where the chat history bubbles should load.
 * @returns {Promise<void>} Resolves when the message elements are completely loaded and drawn into the UI.
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
 * Adds a conversation item into the tracking sidebar, including its rename/share/delete action dropdown menu.
 *
 * @param {HTMLElement} container - The HTML sidebar list element (`<ul>`).
 * @param {object} convo - The data object representing the conversation thread.
 * @param {string} convo.id - The unique ID of the conversation.
 * @param {string} convo.title - The visible name/title of the conversation.
 * @returns {void} This function manipulates the HTML layout directly and does not return a value.
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

    if (newName) {
        const response = renameUserConversation(id, newName);

        if (response) {
            window.alert(response);
            window.location.reload();
        } else {
            window.alert("Fail to Rename conversation.")
        }
    }
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
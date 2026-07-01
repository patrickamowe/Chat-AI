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
 * Automatically switches execution routes depending on whether a guest lifecycle
 * or an active user session token context is found.
 * * @async
 * @function userChat
 * @param {string} userPrompt - Raw message text submitted by the user.
 * @param {string|number|null} [conversationId=null] - The tracking UUID targeting an existing chat row.
 * @returns {Promise<Object|string|null>} Parsed content object response from the engine on success, otherwise null.
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
 * Downloads a structured historical index containing all past conversation meta
 * records tied explicitly to the authenticated user profile.
 * * @async
 * @function getUserConversations
 * @returns {Promise<Array<Object>|null>} Chronological list of conversation tracking blocks on success, otherwise null.
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
 * Requests global server-side removal of all conversational indices
 * tied to the currently active authenticated profile.
 * * @async
 * @function deleteUserConversations
 * @returns {Promise<string|null>} Success message confirmation text from backend payload on execution, otherwise null.
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
 * Fetches the entire full-length message history stream log bound
 * inside a distinct conversation ID.
 * * @async
 * @function getUserConversation
 * @param {string|number} conversationId - The targeting structural ID of the selected conversation thread.
 * @returns {Promise<Array<Object>|Object|null>} Array block containing granular dialogue historical rows on success, otherwise null.
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
 * * @async
 * @function deleteUserConversation
 * @param {string|number} conversationId - The targeting structural ID of the thread flagged for deletion.
 * @returns {Promise<string|null>} Success message confirmation text from backend payload on execution, otherwise null.
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
 * Automatically parses markdown content for assistant prompts, and safely switches to textContent
 * strings for human strings to block potential XSS injection vulnerabilities.
 * * @function appendMessageBubble
 * @param {HTMLElement} stream - The scrolling message stream panel node.
 * @param {'user'|'assistant'} role - Identity flag determining structural style configurations.
 * @param {string} text - Message context payload being forced down visual trees.
 */
function appendMessageBubble(stream, role, text) {
    if (!stream) return;

    const row = document.createElement('div');
    row.classList.add('message-row', role === 'user' ? 'user-msg' : 'assistant-msg');

    let formattedText = text;

    if (role === 'assistant' && typeof marked !== 'undefined') {
        formattedText = marked.parse(text);
    } else {
        const tempDiv = document.createElement('div');
        tempDiv.textContent = text;
        formattedText = tempDiv.innerHTML;
    }

    row.innerHTML = `<div class="msg-bubble">${formattedText}</div>`;
    stream.appendChild(row);
}

/**
 * UI UTILITY: Force scrolls the active message pool target into instant user visibility.
 * * @function scrollToBottom
 * @param {HTMLElement} stream - The scrolling message stream panel node target.
 */
function scrollToBottom(stream) {
    if (stream) stream.scrollTop = stream.scrollHeight;
}

/**
 * CORE LOGIC: Orchestrates submission stream pipelines, updating structural layouts.
 * Processes local updates, shifts user content out instantly, fires API commands, and displays results.
 * @async
 * @function handleQuerySubmission
 * @param {Object} context - Structured data requirements package map.
 * @param {HTMLInputElement|HTMLTextAreaElement} context.chatInput - Dom tracking element collecting data text inputs.
 * @param {HTMLElement} context.chatInterface - Global layout view panel framing active chat structures.
 * @param {HTMLElement} context.messageStream - Thread window viewport hosting message rows.
 * @param {HTMLElement|null} context.ulConversations - The sidebar historic thread list context.
 * @param {string|number|null} context.currentConversationId - Tracking state identifier representing active data stream context.
 * @returns {Promise<string|number|null>} Returns the updated conversation tracking identifier string if thread is freshly generated, otherwise null.
 */
export async function handleQuerySubmission({
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

    // Instantly wipe query data input cache buffers and snap input node dimensions back to layout defaults
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

        appendMessageBubble(messageStream, 'assistant', reply);

        // State Validation: Ensure string "null" from storage layers doesn't bypass this block
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
            return nextId; // Return new token ID to sync main script context states
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
 * @async
 * @function loadActiveMessages
 * @param {string|number} conversationId - Targeting ID key representing thread index data.
 * @param {HTMLElement} messageStream - Structural pool parent container parsing text nodes.
 */
async function loadActiveMessages(conversationId, messageStream) {
    if (!messageStream) return;
    messageStream.innerHTML = '';

    try {
        const responseData = await getUserConversation(conversationId);
        const messageList = Array.isArray(responseData) ? responseData : (responseData?.content || []);

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

/**
 * SIDEBAR UTILITY: Formats and shifts a historical list item directly into tracking sidebar slots.
 * Inserts elements at the top of the container layout pipeline using the firstChild reference.
 * Includes a vertical three-dot context menu for Delete, Share, and Rename actions.
 * * @function appendHistoryItemToSidebar
 * @param {HTMLElement} container - The navigation sidebar UL layout container wrapper.
 * @param {Object} convo - Data packet defining tracking points.
 * @param {string|number} convo.id - Unique database element index key.
 * @param {string} [convo.title] - Readable string preview describing past chat contents.
 */
function appendHistoryItemToSidebar(container, convo) {
    const li = document.createElement('li');
    li.classList.add('chat-history-item');
    li.setAttribute('item-id', convo.id);

    // 1. Create a span for the text content so it doesn't conflict with the menu layout
    const textSpan = document.createElement('span');
    textSpan.classList.add('chat-history-text');
    textSpan.textContent = convo.title || `Conversation #${convo.id}`;
    li.appendChild(textSpan);

    // 2. Create the Menu Wrapper
    const menuWrapper = document.createElement('div');
    menuWrapper.classList.add('history-menu-wrapper');

    // 3. Create the Three-Dot Button (Vertical Ellipsis: &#8942;)
    const menuBtn = document.createElement('button');
    menuBtn.classList.add('history-menu-btn');
    menuBtn.innerHTML = '&#8942;';
    menuWrapper.appendChild(menuBtn);

    // 4. Create the Dropdown Content
    const dropdown = document.createElement('div');
    dropdown.classList.add('history-dropdown');
    dropdown.style.display = 'none'; // Hidden by default

    // Define the menu options
    const actions = [
        { label: 'Rename', class: 'action-rename', fn: () => renameConvo(convo.id) },
        { label: 'Share', class: 'action-share', fn: () => shareConvo(convo.id) },
        { label: 'Delete', class: 'action-delete', fn: async () => await deleteConvo(convo.id) }
    ];

    // Build option elements
    actions.forEach(action => {
        const option = document.createElement('div');
        option.classList.add('dropdown-item', action.class);
        option.textContent = action.label;
        option.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent triggering background clicks
            action.fn();
            dropdown.style.display = 'none'; // Close menu after action
        });
        dropdown.appendChild(option);
    });

    menuWrapper.appendChild(dropdown);
    li.appendChild(menuWrapper);

    // 5. Toggle Dropdown Menu Visibility
    menuBtn.addEventListener('click', (e) => {
        e.stopPropagation(); // Stop click from bubbling to the LI itself

        // Close any other open history dropdowns first
        document.querySelectorAll('.history-dropdown').forEach(d => {
            if (d !== dropdown) d.style.display = 'none';
        });

        // Toggle current dropdown
        const isHidden = dropdown.style.display === 'none';
        dropdown.style.display = isHidden ? 'block' : 'none';
    });

    // Close dropdown if user clicks anywhere else on the page
    document.addEventListener('click', () => {
        dropdown.style.display = 'none';
    });

    // Insert the finalized list item into the sidebar
    container.insertBefore(li, container.firstChild);
}

// --- Placeholder Handler Functions (Implement your logic here) ---
function renameConvo(id) {
    const newName = prompt("Enter new conversation name:");
    if (newName) console.log(`Renaming convo ${id} to: ${newName}`);
}

function shareConvo(id) {
    console.log(`Sharing convo ${id}`);
}

async function deleteConvo(id) {
    if (confirm("Are you sure you want to delete this conversation?")) {
        const response = await deleteUserConversation(id);
        if (response){
            // Remove the deleted id from the session storage
            const currentConversationId = sessionStorage.getItem('active_conversation_id') || null;
            if (currentConversationId){
                if (currentConversationId === id.toString()){
                    sessionStorage.removeItem('active_conversation_id');
                }
            }

            // Alert the user for successful deletion and reload the current page
            window.alert(response);
            window.location.reload();
        } else {
            window.alert("Fail to Delete user account.");
        }


    }
}

export {
    getUserConversations,
    deleteUserConversations,
    getUserConversation,
    deleteUserConversation,
    userChat,
    appendHistoryItemToSidebar,
    scrollToBottom,
    appendMessageBubble,
    loadActiveMessages
};
// Global variables
let conversationHistory = [];
let isTyping = false;
let currentSessionId = null;
let sessions = [];

// DOM elements
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const typingIndicator = document.getElementById('typingIndicator');
const errorModal = document.getElementById('errorModal');
const errorMessage = document.getElementById('errorMessage');
const fileUploadArea = document.getElementById('fileUploadArea');
const fileInput = document.getElementById('fileInput');
const sidebar = document.getElementById('sidebar');
const sessionsList = document.getElementById('sessionsList');

// Initialize the chat
document.addEventListener('DOMContentLoaded', function() {
    messageInput.focus();
    updateSendButton();
    loadSessions();
    // Setup file drag and drop
    setupFileDragDrop();
});

// Handle input changes
messageInput.addEventListener('input', function() {
    updateSendButton();
    adjustTextareaHeight();
});

// Update send button state
function updateSendButton() {
    const hasText = messageInput.value.trim().length > 0;
    sendButton.disabled = !hasText || isTyping;
}

// Adjust textarea height based on content
function adjustTextareaHeight() {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
}

// Handle keyboard events
function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        if (!sendButton.disabled) {
            sendMessage();
        }
    }
}

// Session Management
async function createNewSession() {
    try {
        const response = await fetch('/api/sessions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        if (data.success) {
            currentSessionId = data.session_id;
            conversationHistory = [];
            clearChatDisplay();
            loadSessions();
        }
    } catch (error) {
        console.error('Error creating session:', error);
        showError('Failed to create new session');
    }
}

async function loadSessions() {
    try {
        const response = await fetch('/api/sessions');
        const data = await response.json();
        sessions = data.sessions;
        renderSessions();
    } catch (error) {
        console.error('Error loading sessions:', error);
    }
}

function renderSessions() {
    sessionsList.innerHTML = '';
    if (sessions.length === 0) {
        sessionsList.style.display = 'none';
        return;
    } else {
        sessionsList.style.display = '';
    }
    sessions.forEach(session => {
        const sessionElement = document.createElement('div');
        sessionElement.className = `session-item ${session.session_id === currentSessionId ? 'active' : ''}`;
        // Session title and meta
        const titleDiv = document.createElement('div');
        titleDiv.className = 'session-title';
        titleDiv.textContent = session.title;
        titleDiv.onclick = () => loadSession(session.session_id);
        const metaDiv = document.createElement('div');
        metaDiv.className = 'session-meta';
        metaDiv.innerHTML = `<span>${session.message_count} messages</span><span>${formatDate(session.created_at)}</span>`;
        // Delete button
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'delete-session-btn';
        deleteBtn.title = 'Delete session';
        deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
        deleteBtn.onclick = (e) => {
            e.stopPropagation();
            deleteSession(session.session_id);
        };
        sessionElement.appendChild(titleDiv);
        sessionElement.appendChild(metaDiv);
        sessionElement.appendChild(deleteBtn);
        sessionsList.appendChild(sessionElement);
    });
// Delete session function
async function deleteSession(sessionId) {
    if (!sessionId) return;
    if (!confirm('Are you sure you want to delete this chat session?')) return;
    try {
        const response = await fetch(`/api/sessions/${sessionId}`, { method: 'DELETE' });
        if (response.ok) {
            // If deleted session is current, create a new one
            if (sessionId === currentSessionId) {
                await createNewSession();
            } else {
                await loadSessions();
            }
        } else {
            showError('Failed to delete session');
        }
    } catch (error) {
        console.error('Error deleting session:', error);
        showError('Failed to delete session');
    }
}
// Add CSS for delete button
style.textContent += `
    .delete-session-btn {
        background: none;
        border: none;
        color: #e74c3c;
        font-size: 1rem;
        cursor: pointer;
        margin-left: 0.5rem;
        transition: color 0.2s;
    }
    .delete-session-btn:hover {
        color: #c0392b;
    }
`;
}

async function loadSession(sessionId) {
    try {
        const response = await fetch(`/api/sessions/${sessionId}`);
        const data = await response.json();
        
        if (data.success) {
            currentSessionId = sessionId;
            conversationHistory = data.session_data.messages || [];
            displaySessionMessages();
            renderSessions();
            closeSidebar();
        }
    } catch (error) {
        console.error('Error loading session:', error);
        showError('Failed to load session');
    }
}

function displaySessionMessages() {
    clearChatDisplay();
    
    conversationHistory.forEach(msg => {
        addMessage(msg.content, msg.role, false, false);
    });
    
    scrollToBottom();
}

function clearChatDisplay() {
    const messages = chatMessages.querySelectorAll('.message');
    messages.forEach(message => message.remove());
}

async function exportCurrentSession() {
    if (!currentSessionId) {
        showError('No active session to export');
        return;
    }
    
    try {
        const response = await fetch(`/api/sessions/${currentSessionId}/export`);
        const text = await response.text();
        
        // Create download
        const blob = new Blob([text], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat-export-${new Date().toISOString().slice(0, 10)}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    } catch (error) {
        console.error('Error exporting session:', error);
        showError('Failed to export session');
    }
}

async function clearCurrentSession() {
    if (!currentSessionId) {
        return;
    }
    
    if (confirm('Are you sure you want to clear this chat session?')) {
        try {
            await fetch(`/api/sessions/${currentSessionId}`, {
                method: 'DELETE'
            });
            
            await createNewSession();
        } catch (error) {
            console.error('Error clearing session:', error);
            showError('Failed to clear session');
        }
    }
}

// File Upload Functions
function toggleFileUpload() {
    const isVisible = fileUploadArea.style.display !== 'none';
    fileUploadArea.style.display = isVisible ? 'none' : 'block';
}

function setupFileDragDrop() {
    const uploadZone = document.querySelector('.upload-zone');
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadZone.addEventListener(eventName, preventDefaults, false);
    });
    
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadZone.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadZone.addEventListener(eventName, unhighlight, false);
    });
    
    uploadZone.addEventListener('drop', handleDrop, false);
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight(e) {
    e.currentTarget.classList.add('highlight');
}

function unhighlight(e) {
    e.currentTarget.classList.remove('highlight');
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    
    if (files.length > 0) {
        uploadFile(files[0]);
    }
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        uploadFile(file);
    }
}

async function uploadFile(file) {
    try {
        const formData = new FormData();
        formData.append('file', file);
        if (currentSessionId) {
            formData.append('session_id', currentSessionId);
        }
        
        // Show upload progress
        addMessage(`📎 Uploading ${file.name}...`, 'user', false, true);
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        // Remove upload message
        const uploadMsg = chatMessages.querySelector('.message:last-child');
        if (uploadMsg) uploadMsg.remove();
        
        if (data.success) {
            // Add file upload message
            const fileMessage = `📎 Uploaded: ${data.filename}\n\n${data.content_preview}`;
            addMessage(fileMessage, 'user');
            
            // Add to conversation history
            conversationHistory.push({
                role: 'user',
                content: fileMessage,
                timestamp: new Date().toISOString()
            });
            
            // Hide upload area
            fileUploadArea.style.display = 'none';
            
            // Clear file input
            fileInput.value = '';
            
            // You can automatically send a message about the file
            setTimeout(() => {
                sendAutoMessage(`I've uploaded a file (${file.name}). Can you help me analyze or work with this content?`);
            }, 500);
        } else {
            showError(data.error || 'Failed to upload file');
        }
    } catch (error) {
        console.error('Error uploading file:', error);
        showError('Failed to upload file');
    }
}

async function sendAutoMessage(message) {
    messageInput.value = message;
    updateSendButton();
    await sendMessage();
}

// Send message function
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || isTyping) return;

    // Clear input
    messageInput.value = '';
    adjustTextareaHeight();
    updateSendButton();

    // Add user message to chat
    addMessage(message, 'user');
    
    // Add to conversation history
    conversationHistory.push({
        role: 'user',
        content: message,
        timestamp: new Date().toISOString()
    });

    // Show typing indicator
    showTypingIndicator();
    
    try {
        // Send request to backend
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                conversation_history: conversationHistory.slice(-10), // Keep last 10 messages for context
                session_id: currentSessionId
            })
        });

        const data = await response.json();

        if (data.success) {
            // Add bot response to chat
            addMessage(data.response, 'bot');
            
            // Add to conversation history
            conversationHistory.push({
                role: 'assistant',
                content: data.response,
                timestamp: new Date().toISOString()
            });
            
            // Update session ID if new session was created
            if (data.session_id && data.session_id !== currentSessionId) {
                currentSessionId = data.session_id;
                loadSessions();
            }
        } else {
            throw new Error(data.error || 'Unknown error occurred');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        showError('Failed to send message. Please check your internet connection and try again.');
        
        // Add error message to chat
        addMessage('Sorry, I encountered an error while processing your request. Please try again.', 'bot', true);
    } finally {
        hideTypingIndicator();
        messageInput.focus();
    }
}

// Add message to chat
function addMessage(content, sender, isError = false, isTemporary = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender} ${isTemporary ? 'temporary' : ''}`;
    
    let avatarHtml = '';
    if (sender === 'user') {
        avatarHtml = '<div class="avatar user-avatar"><i class="fas fa-user"></i></div>';
    } else {
        avatarHtml = '<div class="avatar bot-avatar"><i class="fas fa-robot"></i></div>';
    }
    
    const bubbleClass = isError ? 'message-bubble error' : 'message-bubble';
    
    messageDiv.innerHTML = `
        ${avatarHtml}
        <div class="${bubbleClass}">
            ${formatMessage(content)}
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// Format message content
function formatMessage(content) {
    // Convert newlines to <br> tags
    content = content.replace(/\n/g, '<br>');
    
    // Convert **bold** to <strong>
    content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Convert *italic* to <em>
    content = content.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Convert `code` to <code>
    content = content.replace(/`(.*?)`/g, '<code>$1</code>');
    
    // File attachment styling
    if (content.startsWith('📎')) {
        content = content.replace('📎', '<i class="fas fa-paperclip"></i>');
    }
    
    return content;
}

// Sidebar functions
function toggleSidebar() {
    sidebar.classList.toggle('open');
}

function closeSidebar() {
    sidebar.classList.remove('open');
}

// New Chat button handler
document.addEventListener('DOMContentLoaded', function() {
    const newChatBtn = document.querySelector('.new-chat-btn');
    if (newChatBtn) {
        newChatBtn.addEventListener('click', function() {
            createNewSession();
        });
    }
});

// Show typing indicator
function showTypingIndicator() {
    isTyping = true;
    typingIndicator.style.display = 'flex';
    updateSendButton();
    scrollToBottom();
}

// Hide typing indicator
function hideTypingIndicator() {
    isTyping = false;
    typingIndicator.style.display = 'none';
    updateSendButton();
}

// Scroll to bottom of chat
function scrollToBottom() {
    setTimeout(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 100);
}

// Show error modal
function showError(message) {
    errorMessage.textContent = message;
    errorModal.style.display = 'flex';
}

// Close error modal
function closeModal() {
    errorModal.style.display = 'none';
}

// Close modal when clicking outside
errorModal.addEventListener('click', function(event) {
    if (event.target === errorModal) {
        closeModal();
    }
});

// Utility functions
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) {
        return 'Today';
    } else if (diffDays === 2) {
        return 'Yesterday';
    } else if (diffDays <= 7) {
        return `${diffDays - 1} days ago`;
    } else {
        return date.toLocaleDateString();
    }
}

// Health check function
async function checkHealth() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        console.log('Health check:', data);
    } catch (error) {
        console.error('Health check failed:', error);
    }
}

// Check health on load
checkHealth();

// Add some CSS for new features
const style = document.createElement('style');
style.textContent = `
    .message-bubble.error {
        background: #ffeaea !important;
        border-color: #ffcdd2 !important;
        color: #c62828 !important;
    }
    
    .message.temporary {
        opacity: 0.7;
    }
    
    .upload-zone.highlight {
        border-color: #667eea !important;
        background: #f0f4ff !important;
    }
    
    code {
        background: rgba(0, 0, 0, 0.1);
        padding: 2px 4px;
        border-radius: 3px;
        font-family: 'Courier New', monospace;
        font-size: 0.9em;
    }
    
    .sidebar.open {
        transform: translateX(0) !important;
    }
    
    @media (max-width: 768px) {
        .sidebar {
            transform: translateX(-100%);
        }
    }
`;
document.head.appendChild(style);

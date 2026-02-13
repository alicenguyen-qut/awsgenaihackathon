let currentChatId = null;
let currentUsername = '';

function toggleSidebar() {
    document.querySelector('.sidebar').classList.toggle('hidden');
}

const textarea = document.getElementById('userInput');
textarea.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 200) + 'px';
});

async function login() {
    const username = document.getElementById('usernameInput').value.trim();
    const password = document.getElementById('passwordInput').value.trim();
    
    if (!username) {
        alert('Please enter your name');
        return;
    }
    
    if (!password) {
        alert('Please enter a password');
        return;
    }
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentUsername = username;
            document.getElementById('userName').textContent = username;
            document.getElementById('userAvatar').textContent = username.charAt(0).toUpperCase();
            document.getElementById('loginModal').classList.add('hidden');
            await loadSession();
        } else {
            alert(data.error || 'Login failed');
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('Login failed. Please try again.');
    }
}

function handleLoginKeyPress(event) {
    if (event.key === 'Enter') login();
}

async function loadSession() {
    try {
        const response = await fetch('/api/session');
        const data = await response.json();
        
        if (data.username) {
            currentUsername = data.username;
            document.getElementById('userName').textContent = data.username;
            document.getElementById('userAvatar').textContent = data.username.charAt(0).toUpperCase();
            document.getElementById('loginModal').classList.add('hidden');
        } else {
            document.getElementById('loginModal').classList.remove('hidden');
        }
        
        renderChatList(data.chats || []);
        if (data.current_chat) {
            loadChat(data.current_chat);
        }
    } catch (error) {
        console.error('Load session error:', error);
    }
}

function renderChatList(chats) {
    const chatList = document.getElementById('chatList');
    const currentHTML = chatList.innerHTML;
    const newHTML = chats.map(chat => `
        <div class="chat-item ${chat.id === currentChatId ? 'active' : ''}" onclick="loadChat('${chat.id}')">
            <div class="chat-item-title">${chat.title}</div>
            <div class="chat-item-date">${new Date(chat.created_at).toLocaleDateString()}</div>
            <button class="delete-chat" onclick="event.stopPropagation(); deleteChat('${chat.id}')">×</button>
        </div>
    `).join('');
    
    if (currentHTML !== newHTML) {
        chatList.innerHTML = newHTML;
    }
}

async function createNewChat() {
    const response = await fetch('/api/chat/new', { method: 'POST' });
    const data = await response.json();
    currentChatId = data.chat_id;
    showWelcomeMessage();
    await loadSession();
}

function showWelcomeMessage() {
    document.getElementById('chatContainer').innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">🍳</div>
            <h2>Your Personal Cooking Assistant</h2>
            <p>Get personalized recipes, nutrition advice, and meal planning help!</p>
            <div class="suggestions">
                <div class="suggestion-card" onclick="sendSuggestion('Show me high-protein low-carb recipes')">
                    <div class="suggestion-icon">💪</div>
                    <div class="suggestion-title">High-Protein Meals</div>
                    <div class="suggestion-desc">Discover delicious low-carb recipes perfect for building muscle and staying energized</div>
                </div>
                <div class="suggestion-card" onclick="sendSuggestion('I need a vegan dinner idea')">
                    <div class="suggestion-icon">🌱</div>
                    <div class="suggestion-title">Vegan Recipes</div>
                    <div class="suggestion-desc">Explore plant-based meals that are nutritious, flavorful, and easy to prepare</div>
                </div>
                <div class="suggestion-card" onclick="sendSuggestion('Quick breakfast under 15 minutes')">
                    <div class="suggestion-icon">⏰</div>
                    <div class="suggestion-title">Quick Breakfast</div>
                    <div class="suggestion-desc">Fast and healthy morning meals to kickstart your day in under 15 minutes</div>
                </div>
                <div class="suggestion-card" onclick="sendSuggestion('Healthy meal for weight loss')">
                    <div class="suggestion-icon">🥗</div>
                    <div class="suggestion-title">Weight Loss Meals</div>
                    <div class="suggestion-desc">Nutritious low-calorie recipes that help you reach your health goals</div>
                </div>
            </div>
        </div>
    `;
}

async function loadChat(chatId) {
    const response = await fetch(`/api/chat/${chatId}`);
    const chat = await response.json();
    currentChatId = chatId;
    
    const container = document.getElementById('chatContainer');
    container.innerHTML = '';
    
    chat.messages.forEach(msg => {
        addMessage(msg.content, msg.role === 'user');
    });
    
    document.querySelectorAll('.chat-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[onclick="loadChat('${chatId}')"]`)?.classList.add('active');
}

async function deleteChat(chatId) {
    if (confirm('Delete this chat?')) {
        await fetch(`/api/chat/${chatId}`, { method: 'DELETE' });
        await loadSession();
    }
}

async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const files = fileInput.files;
    if (!files.length) return;
    
    for (let file of files) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/upload', { method: 'POST', body: formData });
        const data = await response.json();
    }
    
    await loadFiles();
    fileInput.value = '';
}

async function loadFiles() {
    const response = await fetch('/api/files');
    const data = await response.json();
    renderFileList(data.files || []);
}

function renderFileList(files) {
    const fileList = document.getElementById('fileList');
    if (!fileList) return;
    
    if (files.length === 0) {
        fileList.innerHTML = '<div style="padding: 12px; color: #718096; font-size: 13px;">No files uploaded</div>';
        return;
    }
    
    fileList.innerHTML = files.map(file => `
        <div class="file-item" onclick="viewFile('${file.id}')">
            <div class="file-icon">📄</div>
            <div class="file-name">${file.filename}</div>
            <button class="delete-file" onclick="event.stopPropagation(); deleteFile('${file.id}')">×</button>
        </div>
    `).join('');
}

async function viewFile(fileId) {
    const response = await fetch(`/api/files/${fileId}`);
    const data = await response.json();
    
    if (data.filename) {
        const modal = document.getElementById('fileModal');
        document.getElementById('fileModalTitle').textContent = data.filename;
        
        if (data.filename.endsWith('.txt') || data.filename.endsWith('.docx')) {
            document.getElementById('fileModalContent').textContent = data.content;
        } else {
            document.getElementById('fileModalContent').textContent = 'This file format cannot be displayed. Only .txt files are supported.';
        }
        
        modal.classList.remove('hidden');
    }
}

function closeFileModal() {
    document.getElementById('fileModal').classList.add('hidden');
}

async function deleteFile(fileId) {
    if (confirm('Delete this file?')) {
        await fetch(`/api/files/${fileId}`, { method: 'DELETE' });
        await loadFiles();
    }
}

function addMessage(content, isUser) {
    const container = document.getElementById('chatContainer');
    const welcome = container.querySelector('.welcome-message');
    if (welcome) welcome.remove();
    
    const div = document.createElement('div');
    div.className = `message ${isUser ? 'user' : 'bot'}`;
    const avatar = isUser ? currentUsername.charAt(0).toUpperCase() : '🤖';
    div.innerHTML = `
        <div class="message-inner">
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">${content.replace(/\n/g, '<br>')}</div>
        </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

async function sendMessage() {
    const input = document.getElementById('userInput');
    const query = input.value.trim();
    if (!query) return;
    
    addMessage(query, true);
    input.value = '';
    input.style.height = 'auto';
    
    const sendBtn = document.getElementById('sendBtn');
    const loading = document.getElementById('loading');
    sendBtn.disabled = true;
    loading.classList.add('active');
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({query})
        });
        const data = await response.json();
        addMessage(data.response, false);
    } catch (error) {
        addMessage('Error connecting', false);
    } finally {
        sendBtn.disabled = false;
        loading.classList.remove('active');
    }
}

function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

function sendSuggestion(text) {
    document.getElementById('userInput').value = text;
    sendMessage();
}

loadSession();
loadFiles();

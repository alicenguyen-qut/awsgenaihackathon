// Chat Management
let currentChatId = null;

async function createNewChat() {
    const response = await fetch('/api/chat/new', { method: 'POST' });
    const data = await response.json();
    currentChatId = data.chat_id;
    showWelcomeMessage();
    await loadSession();
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

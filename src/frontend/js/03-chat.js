// Chat functionality - list, messages, send/receive

// Simple markdown renderer: bold, italic, headers, bullet/numbered lists, inline code
function renderMarkdown(text) {
    let html = text
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/^### (.+)$/gm, '<h4 style="margin:10px 0 4px;color:#2d3748;font-size:15px;">$1</h4>')
        .replace(/^## (.+)$/gm, '<h3 style="margin:12px 0 6px;color:#2d3748;font-size:16px;">$1</h3>')
        .replace(/^# (.+)$/gm, '<h2 style="margin:14px 0 8px;color:#2d3748;font-size:18px;">$1</h2>')
        .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code style="background:#f0f0f0;padding:2px 5px;border-radius:4px;font-size:13px;">$1</code>');
    // Bullet lists
    html = html.replace(/((?:^[•\-\*] .+(?:\n|$))+)/gm, (block) => {
        const items = block.trim().split('\n').map(l => `<li>${l.replace(/^[•\-\*] /, '')}</li>`).join('');
        return `<ul style="margin:6px 0 6px 18px;">${items}</ul>`;
    });
    // Numbered lists - merge items even when separated by blank lines
    html = html.replace(/((?:^\d+\. .+$\n?)+)/gm, (block) => {
        const items = block.trim().split('\n').filter(l => /^\d+\./.test(l.trim())).map(l => `<li>${l.replace(/^\d+\. /, '')}</li>`).join('');
        return `<ol style="margin:6px 0 6px 18px;">${items}</ol>`;
    });
    html = html.replace(/<\/ol>(\n|<br>)*<ol[^>]*>/g, '');
    return html.replace(/\n/g, '<br>');
}

// Chat list management
async function createNewChat() {
    const response = await fetch('/api/chat/new', { method: 'POST' });
    const data = await response.json();
    currentChatId = data.chat_id;
    showWelcomeMessage();
    // Reload session but don't load the chat content (keep welcome message)
    const sessionResponse = await fetch('/api/session');
    const sessionData = await sessionResponse.json();
    if (typeof renderChatList === 'function' && sessionData.chats) {
        renderChatList(sessionData.chats);
    }
}

function renderChatList(chats) {
    const chatList = document.getElementById('chatList');
    chatList.innerHTML = chats.map(chat => `
        <div class="chat-item ${chat.id === currentChatId ? 'active' : ''}" onclick="loadChat('${chat.id}')">
            <div class="chat-item-title">${chat.title}</div>
            <div class="chat-item-date">${new Date(chat.created_at).toLocaleDateString()}</div>
            <button class="delete-chat" onclick="event.stopPropagation(); deleteChat('${chat.id}')">×</button>
        </div>
    `).join('');
}

async function loadChat(chatId) {
    const response = await fetch(`/api/chat/${chatId}`);
    const chat = await response.json();
    currentChatId = chatId;
    
    const container = document.getElementById('chatContainer');
    container.innerHTML = '';
    chat.messages.forEach(msg => addMessage(msg.content, msg.role === 'user'));
    
    document.querySelectorAll('.chat-item').forEach(item => item.classList.remove('active'));
    document.querySelector(`[onclick="loadChat('${chatId}')"]`)?.classList.add('active');
}

async function deleteChat(chatId) {
    showConfirm('Delete this chat?', async () => {
        await fetch(`/api/chat/${chatId}`, { method: 'DELETE' });
        if (currentChatId === chatId) {
            currentChatId = null;
            const container = document.getElementById('chatContainer');
            container.innerHTML = '';
            showWelcomeMessage();
        }
        await loadSession();
        showAlert('Chat deleted!', 'info');
    });
}

// Message handling
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
            <div class="message-content">${isUser ? content.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br>') : renderMarkdown(content)}</div>
        </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

let _statusInterval = null;

function showStatus(el, message) {
    const base = message.replace(/\.+$/, '');
    let dots = 0;
    clearInterval(_statusInterval);
    el.innerHTML = `<span class="stream-status">${base}</span>`;
    const span = el.querySelector('.stream-status');
    _statusInterval = setInterval(() => {
        dots = (dots % 3) + 1;
        span.textContent = base + '.'.repeat(dots);
    }, 400);
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

    // Create bot message bubble for streaming
    const container = document.getElementById('chatContainer');
    const botDiv = document.createElement('div');
    botDiv.className = 'message bot';
    botDiv.innerHTML = `
        <div class="message-inner">
            <div class="message-avatar">🤖</div>
            <div class="message-content"></div>
            </div>
        </div>`;
    container.appendChild(botDiv);
    container.scrollTop = container.scrollHeight;
    const contentEl = botDiv.querySelector('.message-content');

    showStatus(contentEl, '✨ Thinking...');

    let fullResponse = '';
    let toolCalls = [];

    try {
        const response = await fetch('/chat/stream', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({query})
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });

            const parts = buffer.split('\n\n');
            buffer = parts.pop(); // keep incomplete chunk

            for (const part of parts) {
                const eventMatch = part.match(/^event: (\w+)/);
                const dataMatch = part.match(/^data: (.+)/m);
                if (!eventMatch || !dataMatch) continue;

                const event = eventMatch[1];
                const data = JSON.parse(dataMatch[1]);

                if (event === 'status') {
                    showStatus(contentEl, data.message);
                    container.scrollTop = container.scrollHeight;
                } else if (event === 'tool_action') {
                    clearInterval(_statusInterval);
                    contentEl.querySelectorAll('.tool-status').forEach(e => e.remove());
                    const friendlyLabels = {
                        'search_recipes': '🔍 Searching recipes',
                        'add_to_meal_plan': '📅 Updating meal plan',
                        'add_to_shopping_list': '🛒 Updating shopping list',
                        'add_to_favorites': '⭐ Saving to favourites',
                        'log_nutrition': '📊 Logging nutrition',
                        'get_nutrition_stats': '📈 Checking nutrition stats'
                    };
                    const base = friendlyLabels[data.tool] || `⚙️ ${data.tool.replace(/_/g, ' ')}`;
                    const statusEl = document.createElement('div');
                    statusEl.className = 'tool-status';
                    statusEl.style.cssText = 'font-size:12px;color:#888;margin:4px 0;';
                    statusEl.textContent = base + '...';
                    contentEl.appendChild(statusEl);
                    let dots = 0;
                    _statusInterval = setInterval(() => { dots = (dots % 3) + 1; statusEl.textContent = base + '.'.repeat(dots); }, 400);
                    container.scrollTop = container.scrollHeight;
                } else if (event === 'token') {
                    if (fullResponse === '') {
                        clearInterval(_statusInterval);
                        contentEl.querySelectorAll('.stream-status, .tool-status').forEach(e => e.remove());
                    }
                    fullResponse += data.text;
                    // preserve tool pills, update only the text node after them
                    let textNode = contentEl.querySelector('.chat-response-text');
                    if (!textNode) {
                        textNode = document.createElement('div');
                        textNode.className = 'chat-response-text';
                        contentEl.appendChild(textNode);
                    }
                    textNode.innerHTML = renderMarkdown(fullResponse);
                    container.scrollTop = container.scrollHeight;
                } else if (event === 'done') {
                    clearInterval(_statusInterval);
                    contentEl.querySelectorAll('.stream-status, .tool-status').forEach(e => e.remove());
                    toolCalls = data.tool_calls || [];
                } else if (event === 'suggestions') {
                    const chips = document.createElement('div');
                    chips.style.cssText = 'display:flex;flex-wrap:wrap;gap:8px;margin-top:10px;';
                    chips.innerHTML = data.items.map(s =>
                        `<button onclick="document.getElementById('userInput').value=this.dataset.q;sendMessage()" data-q="${s.replace(/"/g,'&quot;')}" style="background:#f0f4ff;border:1px solid #c3d0f5;border-radius:16px;padding:6px 12px;font-size:13px;cursor:pointer;color:#3d5a99;">${s}</button>`
                    ).join('');
                    contentEl.appendChild(chips);
                    container.scrollTop = container.scrollHeight;
                } else if (event === 'error') {
                    contentEl.innerHTML = `<span style="color:red;">Error: ${data.message}</span>`;
                }
            }
        }

        // Handle tool calls
        const mutatingTools = ['add_to_favorites', 'add_to_meal_plan', 'add_to_shopping_list', 'log_nutrition'];
        const actionableCalls = toolCalls.filter(c => mutatingTools.includes(c.tool));
        if (actionableCalls.length > 0) {
            displayToolCalls(actionableCalls);
            await loadAgentContext();
            if (!document.getElementById('mealPlannerModal').classList.contains('hidden')) loadMealPlan();
            if (!document.getElementById('shoppingListModal').classList.contains('hidden')) loadShoppingList();
            if (actionableCalls.some(c => c.tool === 'log_nutrition')) {
                if (!document.getElementById('dailyTrackerModal').classList.contains('hidden')) await updateDashboard();
            }
        }

        if (actionableCalls.length === 0) {
            const actions = await executeAgentActions(query, fullResponse);
            if (actions && actions.length > 0) {
                displayAgentActions(actions);
                await loadAgentContext();
            }
        }
    } catch (error) {
        contentEl.innerHTML = 'Error connecting';
    } finally {
        sendBtn.disabled = false;
        loading.classList.remove('active');
    }
}

function displayToolCalls(toolCalls) {
    const container = document.getElementById('chatContainer');
    const actionsDiv = document.createElement('div');
    actionsDiv.style.cssText = 'margin: 20px 0; padding: 16px; background: linear-gradient(135deg, rgba(195, 240, 202, 0.2), rgba(116, 185, 255, 0.1)); border-left: 4px solid #74b9ff; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);';
    
    const toolIcons = {
        'search_recipes': '🔍',
        'add_to_favorites': '⭐',
        'add_to_meal_plan': '📅',
        'add_to_shopping_list': '🛒',
        'log_nutrition': '📊',
        'get_nutrition_stats': '📈'
    };
    
    actionsDiv.innerHTML = `
        <div style="font-weight: 700; color: #2d3748; margin-bottom: 12px; font-size: 15px; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 20px;">🤖</span>
            <span>Agent Actions Completed</span>
        </div>
        ${toolCalls.map(call => {
            const icon = toolIcons[call.tool] || '🔧';
            const result = call.result || {};
            const message = result.message || JSON.stringify(result);
            return `
                <div style="font-size: 14px; color: #4a5568; margin: 8px 0; padding: 10px; background: white; border-radius: 8px; display: flex; align-items: start; gap: 10px;">
                    <span style="font-size: 18px;">${icon}</span>
                    <div style="flex: 1;">
                        <div style="font-weight: 600; color: #2d3748; margin-bottom: 4px;">${call.tool.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</div>
                        <div style="color: #718096;">${message}</div>
                    </div>
                </div>
            `;
        }).join('')}
    `;
    
    container.appendChild(actionsDiv);
    container.scrollTop = container.scrollHeight;
}

function sendSuggestion(text) {
    document.getElementById('userInput').value = text;
    sendMessage();
}

function showWelcomeMessage() {
    document.getElementById('chatContainer').innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">🍳</div>
            <h2>MealBuddy 🍳</h2>
                    <p style="font-size:15px; color:#8b6f8f; font-style:italic; margin-bottom:8px;">Your Personalised AI Nutrition Buddy</p>
            <div class="suggestions">
                <div class="suggestion-card" onclick="sendSuggestion('Show me high-protein low-carb meal ideas')">
                    <div class="suggestion-icon">💪</div>
                    <div class="suggestion-title">High-Protein Meals</div>
                    <div class="suggestion-desc">Discover delicious low-carb recipes perfect for building muscle and staying energized</div>
                </div>
                <div class="suggestion-card" onclick="sendSuggestion('I need a vegan dinner idea')">
                    <div class="suggestion-icon">🌱</div>
                    <div class="suggestion-title">Vegan Meals</div>
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

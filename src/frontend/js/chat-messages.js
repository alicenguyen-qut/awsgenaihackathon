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
        
        // Execute autonomous agent actions
        const actions = await executeAgentActions(query, data.response);
        if (actions && actions.length > 0) {
            displayAgentActions(actions);
            await loadAgentContext(); // Refresh context
        }
    } catch (error) {
        addMessage('Error connecting', false);
    } finally {
        sendBtn.disabled = false;
        loading.classList.remove('active');
    }
}

function sendSuggestion(text) {
    document.getElementById('userInput').value = text;
    sendMessage();
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

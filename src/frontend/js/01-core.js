// Core UI utilities and initialization

// Shared state
let currentUsername = '';
let currentChatId = null;

function toggleSidebar() {
    document.querySelector('.sidebar').classList.toggle('hidden');
}

function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    const textarea = document.getElementById('userInput');
    if (textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 200) + 'px';
        });
    }
    
    // Initialize after other scripts load
    setTimeout(() => {
        if (typeof loadSession === 'function') loadSession();
        if (typeof loadFiles === 'function') loadFiles();
    }, 100);
});

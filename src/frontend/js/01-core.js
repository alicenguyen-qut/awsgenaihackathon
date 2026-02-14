// Core UI utilities and initialization

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
    
    loadSession();
    loadFiles();
});

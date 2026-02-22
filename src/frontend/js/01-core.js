// Core UI utilities and initialization

// Shared state
let currentUsername = '';
let currentChatId = null;

// Beautiful confirmation/alert modals
function showAlert(message, type = 'success') {
    const colors = {
        success: { bg: '#c3f0ca', icon: '✅' },
        error: { bg: '#fab1a0', icon: '❌' },
        info: { bg: '#74b9ff', icon: 'ℹ️' },
        warning: { bg: '#ffeaa7', icon: '⚠️' }
    };
    const color = colors[type] || colors.success;
    
    const alert = document.createElement('div');
    alert.style.cssText = `position: fixed; top: 20px; right: 20px; background: ${color.bg}; color: #2d3748; padding: 16px 24px; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.2); z-index: 9999; font-weight: 600; display: flex; align-items: center; gap: 12px; animation: slideInRight 0.3s ease;`;
    alert.innerHTML = `<span style="font-size: 20px;">${color.icon}</span><span>${message}</span>`;
    document.body.appendChild(alert);
    setTimeout(() => {
        alert.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => alert.remove(), 300);
    }, 3000);
}

function showConfirm(message, onConfirm) {
    const modal = document.createElement('div');
    modal.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); backdrop-filter: blur(10px); display: flex; align-items: center; justify-content: center; z-index: 9999; animation: fadeIn 0.3s;';
    
    modal.innerHTML = `
        <div style="background: white; padding: 32px; border-radius: 24px; max-width: 400px; width: 90%; box-shadow: 0 25px 60px rgba(0,0,0,0.4); animation: scaleIn 0.3s;">
            <div style="font-size: 48px; text-align: center; margin-bottom: 16px;">🤔</div>
            <p style="font-size: 16px; color: #2d3748; text-align: center; margin-bottom: 24px; line-height: 1.6;">${message}</p>
            <div style="display: flex; gap: 12px;">
                <button onclick="this.closest('div').parentElement.remove()" style="flex: 1; padding: 12px; background: #e2e8f0; color: #2d3748; border: none; border-radius: 12px; font-size: 14px; font-weight: 600; cursor: pointer;">Cancel</button>
                <button id="confirmBtn" style="flex: 1; padding: 12px; background: linear-gradient(135deg, #fab1a0 0%, #f8a390 100%); color: white; border: none; border-radius: 12px; font-size: 14px; font-weight: 600; cursor: pointer;">Confirm</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    modal.querySelector('#confirmBtn').onclick = () => {
        modal.remove();
        onConfirm();
    };
}

window.showAlert = showAlert;
window.showConfirm = showConfirm;

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

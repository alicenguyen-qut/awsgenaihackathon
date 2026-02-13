// Main integration for daily features
import { updateDashboard, getStreaks } from './nutrition-tracker.js';

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    // Update streaks on login
    try {
        const streaksData = await getStreaks();
        const streaksEl = document.getElementById('streaks-display');
        if (streaksEl && streaksData.streaks) {
            streaksEl.innerHTML = `
                <div style="font-size: 13px; font-weight: 600; color: #8b6f8f; margin-bottom: 8px;">🔥 Daily Streak</div>
                <div style="font-size: 36px; font-weight: 700; color: #2d3748; line-height: 1; margin: 4px 0;">${streaksData.streaks.current} days</div>
                <div style="font-size: 13px; color: #8b6f8f; font-weight: 500;">Best: ${streaksData.streaks.longest} days</div>
            `;
        }
    } catch (e) {
        console.log('Streaks not loaded yet');
    }
});

// Open daily tracker modal
window.openDailyTracker = async () => {
    console.log('Opening daily tracker...');
    document.getElementById('dailyTrackerModal').classList.remove('hidden');
    
    // Add time period selector
    const modal = document.getElementById('dailyTrackerModal');
    const header = modal.querySelector('.settings-header h2');
    header.innerHTML = `
        📊 Nutrition Analytics
        <select id="time-period" style="margin-left: 20px; padding: 5px; border-radius: 5px;">
            <option value="today">Today</option>
            <option value="week">This Week</option>
            <option value="month">This Month</option>
            <option value="year">This Year</option>
        </select>
    `;
    
    // Add change listener
    document.getElementById('time-period').addEventListener('change', updateDashboard);
    
    setTimeout(async () => {
        await updateDashboard();
    }, 50);
};

// Close daily tracker modal
window.closeDailyTracker = () => {
    document.getElementById('dailyTrackerModal').classList.add('hidden');
};

// Refresh dashboard when modal opens
const originalOpenSettings = window.openSettings;
window.openSettings = async function() {
    if (originalOpenSettings) originalOpenSettings();
    try {
        const streaksData = await getStreaks();
        // Could show streaks in settings too
    } catch (e) {}
};

// Nutrition tracking, streaks, analytics

async function logMeal(mealData) {
    const res = await fetch('/api/nutrition/log', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(mealData)
    });
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    return await res.json();
}

async function getTodayStats() {
    const res = await fetch(`/api/nutrition/stats?date=${new Date().toISOString().split('T')[0]}`);
    return res.ok ? await res.json() : { stats: { calories: 0, protein: 0, carbs: 0, fats: 0 }, meal_count: 0 };
}

async function getTodayLogs() {
    const res = await fetch(`/api/nutrition/logs?date=${new Date().toISOString().split('T')[0]}`);
    return res.ok ? await res.json() : { logs: [] };
}

async function deleteLog(logId) {
    const res = await fetch(`/api/nutrition/logs/${logId}`, {method: 'DELETE'});
    return res.json();
}

async function getStreaks() {
    const res = await fetch('/api/streaks');
    return res.json();
}

async function getDailyRecommendations() {
    const res = await fetch('/api/recommendations/daily');
    return res.json();
}

async function getAnalytics(period = 'today') {
    const res = await fetch(`/api/nutrition/analytics?period=${period}`);
    return res.json();
}

async function updateDashboard() {
    const period = document.getElementById('time-period')?.value || 'today';
    const [stats, logs, streaks, recs, analytics] = await Promise.all([
        getTodayStats(), getTodayLogs(), getStreaks(), getDailyRecommendations(), getAnalytics(period)
    ]);
    
    const statsEl = document.getElementById('nutrition-stats');
    if (statsEl) {
        if (period === 'today') {
            const s = stats.stats;
            statsEl.innerHTML = `
                <div class="stat"><span>Calories</span><strong>${s.calories}</strong></div>
                <div class="stat"><span>Protein</span><strong>${s.protein}g</strong></div>
                <div class="stat"><span>Carbs</span><strong>${s.carbs}g</strong></div>
                <div class="stat"><span>Fats</span><strong>${s.fats}g</strong></div>
            `;
        } else {
            const a = analytics.analytics;
            statsEl.innerHTML = `
                <div class="stat"><span>Avg Calories</span><strong>${Math.round(a.avgCalories)}</strong></div>
                <div class="stat"><span>Avg Protein</span><strong>${Math.round(a.avgProtein)}g</strong></div>
                <div class="stat"><span>Total Days</span><strong>${a.totalDays}</strong></div>
                <div class="stat"><span>Best Day</span><strong>${a.bestDay}cal</strong></div>
            `;
        }
    }
    
    const mealsEl = document.getElementById('today-meals');
    if (mealsEl) {
        if (period === 'today') {
            mealsEl.innerHTML = logs.logs.length === 0 
                ? '<p style="text-align: center; color: #718096; font-style: italic; padding: 20px;">No meals logged today. Click "+ Log Meal" to get started!</p>'
                : logs.logs.map(l => `
                    <div class="meal-log">
                        <span><strong>${l.meal_type}:</strong> ${l.name}</span>
                        <span>${l.calories} cal</span>
                        <button onclick="deleteMealLog('${l.id}')">×</button>
                    </div>
                `).join('');
        } else {
            const insights = analytics.insights || [];
            mealsEl.innerHTML = `
                <h4>📈 ${period.charAt(0).toUpperCase() + period.slice(1)} Insights</h4>
                ${insights.map(i => `<div style="padding: 8px; background: #f0f8ff; margin: 4px 0; border-radius: 6px;">${i}</div>`).join('')}
            `;
        }
    }
    
    const streaksEl = document.getElementById('streaks-display');
    if (streaksEl && streaks.streaks) {
        streaksEl.innerHTML = `
            <div style="font-size: 13px; font-weight: 600; color: #8b6f8f; margin-bottom: 8px;">🔥 Daily Streak</div>
            <div style="font-size: 36px; font-weight: 700; color: #2d3748; line-height: 1; margin: 4px 0;">${streaks.streaks.current} days</div>
            <div style="font-size: 13px; color: #8b6f8f; font-weight: 500;">Best: ${streaks.streaks.longest} days</div>
        `;
    }
    
    const recsEl = document.getElementById('recommendations');
    if (recsEl && recs.recommendations) {
        recsEl.innerHTML = recs.recommendations.length === 0 
            ? '<p>Great job! You\'re on track today.</p>'
            : recs.recommendations.map(r => r.type === 'meal' 
                ? `<div class="rec-card"><strong>${r.title}</strong> (${r.calories} cal, ${r.protein}g protein)<br><small>${r.reason}</small></div>`
                : `<div class="rec-tip">${r.message}</div>`
            ).join('');
    }
}

window.showLogMealModal = () => {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <h3>Log Meal</h3>
            <select id="meal-type"><option>Breakfast</option><option>Lunch</option><option>Dinner</option><option>Snack</option></select>
            <input id="meal-name" placeholder="Meal name" />
            <input id="meal-cal" type="number" placeholder="Calories" />
            <input id="meal-protein" type="number" placeholder="Protein (g)" />
            <input id="meal-carbs" type="number" placeholder="Carbs (g)" />
            <input id="meal-fats" type="number" placeholder="Fats (g)" />
            <button onclick="submitMealLog()">Save</button>
            <button onclick="this.closest('.modal').remove()">Cancel</button>
        </div>
    `;
    document.body.appendChild(modal);
};

window.submitMealLog = async () => {
    const data = {
        meal_type: document.getElementById('meal-type').value,
        name: document.getElementById('meal-name').value,
        calories: parseInt(document.getElementById('meal-cal').value) || 0,
        protein: parseInt(document.getElementById('meal-protein').value) || 0,
        carbs: parseInt(document.getElementById('meal-carbs').value) || 0,
        fats: parseInt(document.getElementById('meal-fats').value) || 0
    };
    
    if (!data.name.trim()) return alert('Please enter a meal name');
    
    await logMeal(data);
    document.querySelector('.modal').remove();
    await updateDashboard();
    alert('Meal logged successfully!');
};

window.deleteMealLog = async (logId) => {
    const result = await deleteLog(logId);
    if (result.success) {
        await updateDashboard();
        const msg = document.createElement('div');
        msg.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #e53e3e; color: white; padding: 12px 20px; border-radius: 8px; z-index: 9999; font-weight: 600;';
        msg.textContent = '🗑️ Meal deleted!';
        document.body.appendChild(msg);
        setTimeout(() => msg.remove(), 2000);
    }
};

window.openDailyTracker = async () => {
    document.getElementById('dailyTrackerModal').classList.remove('hidden');
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
    document.getElementById('time-period').addEventListener('change', updateDashboard);
    setTimeout(() => updateDashboard(), 50);
};

window.closeDailyTracker = () => {
    document.getElementById('dailyTrackerModal').classList.add('hidden');
};

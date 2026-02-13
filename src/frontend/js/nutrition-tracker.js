// Daily Nutrition Tracking, Streaks, and Recommendations

export async function logMeal(mealData) {
    try {
        const res = await fetch('/api/nutrition/log', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(mealData)
        });
        
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        
        return await res.json();
    } catch (error) {
        console.error('Error logging meal:', error);
        throw error;
    }
}

export async function getTodayStats() {
    try {
        const res = await fetch(`/api/nutrition/stats?date=${new Date().toISOString().split('T')[0]}`);
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        return await res.json();
    } catch (error) {
        console.error('Error getting stats:', error);
        return { stats: { calories: 0, protein: 0, carbs: 0, fats: 0 }, meal_count: 0 };
    }
}

export async function getTodayLogs() {
    try {
        const res = await fetch(`/api/nutrition/logs?date=${new Date().toISOString().split('T')[0]}`);
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        return await res.json();
    } catch (error) {
        console.error('Error getting logs:', error);
        return { logs: [] };
    }
}

export async function deleteLog(logId) {
    const res = await fetch(`/api/nutrition/logs/${logId}`, {method: 'DELETE'});
    return res.json();
}

export async function getStreaks() {
    const res = await fetch('/api/streaks');
    return res.json();
}

export async function getDailyRecommendations() {
    const res = await fetch('/api/recommendations/daily');
    return res.json();
}

export function renderNutritionTracker() {
    return `
        <div class="daily-tracker">
            <h3>📊 Today's Nutrition</h3>
            <div id="nutrition-stats" class="stats-grid"></div>
            <button onclick="window.showLogMealModal()" class="btn-primary">+ Log Meal</button>
            <div id="today-meals" class="meals-list"></div>
        </div>
    `;
}

export function renderStreaks(streaks) {
    return `
        <div class="streaks-card">
            <h3>🔥 Streak</h3>
            <div class="streak-number">${streaks.current} days</div>
            <div class="streak-best">Best: ${streaks.longest} days</div>
        </div>
    `;
}

export function renderRecommendations(recs) {
    if (!recs.length) return '<p>Great job! You\'re on track today.</p>';
    return recs.map(r => {
        if (r.type === 'meal') {
            return `<div class="rec-card">
                <strong>${r.title}</strong> (${r.calories} cal, ${r.protein}g protein)
                <br><small>${r.reason}</small>
            </div>`;
        }
        return `<div class="rec-tip">${r.message}</div>`;
    }).join('');
}

export async function getAnalytics(period = 'today') {
    const res = await fetch(`/api/nutrition/analytics?period=${period}`);
    return res.json();
}

export async function updateDashboard() {
    try {
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
                if (logs.logs.length === 0) {
                    mealsEl.innerHTML = '<p style="text-align: center; color: #718096; font-style: italic; padding: 20px;">No meals logged today. Click "+ Log Meal" to get started!</p>';
                } else {
                    mealsEl.innerHTML = logs.logs.map(l => `
                        <div class="meal-log">
                            <span><strong>${l.meal_type}:</strong> ${l.name}</span>
                            <span>${l.calories} cal</span>
                            <button onclick="window.deleteMealLog('${l.id}')">×</button>
                        </div>
                    `).join('');
                }
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
            streaksEl.innerHTML = renderStreaks(streaks.streaks);
        }
        
        const recsEl = document.getElementById('recommendations');
        if (recsEl && recs.recommendations) {
            recsEl.innerHTML = renderRecommendations(recs.recommendations);
        }
    } catch (error) {
        console.error('Error updating dashboard:', error);
    }
}

window.showLogMealModal = () => {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <h3>Log Meal</h3>
            <select id="meal-type">
                <option>Breakfast</option>
                <option>Lunch</option>
                <option>Dinner</option>
                <option>Snack</option>
            </select>
            <input id="meal-name" placeholder="Meal name" />
            <input id="meal-cal" type="number" placeholder="Calories" />
            <input id="meal-protein" type="number" placeholder="Protein (g)" />
            <input id="meal-carbs" type="number" placeholder="Carbs (g)" />
            <input id="meal-fats" type="number" placeholder="Fats (g)" />
            <button onclick="window.submitMealLog()">Save</button>
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
    
    if (!data.name.trim()) {
        alert('Please enter a meal name');
        return;
    }
    
    try {
        await logMeal(data);
        document.querySelector('.modal').remove();
        
        // Immediate DOM update
        const statsEl = document.getElementById('nutrition-stats');
        const mealsEl = document.getElementById('today-meals');
        
        // Add meal to display immediately
        if (mealsEl) {
            const mealHtml = `
                <div class="meal-log">
                    <span><strong>${data.meal_type}:</strong> ${data.name}</span>
                    <span>${data.calories} cal</span>
                    <button onclick="location.reload()">×</button>
                </div>
            `;
            if (mealsEl.innerHTML.includes('No meals logged')) {
                mealsEl.innerHTML = mealHtml;
            } else {
                mealsEl.innerHTML += mealHtml;
            }
        }
        
        // Update stats immediately
        if (statsEl) {
            const currentStats = {
                calories: parseInt(statsEl.querySelector('.stat:nth-child(1) strong')?.textContent || '0') + data.calories,
                protein: parseInt(statsEl.querySelector('.stat:nth-child(2) strong')?.textContent || '0') + data.protein,
                carbs: parseInt(statsEl.querySelector('.stat:nth-child(3) strong')?.textContent || '0') + data.carbs,
                fats: parseInt(statsEl.querySelector('.stat:nth-child(4) strong')?.textContent || '0') + data.fats
            };
            
            statsEl.innerHTML = `
                <div class="stat"><span>Calories</span><strong>${currentStats.calories}</strong></div>
                <div class="stat"><span>Protein</span><strong>${currentStats.protein}g</strong></div>
                <div class="stat"><span>Carbs</span><strong>${currentStats.carbs}g</strong></div>
                <div class="stat"><span>Fats</span><strong>${currentStats.fats}g</strong></div>
            `;
        }
        
        alert('Meal logged successfully!');
    } catch (error) {
        alert('Error logging meal');
    }
};

window.deleteMealLog = async (logId) => {
    try {
        const result = await deleteLog(logId);
        if (result.success) {
            // Force update dashboard if modal is open
            if (!document.getElementById('dailyTrackerModal').classList.contains('hidden')) {
                await updateDashboard();
            }
            
            // Show success feedback
            const successMsg = document.createElement('div');
            successMsg.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #e53e3e; color: white; padding: 12px 20px; border-radius: 8px; z-index: 9999; font-weight: 600;';
            successMsg.textContent = '🗑️ Meal deleted!';
            document.body.appendChild(successMsg);
            setTimeout(() => successMsg.remove(), 2000);
        }
    } catch (error) {
        console.error('Error deleting meal:', error);
        alert('Error deleting meal. Please try again.');
    }
};

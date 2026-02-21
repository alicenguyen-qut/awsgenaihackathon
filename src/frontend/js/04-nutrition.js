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

function getLocalDate() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
}

async function getTodayStats() {
    const res = await fetch(`/api/nutrition/stats?date=${getLocalDate()}`);
    return res.ok ? await res.json() : { stats: { calories: 0, protein: 0, carbs: 0, fats: 0 }, meal_count: 0 };
}

async function getTodayLogs() {
    const res = await fetch(`/api/nutrition/logs?date=${getLocalDate()}`);
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

async function getLogsForDate(date) {
    const res = await fetch(`/api/nutrition/logs?date=${date}`);
    return res.ok ? await res.json() : { logs: [] };
}

async function getStatsForDate(date) {
    const res = await fetch(`/api/nutrition/stats?date=${date}`);
    return res.ok ? await res.json() : { stats: { calories: 0, protein: 0, carbs: 0, fats: 0 } };
}

async function updateDashboard() {
    const period = document.getElementById('time-period')?.value || 'today';
    const selectedDate = document.getElementById('selected-date')?.value || getLocalDate();

    const [stats, logs, streaks, recs, analytics] = await Promise.all([
        getStatsForDate(selectedDate), getLogsForDate(selectedDate),
        getStreaks(), getDailyRecommendations(), getAnalytics(period)
    ]);

    // Show/hide date picker based on period
    const datePicker = document.getElementById('date-picker-row');
    if (datePicker) datePicker.style.display = period === 'today' ? 'flex' : 'none';

    const statsEl = document.getElementById('nutrition-stats');
    if (statsEl) {
        if (period === 'today') {
            const s = stats.stats;
            const goal = stats.calorie_goal || 2000;
            const remaining = stats.calories_remaining ?? Math.max(0, goal - s.calories);
            const pct = Math.min(100, Math.round((s.calories / goal) * 100));
            const over = s.calories > goal;
            const barColor = over ? 'linear-gradient(90deg,#fc8181,#e53e3e)' : pct >= 75 ? 'linear-gradient(90deg,#f6ad55,#ed8936)' : 'linear-gradient(90deg,#74b9ff,#a29bfe)';
            const b = stats.goal_breakdown || {};
            const goalNote = b.method === 'mifflin'
                ? `<div style="margin-top:12px;padding:10px 14px;background:rgba(116,185,255,0.08);border-radius:10px;border-left:3px solid #74b9ff;font-size:12px;color:#4a5568;line-height:1.7;">
                    <span style="font-weight:700;color:#2b6cb0;">📐 How your goal was calculated</span><br>
                    Mifflin-St Jeor BMR: <strong>${b.bmr} cal</strong><br>
                    × 1.375 activity factor → TDEE: <strong>${b.tdee} cal</strong><br>
                    ${b.adjustment !== 0 ? `Goal adjustment (${b.inputs?.health_goal}): <strong>${b.adjustment > 0 ? '+' : ''}${b.adjustment} cal</strong><br>` : ''}
                    Daily goal: <strong>${b.goal} cal</strong>
                   </div>`
                : `<div style="margin-top:12px;padding:8px 14px;background:rgba(160,174,192,0.08);border-radius:10px;border-left:3px solid #a0aec0;font-size:12px;color:#718096;">
                    💡 Goal based on <strong>${b.health_goal || 'default'}</strong> preset. Add your age, weight, height &amp; gender in Settings for a personalised goal.
                   </div>`;
            statsEl.style.display = 'block';
            statsEl.innerHTML = `
                <div style="background:linear-gradient(135deg,#f8f9ff,#f0f4ff);border:1px solid rgba(116,185,255,0.2);border-radius:20px;padding:20px 24px;">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px;">
                        <div>
                            <div style="font-size:11px;font-weight:700;color:#a0aec0;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">🔥 Calories Today</div>
                            <div style="font-size:32px;font-weight:800;color:#2d3748;line-height:1;">${s.calories}<span style="font-size:16px;font-weight:400;color:#cbd5e0;"> / ${goal}</span></div>
                        </div>
                        <div style="text-align:center;background:${over ? 'linear-gradient(135deg,#fff5f5,#fed7d7)' : 'linear-gradient(135deg,#f0fff4,#c6f6d5)'};border-radius:14px;padding:10px 16px;min-width:80px;">
                            <div style="font-size:10px;font-weight:700;color:${over ? '#c53030' : '#276749'};text-transform:uppercase;letter-spacing:0.5px;margin-bottom:2px;">${over ? 'Over' : 'Left'}</div>
                            <div style="font-size:22px;font-weight:800;color:${over ? '#e53e3e' : '#38a169'};line-height:1;">${over ? s.calories - goal : remaining}</div>
                        </div>
                    </div>
                    <div style="background:#e8edf5;border-radius:99px;height:8px;overflow:hidden;margin-bottom:6px;">
                        <div style="height:100%;width:${pct}%;background:${barColor};border-radius:99px;transition:width 0.6s cubic-bezier(.4,0,.2,1);"></div>
                    </div>
                    <div style="font-size:11px;color:#a0aec0;text-align:right;">${pct}% of daily goal</div>
                    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:16px;">
                        <div style="background:linear-gradient(135deg,#ebf8ff,#bee3f8);border-radius:12px;padding:12px;text-align:center;">
                            <div style="font-size:10px;font-weight:700;color:#2b6cb0;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">💪 Protein</div>
                            <div style="font-size:20px;font-weight:800;color:#2c5282;">${s.protein}<span style="font-size:12px;font-weight:500;">g</span></div>
                        </div>
                        <div style="background:linear-gradient(135deg,#fffff0,#fefcbf);border-radius:12px;padding:12px;text-align:center;">
                            <div style="font-size:10px;font-weight:700;color:#975a16;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">🌾 Carbs</div>
                            <div style="font-size:20px;font-weight:800;color:#744210;">${s.carbs}<span style="font-size:12px;font-weight:500;">g</span></div>
                        </div>
                        <div style="background:linear-gradient(135deg,#fff5f5,#fed7d7);border-radius:12px;padding:12px;text-align:center;">
                            <div style="font-size:10px;font-weight:700;color:#c53030;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">🥑 Fats</div>
                            <div style="font-size:20px;font-weight:800;color:#9b2c2c;">${s.fats}<span style="font-size:12px;font-weight:500;">g</span></div>
                        </div>
                    </div>
                    ${goalNote}
                </div>
            `;
            document.getElementById('calorie-progress-bar')?.remove();
        } else {
            const a = analytics.analytics;
            statsEl.innerHTML = `
                <div class="stat"><span>Avg Calories</span><strong>${Math.round(a.avgCalories)}</strong></div>
                <div class="stat"><span>Avg Protein</span><strong>${Math.round(a.avgProtein)}g</strong></div>
                <div class="stat"><span>Total Days</span><strong>${a.totalDays}</strong></div>
                <div class="stat"><span>Best Day</span><strong>${a.bestDay} cal</strong></div>
            `;
        }
    }

    const mealsEl = document.getElementById('today-meals');
    if (mealsEl) {
        if (period === 'today') {
            const mealTypeColors = { Breakfast: '#ffd89b', Lunch: '#a8e6cf', Dinner: '#d5c5f0', Snack: '#ffc9ba' };
            mealsEl.innerHTML = logs.logs.length === 0
                ? '<p style="text-align:center;color:#718096;font-style:italic;padding:20px;">No meals logged for this day.</p>'
                : logs.logs.map(l => {
                    const color = mealTypeColors[l.meal_type] || '#e2e8f0';
                    return `
                    <div style="display:flex;align-items:center;gap:12px;padding:12px 16px;background:white;border-radius:12px;margin-bottom:8px;box-shadow:0 2px 8px rgba(0,0,0,0.06);border-left:4px solid ${color};">
                        <span style="background:${color};padding:4px 10px;border-radius:8px;font-size:12px;font-weight:600;color:#4a5568;white-space:nowrap;">${l.meal_type}</span>
                        <span style="flex:1;font-weight:500;color:#2d3748;font-size:14px;">${l.name}</span>
                        <span style="background:linear-gradient(135deg,#ffeaa7,#ffd89b);padding:4px 10px;border-radius:8px;font-size:13px;font-weight:700;color:#8b6f47;white-space:nowrap;">🔥 ${l.calories} cal</span>
                        ${l.protein ? `<span style="font-size:12px;color:#718096;">💪 ${l.protein}g</span>` : ''}
                        <button onclick="deleteMealLog('${l.id}')" style="background:none;border:none;color:#cbd5e0;font-size:18px;cursor:pointer;padding:0 4px;line-height:1;" onmouseover="this.style.color='#e53e3e'" onmouseout="this.style.color='#cbd5e0'">×</button>
                    </div>`;
                }).join('');
        } else {
            // Group logs by date from analytics period
            const insights = analytics.insights || [];
            const dayLogs = analytics.day_logs || [];
            mealsEl.innerHTML = `
                <div style="margin-bottom:16px;">
                    ${insights.map(i => `<div style="padding:8px 12px;background:#f0f8ff;margin-bottom:6px;border-radius:8px;font-size:13px;color:#4a5568;">${i}</div>`).join('')}
                </div>
                ${dayLogs.length === 0
                    ? '<p style="text-align:center;color:#718096;font-style:italic;padding:12px;">No meals logged in this period.</p>'
                    : dayLogs.map(d => `
                        <div style="padding:12px 16px;background:white;border-radius:12px;margin-bottom:8px;box-shadow:0 2px 8px rgba(0,0,0,0.06);cursor:pointer;"
                             onclick="document.getElementById('time-period').value='today'; document.getElementById('selected-date').value='${d.date}'; updateDashboard();">
                            <div style="display:flex;justify-content:space-between;align-items:center;">
                                <span style="font-weight:600;color:#2d3748;font-size:14px;">${new Date(d.date + 'T12:00:00').toLocaleDateString('en-AU', {weekday:'short', day:'numeric', month:'short'})}</span>
                                <div style="display:flex;gap:8px;">
                                    <span style="background:linear-gradient(135deg,#ffeaa7,#ffd89b);padding:3px 10px;border-radius:8px;font-size:12px;font-weight:700;color:#8b6f47;">🔥 ${d.calories} cal</span>
                                    <span style="background:#e2e8f0;padding:3px 10px;border-radius:8px;font-size:12px;color:#4a5568;">${d.meal_count} meals</span>
                                </div>
                            </div>
                        </div>`
                    ).join('')
                }`;
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
            ? '<p style="text-align: center; color: #718096; padding: 20px;">🎉 Great job! You\'re on track today.</p>'
            : recs.recommendations.map((r, i) => r.type === 'meal' 
                ? `<div class="rec-card" onclick="showRecommendationDetails(${i})" style="background: white; border: 2px solid rgba(116, 185, 255, 0.3); padding: 16px; border-radius: 12px; margin-bottom: 12px; transition: all 0.3s; cursor: pointer;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(116, 185, 255, 0.2)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'"><div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;"><strong style="color: #2d3748; font-size: 16px;">${r.title}</strong><span style="background: linear-gradient(135deg, #74b9ff 0%, #a29bfe 100%); color: white; padding: 4px 12px; border-radius: 8px; font-size: 12px; font-weight: 600;">${r.calories} cal</span></div><div style="color: #718096; font-size: 13px; margin-bottom: 8px;">${r.reason}</div><div style="color: #74b9ff; font-size: 12px; font-weight: 600;">💪 ${r.protein}g protein • Click for recipe</div></div>`
                : `<div class="rec-tip" style="background: linear-gradient(135deg, #ffeaa7 0%, #ffd89b 100%); padding: 14px 16px; border-radius: 10px; margin-bottom: 10px; font-size: 14px; color: #2d3748; font-weight: 500; box-shadow: 0 2px 8px rgba(255, 234, 167, 0.3);">${r.message}</div>`
            ).join('');
    }
    
    window.currentRecommendations = recs.recommendations;
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
        date: getLocalDate(),
        meal_type: document.getElementById('meal-type').value,
        name: document.getElementById('meal-name').value,
        calories: parseInt(document.getElementById('meal-cal').value) || 0,
        protein: parseInt(document.getElementById('meal-protein').value) || 0,
        carbs: parseInt(document.getElementById('meal-carbs').value) || 0,
        fats: parseInt(document.getElementById('meal-fats').value) || 0
    };
    
    if (!data.name.trim()) return showAlert('Please enter a meal name', 'warning');
    
    await logMeal(data);
    document.querySelector('.modal').remove();
    await updateDashboard();
    showAlert('Meal logged successfully!', 'success');
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
        <select id="time-period" style="margin-left:16px;padding:6px 10px;border-radius:8px;border:2px solid rgba(250,177,160,0.3);font-size:13px;outline:none;">
            <option value="today">Daily View</option>
            <option value="week">This Week</option>
            <option value="month">This Month</option>
            <option value="year">This Year</option>
        </select>
    `;
    // Inject date picker below header
    let pickerRow = document.getElementById('date-picker-row');
    if (!pickerRow) {
        pickerRow = document.createElement('div');
        pickerRow.id = 'date-picker-row';
        pickerRow.style.cssText = 'display:flex;align-items:center;gap:10px;margin-bottom:16px;';
        pickerRow.innerHTML = `
            <label style="font-size:13px;font-weight:600;color:#718096;">📅 Date:</label>
            <input type="date" id="selected-date" value="${getLocalDate()}"
                style="padding:6px 12px;border:2px solid rgba(250,177,160,0.3);border-radius:8px;font-size:13px;outline:none;color:#2d3748;"
                onchange="updateDashboard()">
            <button onclick="document.getElementById('selected-date').value=getLocalDate();updateDashboard();"
                style="padding:6px 12px;background:rgba(250,177,160,0.15);border:none;border-radius:8px;font-size:12px;font-weight:600;color:#8b6f8f;cursor:pointer;">Today</button>
        `;
        modal.querySelector('.settings-box').insertBefore(pickerRow, document.getElementById('nutrition-stats'));
    }
    document.getElementById('time-period').addEventListener('change', updateDashboard);
    setTimeout(() => updateDashboard(), 50);
};

window.closeDailyTracker = () => {
    document.getElementById('dailyTrackerModal').classList.add('hidden');
};

// Initialize streaks on page load
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const streaksData = await getStreaks();
        const streaksEl = document.getElementById('streaks-display');
        if (streaksEl && streaksData.streaks) {
            streaksEl.innerHTML = `
                <div style="font-size: 13px; font-weight: 600; color: #8b6f8f; margin-bottom: 8px;">🔥 Daily Streak</div>
                <div style="font-size: 36px; font-weight: 700; color: #2d3748; line-height: 1; margin: 4px 0;">${streaksData.streaks.current} days</div>
                <div style="font-size: 13px; color: #8b6f8f; font-weight: 500;">Best: ${streaksData.streaks.longest} days</div>
            `;
            streaksEl.style.cursor = 'pointer';
            streaksEl.onclick = () => showStreakDetails(streaksData.streaks);
        }
    } catch (e) {
        console.log('Streaks not loaded yet');
    }
});

function showStreakDetails(streaks) {
    const motivationalMessages = [
        "Keep it up! Consistency is key! 💪",
        "You're building amazing habits! 🌟",
        "Every day counts towards your goals! 🎯",
        "Your dedication is inspiring! 🚀",
        "Small steps lead to big changes! 🌱"
    ];
    
    const milestones = [
        { days: 7, message: "One week strong! 🎉", achieved: streaks.current >= 7 },
        { days: 30, message: "One month milestone! 🏆", achieved: streaks.current >= 30 },
        { days: 100, message: "Century club! 🔥", achieved: streaks.current >= 100 },
        { days: 365, message: "One year champion! 🌟", achieved: streaks.current >= 365 }
    ];
    
    const nextMilestone = milestones.find(m => !m.achieved);
    const daysToNext = nextMilestone ? nextMilestone.days - streaks.current : 0;
    
    const modal = document.createElement('div');
    modal.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); backdrop-filter: blur(10px); display: flex; align-items: center; justify-content: center; z-index: 2000;';
    modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
    
    modal.innerHTML = `
        <div style="background: white; padding: 32px; border-radius: 24px; max-width: 500px; width: 90%; box-shadow: 0 25px 60px rgba(0,0,0,0.4);">
            <div style="text-align: center; margin-bottom: 24px;">
                <div style="font-size: 64px; margin-bottom: 16px;">🔥</div>
                <h2 style="font-size: 28px; font-weight: 700; color: #2d3748; margin-bottom: 8px;">Your Streak</h2>
                <div style="font-size: 48px; font-weight: 700; color: #fab1a0; margin: 16px 0;">${streaks.current} days</div>
                <p style="color: #718096; font-size: 14px;">Best streak: ${streaks.longest} days</p>
            </div>
            
            <div style="background: linear-gradient(135deg, #ffeaa7 0%, #ffd89b 100%); padding: 20px; border-radius: 16px; margin-bottom: 20px; text-align: center;">
                <p style="font-size: 16px; font-weight: 600; color: #8b6f8f; margin: 0;">${motivationalMessages[Math.floor(Math.random() * motivationalMessages.length)]}</p>
            </div>
            
            ${nextMilestone ? `
                <div style="background: rgba(250, 177, 160, 0.1); padding: 16px; border-radius: 12px; margin-bottom: 20px;">
                    <p style="font-size: 14px; color: #718096; margin-bottom: 8px;">Next Milestone</p>
                    <p style="font-size: 18px; font-weight: 600; color: #2d3748; margin: 0;">${nextMilestone.message}</p>
                    <p style="font-size: 14px; color: #fab1a0; margin-top: 4px;">${daysToNext} days to go!</p>
                </div>
            ` : '<div style="text-align: center; padding: 16px;"><p style="font-size: 18px; color: #fab1a0; font-weight: 600;">🏆 You\'ve reached all milestones!</p></div>'}
            
            <div style="margin-bottom: 20px;">
                <p style="font-size: 14px; font-weight: 600; color: #2d3748; margin-bottom: 12px;">Achievements</p>
                ${milestones.map(m => `
                    <div style="display: flex; align-items: center; gap: 12px; padding: 8px; background: ${m.achieved ? 'rgba(195, 240, 202, 0.3)' : 'rgba(0,0,0,0.05)'}; border-radius: 8px; margin-bottom: 8px;">
                        <span style="font-size: 24px;">${m.achieved ? '✅' : '🔒'}</span>
                        <div style="flex: 1;">
                            <p style="font-size: 14px; font-weight: 600; color: ${m.achieved ? '#2d3748' : '#718096'}; margin: 0;">${m.days} Days</p>
                            <p style="font-size: 12px; color: #718096; margin: 0;">${m.message}</p>
                        </div>
                    </div>
                `).join('')}
            </div>
            
            <button onclick="this.closest('div').parentElement.remove()" style="width: 100%; padding: 14px; background: linear-gradient(135deg, #ffc9ba 0%, #ffb3a7 100%); color: #8b6f8f; border: none; border-radius: 12px; font-size: 16px; font-weight: 600; cursor: pointer;">
Close</button>
        </div>
    `;
    
    document.body.appendChild(modal);
}

window.showRecommendationDetails = (index) => {
    const rec = window.currentRecommendations[index];
    if (!rec || rec.type !== 'meal') return;

    const modal = document.createElement('div');
    modal.id = 'rec-modal';
    modal.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); backdrop-filter: blur(10px); display: flex; align-items: center; justify-content: center; z-index: 2000;';
    modal.innerHTML = `
        <div style="background: white; padding: 32px; border-radius: 24px; max-width: 600px; width: 90%; max-height: 80vh; overflow-y: auto; box-shadow: 0 25px 60px rgba(0,0,0,0.4);">
            <div style="text-align: center; margin-bottom: 20px;">
                <div style="font-size: 48px; margin-bottom: 12px;">🍽️</div>
                <h2 style="font-size: 24px; font-weight: 700; color: #2d3748;">${rec.title}</h2>
                <p style="color: #718096; margin-top: 8px;">${rec.reason}</p>
                <div style="display:flex; gap:8px; justify-content:center; margin-top:12px;">
                    <span style="background:#e2e8f0; padding:4px 12px; border-radius:8px; font-size:13px; color:#4a5568;">🔥 ${rec.calories} cal</span>
                    <span style="background:#e2e8f0; padding:4px 12px; border-radius:8px; font-size:13px; color:#4a5568;">💪 ${rec.protein}g protein</span>
                </div>
            </div>
            <div id="recipe-content" style="text-align: center; padding: 20px; color: #718096;">
                <button onclick="loadRecipeDetails(${index})" style="padding: 12px 24px; background: linear-gradient(135deg, #74b9ff 0%, #a29bfe 100%); color: white; border: none; border-radius: 12px; font-size: 15px; font-weight: 600; cursor: pointer;">📖 View Recipe</button>
            </div>
            <div style="display: flex; gap: 12px; margin-top: 20px;">
                <button onclick="document.getElementById('rec-modal').remove()" style="flex: 1; padding: 12px; background: #e2e8f0; color: #2d3748; border: none; border-radius: 12px; font-weight: 600; cursor: pointer;">Close</button>
                <button onclick="quickLogRecommendation(${index})" style="flex: 1; padding: 12px; background: linear-gradient(135deg, #74b9ff 0%, #a29bfe 100%); color: white; border: none; border-radius: 12px; font-weight: 600; cursor: pointer;">✓ Log This Meal</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
};

window.loadRecipeDetails = async (index) => {
    const rec = window.currentRecommendations[index];
    const contentEl = document.getElementById('recipe-content');
    contentEl.innerHTML = '<span style="color:#8b6f8f; font-style:italic;">⏳ Loading recipe...</span>';
    try {
        const response = await fetch('/chat/stream', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({query: `Give me a detailed recipe for ${rec.title} with ingredients and instructions`})
        });
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '', text = '';
        contentEl.innerHTML = '<div id="recipe-text" style="white-space: pre-wrap; text-align: left; line-height: 1.8; color: #2d3748;"></div>';
        const textEl = document.getElementById('recipe-text');
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const parts = buffer.split('\n\n');
            buffer = parts.pop();
            for (const part of parts) {
                const eventMatch = part.match(/^event: (\w+)/);
                const dataMatch = part.match(/^data: (.+)/m);
                if (eventMatch && dataMatch && eventMatch[1] === 'token') {
                    text += JSON.parse(dataMatch[1]).text;
                    textEl.innerHTML = text.replace(/\n/g, '<br>');
                }
            }
        }
    } catch (e) {
        document.getElementById('recipe-content').innerHTML = '<p style="color:#e53e3e;">Failed to load recipe</p>';
    }
};

window.quickLogRecommendation = async (index) => {
    const rec = window.currentRecommendations[index];
    await logMeal({
        meal_type: 'Lunch',
        name: rec.title,
        calories: rec.calories,
        protein: rec.protein,
        carbs: Math.round(rec.calories * 0.5 / 4),
        fats: Math.round(rec.calories * 0.3 / 9)
    });
    document.getElementById('rec-modal')?.remove();
    await updateDashboard();
    showAlert('Meal logged successfully!', 'success');
};

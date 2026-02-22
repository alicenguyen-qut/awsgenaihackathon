// Recipe Favorites
async function toggleFavorite(recipeId, recipeName) {
    try {
        const response = await fetch('/api/favorites', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({recipeId, recipeName})
        });
        const data = await response.json();
        if (data.success) {
            showAlert(data.added ? 'Added to favorites!' : 'Removed from favorites!', data.added ? 'success' : 'info');
            loadFavorites();
        }
    } catch (error) {
        console.error('Toggle favorite error:', error);
    }
}

async function loadFavorites() {
    try {
        const response = await fetch('/api/favorites');
        const data = await response.json();
        const list = document.getElementById('favoritesList');
        if (data.favorites && data.favorites.length > 0) {
            list.innerHTML = data.favorites.map(f => 
                `<div style="padding: 12px; background: rgba(250, 177, 160, 0.1); border-radius: 8px; margin-bottom: 8px;">
                    <div style="font-weight: 500; color: #2d3748; margin-bottom: 8px;">${f.recipeName}</div>
                    <div style="display: flex; gap: 8px;">
                        <button onclick="viewFavoriteRecipe('${f.recipeId}', '${f.recipeName.replace(/'/g, "\\'") }', \`${(f.content || '').replace(/`/g, '\\`').replace(/\$/g, '\\$')}\`)" style="flex: 1; background: #74b9ff; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600;">📖 View</button>
                        <button onclick="toggleFavorite('${f.recipeId}', '${f.recipeName.replace(/'/g, "\\'")}')" style="background: #fab1a0; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600;">❌ Remove</button>
                    </div>
                </div>`
            ).join('');
        } else {
            list.innerHTML = '<p style="color: #718096; text-align: center; padding: 20px; font-style: italic;">No favorites yet. Click "Add to Favorites" on any recipe in chat!</p>';
        }
    } catch (error) {
        console.error('Load favorites error:', error);
    }
}

// Extract recipe from last AI message and add to favorites
function addLastRecipeToFavorites() {
    const messages = document.querySelectorAll('.message.bot');
    if (messages.length === 0) {
        showAlert('No recipes found. Ask for a recipe first!', 'warning');
        return;
    }
    
    const lastMessage = messages[messages.length - 1];
    const content = lastMessage.querySelector('.message-content').textContent;
    
    // Extract recipe name (first line or bullet point)
    const lines = content.split('\n');
    let recipeName = '';
    
    for (const line of lines) {
        const match = line.match(/^[\u2022\-\*\d\.)]?\s*([A-Z][^\-\(\n]{5,50})/);
        if (match) {
            recipeName = match[1].trim();
            break;
        }
    }
    
    if (!recipeName) {
        recipeName = lines[0].substring(0, 50).trim();
    }
    
    if (recipeName) {
        const recipeId = Date.now().toString();
        // Store full content with the favorite
        saveFavoriteWithContent(recipeId, recipeName, content);
    } else {
        showAlert('Could not extract recipe name. Try asking for a specific recipe!', 'warning');
    }
}

async function saveFavoriteWithContent(recipeId, recipeName, content) {
    try {
        const response = await fetch('/api/favorites', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({recipeId, recipeName, content})
        });
        const data = await response.json();
        if (data.success) {
            showAlert('Added to favorites!', 'success');
            loadFavorites();
        }
    } catch (error) {
        console.error('Save favorite error:', error);
        showAlert('Failed to save favorite', 'error');
    }
}

function viewFavoriteRecipe(recipeId, recipeName, content) {
    const favModal = document.getElementById('favoritesModal');
    favModal.classList.add('hidden');

    const modal = document.createElement('div');
    modal.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); backdrop-filter: blur(10px); display: flex; align-items: center; justify-content: center; z-index: 2000;';

    const closeModal = () => { modal.remove(); favModal.classList.remove('hidden'); };
    modal.onclick = (e) => { if (e.target === modal) closeModal(); };

    modal.innerHTML = `
        <div style="background: white; padding: 32px; border-radius: 24px; max-width: 700px; width: 90%; max-height: 80vh; overflow-y: auto; box-shadow: 0 25px 60px rgba(0,0,0,0.4);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 16px; border-bottom: 2px solid rgba(250, 177, 160, 0.2);">
                <h2 style="font-size: 24px; font-weight: 700; color: #2d3748;">${recipeName}</h2>
                <button id="closeFavRecipeBtn" style="background: #fab1a0; color: white; border: none; width: 32px; height: 32px; border-radius: 8px; cursor: pointer; font-size: 18px;">×</button>
            </div>
            <div style="white-space: pre-wrap; font-size: 15px; color: #2d3748; line-height: 1.8;">${content || 'Recipe content not available. Try re-adding this recipe.'}</div>
            <button id="closeFavRecipeBtn2" style="width: 100%; padding: 12px; background: linear-gradient(135deg, #ffc9ba 0%, #ffb3a7 100%); color: #8b6f8f; border: none; border-radius: 12px; font-size: 14px; font-weight: 600; cursor: pointer; margin-top: 20px;">Close</button>
        </div>
    `;

    document.body.appendChild(modal);
    modal.querySelector('#closeFavRecipeBtn').onclick = closeModal;
    modal.querySelector('#closeFavRecipeBtn2').onclick = closeModal;
}

// Meal Planner
function openMealPlanner() {
    document.getElementById('mealPlannerModal').classList.remove('hidden');
    loadMealPlan();
}

function closeMealPlanner() {
    document.getElementById('mealPlannerModal').classList.add('hidden');
}

async function loadMealPlan() {
    try {
        const response = await fetch('/api/meal-plan');
        const data = await response.json();
        const container = document.getElementById('mealPlanContainer');
        
        const days = [
            {name: 'Monday', emoji: '📅', color: '#ffc9ba'},
            {name: 'Tuesday', emoji: '📆', color: '#d5c5f0'},
            {name: 'Wednesday', emoji: '📋', color: '#c3f0ca'},
            {name: 'Thursday', emoji: '📝', color: '#ffeaa7'},
            {name: 'Friday', emoji: '🎯', color: '#fab1a0'},
            {name: 'Saturday', emoji: '🌟', color: '#a29bfe'},
            {name: 'Sunday', emoji: '☀️', color: '#ffd6e8'}
        ];
        
        container.innerHTML = `
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 20px;">
                ${days.map(day => {
                    const meal = data.plan?.[day.name] || '';
                    return `
                        <div style="background: white; border: 2px solid ${day.color}; border-radius: 16px; padding: 16px; transition: all 0.3s; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" 
                             onmouseover="this.style.transform='translateY(-4px)'; this.style.boxShadow='0 8px 16px rgba(0,0,0,0.15)'" 
                             onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px rgba(0,0,0,0.1)'">
                            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid ${day.color};">
                                <span style="font-size: 24px;">${day.emoji}</span>
                                <span style="font-weight: 700; color: #2d3748; font-size: 16px;">${day.name}</span>
                            </div>
                            <textarea id="meal-${day.name}" placeholder="Plan your meal..." 
                                style="width: 100%; min-height: 80px; padding: 12px; border: 2px solid rgba(0,0,0,0.1); border-radius: 12px; outline: none; font-size: 14px; resize: vertical; font-family: 'Plus Jakarta Sans', sans-serif; transition: all 0.3s;"
                                onfocus="this.style.borderColor='${day.color}'; this.style.boxShadow='0 0 0 3px ${day.color}20'"
                                onblur="this.style.borderColor='rgba(0,0,0,0.1)'; this.style.boxShadow='none'">${meal}</textarea>
                            <div style="display: flex; gap: 8px; margin-top: 12px;">
                                ${meal
                                    ? `<button data-day="${day.name}" data-meal="${meal.replace(/"/g, '&quot;')}" onclick="viewRecipeDetails(this.dataset.day, this.dataset.meal)"
                                        style="flex: 1; padding: 8px; background: ${day.color}; color: #2d3748; border: none; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.2s;"
                                        onmouseover="this.style.opacity='0.8'"
                                        onmouseout="this.style.opacity='1'">📖 View Recipe</button>`
                                    : `<button onclick="generateRecipeForDay('${day.name}')"
                                        style="flex: 1; padding: 8px; background: linear-gradient(135deg, ${day.color}, ${day.color}dd); color: #2d3748; border: none; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.2s;"
                                        onmouseover="this.style.opacity='0.8'"
                                        onmouseout="this.style.opacity='1'">✨ Generate</button>`
                                }
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    } catch (error) {
        console.error('Load meal plan error:', error);
    }
}

async function generateRecipeForDay(day) {
    const mealInput = document.getElementById(`meal-${day}`);
    const currentMeal = mealInput.value.trim();
    
    const prompt = currentMeal ? `Give me a detailed recipe for ${currentMeal}` : `Suggest a healthy meal for ${day}`;
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({query: prompt})
        });
        const data = await response.json();
        
        // Extract meal name from response
        const meals = extractMealsFromResponse(data.response);
        if (meals.length > 0 && !currentMeal) {
            mealInput.value = meals[0];
        }
        
        // Show recipe details
        viewRecipeDetails(day, mealInput.value, data.response);
    } catch (error) {
        console.error('Generate recipe error:', error);
        alert('Failed to generate recipe');
    }
}

function viewRecipeDetails(day, mealName, recipeDetails = null) {
    if (!recipeDetails) {
        // Fetch recipe details from AI
        fetch('/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({query: `Give me a detailed recipe for ${mealName} including ingredients, instructions, and nutrition info`})
        })
        .then(r => r.json())
        .then(data => {
            showRecipeModal(day, mealName, data.response);
        })
        .catch(error => {
            console.error('Fetch recipe error:', error);
            alert('Failed to load recipe details');
        });
    } else {
        showRecipeModal(day, mealName, recipeDetails);
    }
}

function showRecipeModal(day, mealName, recipeDetails) {
    const modal = document.createElement('div');
    modal.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); backdrop-filter: blur(10px); display: flex; align-items: center; justify-content: center; z-index: 2000; animation: fadeIn 0.3s;';
    
    modal.innerHTML = `
        <div style="background: white; padding: 32px; border-radius: 24px; max-width: 700px; width: 90%; max-height: 80vh; overflow-y: auto; box-shadow: 0 25px 60px rgba(0,0,0,0.4);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 16px; border-bottom: 2px solid rgba(250, 177, 160, 0.2);">
                <div>
                    <h2 style="font-size: 24px; font-weight: 700; color: #2d3748; margin-bottom: 4px;">${mealName}</h2>
                    <p style="font-size: 14px; color: #718096;">📅 ${day}</p>
                </div>
                <button onclick="this.closest('div').parentElement.parentElement.remove()" 
                    style="background: #fab1a0; color: white; border: none; width: 32px; height: 32px; border-radius: 8px; cursor: pointer; font-size: 18px;">×</button>
            </div>
            <div style="white-space: pre-wrap; font-size: 15px; color: #2d3748; line-height: 1.8;">${recipeDetails}</div>
            <button onclick="this.closest('div').parentElement.remove()" 
                style="width: 100%; padding: 12px; background: linear-gradient(135deg, #ffc9ba 0%, #ffb3a7 100%); color: white; border: none; border-radius: 12px; font-size: 14px; font-weight: 600; cursor: pointer; margin-top: 20px;">Close</button>
        </div>
    `;
    
    document.body.appendChild(modal);
}

async function saveMealPlan() {
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const plan = {};
    days.forEach(day => {
        plan[day] = document.getElementById(`meal-${day}`).value;
    });
    
    try {
        const response = await fetch('/api/meal-plan', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({plan})
        });
        const data = await response.json();
        if (data.success) {
            showAlert('Meal plan saved! 📅', 'success');
        }
    } catch (error) {
        console.error('Save meal plan error:', error);
    }
}

// Shopping List
function openShoppingList() {
    document.getElementById('shoppingListModal').classList.remove('hidden');
    loadShoppingList();
}

function closeShoppingList() {
    document.getElementById('shoppingListModal').classList.add('hidden');
}

// Favorites modal
function openFavorites() {
    document.getElementById('favoritesModal').classList.remove('hidden');
    loadFavorites();
}

function closeFavorites() {
    document.getElementById('favoritesModal').classList.add('hidden');
}

async function loadShoppingList() {
    try {
        const response = await fetch('/api/shopping-list');
        const data = await response.json();
        const list = document.getElementById('shoppingItems');
        
        if (data.items && data.items.length > 0) {
            list.innerHTML = data.items.map((item, i) => 
                `<div style="display: flex; align-items: center; gap: 10px; padding: 10px; background: rgba(250, 177, 160, 0.1); border-radius: 8px; margin-bottom: 6px;">
                    <input type="checkbox" ${item.checked ? 'checked' : ''} onchange="toggleShoppingItem(${i})">
                    <span style="flex: 1; ${item.checked ? 'text-decoration: line-through; color: #718096;' : ''}">${item.name}</span>
                    <button onclick="deleteShoppingItem(${i})" style="background: #fab1a0; color: white; border: none; padding: 4px 8px; border-radius: 6px; cursor: pointer;">🗑️</button>
                </div>`
            ).join('');
        } else {
            list.innerHTML = '<p style="color: #718096;">No items in shopping list</p>';
        }
    } catch (error) {
        console.error('Load shopping list error:', error);
    }
}

async function addShoppingItem() {
    const input = document.getElementById('newShoppingItem');
    const name = input.value.trim();
    
    if (!name) return;
    
    try {
        const response = await fetch('/api/shopping-list', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name})
        });
        const data = await response.json();
        if (data.success) {
            input.value = '';
            loadShoppingList();
        }
    } catch (error) {
        console.error('Add shopping item error:', error);
    }
}

async function toggleShoppingItem(index) {
    try {
        await fetch(`/api/shopping-list/${index}/toggle`, {method: 'POST'});
        loadShoppingList();
    } catch (error) {
        console.error('Toggle item error:', error);
    }
}

async function deleteShoppingItem(index) {
    try {
        await fetch(`/api/shopping-list/${index}`, {method: 'DELETE'});
        loadShoppingList();
    } catch (error) {
        console.error('Delete item error:', error);
    }
}

async function clearShoppingList() {
    const modal = document.createElement('div');
    modal.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); backdrop-filter: blur(10px); display: flex; align-items: center; justify-content: center; z-index: 2000;';
    
    modal.innerHTML = `
        <div style="background: white; padding: 32px; border-radius: 24px; max-width: 400px; width: 90%; box-shadow: 0 25px 60px rgba(0,0,0,0.4); text-align: center;">
            <div style="font-size: 48px; margin-bottom: 16px;">⚠️</div>
            <h2 style="font-size: 24px; font-weight: 700; color: #2d3748; margin-bottom: 12px;">Clear Shopping List?</h2>
            <p style="color: #718096; margin-bottom: 24px; line-height: 1.6;">This will permanently delete all items from your shopping list. This action cannot be undone.</p>
            <div style="display: flex; gap: 12px;">
                <button onclick="this.closest('div').parentElement.parentElement.remove()" 
                    style="flex: 1; padding: 12px; background: #e2e8f0; color: #2d3748; border: none; border-radius: 12px; font-size: 14px; font-weight: 600; cursor: pointer;">Cancel</button>
                <button id="confirmClearBtn" 
                    style="flex: 1; padding: 12px; background: #fab1a0; color: white; border: none; border-radius: 12px; font-size: 14px; font-weight: 600; cursor: pointer;">Clear All</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    document.getElementById('confirmClearBtn').onclick = async () => {
        modal.remove();
        try {
            await fetch('/api/shopping-list/clear', {method: 'POST'});
            loadShoppingList();
            showAlert('Shopping list cleared', 'success');
        } catch (error) {
            console.error('Clear list error:', error);
            showAlert('Failed to clear list', 'error');
        }
    };
}

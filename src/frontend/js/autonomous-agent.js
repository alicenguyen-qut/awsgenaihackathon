// Agentic AI System - Autonomous Actions

// Agent context and memory
let agentContext = {
    userProfile: null,
    favorites: [],
    mealPlan: {},
    shoppingList: [],
    conversationHistory: []
};

// Load agent context
async function loadAgentContext() {
    try {
        const [profile, favorites, mealPlan, shoppingList] = await Promise.all([
            fetch('/api/nutrition-profile').then(r => r.json()),
            fetch('/api/favorites').then(r => r.json()),
            fetch('/api/meal-plan').then(r => r.json()),
            fetch('/api/shopping-list').then(r => r.json())
        ]);
        
        agentContext.userProfile = profile.profile || {};
        agentContext.favorites = favorites.favorites || [];
        agentContext.mealPlan = mealPlan.plan || {};
        agentContext.shoppingList = shoppingList.items || [];
    } catch (error) {
        console.error('Load agent context error:', error);
    }
}

// Detect user intent and extract actions
function detectIntent(message) {
    const msg = message.toLowerCase();
    const intents = [];
    
    // Multi-step planning intent
    if (msg.includes('plan my week') || msg.includes('weekly meal plan') || msg.includes('plan meals for the week')) {
        intents.push({type: 'PLAN_WEEK', confidence: 0.9});
    }
    
    // Shopping list generation
    if (msg.includes('shopping list') || msg.includes('grocery list') || msg.includes('what do i need to buy')) {
        intents.push({type: 'GENERATE_SHOPPING_LIST', confidence: 0.85});
    }
    
    // Save to favorites
    if (msg.includes('save this') || msg.includes('add to favorites') || msg.includes('bookmark this')) {
        intents.push({type: 'SAVE_FAVORITE', confidence: 0.8});
    }
    
    // Add to meal plan
    if (msg.includes('add to') && (msg.includes('monday') || msg.includes('tuesday') || msg.includes('wednesday') || 
        msg.includes('thursday') || msg.includes('friday') || msg.includes('saturday') || msg.includes('sunday'))) {
        intents.push({type: 'ADD_TO_MEAL_PLAN', confidence: 0.85});
    }
    
    // Proactive suggestions
    if (msg.includes('what should i') || msg.includes('suggest') || msg.includes('recommend')) {
        intents.push({type: 'PROACTIVE_SUGGEST', confidence: 0.7});
    }
    
    return intents;
}

// Execute autonomous actions
async function executeAgentActions(message, response) {
    const intents = detectIntent(message);
    const actions = [];
    
    for (const intent of intents) {
        switch (intent.type) {
            case 'PLAN_WEEK':
                actions.push(await planWeekAutonomously(response));
                break;
            case 'GENERATE_SHOPPING_LIST':
                actions.push(await generateShoppingListFromPlan());
                break;
            case 'SAVE_FAVORITE':
                actions.push(await autoSaveFavorite(response));
                break;
            case 'ADD_TO_MEAL_PLAN':
                actions.push(await autoAddToMealPlan(message, response));
                break;
        }
    }
    
    return actions;
}

// Autonomous action: Plan entire week
async function planWeekAutonomously(aiResponse) {
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const meals = extractMealsFromResponse(aiResponse);
    
    console.log('Planning week with meals:', meals);
    
    if (meals.length >= 3) {  // Lowered threshold from 7 to 3
        const plan = {};
        days.forEach((day, i) => {
            if (meals[i]) plan[day] = meals[i];
        });
        
        try {
            const response = await fetch('/api/meal-plan', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({plan})
            });
            const data = await response.json();
            console.log('Meal plan saved:', data);
            
            return {action: 'MEAL_PLAN_UPDATED', data: plan, message: `✅ Automatically added ${Object.keys(plan).length} meals to your meal planner!`};
        } catch (error) {
            console.error('Error saving meal plan:', error);
            return null;
        }
    }
    console.log('Not enough meals found (need at least 3)');
    return null;
}

// Autonomous action: Generate shopping list from meal plan
async function generateShoppingListFromPlan() {
    console.log('Generating shopping list from:', agentContext.mealPlan);
    const ingredients = extractIngredientsFromMealPlan(agentContext.mealPlan);
    
    if (ingredients.length === 0) {
        console.log('No ingredients found in meal plan');
        return {action: 'SHOPPING_LIST_EMPTY', message: '⚠️ No meal plan found. Plan your week first!'};
    }
    
    try {
        for (const ingredient of ingredients) {
            await fetch('/api/shopping-list', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: ingredient})
            });
        }
        console.log('Shopping list generated:', ingredients);
        return {action: 'SHOPPING_LIST_GENERATED', data: ingredients, message: `✅ Added ${ingredients.length} items to shopping list!`};
    } catch (error) {
        console.error('Error generating shopping list:', error);
        return null;
    }
}

// Autonomous action: Auto-save favorite
async function autoSaveFavorite(response) {
    const recipe = extractRecipeFromResponse(response);
    
    if (recipe) {
        await fetch('/api/favorites', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({recipeId: recipe.id, recipeName: recipe.name})
        });
        
        return {action: 'FAVORITE_SAVED', data: recipe, message: '⭐ Saved to favorites!'};
    }
    return null;
}

// Autonomous action: Add to meal plan
async function autoAddToMealPlan(message, response) {
    const day = extractDayFromMessage(message);
    const meal = extractMealsFromResponse(response)[0];
    
    if (day && meal) {
        const plan = {...agentContext.mealPlan, [day]: meal};
        await fetch('/api/meal-plan', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({plan})
        });
        
        return {action: 'ADDED_TO_MEAL_PLAN', data: {day, meal}, message: `📅 Added to ${day}!`};
    }
    return null;
}

// Context-aware proactive suggestions
function generateProactiveSuggestion() {
    const hour = new Date().getHours();
    const profile = agentContext.userProfile;
    const favorites = agentContext.favorites;
    
    let suggestion = '';
    
    // Time-based suggestions
    if (hour >= 6 && hour < 10) {
        suggestion = '🌅 Good morning! ';
        if (profile.healthGoal === 'weight-loss') {
            suggestion += 'How about a light, protein-rich breakfast?';
        } else if (profile.healthGoal === 'muscle-gain') {
            suggestion += 'Ready for a high-protein breakfast to fuel your day?';
        } else {
            suggestion += 'What would you like for breakfast?';
        }
    } else if (hour >= 11 && hour < 14) {
        suggestion = '🍽️ Lunch time! ';
        if (favorites.length > 0) {
            suggestion += `You loved ${favorites[0].recipeName} before. Want something similar?`;
        } else {
            suggestion += 'Need a quick and healthy lunch idea?';
        }
    } else if (hour >= 17 && hour < 21) {
        suggestion = '🌙 Dinner time! ';
        const today = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][new Date().getDay()];
        if (agentContext.mealPlan[today]) {
            suggestion += `You planned ${agentContext.mealPlan[today]} for tonight. Need the recipe?`;
        } else {
            suggestion += 'What are you in the mood for tonight?';
        }
    }
    
    // Profile-based suggestions
    if (profile.dietary && profile.dietary.length > 0) {
        suggestion += ` (${profile.dietary.join(', ')} options available)`;
    }
    
    return suggestion;
}

// Helper: Extract meals from AI response
function extractMealsFromResponse(response) {
    const meals = [];
    const lines = response.split('\n');
    
    for (const line of lines) {
        // Match bullet points, dashes, asterisks, or numbered lists
        const match = line.match(/^[•\-\*\d\.)]\s*(.+)/);
        if (match) {
            let meal = match[1].trim();
            // Remove everything after dash or colon
            meal = meal.split(/[-:]/)[0].trim();
            // Remove parentheses content
            meal = meal.replace(/\([^)]*\)/g, '').trim();
            if (meal.length > 3 && meal.length < 100) {
                meals.push(meal);
            }
        }
    }
    
    console.log('Extracted meals:', meals);
    return meals;
}

// Helper: Extract recipe from response
function extractRecipeFromResponse(response) {
    const lines = response.split('\n');
    for (const line of lines) {
        // Try multiple patterns
        const patterns = [
            /^[•\-\*\d\.)]\s*(.+?)\s*[-:]/,  // Bullet with dash/colon
            /^[•\-\*\d\.)]\s*([^\(]+)/,      // Bullet without parentheses
            /^(.+?)\s*[-:]/                      // Any line with dash/colon
        ];
        
        for (const pattern of patterns) {
            const match = line.match(pattern);
            if (match && match[1].trim().length > 3) {
                const name = match[1].trim().replace(/\([^)]*\)/g, '').trim();
                console.log('Extracted recipe:', name);
                return {id: Date.now().toString(), name};
            }
        }
    }
    console.log('No recipe found in response');
    return null;
}

// Helper: Extract day from message
function extractDayFromMessage(message) {
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    for (const day of days) {
        if (message.toLowerCase().includes(day.toLowerCase())) {
            return day;
        }
    }
    return null;
}

// Helper: Extract ingredients from meal plan
function extractIngredientsFromMealPlan(mealPlan) {
    const commonIngredients = {
        'chicken': ['chicken breast', 'olive oil', 'garlic'],
        'salmon': ['salmon fillet', 'lemon', 'dill'],
        'pasta': ['pasta', 'tomato sauce', 'parmesan'],
        'salad': ['lettuce', 'tomatoes', 'cucumber', 'olive oil'],
        'rice': ['rice', 'vegetables', 'soy sauce'],
        'soup': ['broth', 'vegetables', 'herbs']
    };
    
    const ingredients = new Set();
    Object.values(mealPlan).forEach(meal => {
        const mealLower = meal.toLowerCase();
        Object.keys(commonIngredients).forEach(key => {
            if (mealLower.includes(key)) {
                commonIngredients[key].forEach(ing => ingredients.add(ing));
            }
        });
    });
    
    return Array.from(ingredients);
}

// Display agent actions in chat
function displayAgentActions(actions) {
    if (!actions || actions.length === 0) return;
    
    const container = document.getElementById('chatContainer');
    const actionsDiv = document.createElement('div');
    actionsDiv.style.cssText = 'margin: 20px 0; padding: 16px; background: rgba(195, 240, 202, 0.2); border-left: 4px solid #c3f0ca; border-radius: 12px;';
    
    actionsDiv.innerHTML = `
        <div style="font-weight: 600; color: #2d3748; margin-bottom: 8px;">🤖 Agent Actions:</div>
        ${actions.filter(a => a).map(action => `
            <div style="font-size: 14px; color: #4a5568; margin: 4px 0;">${action.message}</div>
        `).join('')}
    `;
    
    container.appendChild(actionsDiv);
    container.scrollTop = container.scrollHeight;
}

// Initialize agent on page load
window.addEventListener('load', () => {
    loadAgentContext();
    
    // Show proactive suggestion after 3 seconds
    setTimeout(() => {
        const suggestion = generateProactiveSuggestion();
        if (suggestion && document.getElementById('chatContainer').children.length === 1) {
            const welcomeMsg = document.querySelector('.welcome-message p');
            if (welcomeMsg) {
                welcomeMsg.textContent = suggestion;
            }
        }
    }, 3000);
});

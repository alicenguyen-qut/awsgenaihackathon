# Features Guide

Complete guide to all features in the AI Cooking Assistant.

---

## 🍳 Core Features

### 1. AI-Powered Chat
- **RAG-based responses** using Amazon Bedrock (Claude 3 Haiku)
- **Semantic recipe search** with Titan Embeddings
- **Multi-chat management** - Create, switch, delete conversations
- **Document upload** - Upload .txt/.docx files for context

### 2. User Profile & Personalization
- **Authentication** - Secure login/register with password hashing
- **Profile photo** - Upload custom avatar
- **Nutrition profile**:
  - Dietary restrictions (vegan, vegetarian, gluten-free, dairy-free, nut-free)
  - Health goals (weight loss, muscle gain, maintenance, heart health, energy boost)
  - Allergy tracking
- **Personalized recommendations** based on profile

### 3. Recipe Management
- **Favorites** - Bookmark recipes with one click
- **Recipe history** - Track what you've cooked
- **Quick access** - View saved recipes anytime

### 4. Meal Planning
- **Weekly planner** - Schedule meals for each day
- **Drag-and-drop** - Easy meal scheduling
- **Edit/delete** - Modify plans anytime
- **Persistent storage** - Plans saved to your profile

### 5. Shopping List
- **Add items** - Manual or from recipes
- **Check off** - Mark items as purchased
- **Clear completed** - Remove checked items
- **Persistent** - List syncs across sessions

---

## 📊 Daily-Use Features

These features drive daily engagement and replace nutritionist visits.

### 1. Daily Nutrition Tracking

**Purpose:** Log meals and track macros in real-time

**How to Use:**
1. Click "📊 Daily Tracker" in sidebar
2. Click "+ Log Meal"
3. Enter meal details:
   - Type (Breakfast/Lunch/Dinner/Snack)
   - Name
   - Calories, protein, carbs, fats
4. Save and watch stats update instantly

**Features:**
- Real-time daily totals dashboard
- Visual stats grid (calories, protein, carbs, fats)
- Meal history with timestamps
- Delete meals with one click
- Date-based filtering

**API Endpoints:**
```
POST   /api/nutrition/log              - Log a meal
GET    /api/nutrition/logs?date=...    - Get meal logs
GET    /api/nutrition/stats?date=...   - Get daily totals
DELETE /api/nutrition/logs/<log_id>    - Delete meal log
```

### 2. Habit Streaks

**Purpose:** Gamification to encourage daily logins

**How It Works:**
- Automatically increments on daily login
- Resets if you miss a day
- Tracks longest streak ever
- Visual display in sidebar with 🔥 icon

**Logic:**
- Same day login → No change
- Yesterday login → Current streak + 1
- Older login → Reset to 1
- Updates longest if current > longest

**API Endpoint:**
```
GET /api/streaks - Get current & longest streak
```

**Interactive Features:**
- Click on streak display to view detailed modal
- Motivational messages
- Achievement badges: 7, 30, 100, 365 days
- Progress tracking to next milestone
- Visual achievement system with unlocked badges

### 3. Smart Daily Recommendations

**Purpose:** AI suggests meals based on today's nutrition gaps

**How It Works:**
1. Analyzes today's logged meals
2. Calculates nutrition gaps
3. Considers your dietary preferences
4. Suggests meals to fill gaps
5. Updates in real-time as you log meals

**Recommendation Triggers:**
- Low calories (<800) → High-calorie meals
- Low protein (<30g) → Protein-rich meals
- Vegan diet → Plant-based options
- Health goals → Goal-aligned meals

**API Endpoint:**
```
GET /api/recommendations/daily - Get personalized suggestions
```

**Example Response:**
```json
{
  "recommendations": [
    {
      "type": "meal",
      "title": "Grilled Chicken Salad",
      "reason": "High protein, low carb",
      "calories": 380,
      "protein": 42
    },
    {
      "type": "tip",
      "message": "Add more protein today - try eggs or Greek yogurt"
    }
  ]
}
```

---

## 🤖 Autonomous Agent System

Two-tier agentic architecture that executes actions without explicit commands.

### Frontend Agent (Browser)

**Capabilities:**
- **Intent detection** - Understands natural language commands
- **Autonomous actions** - Executes multi-step workflows
- **Context memory** - Remembers preferences and history
- **Proactive suggestions** - Time-based meal recommendations

**Supported Intents:**

| Intent | Trigger Keywords | Action |
|--------|-----------------|--------|
| `PLAN_WEEK` | "plan my week", "weekly meal plan" | Auto-populates 7-day planner |
| `GENERATE_SHOPPING_LIST` | "shopping list", "grocery list" | Extracts ingredients from meal plan |
| `SAVE_FAVORITE` | "save this", "add to favorites" | Bookmarks current recipe |
| `ADD_TO_MEAL_PLAN` | "add to Monday" | Adds meal to specific day |
| `PROACTIVE_SUGGEST` | "what should i", "suggest" | Context-aware suggestions |

**Example Workflows:**

```javascript
// User: "Plan my week with vegan meals"
// Agent:
1. Detects PLAN_WEEK intent
2. Extracts 7 meals from AI response
3. Automatically saves to meal planner
4. Shows: "✅ Automatically added to your meal planner!"

// User: "Generate shopping list"
// Agent:
1. Analyzes current meal plan
2. Extracts ingredients
3. Adds all items to shopping list
4. Shows: "✅ Added 12 items to shopping list!"
```

**Context-Aware Proactive Suggestions:**

- **Morning (6am-10am):** "🌅 Good morning! Ready for a high-protein breakfast?"
- **Lunch (11am-2pm):** "🍽️ Lunch time! You loved Vegan Buddha Bowl before. Want something similar?"
- **Dinner (5pm-9pm):** "🌙 Dinner time! You planned Salmon with Vegetables for tonight. Need the recipe?"

### Backend Agent (Lambda)

**Tool Orchestration:**

Claude decides which tools to use based on user query:

```python
TOOLS = [
    {
        "name": "search_recipes",
        "description": "Search for recipes based on ingredients, cuisine, or dietary preferences"
    },
    {
        "name": "filter_by_dietary_constraint",
        "description": "Filter recipes by dietary constraints"
    },
    {
        "name": "get_nutrition_info",
        "description": "Get detailed nutrition information for a recipe"
    }
]
```

**Agent Workflow:**
1. Claude analyzes query and selects tool
2. Execute tool with parameters
3. Generate final response with tool result

---

## 🎨 UI/UX Features

### Design System
- **Color scheme:** Soft pastel pink & lavender
- **Typography:** Clean, modern fonts
- **Animations:** Smooth transitions and hover effects
- **Responsive:** Works on desktop, tablet, mobile

### Components
- **Sidebar:** Navigation, streaks, daily tracker
- **Chat interface:** Message bubbles, typing indicators
- **Modals:** Settings, file viewer, daily tracker, meal logging
- **Cards:** Suggestion cards, meal plan cards, shopping list items

### Interactions
- **Auto-resize textarea** - Expands as you type
- **Keyboard shortcuts** - Enter to send, Shift+Enter for new line
- **Click suggestions** - Pre-filled prompts
- **Drag-and-drop** - File uploads

---

## 💾 Data Structure

### User Session JSON
```json
{
  "username": "Alice",
  "password_hash": "...",
  "profile_photo": "/uploads/user_profile.jpg",
  "nutrition_profile": {
    "dietary": ["vegan", "gluten-free"],
    "healthGoal": "weight-loss",
    "allergies": ["shellfish", "soy"]
  },
  "nutrition_logs": [
    {
      "id": "uuid",
      "date": "2024-01-15",
      "meal_type": "Breakfast",
      "name": "Oatmeal",
      "calories": 350,
      "protein": 12,
      "carbs": 58,
      "fats": 8,
      "timestamp": "2024-01-15T08:30:00"
    }
  ],
  "streaks": {
    "current": 7,
    "longest": 14,
    "last_login": "2024-01-15"
  },
  "favorites": [
    {"recipeId": "1", "recipeName": "Vegan Buddha Bowl"}
  ],
  "meal_plan": {
    "Monday": "Grilled Chicken Salad",
    "Tuesday": "Salmon with Vegetables"
  },
  "shopping_list": [
    {"name": "Quinoa", "checked": false},
    {"name": "Chickpeas", "checked": true}
  ],
  "chats": [],
  "uploaded_files": []
}
```

---

## 🔒 Security Features

- **Password hashing** - werkzeug.security
- **Secure filenames** - Sanitized uploads
- **Session-based auth** - No tokens in URLs
- **File type validation** - Only .txt, .docx allowed
- **Input sanitization** - XSS prevention
- **User data isolation** - Separate session files

---

## 📈 Performance

### Speed
- Meal logging: <100ms
- Stats calculation: <50ms
- Recommendations: <200ms
- Chat response: 2-5s (includes AI inference)

### Storage
- Per user: ~10KB for 30 days of logs
- Efficient JSON structure
- No database overhead (local mode)

---

## 🚀 Future Enhancements

### Phase 2 (Next Sprint)
- [ ] Weekly nutrition reports with charts
- [ ] Calorie/macro goals with progress bars
- [ ] Hydration tracking
- [ ] Weight/measurement trends

### Phase 3 (Advanced)
- [ ] Photo-based meal logging (AI food recognition)
- [ ] Correlation insights ("You have more energy on high-protein days")
- [ ] Social features (share streaks, challenges)
- [ ] Push notifications for meal reminders

### Phase 4 (Premium)
- [ ] Export reports as PDF
- [ ] Integration with fitness trackers
- [ ] Voice input for meal logging
- [ ] Meal prep batch suggestions
- [ ] Recipe scaling calculator
- [ ] Cooking timers
- [ ] Integration with smart kitchen devices

---

## 💰 Business Value

### Cost Savings for Users
- **Nutritionist:** $400-800/month
- **This app:** $0 (local) or ~$1/month (AWS)
- **Annual savings:** $4,800-9,600

### Competitive Advantages

| Feature | MyFitnessPal | Nutritionist | Our App |
|---------|--------------|--------------|---------|
| Daily Tracking | ✅ | ❌ | ✅ |
| Streaks | ✅ | ❌ | ✅ |
| AI Recommendations | ❌ | ✅ | ✅ |
| Real-time Feedback | ✅ | ❌ | ✅ |
| Personalized Recipes | ❌ | ✅ | ✅ |
| Cost | $10/mo | $400/mo | FREE |

### Retention Impact
- **Before:** 20% return after 1 week
- **After:** 60%+ return after 1 week (projected)
- **Reason:** Daily habit formation through streaks

---

## 🎯 Success Metrics

Track these KPIs:
1. **Daily Active Users (DAU)** - Target: 70%+
2. **Average Streak Length** - Target: 14+ days
3. **Meals Logged Per Day** - Target: 2-3
4. **Recommendation Click Rate** - Target: 40%+
5. **7-Day Retention** - Target: 60%+
6. **30-Day Retention** - Target: 40%+

---

## 🧪 Testing

### Manual Testing
```bash
# Start app
python src/app_local.py

# Open browser
http://localhost:5000

# Test workflow
1. Login with any username/password
2. Click "📊 Daily Tracker"
3. Log a meal
4. Watch stats update
5. Check recommendations
6. Try agent commands: "plan my week"
```

### Automated Testing
```bash
python test_daily_features.py
```
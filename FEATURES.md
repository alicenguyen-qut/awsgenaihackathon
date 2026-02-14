# Features Guide

## 🍳 Core Features

### 1. AI-Powered Chat
- RAG-based responses using Amazon Bedrock (Claude 3 Haiku)
- Semantic recipe search with Titan Embeddings
- Multi-chat management
- Document upload (.txt, .docx, .pdf)

### 2. User Profile
- Secure authentication with password hashing
- Profile photo upload/delete
- Dietary restrictions (vegan, vegetarian, gluten-free, dairy-free, nut-free)
- Health goals (weight loss, muscle gain, maintenance, heart health, energy boost)
- Allergy tracking

### 3. Recipe Management
- Bookmark favorites
- Quick access to saved recipes

### 4. Meal Planning
- Weekly planner
- Edit/delete meals
- Persistent storage

### 5. Shopping List
- Add/remove items
- Check off purchased items
- Syncs across sessions

---

## 📊 Daily Nutrition Features

### Daily Tracking
- Log meals with calories and macros
- Real-time daily totals
- Meal history with timestamps
- Delete meals

### Habit Streaks
- Auto-increments on daily login
- Tracks current and longest streak
- Achievement badges: 7, 30, 100, 365 days
- Visual display with 🔥 icon

### Smart Recommendations
- AI suggests meals based on nutrition gaps
- Considers dietary preferences and health goals
- Updates in real-time

---

## 🤖 Autonomous Agent

### Frontend Agent
Executes actions without explicit commands:

| Intent | Keywords | Action |
|--------|----------|--------|
| Plan Week | "plan my week" | Auto-populates 7-day planner |
| Shopping List | "shopping list" | Extracts ingredients from plan |
| Save Favorite | "save this" | Bookmarks recipe |
| Add to Plan | "add to Monday" | Adds meal to specific day |

### Proactive Suggestions
- Morning: Breakfast suggestions
- Lunch: Based on preferences
- Dinner: Reminds of planned meals

---

## 💰 Cost Comparison

| Feature | MyFitnessPal | Nutritionist | Our App |
|---------|--------------|--------------|---------|
| Daily Tracking | ✅ | ❌ | ✅ |
| Streaks | ✅ | ❌ | ✅ |
| AI Recommendations | ❌ | ✅ | ✅ |
| Personalized Recipes | ❌ | ✅ | ✅ |
| Cost | $10/mo | $400/mo | FREE |

**Annual Savings:** $4,800-9,600 vs nutritionist

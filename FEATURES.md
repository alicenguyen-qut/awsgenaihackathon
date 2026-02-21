# Features Guide

## 🍳 Core Features

### 1. AI-Powered Chat
- RAG-based responses using Amazon Bedrock (Claude 3 Haiku)
- Agentic capabilities via Strands Agent with 6 built-in tools
- Semantic recipe search with Amazon Titan Embeddings V2 (1024-dim, cosine similarity)
- Multi-chat management (create, switch, delete)
- Document upload and RAG over user files (.txt, .docx, .pdf)

### 2. User Profile
- Secure authentication with password hashing 
- Profile photo upload/delete
- Dietary restrictions (vegan, vegetarian, gluten-free, dairy-free, nut-free)
- Health goals (weight loss, muscle gain, maintenance, heart health, energy boost)
- Allergy tracking

### 3. Recipe Management
- Bookmark favorites (add/remove toggle)
- Quick access to saved recipes

### 4. Meal Planning
- Weekly planner (Monday–Sunday)
- Edit/delete meals per day
- Persistent storage 

### 5. Shopping List
- Add/remove items
- Check off purchased items
- Clear all items
- Syncs across sessions

---

## 📊 Daily Nutrition Features

### Daily Tracking
- Log meals with calories and macros (protein, carbs, fats)
- Real-time daily totals
- Meal history by date/month/year
- Delete individual meal logs

### Analytics
- Period analytics: today, week, month, year
- Average daily calories and protein
- Best day tracking
- Most common meal type insights

### Habit Streaks
- Auto-increments on daily login
- Tracks current and longest streak
- Achievement badges: 7, 30, 100, 365 days

### Smart Recommendations
- AI suggests meals based on today's nutrition gaps
- Considers dietary preferences and health goals

---

## 🤖 Strands Agent Tools

The agent (powered by Strands + Claude 3 Haiku) autonomously executes the following tools:

| Tool | Description |
|------|-------------|
| `search_recipes` | Semantic search over S3-indexed recipes |
| `add_to_favorites` | Bookmarks a recipe to the user's favourites |
| `add_to_meal_plan` | Adds a meal to a specific day (Monday–Sunday) |
| `add_to_shopping_list` | Appends ingredients to the shopping list |
| `log_nutrition` | Logs a meal with calories and macros |
| `get_nutrition_stats` | Returns today's nutrition totals and remaining budget |

All tool calls are logged and returned to the frontend for transparent visual feedback.

Example of keyword-based intent detection that triggers agent actions:

| Intent | Keywords | Action |
|--------|----------|--------|
| Plan Week | "plan my week" | Auto-populates 7-day planner |
| Shopping List | "shopping list" | Extracts ingredients from plan |
| Save Favorite | "save this" | Bookmarks recipe |
| Add to Plan | "add to Monday" | Adds meal to specific day |

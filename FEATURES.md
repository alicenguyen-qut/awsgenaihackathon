# Features Guide

## 🍳 Core Features

### 1. AI-Powered Chat
- Multi-agent architecture: Coordinator routes to specialist Planner, Nutrition, and Document agents
- RAG-based responses using Amazon Bedrock (Claude 3 Haiku)
- Semantic recipe search with Amazon Titan Embeddings V2 (cosine similarity)
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

## 🤖 Multi-Agent System (Strands)

MealBuddy uses a **coordinator + specialist agent** pattern powered by Strands and Claude 3 Haiku on Amazon Bedrock.

```
User Message
     │
     ▼
Coordinator (intent router)
     │
     ├──► 🥗 Planner Agent      → meal planning, shopping list, favourites
     ├──► 📊 Nutrition Agent    → calorie tracking, macro stats, snack suggestions
     └──► 📄 Document Agent     → RAG over uploaded PDFs, dietary restrictions
```

| Agent | Triggers | Tools |
|-------|----------|-------|
| **Planner Agent** | plan, meal, shopping, grocery, favourite | `add_to_meal_plan`, `add_to_shopping_list`, `add_to_favorites` |
| **Nutrition Agent** | calorie, macro, remaining, log, track, snack | `get_nutrition_stats`, `log_nutrition` |
| **Document Agent** | restriction, allergy, document, pdf, my file | none (pure RAG) |

All tool calls are logged and returned to the frontend for transparent visual feedback.

**Why multi-agent?** Each specialist agent has a short, focused system prompt — this significantly improves Claude 3 Haiku's reliability compared to a single agent handling all intents.

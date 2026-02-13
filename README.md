# AI Cooking Assistant

Personalized AI cooking assistant using RAG (Retrieval-Augmented Generation) with AWS services.

## Architecture

```
User → Flask UI → API Gateway → Lambda → Bedrock (Claude)
                                    ↓
                              S3 (Embeddings)
                                    ↑
                              Titan Embeddings
```

**Cost-Optimized:** Uses S3 + in-memory vector search instead of OpenSearch (~$700/month savings!)

## Key Features

### 🔥 Daily-Use Features (Replaces Nutritionist Visits!)
- **📊 Daily Nutrition Tracking** - Log meals with calories/macros, see real-time totals
- **🔥 Habit Streaks** - Gamified daily login streaks to build consistency
- **💡 Smart Recommendations** - AI suggests meals based on today's nutrition gaps

### 🤖 Autonomous Agent System
- **Intent detection** - Understands "plan my week", "generate shopping list"
- **Multi-step execution** - Chains actions automatically
- **Proactive suggestions** - Time-based meal recommendations

### 🍳 Core Features
- AI-powered chat with RAG
- Recipe favorites & meal planning
- Shopping list management
- User profiles with dietary preferences
- Document upload support

**See [FEATURES.md](FEATURES.md) for complete feature documentation.**

## Tech Stack

- **Frontend:** Flask + HTML/CSS + JavaScript
- **Backend:** Python (Flask)
- **LLM:** Amazon Bedrock (Claude 3 Haiku)
- **Embeddings:** Amazon Titan Embeddings
- **Vector Storage:** S3 + NumPy cosine similarity
- **Infrastructure:** CloudFormation
- **Session Storage:** JSON file-based

## Quick Start

### Local Development (No AWS Required)
```bash
# Install dependencies
pip install -r requirements.txt

# Run local server
python src/app_local.py

# Visit http://localhost:5000
```

### AWS Deployment
See [DEPLOYMENT.md](DEPLOYMENT.md) for full AWS deployment instructions.

## Project Structure

```
├── data/                          # Recipe documents (RAG optimized)
├── infrastructure/                # CloudFormation templates
├── scripts/                       # Indexing and deployment scripts
├── src/
│   ├── app_local.py              # Local Flask application
│   ├── app.py                    # AWS Flask application
│   ├── lambda_function.py        # Lambda handler
│   ├── frontend/js/
│   │   ├── session-manager.js    # Login, logout, profile, settings
│   │   ├── chat-manager.js       # Chat list, create/delete chats
│   │   ├── chat-messages.js      # Send/display messages
│   │   ├── autonomous-agent.js   # AI agent intent detection & actions
│   │   ├── nutrition-tracker.js  # Meal logging & nutrition stats
│   │   ├── nutrition-init.js     # Initialize nutrition features
│   │   ├── meal-features.js      # Favorites, meal planner, shopping list
│   │   ├── files.js              # File upload/view/delete
│   │   └── app-init.js           # App startup & UI initialization
│   └── templates/
│       └── index.html            # Main UI template
├── sessions/                     # User session data (local)
├── uploads/                      # Uploaded files & profile photos
└── requirements.txt
```

## API Endpoints

See [FEATURES.md](FEATURES.md) for complete API documentation.

**Key endpoints:**
- Authentication: `/api/login`, `/api/logout`, `/api/session`
- Chat: `/api/chat/new`, `/api/chat/<id>`, `/chat`
- Daily Tracking: `/api/nutrition/log`, `/api/nutrition/stats`, `/api/streaks`
- Features: `/api/favorites`, `/api/meal-plan`, `/api/shopping-list`

## Testing

```bash
# Run automated tests
python test_daily_features.py

# Manual testing
1. Start app: python src/app_local.py
2. Open: http://localhost:5000
3. Login with any username/password
4. Try features: Daily Tracker, Meal Planning, Agent commands
```

## Documentation

- **[FEATURES.md](FEATURES.md)** - Complete feature guide
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - AWS deployment instructions
- **README.md** (this file) - Quick start & overview

## Future Enhancements

- [ ] Weekly nutrition reports with charts
- [ ] Photo-based meal logging (AI food recognition)
- [ ] Hydration tracking
- [ ] Weight/measurement trends
- [ ] Voice input support
- [ ] Mobile app

## License

MIT License

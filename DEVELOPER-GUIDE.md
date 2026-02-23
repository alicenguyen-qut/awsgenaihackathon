# Developer Guide

## 1. Overview
```
User → Flask UI → Elastic Beanstalk → Bedrock (Claude 3 Haiku + Titan Embeddings V2)
                      ↓
                  S3 Bucket
                  ├── embeddings/    (Recipe embeddings — recipe_embeddings.json)
                  ├── recipes/       (Recipe raw data)
                  ├── sessions/      (User session JSON files)
                  └── uploads/       (User-uploaded files + per-user embeddings)
```

**AWS Services Selected for Cost-Optimised For Hackathon Demo** Elastic Beanstalk t3.micro (webapp host) + S3 (data storage) + AWS Bedrock models (for LLM) + Open source Stands Agent + In-memory NumPy cosine similarity for RAG

## 2. Key Features

### 2.1 🔥 Daily-Use Features
- **📊 Daily Nutrition Tracking** — Log meals with calories/macros, real-time totals, period analytics (today/week/month/year)
- **🔥 Habit Streaks** — Gamified daily login streaks with badges at 7, 30, 100, 365 days
- **💡 Smart Recommendations** — AI suggests meals based on today's nutrition gaps and user profile

### 2.2 🤖 Strands Agent System
- **Coordinator agent tools** — `ask_planner`, `ask_nutrition`, `ask_document` (routes to specialist sub-agents)
- **Planner sub-agent tools** — `search_recipes`, `add_to_meal_plan`, `add_to_shopping_list`, `add_to_favorites`
- **Nutrition sub-agent tools** — `log_nutrition`, `get_nutrition_stats`
- **Tool call logging** — All agent actions returned to frontend for transparent visual feedback
- **RAG over user uploads** — Per-user embeddings for personalisation

### 2.3 🍳 Core Features
- AI-powered chat with RAG (Titan Embeddings V2, 1024-dim)
- Recipe favourites & weekly meal planning
- Shopping list management
- User profiles with dietary preferences and health goals
- Document upload: .txt, .docx, .pdf

**See [FEATURES.md](FEATURES.md) for complete feature documentation.**

## 3. Tech Stack

- **Frontend:** JavaScript + HTLM/CSS
- **Backend:** Python 3.9+ with FlaskAPI
- **AI Agent:** Strands Agents (`strands-agents`) + Amazon Bedrock Claude 3 Haiku
- **Embeddings:** Amazon Titan Embeddings V2 (`amazon.titan-embed-text-v2:0`)
- **Storage:** S3 
- **Infrastructure:** Elastic Beanstalk (t3.micro) + S3 + IAM, deployed via CloudFormation

## 4. CloudFormation Deployment
- Elastic Beanstalk app with t3.micro EC2 running Flask via Gunicorn
- S3 bucket for recipes, embeddings, sessions, and uploads
- IAM Role with S3 + Bedrock permissions

## 5. Quick Start

### 5.1 Prerequisites
- Python 3.9+
- `uv` and `pip`
- AWS CLI (for deployment)
- `make`

### 5.2 Installation

```bash
make install
```

### 5.3 Running Locally

**Option 1: Without AWS (Mock Mode)**
```bash
# No AWS credentials needed — uses mock recipe data and mock chat responses
make run-local
```

**Option 2: With AWS (Bedrock + S3)**
```bash
# Requires AWS CLI configured with Bedrock access + S3 deployed with embeddings
make run-aws
```

Access at: http://localhost:5000

### 5.4 Deploy to AWS

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

**What gets deployed:**
- Elastic Beanstalk application (t3.micro EC2)
- S3 bucket for recipes, embeddings, sessions, and uploads
- IAM role with S3 and Bedrock permissions
- Recipe embeddings indexed with Titan V2 (`scripts/index_recipes.py`)

### 5.5 Clean Up

```bash
chmod +x scripts/cleanup.sh
./scripts/cleanup.sh
```

## 6. Project Structure

```
awsgenaihackathon/
├── architecture_diagrams/         # AWS architecture diagrams 
├── data/                          # Recipe documents
│   ├── nutrition_guidelines.txt
│   └── recipe_*.txt             
├── infrastructure/
│   └── cloudformation.yaml        # CI/CD deployment
├── scripts/
│   ├── deploy.sh                  # Deploys AWS resources
│   ├── cleanup.sh                 # Destroys AWS resources
│   ├── index_recipes.py           # Indexes recipes → S3 embeddings
│   └── misc/                      # Miscellaneous utility scripts
├── src/
│   ├── app.py                     # Flask app + all API routes
│   ├── models/
│   │   └── bedrock_rag.py         # BedrockRAG: embeddings, search, Strands agent
│   ├── utils/
│   │   ├── config.py              # Configs
│   │   ├── storage.py             # Data storage abstraction
│   │   ├── helpers.py             # Helper utils
│   │   ├── analytics.py           # Nutrition stats, period analytics, streak logic
│   │   ├── recommendations.py     # Daily meal recommendations
│   │   └── responses.py           # Mock chat responses (for local testing mode)
│   └── frontend/
│       ├── js/
│       │   ├── 01-core.js         # Core utilities & initialisation
│       │   ├── 02-auth.js         # Authentication & user management
│       │   ├── 03-chat.js         # Chat operations & messages
│       │   ├── 04-nutrition.js    # Nutrition tracking & analytics
│       │   ├── 05-meals.js        # Favourites, planner, shopping list
│       │   ├── 06-files.js        # File upload/management
│       │   └── 07-agent.js        # Frontend intent detection & agent actions
│       └── templates/
│           └── index.html         # Frontend index
├── Procfile                       # Gunicorn entry point for Elastic Beanstalk
├── Makefile
├── requirements.txt
├── FEATURES.md
├── DEVELOPER-GUIDE.md
└── README.md
```

## 7. API Endpoints

### 7.1 Authentication
- `POST /api/login` — Login or register
- `POST /api/logout` — Clear session
- `GET /api/session` — Get current session, username, and chat list
- `POST /api/change-password` — Change password

### 7.2 Chat
- `POST /api/chat/new` — Create new chat
- `GET /api/chat/<id>` — Get chat by ID
- `DELETE /api/chat/<id>` — Delete chat
- `POST /chat` — Send and receive chat messages
- `POST /chat/stream` — Send chat message and receive streaming response
- `POST /api/clear-chats` — Clear all chat history

### 7.3 Nutrition Tracking
- `POST /api/nutrition/log` — Log a meal 
- `GET /api/nutrition/logs?date=YYYY-MM-DD` — Get logs for a date
- `GET /api/nutrition/stats?date=YYYY-MM-DD` — Get daily totals
- `DELETE /api/nutrition/logs/<id>` — Delete a log entry
- `GET /api/nutrition/analytics?period=today|week|month|year` — Period analytics
- `GET /api/streaks` — Get current/longest streak and trigger daily update
- `GET /api/recommendations/daily` — AI-powered meal recommendations

### 7.4 Meal Features
- `POST /api/favorites` — Toggle favourite
- `GET /api/favorites` — List all favourites
- `GET /api/meal-plan` — Get weekly plan
- `POST /api/meal-plan` — Save weekly plan
- `GET /api/shopping-list` — Get shopping list
- `POST /api/shopping-list` — Add item
- `POST /api/shopping-list/<index>/toggle` — Toggle checked status
- `DELETE /api/shopping-list/<index>` — Delete item
- `POST /api/shopping-list/clear` — Clear all items

### 7.5 User Profile
- `POST /api/nutrition-profile` — Save dietary preferences, health goal, allergies
- `GET /api/nutrition-profile` — Get profile
- `POST /api/profile-photo` — Upload profile photo
- `GET /api/profile-photo` — Get photo URL
- `DELETE /api/profile-photo` — Delete photo

### 7.6 File Management
- `POST /upload` — Upload file (.txt, .docx, .pdf); auto-embeds to S3
- `GET /uploads/<filename>` — Serve an uploaded file 
- `GET /api/files` — List uploaded files
- `GET /api/files/<id>` — Get file content/metadata
- `DELETE /api/files/<id>` — Delete file and remove S3 embeddings
- `POST /api/clear-files` — Clear all uploaded files
# Personal Cooking Assistant

Personalized AI cooking assistant using RAG (Retrieval-Augmented Generation) with AWS Bedrock services, hosted on AWS EC2 and data storage via S3.

## Architecture

```
User → Flask UI → EC2 Instance → Bedrock (Claude + Titan)
                      ↓
                  S3 Bucket
                  ├── embeddings/    (Recipe embeddings)
                  ├── recipes/       (Recipe texts)
                  ├── sessions/      (User data)
                  └── uploads/       (User-uploaded files)
```

**Cost-Optimized:** Uses EC2 t3.micro + S3 Vector + in-memory vector search

## Key Features

### 🔥 Daily-Use Features
- **📊 Daily Nutrition Tracking** - Log meals with calories/macros, see real-time totals
- **🔥 Habit Streaks** - Gamified daily login streaks with achievements and milestones (clickable for details)
- **💡 Smart Recommendations** - AI suggests meals based on today's nutrition gaps
- **🏆 Achievement System** - Unlock badges at 7, 30, 100, and 365-day milestones

### 🤖 Autonomous Agent System
- **Intent detection** - Understands "plan my week", "generate shopping list"
- **Multi-step execution** - Chains actions automatically 
- **Proactive suggestions** - Time-based meal recommendations
- **Tool use capabilities** - Autonomously searches recipes, adds favorites, plans meals, generates shopping lists, and logs nutrition
- **Transparent actions** - All agent actions are displayed with visual feedback

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
- **Infrastructure:** EC2 t3.micro + CloudFormation
- **LLM:** Amazon Bedrock 
- **Embeddings:** Amazon Titan Embeddings
- **S3 Vector:** S3 + NumPy cosine similarity
- **Session Storage:** S3 
## Quick Start

### Prerequisites
- Python 3.9+
- pip/uv (Python package manager)
- make CLI
- AWS CLI (for deployment)
- EB CLI (for Elastic Beanstalk): `pip install awsebcli`

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd awsgenaihackathon

# Install dependencies
make install
```

### Running Locally (No AWS Required)

```bash
make run
# Visit http://localhost:5000
```

The app will start in **LOCAL MODE** by default, using mock data and file-based storage.

### Running with AWS (Elastic Beanstalk)

**Much simpler than EC2!**

```bash
# 1. Install EB CLI
pip install awsebcli

# 2. Clean up old EC2 deployment (if exists)
chmod +x scripts/cleanup.sh
./scripts/cleanup.sh

# 3. Deploy to Elastic Beanstalk
chmod +x scripts/deploy_eb.sh
./scripts/deploy_eb.sh

# 4. Get your URL
eb status

# View logs
eb logs

# Cleanup when done
./scripts/cleanup_eb.sh
```

**That's it!** No SSH, no systemd, no nginx config needed.

## Project Structure

```
awsgenaihackathon/
├── data/                          # Recipe documents (RAG optimized)
│   ├── nutrition_guidelines.txt
│   └── recipe_*.txt
├── infrastructure/                # CloudFormation templates
│   └── cloudformation.yaml       # EC2 deployment template
├── scripts/                       # Deployment scripts
│   ├── deploy.sh                 # EC2 deployment
│   ├── cleanup.sh                # Delete all AWS resources
│   └── index_recipes.py          # Recipe indexing (Titan V2)
├── src/
│   ├── app.py                     # Main Flask application
│   ├── models/                    # AI/ML models
│   │   ├── __init__.py
│   │   └── bedrock_rag.py        # Bedrock RAG (Titan V2 + Claude)
│   ├── utils/                     # Helper functions & config
│   │   ├── __init__.py
│   │   ├── config.py             # Configuration & constants
│   │   └── helpers.py            # User data, file handling
│   └── frontend/                 # Frontend assets
│       ├── js/                   # Modular JavaScript
│       │   ├── 01-core.js       # Core utilities & initialization
│       │   ├── 02-auth.js       # Authentication & user management
│       │   ├── 03-chat.js       # Chat operations & messages
│       │   ├── 04-nutrition.js  # Nutrition tracking & analytics
│       │   ├── 05-meals.js      # Favorites, planner, shopping
│       │   ├── 06-files.js      # File upload/management
│       │   └── 07-agent.js      # AI autonomous agent
│       └── templates/
│           └── index.html       # Main UI template
├── sessions/                      # Local user session data (gitignored)
├── uploads/                       # Local uploaded files (gitignored)
├── .env                           # Environment variables (gitignored)
├── .env.example                   # Environment variables template
├── .gitignore
├── DEPLOYMENT.md                  # AWS deployment guide
├── FEATURES.md                    # Feature documentation
├── Makefile                       # Build commands
├── README.md                      # Main documentation
└── requirements.txt               # Python dependencies
```

## API Endpoints

### Authentication
- `POST /api/login` - Login or register user
- `POST /api/logout` - Logout user
- `GET /api/session` - Get current session

### Chat
- `POST /api/chat/new` - Create new chat
- `GET /api/chat/<id>` - Get chat by ID
- `DELETE /api/chat/<id>` - Delete chat
- `POST /chat` - Send message and get AI response

### Nutrition Tracking
- `POST /api/nutrition/log` - Log a meal
- `GET /api/nutrition/logs` - Get today's meal logs
- `GET /api/nutrition/stats` - Get nutrition statistics
- `DELETE /api/nutrition/logs/<id>` - Delete meal log
- `GET /api/streaks` - Get login streaks
- `GET /api/nutrition/analytics` - Get analytics (today/week/month/year)
- `GET /api/recommendations/daily` - Get daily meal recommendations

### Meal Features
- `POST /api/favorites` - Toggle favorite recipe
- `GET /api/favorites` - Get favorite recipes
- `GET /api/meal-plan` - Get weekly meal plan
- `POST /api/meal-plan` - Save meal plan
- `GET /api/shopping-list` - Get shopping list
- `POST /api/shopping-list` - Add item to shopping list
- `POST /api/shopping-list/<index>/toggle` - Toggle item checked
- `DELETE /api/shopping-list/<index>` - Delete item
- `POST /api/shopping-list/clear` - Clear all items

### User Profile
- `POST /api/nutrition-profile` - Save nutrition profile
- `GET /api/nutrition-profile` - Get nutrition profile
- `POST /api/profile-photo` - Upload profile photo
- `GET /api/profile-photo` - Get profile photo URL
- `DELETE /api/profile-photo` - Delete profile photo
- `POST /api/change-password` - Change password

### File Management
- `POST /upload` - Upload file (.txt, .docx, or .pdf)
- `GET /api/files` - List uploaded files
- `GET /api/files/<id>` - Get file content
- `DELETE /api/files/<id>` - Delete file

### Settings
- `POST /api/clear-chats` - Clear all chats
- `POST /api/clear-files` - Clear all uploaded files

See [FEATURES.md](FEATURES.md) for detailed API documentation with examples.
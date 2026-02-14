# Personal Cooking Assistant

Personalized AI cooking assistant using RAG (Retrieval-Augmented Generation) with AWS Bedrock services, hosted on AWS Elastic Beanstalk and data storage via S3.

## Architecture

```
User → Flask UI → Elastic Beanstalk → Bedrock (Claude + Titan)
                      ↓
                  S3 Bucket
                  ├── embeddings/    (Recipe embeddings)
                  ├── recipes/       (Recipe texts)
                  ├── sessions/      (User data)
                  └── uploads/       (User-uploaded files)
```

**Cost-Optimized:** Uses Elastic Beanstalk t3.micro + S3 + in-memory vector search

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
- **Infrastructure:** Webapp hosted on Elastic Beanstalk All services deployed via CloudFormation
- **LLM:** Amazon Bedrock Haiku 
- **Embeddings:** Amazon Titan Embeddings
- **S3 Storage:** S3 (User data, session data, embedding data running NumPy cosine similarity)

## Cloudformation deployment
- Elastic Beanstalk using t3.micro EC2 instance with Flask app
- S3 bucket for all data storage
- Security Group (HTTP, HTTPS, SSH)
- IAM Role (S3 + Bedrock permissions)

## Quick Start

### Prerequisites
- Python 3.9+
- uv and pip (Python package manager)
- AWS CLI (for deployment)
- Make CLI

### Installation

```bash
make install
```

### Running Locally

**Option 1: Without AWS (Mock Mode)**
```bash
make run-local
# No AWS credentials needed - uses mock data responses
# Visit http://localhost:5000
```

**Option 2: With AWS Bedrock + S3**
```bash
make run-aws
# Requires: AWS CLI configured with Bedrock access + S3 deployed with embeddings (Please see Deploy to AWS)
# Visit http://localhost:5000
```

### Deploy to AWS

```bash
# Deploy to AWS
# This script will also run AWS Cloudformation CLI to deploy `infrastructure/cloudformation.yaml`
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```
```bash
# Cleanup - deleting all resrouces
chmod +x scripts/cleanup.sh
./scripts/cleanup.sh
```

## Project Structure

```
awsgenaihackathon/
├── data/                          # Recipe documents (RAG optimized)
│   ├── nutrition_guidelines.txt
│   └── recipe_*.txt
├── infrastructure/                # CloudFormation templates
│   └── cloudformation.yaml       # Elastic Beanstalk deployment
├── scripts/                       # Deployment scripts
│   ├── deploy.sh                 # Single deployment script
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
├── Procfile                       # Elastic Beanstalk process config
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
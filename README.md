# Personal Cooking Assistant

Personalized AI cooking assistant using RAG (Retrieval-Augmented Generation) with AWS Bedrock services (Claude Haiku for chat, Titan Embeddings V2 for semantic search), hosted on AWS Elastic Beanstalk with S3 storage.

## 1. Architecture
```
User → Flask UI → Elastic Beanstalk → Bedrock (Claude + Titan Embeddings V2 )
                      ↓
                  S3 Bucket
                  ├── embeddings/    (Recipe embeddings)
                  ├── recipes/       (Recipe raw data)
                  ├── sessions/      (User chat session data & configs)
                  └── uploads/       (User-uploaded files)
```

**Cost-Optimized:** Uses Elastic Beanstalk t3.micro + S3 + in-memory vector search

## 2. Key Features

### 2.1 🔥 Daily-Use Features
- **📊 Daily Nutrition Tracking** - Log meals with calories/macros, see real-time totals
- **🔥 Habit Streaks & Achievement Unlock** - Gamified daily login streaks with achievements and milestones. Unlock badges at 7, 30, 100, and 365-day milestones
- **💡 Smart Recommendations** - AI suggests meals based on today's nutrition gaps

### 2.2 🤖 Autonomous Agent System
- **Intent detection** - Understands "plan my week", "generate shopping list"
- **Multi-step execution** - Chains actions automatically 
- **Proactive suggestions** - Time-based meal recommendations
- **Tool use capabilities** - Autonomously searches recipes, adds favorites, plans meals, generates shopping lists, and logs nutrition
- **Transparent actions** - All agent actions are displayed with visual feedback

### 2.3 🍳 Core Features
- AI-powered chat with RAG
- Recipe favorites & meal planning
- Shopping list management
- User profiles with dietary preferences
- Document upload support

**See [FEATURES.md](FEATURES.md) for complete feature documentation.**

## 3. Tech Stack

- **Frontend:** Flask + HTML/CSS + JavaScript
- **Backend:** Python (Flask)
- **Infrastructure:** Webapp hosted on Elastic Beanstalk All services deployed via CloudFormation
- **LLM:** Amazon Bedrock Haiku 
- **Embeddings:** Amazon Titan Embeddings
- **S3 Storage:** S3 (User data, session data, embedding data running NumPy cosine similarity)

## 4. CloudFormation Deployment
- Elastic Beanstalk using t3.micro EC2 instance with Flask app
- S3 bucket for all data storage
- IAM Role (S3 + Bedrock permissions)

## 5. Quick Start

### 5.1 Prerequisites
- Python 3.9+
- uv and pip (Python package manager)
- AWS CLI (for deployment)
- Make CLI

### 5.2 Installation

```bash
make install
```

### 5.3 Running Locally

**Option 1: Without AWS (Mock Mode to test UI + Features)**
```bash
# No AWS credentials needed - uses mock data responses
make run-local
```

**Option 2: With AWS Bedrock + S3 (To test UI + LLM model + Embeddings stored in S3)**
```bash
# Requires: AWS CLI configured with Bedrock access + S3 deployed with embeddings (Please see Deploy to AWS)
make run-aws
```
Access the local chatbot at: http://localhost:5000

### 5.4 Deploy to AWS

```bash
# Deploy to AWS via CloudFormation
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

**What gets deployed:**
- Elastic Beanstalk application (t3.micro EC2 instance)
- S3 bucket for recipes, embeddings, sessions, and uploads
- IAM role with S3 and Bedrock permissions
- Recipe embeddings indexed with Titan V2

### 5.5 Clean up AWS resources
```bash
# Cleanup - deleting all resrouces
chmod +x scripts/cleanup.sh
./scripts/cleanup.sh
```

## 6. Project Structure

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

## 7. API Endpoints

### 7.1 Authentication
- `POST /api/login` - Login or register user
- `POST /api/logout` - Logout user
- `GET /api/session` - Get current session

### 7.2 Chat
- `POST /api/chat/new` - Create new chat
- `GET /api/chat/<id>` - Get chat by ID
- `DELETE /api/chat/<id>` - Delete chat
- `POST /chat` - Send message and get AI response (includes tool calls)

### 7.3 Nutrition Tracking
- `POST /api/nutrition/log` - Log a meal with calories and macros
- `GET /api/nutrition/logs` - Get meal logs 
- `GET /api/nutrition/stats` - Get nutrition statistics 
- `DELETE /api/nutrition/logs/<id>` - Delete meal log
- `GET /api/streaks` - Get login streaks and achievements
- `GET /api/nutrition/analytics` - Get analytics 
- `GET /api/recommendations/daily` - Get AI-powered daily meal recommendations

### 7.4 Meal Features
- `POST /api/favorites` - Add/remove favorite recipe 
- `GET /api/favorites` - Get all favorite recipes
- `GET /api/meal-plan` - Get weekly meal plan
- `POST /api/meal-plan` - Save meal plan 
- `GET /api/shopping-list` - Get shopping list items
- `POST /api/shopping-list` - Add item to shopping list 
- `POST /api/shopping-list/<index>/toggle` - Toggle item checked status
- `DELETE /api/shopping-list/<index>` - Delete shopping list item
- `POST /api/shopping-list/clear` - Clear all shopping list items

### 7.5 User Profile
- `POST /api/nutrition-profile` - Save nutrition profile (dietary preferences, health goals, allergies)
- `GET /api/nutrition-profile` - Get nutrition profile
- `POST /api/profile-photo` - Upload profile photo 
- `GET /api/profile-photo` - Get profile photo URL
- `DELETE /api/profile-photo` - Delete profile photo
- `POST /api/change-password` - Change password 

### 7.6 File Management
- `POST /upload` - Upload file (multipart/form-data, supports .txt, .docx, .pdf)
- `GET /api/files` - List all uploaded files
- `GET /api/files/<id>` - Get file content and metadata
- `DELETE /api/files/<id>` - Delete uploaded file

### 7.7 Settings
- `POST /api/clear-chats` - Clear all chat history
- `POST /api/clear-files` - Clear all uploaded files
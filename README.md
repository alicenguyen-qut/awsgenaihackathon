# Personal Cooking Assistant

Personalized AI cooking assistant using RAG (Retrieval-Augmented Generation) with AWS services.

## Architecture

```
User → Flask UI → EC2 Instance → Bedrock (Claude + Titan)
                      ↓
                  S3 Bucket
                  ├── embeddings/    (Recipe embeddings)
                  ├── recipes/       (Recipe texts)
                  ├── sessions/      (User data)
                  └── uploads/       (User files)
```

**Cost-Optimized:** Uses EC2 t3.micro + S3 + in-memory vector search

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
- **Vector Storage:** S3 + NumPy cosine similarity
- **Session Storage:** S3 (AWS mode) or JSON file-based (local mode)

## Quick Start

### Prerequisites
- Python 3.9+
- pip (Python package manager)

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd awsgenaihackathon

# Install dependencies
pip install -r requirements.txt
```

### Running Locally (No AWS Required)

```bash
# Run the app
python src/app.py

# Or use make
make run

# Visit http://localhost:5000
```

The app will start in **LOCAL MODE** by default, using mock data and file-based storage.

### Running with AWS

```bash
# Set environment variable
export USE_AWS=true

# Run the app
python src/app.py

# Or use make
make run-aws
```

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
├── .gitignore
├── DEPLOYMENT.md                  # AWS deployment guide
├── FEATURES.md                    # Feature documentation
├── Makefile                       # Build commands
├── README.md                      # Main documentation
└── requirements.txt               # Python dependencies
```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `USE_AWS` | Enable AWS mode | `false` | No |
| `AWS_REGION` | AWS region | `ap-southeast-2` | AWS mode only |
| `S3_BUCKET` | S3 bucket for all data | - | AWS mode only |
| `RECIPES_BUCKET` | S3 bucket (legacy) | Same as S3_BUCKET | AWS mode only |
| `SECRET_KEY` | Flask secret key | `dev-secret-key-change-in-production` | Production only |

## Available Commands

```bash
# Install dependencies
make install

# Run locally
make run

# Deploy to EC2 (Cost Optimized ~$8-12/month)
make deploy-ec2

# Delete all AWS resources
make cleanup

# Clean cache files
make clean

# Show help
make help
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

## Testing

### Manual Testing

1. **Start the app:**
   ```bash
   python src/app.py
   ```

2. **Open browser:**
   ```
   http://localhost:5000
   ```

3. **Test features:**
   - Login with any username/password
   - Create a new chat
   - Send messages to AI
   - Open Daily Tracker (📊 button)
   - Log meals and check stats
   - Open Meal Planner
   - Add meals to weekly plan
   - Open Shopping List
   - Upload files (.txt, .docx, or .pdf)
   - Update profile settings

### Automated Testing

```bash
# Run refactoring tests
python test_refactoring.py

# Run feature tests (if available)
python test_daily_features.py
```

## Development

### Local Development Workflow

1. **Make changes** to code
2. **Restart app** to see changes
3. **Test manually** in browser
4. **Commit changes** to git

### Code Organization

- **Backend:** `src/app.py` - All Flask routes and business logic
- **Configuration:** `src/utils/config.py` - Environment variables and constants
- **Helpers:** `src/utils/helpers.py` - User data and file handling utilities
- **AI Models:** `src/models/bedrock_rag.py` - Bedrock RAG implementation
- **Frontend JS:** `src/frontend/js/` - Modular JavaScript files
- **Templates:** `src/frontend/templates/` - HTML templates
- **Styles:** Inline in `index.html` (consider extracting to CSS file)

### Adding New Features

1. **Backend:** Add route in `src/app.py`
2. **Frontend:** Add function in appropriate JS file in `src/frontend/js/`
3. **UI:** Update `src/frontend/templates/index.html`
4. **Test:** Verify locally before deploying

## Deployment

### AWS EC2 Deployment (Cost Optimized)

**Monthly Cost: ~$8-12/month**

```bash
# Deploy to EC2
make deploy-ec2

# Delete all resources
make cleanup
```

#### What Gets Deployed:
- **EC2 t3.micro instance** - $8.76/month (750 free tier hours)
- **S3 bucket** - ~$1-3/month for all data storage
  - Recipe embeddings (Titan V2)
  - Recipe text files
  - User session data
  - User uploaded files
- **Security groups** - Free
- **IAM roles** - Free
- **EC2 Key Pair** - Free

#### Services Used:
- **Amazon Bedrock** - Claude 3 Haiku + Titan Embeddings (~$15-25/month based on usage)
- **Amazon S3** - Unified storage for recipes and user data
- **Amazon EC2** - Web server hosting

#### Deployment Process:
1. Creates CloudFormation stack with all resources
2. Launches EC2 instance with auto-setup
3. Installs Python dependencies and Flask app
4. Configures nginx reverse proxy
5. Sets up systemd service for auto-restart
6. Indexes recipes to S3 (from local machine)
7. EC2 instance auto-indexes on startup

**See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment guide.**

#### Access:
- **Web App**: `http://<public-ip>`
- **SSH**: `ssh -i cooking-assistant-key.pem ec2-user@<public-ip>`
- **Logs**: `sudo journalctl -u cooking-assistant -f`

## Troubleshooting

### Common Issues

**App won't start:**
- Check Python version: `python --version` (need 3.9+)
- Install dependencies: `pip install -r requirements.txt`
- Check for port conflicts (port 5000)

**Import errors:**
- Ensure all dependencies installed: `pip install -r requirements.txt`
- Check virtual environment activated (if using one)

**Session/upload errors:**
- Folders created automatically on first run
- Check write permissions in project directory

**AWS mode not working:**
- Set environment variable: `export USE_AWS=true`
- Configure AWS credentials: `aws configure`
- Check S3 bucket exists and accessible
- Verify EC2 instance is running: `aws ec2 describe-instances`

**EC2 deployment issues:**
- Check CloudFormation stack status in AWS Console
- SSH to instance: `ssh -i cooking-assistant-key.pem ec2-user@<public-ip>`
- Check app logs: `sudo journalctl -u cooking-assistant -f`
- Restart service: `sudo systemctl restart cooking-assistant`

### Getting Help

1. Check documentation files (README, FEATURES)
2. Review error messages in terminal
3. Check browser console for frontend errors
4. For AWS issues, check CloudWatch logs or SSH to EC2 instance

## Future Enhancements

- [ ] Weekly nutrition reports with charts
- [ ] Photo-based meal logging (AI food recognition)
- [ ] Hydration tracking
- [ ] Weight/measurement trends
- [ ] Voice input support
- [ ] Mobile app (React Native)
- [ ] Social features (share recipes)
- [ ] Integration with fitness trackers
- [ ] Meal prep scheduling
- [ ] Grocery delivery integration

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License
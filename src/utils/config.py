import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Flask Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
UPLOAD_FOLDER = 'uploads'
SESSIONS_FOLDER = 'sessions'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# AWS Configuration
USE_AWS = os.environ.get('USE_AWS', 'false').lower() == 'true'
AWS_REGION = os.environ.get('AWS_REGION', 'ap-southeast-2')

# Mock Recipes Data
MOCK_RECIPES = [
    {
        "name": "Grilled Chicken Salad",
        "description": "Healthy Mediterranean-style grilled chicken salad with fresh vegetables",
        "tags": ["high-protein", "low-carb", "gluten-free"],
        "calories": 380
    },
    {
        "name": "Vegetarian Buddha Bowl",
        "description": "Colorful bowl with quinoa, chickpeas, sweet potato, and tahini dressing",
        "tags": ["vegan", "high-fiber", "gluten-free"],
        "calories": 520
    },
    {
        "name": "Salmon with Roasted Vegetables",
        "description": "Omega-3 rich salmon with broccoli, bell pepper, and zucchini",
        "tags": ["high-protein", "low-carb", "omega-3"],
        "calories": 420
    }
]

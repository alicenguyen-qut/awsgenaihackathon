import json
import os
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'txt', 'docx', 'pdf'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_user_file(user_id, sessions_folder):
    """Get user data file path"""
    return os.path.join(sessions_folder, f'{user_id}.json')

def load_user_data(user_id, sessions_folder):
    """Load user data from JSON file"""
    filepath = get_user_file(user_id, sessions_folder)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return {
        'chats': [],
        'current_chat': None,
        'username': '',
        'uploaded_files': [],
        'password_hash': None,
        'nutrition_logs': [],
        'streaks': {'current': 0, 'longest': 0, 'last_login': ''},
        'favorites': [],
        'meal_plan': {},
        'shopping_list': [],
        'nutrition_profile': {}
    }

def save_user_data(user_id, data, sessions_folder):
    """Save user data to JSON file"""
    filepath = get_user_file(user_id, sessions_folder)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def find_user_by_username(username, sessions_folder):
    """Find user data by username across all sessions"""
    for filename in os.listdir(sessions_folder):
        if filename.endswith('.json'):
            filepath = os.path.join(sessions_folder, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    if data.get('username', '').lower() == username.lower():
                        user_id = filename.replace('.json', '')
                        return user_id, data
            except:
                pass
    return None, None

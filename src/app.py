from flask import Flask, render_template, request, jsonify, session, send_from_directory
import json
import os
import uuid
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from docx import Document

# Import configuration and utilities
from utils.config import USE_AWS, MOCK_RECIPES, SECRET_KEY, UPLOAD_FOLDER, SESSIONS_FOLDER, MAX_CONTENT_LENGTH
from utils.helpers import allowed_file, get_user_file, load_user_data, save_user_data, find_user_by_username

# Import Bedrock RAG if AWS mode
if USE_AWS:
    from models.bedrock_rag import BedrockRAG
    bedrock_rag = BedrockRAG()
else:
    bedrock_rag = None

app = Flask(__name__, static_folder='frontend', template_folder='frontend/templates')
app.secret_key = SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.config['SESSIONS_FOLDER'] = SESSIONS_FOLDER

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['SESSIONS_FOLDER'], exist_ok=True)

def get_user_session():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return session['user_id']

@app.route('/')
def home():
    user_id = get_user_session()
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        # Check if user exists
        existing_user_id, existing_user_data = find_user_by_username(username, app.config["SESSIONS_FOLDER"])
        
        if existing_user_data:
            # Existing user - verify password
            if not check_password_hash(existing_user_data.get('password_hash', ''), password):
                return jsonify({'error': 'Invalid password'}), 401
            
            # Login successful - set session to existing user
            session['user_id'] = existing_user_id
            return jsonify({'success': True, 'username': username})
        else:
            # New user registration
            user_id = get_user_session()  # This creates a new session ID
            user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
            
            user_data['username'] = username
            user_data['password_hash'] = generate_password_hash(password)
            user_data['nutrition_logs'] = []
            user_data['streaks'] = {'current': 1, 'longest': 1, 'last_login': datetime.now().strftime('%Y-%m-%d')}
            user_data['favorites'] = []
            user_data['meal_plan'] = {}
            user_data['shopping_list'] = []
            save_user_data(user_id, user_data, app.config["SESSIONS_FOLDER"])
            
            return jsonify({'success': True, 'username': username})
            
    except Exception as e:
        print(f"Login error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile-photo', methods=['POST'])
def upload_profile_photo():
    try:
        if 'photo' not in request.files:
            return jsonify({'error': 'No photo provided'}), 400
        
        file = request.files['photo']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        user_id = get_user_session()
        user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
        
        # Ensure uploads directory exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        filename = secure_filename(f"{user_id}_profile.jpg")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        user_data['profile_photo'] = f'/uploads/{filename}'
        save_user_data(user_id, user_data, app.config["SESSIONS_FOLDER"])
        
        return jsonify({'success': True, 'photoUrl': user_data['profile_photo']})
    except Exception as e:
        print(f"Profile photo upload error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile-photo', methods=['DELETE'])
def delete_profile_photo():
    try:
        user_id = get_user_session()
        user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
        
        # Delete photo file if exists
        if 'profile_photo' in user_data and user_data['profile_photo']:
            filename = user_data['profile_photo'].replace('/uploads/', '')
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(filepath):
                os.remove(filepath)
        
        user_data['profile_photo'] = ''
        save_user_data(user_id, user_data, app.config["SESSIONS_FOLDER"])
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Profile photo delete error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile-photo', methods=['GET'])
def get_profile_photo():
    try:
        user_id = get_user_session()
        user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
        return jsonify({'photoUrl': user_data.get('profile_photo', '')})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(os.path.abspath(app.config['UPLOAD_FOLDER']), filename)

@app.route('/api/nutrition-profile', methods=['POST'])
def save_nutrition_profile():
    try:
        data = request.json
        user_id = get_user_session()
        user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
        
        user_data['nutrition_profile'] = {
            'dietary': data.get('dietary', []),
            'healthGoal': data.get('healthGoal', ''),
            'allergies': data.get('allergies', [])
        }
        save_user_data(user_id, user_data, app.config["SESSIONS_FOLDER"])
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/nutrition-profile', methods=['GET'])
def get_nutrition_profile():
    try:
        user_id = get_user_session()
        user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
        return jsonify({'profile': user_data.get('nutrition_profile', {})})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/change-password', methods=['POST'])
def change_password():
    try:
        data = request.json
        current_password = data.get('currentPassword', '')
        new_password = data.get('newPassword', '')
        
        if not current_password or not new_password:
            return jsonify({'error': 'All fields required'}), 400
        
        user_id = get_user_session()
        user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
        
        if not check_password_hash(user_data.get('password_hash', ''), current_password):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        user_data['password_hash'] = generate_password_hash(new_password)
        save_user_data(user_id, user_data, app.config["SESSIONS_FOLDER"])
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear-chats', methods=['POST'])
def clear_chats():
    try:
        user_id = get_user_session()
        user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
        user_data['chats'] = []
        user_data['current_chat'] = None
        save_user_data(user_id, user_data, app.config["SESSIONS_FOLDER"])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear-files', methods=['POST'])
def clear_files():
    try:
        user_id = get_user_session()
        user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
        
        for file_info in user_data.get('uploaded_files', []):
            if os.path.exists(file_info['filepath']):
                os.remove(file_info['filepath'])
        
        user_data['uploaded_files'] = []
        save_user_data(user_id, user_data, app.config["SESSIONS_FOLDER"])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/session', methods=['GET'])
def get_session():
    user_id = get_user_session()
    user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
    return jsonify({
        'user_id': user_id, 
        'username': user_data.get('username', ''),
        'chats': user_data['chats'], 
        'current_chat': user_data['current_chat']
    })

@app.route('/api/chat/new', methods=['POST'])
def new_chat():
    user_id = get_user_session()
    user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
    
    chat_id = str(uuid.uuid4())
    new_chat = {
        'id': chat_id,
        'title': 'New Chat',
        'created_at': datetime.now().isoformat(),
        'messages': []
    }
    
    user_data['chats'].append(new_chat)
    user_data['current_chat'] = chat_id
    save_user_data(user_id, user_data, app.config["SESSIONS_FOLDER"])
    
    return jsonify({'success': True, 'chat_id': chat_id})

@app.route('/api/chat/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    user_id = get_user_session()
    user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
    
    chat = next((c for c in user_data['chats'] if c['id'] == chat_id), None)
    if chat:
        user_data['current_chat'] = chat_id
        save_user_data(user_id, user_data, app.config["SESSIONS_FOLDER"])
        return jsonify(chat)
    return jsonify({'error': 'Chat not found'}), 404

@app.route('/api/chat/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    user_id = get_user_session()
    user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
    
    user_data['chats'] = [c for c in user_data['chats'] if c['id'] != chat_id]
    if user_data['current_chat'] == chat_id:
        user_data['current_chat'] = user_data['chats'][0]['id'] if user_data['chats'] else None
    save_user_data(user_id, user_data, app.config["SESSIONS_FOLDER"])
    
    return jsonify({'success': True})

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        user_id = get_user_session()
        user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{user_id}_{filename}")
        file.save(filepath)
        
        if filename.endswith('.pdf'):
            content = 'PDF file uploaded (text extraction not implemented)'
        elif filename.endswith('.docx'):
            try:
                doc = Document(filepath)
                content = '\n'.join([para.text for para in doc.paragraphs])
            except Exception as e:
                print(f"Error reading docx: {e}")
                content = f"Error reading document: {str(e)}"
        else:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        
        file_info = {
            'id': str(uuid.uuid4()),
            'filename': filename,
            'filepath': filepath,
            'content': content,
            'uploaded_at': datetime.now().isoformat()
        }
        
        if 'uploaded_files' not in user_data:
            user_data['uploaded_files'] = []
        user_data['uploaded_files'].append(file_info)
        save_user_data(user_id, user_data, app.config["SESSIONS_FOLDER"])
        
        MOCK_RECIPES.append({
            "name": filename,
            "description": content[:200],
            "tags": ["user-uploaded"],
            "calories": 0
        })
        
        return jsonify({
            'success': True,
            'message': f'Successfully uploaded {filename}',
            'filename': filename,
            'file_id': file_info['id']
        })
    
    return jsonify({'error': 'Invalid file type. Only .txt, .docx, and .pdf files allowed'}), 400

@app.route('/api/files', methods=['GET'])
def get_files():
    user_id = get_user_session()
    user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
    files = user_data.get('uploaded_files', [])
    return jsonify({'files': [{'id': f['id'], 'filename': f['filename'], 'uploaded_at': f['uploaded_at']} for f in files]})

@app.route('/api/files/<file_id>', methods=['GET'])
def get_file_content(file_id):
    user_id = get_user_session()
    user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
    files = user_data.get('uploaded_files', [])
    file_info = next((f for f in files if f['id'] == file_id), None)
    if file_info:
        # For PDF, return the file path for iframe viewing
        if file_info['filename'].endswith('.pdf'):
            return jsonify({'filename': file_info['filename'], 'content': '', 'filepath': file_info['filepath']})
        return jsonify({'filename': file_info['filename'], 'content': file_info['content']})
    return jsonify({'error': 'File not found'}), 404

@app.route('/api/files/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    user_id = get_user_session()
    user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
    files = user_data.get('uploaded_files', [])
    file_info = next((f for f in files if f['id'] == file_id), None)
    if file_info:
        if os.path.exists(file_info['filepath']):
            os.remove(file_info['filepath'])
        user_data['uploaded_files'] = [f for f in files if f['id'] != file_id]
        save_user_data(user_id, user_data, app.config["SESSIONS_FOLDER"])
        return jsonify({'success': True})
    return jsonify({'error': 'File not found'}), 404

@app.route('/chat', methods=['POST'])
def chat():
    user_id = get_user_session()
    user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
    
    data = request.json
    query = data.get('query', '')
    
    # Create new chat if none exists
    if not user_data['current_chat']:
        chat_id = str(uuid.uuid4())
        new_chat = {
            'id': chat_id,
            'title': query[:50] if len(query) > 50 else query,
            'created_at': datetime.now().isoformat(),
            'messages': []
        }
        user_data['chats'].append(new_chat)
        user_data['current_chat'] = chat_id
    
    # Find current chat
    current_chat = next((c for c in user_data['chats'] if c['id'] == user_data['current_chat']), None)
    
    # Generate response
    if USE_AWS and bedrock_rag:
        # AWS Mode: Use Bedrock RAG
        try:
            user_profile = user_data.get('nutrition_profile', {})
            response = bedrock_rag.chat_with_rag(query, MOCK_RECIPES, user_profile)
        except Exception as e:
            print(f"Bedrock error: {e}")
            response = "I apologize, but I'm having trouble connecting to the AI service. Please try again."
    else:
        # Local Mode: Hardcoded responses
        query_lower = query.lower()
        
        if 'plan my week' in query_lower or 'weekly meal plan' in query_lower:
            response = """Here's your weekly meal plan:

• Grilled Chicken Salad - Mediterranean-style with fresh vegetables (380 cal)
• Salmon with Roasted Vegetables - Omega-3 rich with broccoli (420 cal)
• Vegetarian Buddha Bowl - Quinoa, chickpeas, sweet potato (520 cal)
• Pasta Primavera - Whole wheat pasta with seasonal vegetables (450 cal)
• Chicken Stir Fry - Asian-style with brown rice (410 cal)
• Baked Cod with Asparagus - Light and healthy (350 cal)
• Veggie Tacos - Black beans, avocado, salsa (380 cal)

All meals are balanced and nutritious!"""
        
        elif 'vegan' in query_lower:
            response = """🌱 Vegetarian Buddha Bowl - A colorful bowl with quinoa, chickpeas, sweet potato, and tahini dressing. High in fiber and plant-based protein (520 cal).

Ingredients: quinoa, chickpeas, sweet potato, kale, tahini, lemon"""
        
        elif 'protein' in query_lower or 'muscle' in query_lower:
            response = """💪 Grilled Chicken Salad - Mediterranean-style with fresh vegetables. Perfect for muscle growth (380 cal, 42g protein).

🐟 Salmon with Roasted Vegetables - Rich in omega-3 and protein (420 cal, 38g protein)."""
        
        elif 'breakfast' in query_lower:
            response = """⏰ Quick Protein Oatmeal - Steel-cut oats with banana, almonds, and protein powder (350 cal, 20g protein)

🥚 Veggie Egg Scramble - Eggs with spinach, tomatoes, and feta (280 cal, 18g protein)"""
        
        else:
            response = """Here are some recipe suggestions:

• Grilled Chicken Salad - Mediterranean-style with fresh vegetables (380 cal)
• Vegetarian Buddha Bowl - Quinoa, chickpeas, sweet potato (520 cal)  
• Salmon with Roasted Vegetables - Omega-3 rich (420 cal)

All meals are balanced and nutritious!"""
    
    # Save messages to chat history
    if current_chat:
        current_chat['messages'].append({'role': 'user', 'content': query, 'timestamp': datetime.now().isoformat()})
        current_chat['messages'].append({'role': 'assistant', 'content': response, 'timestamp': datetime.now().isoformat()})
        
        # Update title if it's the first message
        if len(current_chat['messages']) == 2:
            current_chat['title'] = query[:50]
        
        save_user_data(user_id, user_data, app.config["SESSIONS_FOLDER"])
    
    return jsonify({'response': response})

@app.route('/api/favorites', methods=['POST'])
def toggle_favorite():
    try:
        data = request.json
        user_id = get_user_session()
        user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
        
        if 'favorites' not in user_data:
            user_data['favorites'] = []
        
        recipe = {
            'recipeId': data['recipeId'], 
            'recipeName': data['recipeName'],
            'content': data.get('content', '')
        }
        existing = next((f for f in user_data['favorites'] if f['recipeId'] == recipe['recipeId']), None)
        
        if existing:
            user_data['favorites'].remove(existing)
            added = False
        else:
            user_data['favorites'].append(recipe)
            added = True
        
        save_user_data(user_id, user_data, app.config["SESSIONS_FOLDER"])
        return jsonify({'success': True, 'added': added})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/favorites', methods=['GET'])
def get_favorites():
    try:
        user_id = get_user_session()
        user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
        return jsonify({'favorites': user_data.get('favorites', [])})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/meal-plan', methods=['GET'])
def get_meal_plan():
    try:
        user_id = get_user_session()
        user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
        return jsonify({'plan': user_data.get('meal_plan', {})})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/meal-plan', methods=['POST'])
def save_meal_plan():
    try:
        data = request.json
        user_id = get_user_session()
        user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
        user_data['meal_plan'] = data['plan']
        save_user_data(user_id, user_data, app.config["SESSIONS_FOLDER"])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/shopping-list', methods=['GET'])
def get_shopping_list():
    try:
        user_id = get_user_session()
        user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
        return jsonify({'items': user_data.get('shopping_list', [])})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/shopping-list', methods=['POST'])
def add_shopping_item():
    try:
        data = request.json
        user_id = get_user_session()
        user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
        
        if 'shopping_list' not in user_data:
            user_data['shopping_list'] = []
        
        user_data['shopping_list'].append({'name': data['name'], 'checked': False})
        save_user_data(user_id, user_data, app.config["SESSIONS_FOLDER"])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/shopping-list/<int:index>/toggle', methods=['POST'])
def toggle_shopping_item(index):
    try:
        user_id = get_user_session()
        user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
        if 'shopping_list' in user_data and index < len(user_data['shopping_list']):
            user_data['shopping_list'][index]['checked'] = not user_data['shopping_list'][index]['checked']
            save_user_data(user_id, user_data, app.config["SESSIONS_FOLDER"])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/shopping-list/<int:index>', methods=['DELETE'])
def delete_shopping_item(index):
    try:
        user_id = get_user_session()
        user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
        if 'shopping_list' in user_data and index < len(user_data['shopping_list']):
            user_data['shopping_list'].pop(index)
            save_user_data(user_id, user_data, app.config["SESSIONS_FOLDER"])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/shopping-list/clear', methods=['POST'])
def clear_shopping_list():
    try:
        user_id = get_user_session()
        user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
        user_data['shopping_list'] = []
        save_user_data(user_id, user_data, app.config["SESSIONS_FOLDER"])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Daily Nutrition Tracking
@app.route('/api/nutrition/log', methods=['POST'])
def log_meal():
    try:
        data = request.json
        user_id = get_user_session()
        user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
        
        if 'nutrition_logs' not in user_data:
            user_data['nutrition_logs'] = []
        
        log = {
            'id': str(uuid.uuid4()),
            'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
            'meal_type': data['meal_type'],
            'name': data['name'],
            'calories': data['calories'],
            'protein': data.get('protein', 0),
            'carbs': data.get('carbs', 0),
            'fats': data.get('fats', 0),
            'timestamp': datetime.now().isoformat()
        }
        user_data['nutrition_logs'].append(log)
        save_user_data(user_id, user_data, app.config["SESSIONS_FOLDER"])
        return jsonify({'success': True, 'log': log})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/nutrition/logs', methods=['GET'])
def get_nutrition_logs():
    try:
        user_id = get_user_session()
        user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        logs = [l for l in user_data.get('nutrition_logs', []) if l['date'] == date]
        return jsonify({'logs': logs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/nutrition/stats', methods=['GET'])
def get_nutrition_stats():
    try:
        user_id = get_user_session()
        user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        logs = [l for l in user_data.get('nutrition_logs', []) if l['date'] == date]
        
        total = {'calories': sum(l['calories'] for l in logs), 'protein': sum(l['protein'] for l in logs),
                 'carbs': sum(l['carbs'] for l in logs), 'fats': sum(l['fats'] for l in logs)}
        return jsonify({'stats': total, 'meal_count': len(logs)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/nutrition/logs/<log_id>', methods=['DELETE'])
def delete_nutrition_log(log_id):
    try:
        user_id = get_user_session()
        user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
        user_data['nutrition_logs'] = [l for l in user_data.get('nutrition_logs', []) if l['id'] != log_id]
        save_user_data(user_id, user_data, app.config["SESSIONS_FOLDER"])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Habit Streaks
@app.route('/api/streaks', methods=['GET'])
def get_streaks():
    try:
        user_id = get_user_session()
        user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
        
        if 'streaks' not in user_data:
            user_data['streaks'] = {'current': 0, 'longest': 0, 'last_login': None}
        
        today = datetime.now().strftime('%Y-%m-%d')
        last = user_data['streaks'].get('last_login')
        
        if last != today:
            if last == (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'):
                user_data['streaks']['current'] += 1
            else:
                user_data['streaks']['current'] = 1
            user_data['streaks']['longest'] = max(user_data['streaks']['current'], user_data['streaks'].get('longest', 0))
            user_data['streaks']['last_login'] = today
            save_user_data(user_id, user_data, app.config["SESSIONS_FOLDER"])
        
        return jsonify({'streaks': user_data['streaks']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/nutrition/analytics', methods=['GET'])
def get_nutrition_analytics():
    try:
        user_id = get_user_session()
        user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
        period = request.args.get('period', 'today')
        
        logs = user_data.get('nutrition_logs', [])
        
        if period == 'today':
            today = datetime.now().strftime('%Y-%m-%d')
            period_logs = [l for l in logs if l['date'] == today]
        elif period == 'week':
            week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            period_logs = [l for l in logs if l['date'] >= week_ago]
        elif period == 'month':
            month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            period_logs = [l for l in logs if l['date'] >= month_ago]
        else:  # year
            year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            period_logs = [l for l in logs if l['date'] >= year_ago]
        
        if not period_logs:
            return jsonify({'analytics': {'avgCalories': 0, 'avgProtein': 0, 'totalDays': 0, 'bestDay': 0}, 'insights': []})
        
        total_cal = sum(l['calories'] for l in period_logs)
        total_protein = sum(l['protein'] for l in period_logs)
        unique_days = len(set(l['date'] for l in period_logs))
        best_day = max((sum(l['calories'] for l in logs if l['date'] == date) for date in set(l['date'] for l in period_logs)), default=0)
        
        analytics = {
            'avgCalories': total_cal / unique_days if unique_days > 0 else 0,
            'avgProtein': total_protein / unique_days if unique_days > 0 else 0,
            'totalDays': unique_days,
            'bestDay': best_day
        }
        
        insights = [
            f"You've logged meals for {unique_days} days",
            f"Average daily intake: {int(analytics['avgCalories'])} calories",
            f"Most common meal type: {max(set(l['meal_type'] for l in period_logs), key=lambda x: sum(1 for l in period_logs if l['meal_type'] == x)) if period_logs else 'None'}"
        ]
        
        return jsonify({'analytics': analytics, 'insights': insights})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Smart Daily Recommendations
@app.route('/api/recommendations/daily', methods=['GET'])
def get_daily_recommendations():
    try:
        user_id = get_user_session()
        user_data = load_user_data(user_id, app.config["SESSIONS_FOLDER"])
        
        today = datetime.now().strftime('%Y-%m-%d')
        logs = [l for l in user_data.get('nutrition_logs', []) if l['date'] == today]
        total_cal = sum(l['calories'] for l in logs)
        total_protein = sum(l['protein'] for l in logs)
        total_carbs = sum(l['carbs'] for l in logs)
        total_fats = sum(l['fats'] for l in logs)
        
        profile = user_data.get('nutrition_profile', {})
        goal = profile.get('healthGoal', '')
        dietary = profile.get('dietary', [])
        
        recommendations = []
        tips = []
        
        # Calorie-based recommendations
        if total_cal < 800:
            if 'vegan' in dietary or 'vegetarian' in dietary:
                recommendations.append({'type': 'meal', 'title': 'Vegetarian Buddha Bowl', 'reason': 'Plant-based protein & fiber', 'calories': 520, 'protein': 18})
                recommendations.append({'type': 'meal', 'title': 'Quinoa Veggie Stir-Fry', 'reason': 'Complete protein source', 'calories': 450, 'protein': 16})
            else:
                recommendations.append({'type': 'meal', 'title': 'Grilled Chicken Salad', 'reason': 'High protein, low carb', 'calories': 380, 'protein': 42})
                recommendations.append({'type': 'meal', 'title': 'Salmon with Vegetables', 'reason': 'Omega-3 rich', 'calories': 420, 'protein': 38})
        elif total_cal < 1200:
            recommendations.append({'type': 'meal', 'title': 'Greek Yogurt Parfait', 'reason': 'Protein-rich snack', 'calories': 280, 'protein': 20})
        elif total_cal > 2000:
            tips.append('You\'ve reached your calorie goal! Consider light snacks or herbal tea.')
        
        # Protein recommendations
        if total_protein < 30:
            tips.append('💪 Boost protein: Add eggs, Greek yogurt, or lean meat to your next meal')
            if 'vegan' in dietary:
                recommendations.append({'type': 'meal', 'title': 'Tofu Scramble', 'reason': 'Plant-based protein', 'calories': 320, 'protein': 24})
        elif total_protein < 60:
            tips.append('Good protein intake! Aim for 20-30g more for optimal muscle maintenance')
        
        # Carb recommendations
        if total_carbs < 50 and goal == 'energy-boost':
            tips.append('🍞 Low on carbs: Add whole grains or fruits for sustained energy')
        
        # Fat recommendations
        if total_fats < 20:
            tips.append('🥑 Healthy fats: Include avocado, nuts, or olive oil for nutrient absorption')
        
        # Goal-specific recommendations
        if goal == 'weight-loss' and total_cal < 1500:
            recommendations.append({'type': 'meal', 'title': 'Zucchini Noodles with Chicken', 'reason': 'Low-calorie, high-volume', 'calories': 340, 'protein': 35})
        elif goal == 'muscle-gain' and total_protein < 100:
            recommendations.append({'type': 'meal', 'title': 'Protein Power Bowl', 'reason': 'High protein for muscle growth', 'calories': 580, 'protein': 48})
        elif goal == 'heart-health':
            recommendations.append({'type': 'meal', 'title': 'Mediterranean Salmon', 'reason': 'Heart-healthy omega-3s', 'calories': 420, 'protein': 38})
        
        # Hydration reminder
        if len(logs) > 0:
            tips.append('💧 Stay hydrated: Drink 8 glasses of water throughout the day')
        
        # Combine tips into recommendations
        for tip in tips:
            recommendations.append({'type': 'tip', 'message': tip})
        
        return jsonify({'recommendations': recommendations})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    mode = "AWS MODE" if USE_AWS else "LOCAL MODE"
    print("\n" + "="*60)
    print(f"🍳 AI Cooking Assistant - {mode}")
    print("="*60)
    if not USE_AWS:
        print("Running without AWS - using mock data")
    print("Visit: http://localhost:5000")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)

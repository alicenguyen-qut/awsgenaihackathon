from flask import Flask, render_template, request, jsonify, session, send_from_directory, Response, stream_with_context
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from docx import Document
import json
import os
import uuid
from datetime import datetime

# Import configuration and utilities
from utils.config import USE_AWS, MOCK_RECIPES, SECRET_KEY, UPLOAD_FOLDER, SESSIONS_FOLDER, MAX_CONTENT_LENGTH
from utils.helpers import allowed_file, get_user_file, now_aest
from utils.responses import get_mock_chat_response
from utils.recommendations import generate_daily_recommendations
from utils.analytics import calculate_nutrition_stats, calculate_period_analytics, update_streak
import utils.storage as storage
import boto3

# Check if using S3 for storage
S3_BUCKET = os.getenv('S3_BUCKET')
USE_S3 = USE_AWS and S3_BUCKET

if USE_S3:
    s3_client = boto3.client('s3', region_name=os.getenv('AWS_REGION', 'ap-southeast-2'))
    storage.init_storage(SESSIONS_FOLDER, s3_client, S3_BUCKET)
    print(f"✅ Using S3 bucket for storage: {S3_BUCKET}")
else:
    storage.init_storage(SESSIONS_FOLDER)
    print("✅ Using local file storage")

# Import Bedrock RAG if AWS mode
RECIPES_BUCKET = os.getenv('RECIPES_BUCKET')
if USE_AWS:
    from models.bedrock_rag import BedrockRAG
    bedrock_rag = BedrockRAG(recipes_bucket=RECIPES_BUCKET)
    # Load recipes from S3 if available
    S3_RECIPES = bedrock_rag.load_recipes_from_s3() if RECIPES_BUCKET else []
    print(f"Loaded {len(S3_RECIPES)} recipes from S3")
else:
    bedrock_rag = None
    S3_RECIPES = []

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
        existing_user_id, existing_user_data = storage.find_user_by_username(username)
        
        if existing_user_data:
            # Existing user - verify password
            if not check_password_hash(existing_user_data.get('password_hash', ''), password):
                return jsonify({'error': 'Invalid password'}), 401
            
            # Login successful - set session to existing user
            session['user_id'] = existing_user_id
            has_profile = bool(existing_user_data.get('nutrition_profile', {}).get('healthGoal') or existing_user_data.get('nutrition_profile', {}).get('dietary'))
            return jsonify({'success': True, 'username': username, 'is_new_user': not has_profile})
        else:
            # New user registration
            user_id = get_user_session()  # This creates a new session ID
            user_data = storage.load_user_data(user_id)
            
            user_data['username'] = username
            user_data['password_hash'] = generate_password_hash(password)
            user_data['nutrition_logs'] = []
            user_data['streaks'] = {'current': 1, 'longest': 1, 'last_login': now_aest().strftime('%Y-%m-%d')}
            user_data['favorites'] = []
            user_data['meal_plan'] = {}
            user_data['shopping_list'] = []
            storage.save_user_data(user_id, user_data)
            
            return jsonify({'success': True, 'username': username, 'is_new_user': True})
            
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
        user_data = storage.load_user_data(user_id)
        
        # Ensure uploads directory exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        filename = secure_filename(f"{user_id}_profile.jpg")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        user_data['profile_photo'] = f'/uploads/{filename}'
        storage.save_user_data(user_id, user_data)
        
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
        user_data = storage.load_user_data(user_id)
        
        # Delete photo file if exists
        if 'profile_photo' in user_data and user_data['profile_photo']:
            filename = user_data['profile_photo'].replace('/uploads/', '')
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(filepath):
                os.remove(filepath)
        
        user_data['profile_photo'] = ''
        storage.save_user_data(user_id, user_data)
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Profile photo delete error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile-photo', methods=['GET'])
def get_profile_photo():
    try:
        user_id = get_user_session()
        user_data = storage.load_user_data(user_id)
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
        user_data = storage.load_user_data(user_id)
        
        user_data['nutrition_profile'] = {
            'dietary': data.get('dietary', []),
            'healthGoal': data.get('healthGoal', ''),
            'allergies': data.get('allergies', []),
            'age': data.get('age'),
            'weight': data.get('weight'),
            'height': data.get('height'),
            'gender': data.get('gender'),
        }
        storage.save_user_data(user_id, user_data)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/nutrition-profile', methods=['GET'])
def get_nutrition_profile():
    try:
        user_id = get_user_session()
        user_data = storage.load_user_data(user_id)
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
        user_data = storage.load_user_data(user_id)
        
        if not check_password_hash(user_data.get('password_hash', ''), current_password):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        user_data['password_hash'] = generate_password_hash(new_password)
        storage.save_user_data(user_id, user_data)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear-chats', methods=['POST'])
def clear_chats():
    try:
        user_id = get_user_session()
        user_data = storage.load_user_data(user_id)
        user_data['chats'] = []
        user_data['current_chat'] = None
        storage.save_user_data(user_id, user_data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear-files', methods=['POST'])
def clear_files():
    try:
        user_id = get_user_session()
        user_data = storage.load_user_data(user_id)
        
        for file_info in user_data.get('uploaded_files', []):
            if os.path.exists(file_info['filepath']):
                os.remove(file_info['filepath'])
        
        user_data['uploaded_files'] = []
        storage.save_user_data(user_id, user_data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/session', methods=['GET'])
def get_session():
    user_id = get_user_session()
    user_data = storage.load_user_data(user_id)
    return jsonify({
        'user_id': user_id, 
        'username': user_data.get('username', ''),
        'chats': user_data['chats'], 
        'current_chat': user_data['current_chat']
    })

@app.route('/api/chat/new', methods=['POST'])
def new_chat():
    user_id = get_user_session()
    user_data = storage.load_user_data(user_id)
    
    chat_id = str(uuid.uuid4())
    new_chat = {
        'id': chat_id,
        'title': 'New Chat',
        'created_at': now_aest().isoformat(),
        'messages': []
    }
    
    user_data['chats'].append(new_chat)
    user_data['current_chat'] = chat_id
    storage.save_user_data(user_id, user_data)
    
    return jsonify({'success': True, 'chat_id': chat_id})

@app.route('/api/chat/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    user_id = get_user_session()
    user_data = storage.load_user_data(user_id)
    
    chat = next((c for c in user_data['chats'] if c['id'] == chat_id), None)
    if chat:
        user_data['current_chat'] = chat_id
        storage.save_user_data(user_id, user_data)
        return jsonify(chat)
    return jsonify({'error': 'Chat not found'}), 404

@app.route('/api/chat/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    user_id = get_user_session()
    user_data = storage.load_user_data(user_id)
    
    user_data['chats'] = [c for c in user_data['chats'] if c['id'] != chat_id]
    if user_data['current_chat'] == chat_id:
        user_data['current_chat'] = user_data['chats'][0]['id'] if user_data['chats'] else None
    storage.save_user_data(user_id, user_data)
    
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
        user_data = storage.load_user_data(user_id)
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{user_id}_{filename}")
        file.save(filepath)
        
        if filename.endswith('.pdf'):
            try:
                import pypdf
                reader = pypdf.PdfReader(filepath)
                content = '\n'.join(page.extract_text() or '' for page in reader.pages)
            except Exception as e:
                print(f"PDF extraction error: {e}")
                content = ''
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
            'uploaded_at': now_aest().isoformat()
        }
        
        if 'uploaded_files' not in user_data:
            user_data['uploaded_files'] = []
        user_data['uploaded_files'].append(file_info)
        storage.save_user_data(user_id, user_data)

        # Embed and store to S3 for RAG
        if USE_AWS and bedrock_rag and S3_BUCKET and content:
            bedrock_rag.embed_and_store_file(content, user_id, file_info['id'], S3_BUCKET)

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
    user_data = storage.load_user_data(user_id)
    files = user_data.get('uploaded_files', [])
    return jsonify({'files': [{'id': f['id'], 'filename': f['filename'], 'uploaded_at': f['uploaded_at']} for f in files]})

@app.route('/api/files/<file_id>', methods=['GET'])
def get_file_content(file_id):
    user_id = get_user_session()
    user_data = storage.load_user_data(user_id)
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
    user_data = storage.load_user_data(user_id)
    files = user_data.get('uploaded_files', [])
    file_info = next((f for f in files if f['id'] == file_id), None)
    if file_info:
        if os.path.exists(file_info['filepath']):
            os.remove(file_info['filepath'])
        user_data['uploaded_files'] = [f for f in files if f['id'] != file_id]
        storage.save_user_data(user_id, user_data)
        # Remove embeddings for this file from S3
        if USE_AWS and bedrock_rag and S3_BUCKET:
            bedrock_rag.embed_and_store_file('', user_id, file_id, S3_BUCKET)  # empty text = just removes old chunks
        return jsonify({'success': True})
    return jsonify({'error': 'File not found'}), 404

@app.route('/chat', methods=['POST'])
def chat():
    user_id = get_user_session()
    user_data = storage.load_user_data(user_id)
    
    data = request.json
    query = data.get('query', '')
    
    # Create new chat if none exists
    if not user_data['current_chat']:
        chat_id = str(uuid.uuid4())
        new_chat = {
            'id': chat_id,
            'title': query[:50] if len(query) > 50 else query,
            'created_at': now_aest().isoformat(),
            'messages': []
        }
        user_data['chats'].append(new_chat)
        user_data['current_chat'] = chat_id
    
    # Find current chat
    current_chat = next((c for c in user_data['chats'] if c['id'] == user_data['current_chat']), None)
    
    # Generate response
    if USE_AWS and bedrock_rag:
        # AWS Mode: Use Bedrock RAG with agentic capabilities
        try:
            user_profile = user_data.get('nutrition_profile', {})
            
            # Use S3 recipes if available, otherwise fallback to MOCK_RECIPES
            recipes = S3_RECIPES if S3_RECIPES else MOCK_RECIPES
            
            # Define tool handler for agent
            def tool_handler(tool_name: str, tool_input: dict) -> dict:
                """Handle tool calls from the agent"""
                try:
                    if tool_name == "search_recipes":
                        query = tool_input.get('query', '')
                        top_k = tool_input.get('top_k', 3)
                        results = bedrock_rag.search_recipes(query, recipes, top_k)
                        return {"success": True, "recipes": [r.get('name', '') for r in results]}
                    
                    elif tool_name == "add_to_favorites":
                        recipe_name = tool_input.get('recipe_name', '')
                        recipe_content = tool_input.get('recipe_content', '')
                        recipe_id = str(uuid.uuid4())
                        
                        if 'favorites' not in user_data:
                            user_data['favorites'] = []
                        
                        user_data['favorites'].append({
                            'recipeId': recipe_id,
                            'recipeName': recipe_name,
                            'content': recipe_content
                        })
                        storage.save_user_data(user_id, user_data)
                        return {"success": True, "message": f"Added '{recipe_name}' to favorites"}
                    
                    elif tool_name == "add_to_meal_plan":
                        day = tool_input.get('day', '')
                        meal_name = tool_input.get('meal_name', '')
                        
                        if 'meal_plan' not in user_data:
                            user_data['meal_plan'] = {}
                        
                        user_data['meal_plan'][day] = meal_name
                        storage.save_user_data(user_id, user_data)
                        return {"success": True, "message": f"Added '{meal_name}' to {day}"}
                    
                    elif tool_name == "add_to_shopping_list":
                        items = tool_input.get('items', [])
                        
                        if 'shopping_list' not in user_data:
                            user_data['shopping_list'] = []
                        
                        for item in items:
                            user_data['shopping_list'].append({'name': item, 'checked': False})
                        
                        storage.save_user_data(user_id, user_data)
                        return {"success": True, "message": f"Added {len(items)} items to shopping list"}
                    
                    elif tool_name == "log_nutrition":
                        if 'nutrition_logs' not in user_data:
                            user_data['nutrition_logs'] = []
                        log = {
                            'id': str(uuid.uuid4()),
                            'date': now_aest().strftime('%Y-%m-%d'),
                            'meal_type': tool_input.get('meal_type', 'snack'),
                            'name': tool_input.get('name', ''),
                            'calories': tool_input.get('calories', 0),
                            'protein': tool_input.get('protein', 0),
                            'carbs': tool_input.get('carbs', 0),
                            'fats': tool_input.get('fats', 0),
                            'timestamp': now_aest().isoformat()
                        }
                        user_data['nutrition_logs'].append(log)
                        storage.save_user_data(user_id, user_data)
                        return {"success": True, "message": f"Logged {log['name']} ({log['calories']} cal)"}

                    elif tool_name == "get_nutrition_stats":
                        today = now_aest().strftime('%Y-%m-%d')
                        profile = user_data.get('nutrition_profile', {})
                        stats = calculate_nutrition_stats(
                            user_data.get('nutrition_logs', []), today, profile.get('healthGoal', ''),
                            age=profile.get('age'), weight_kg=profile.get('weight'),
                            height_cm=profile.get('height'), gender=profile.get('gender')
                        )
                        return {"success": True, "stats": stats, "meal_plan": user_data.get('meal_plan', {})}

                    else:
                        return {"success": False, "error": f"Unknown tool: {tool_name}"}
                        
                except Exception as e:
                    print(f"Tool handler error: {e}")
                    import traceback
                    traceback.print_exc()
                    return {"success": False, "error": str(e)}
            
            result = bedrock_rag.chat_with_rag(query, recipes, user_profile, tool_handler, current_chat.get('messages', []), user_id=user_id, uploads_bucket=S3_BUCKET, meal_plan=user_data.get('meal_plan', {}))
            response = result.get('response', '')
            tool_calls = result.get('tool_calls', [])
            
        except Exception as e:
            print(f"Bedrock error: {e}")
            import traceback
            traceback.print_exc()
            response = "I apologize, but I'm having trouble connecting to the AI service. Please try again."
            tool_calls = []
    else:
        # Local Mode: Mock responses
        response = get_mock_chat_response(query)
        tool_calls = []
    
    # Save messages to chat history
    if current_chat:
        current_chat['messages'].append({'role': 'user', 'content': query, 'timestamp': now_aest().isoformat()})
        current_chat['messages'].append({
            'role': 'assistant', 
            'content': response, 
            'timestamp': now_aest().isoformat(),
            'tool_calls': tool_calls
        })
        
        # Update title if it's the first message
        if len(current_chat['messages']) == 2:
            current_chat['title'] = query[:50]
        
        storage.save_user_data(user_id, user_data)
    
    return jsonify({'response': response, 'tool_calls': tool_calls})

@app.route('/api/favorites', methods=['POST'])
def toggle_favorite():
    try:
        data = request.json
        user_id = get_user_session()
        user_data = storage.load_user_data(user_id)
        
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
        
        storage.save_user_data(user_id, user_data)
        return jsonify({'success': True, 'added': added})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/favorites', methods=['GET'])
def get_favorites():
    try:
        user_id = get_user_session()
        user_data = storage.load_user_data(user_id)
        return jsonify({'favorites': user_data.get('favorites', [])})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/meal-plan', methods=['GET'])
def get_meal_plan():
    try:
        user_id = get_user_session()
        user_data = storage.load_user_data(user_id)
        return jsonify({'plan': user_data.get('meal_plan', {})})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/meal-plan', methods=['POST'])
def save_meal_plan():
    try:
        data = request.json
        user_id = get_user_session()
        user_data = storage.load_user_data(user_id)
        user_data['meal_plan'] = data['plan']
        storage.save_user_data(user_id, user_data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/shopping-list', methods=['GET'])
def get_shopping_list():
    try:
        user_id = get_user_session()
        user_data = storage.load_user_data(user_id)
        return jsonify({'items': user_data.get('shopping_list', [])})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/shopping-list', methods=['POST'])
def add_shopping_item():
    try:
        data = request.json
        user_id = get_user_session()
        user_data = storage.load_user_data(user_id)
        
        if 'shopping_list' not in user_data:
            user_data['shopping_list'] = []
        
        user_data['shopping_list'].append({'name': data['name'], 'checked': False})
        storage.save_user_data(user_id, user_data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/shopping-list/<int:index>/toggle', methods=['POST'])
def toggle_shopping_item(index):
    try:
        user_id = get_user_session()
        user_data = storage.load_user_data(user_id)
        if 'shopping_list' in user_data and index < len(user_data['shopping_list']):
            user_data['shopping_list'][index]['checked'] = not user_data['shopping_list'][index]['checked']
            storage.save_user_data(user_id, user_data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/shopping-list/<int:index>', methods=['DELETE'])
def delete_shopping_item(index):
    try:
        user_id = get_user_session()
        user_data = storage.load_user_data(user_id)
        if 'shopping_list' in user_data and index < len(user_data['shopping_list']):
            user_data['shopping_list'].pop(index)
            storage.save_user_data(user_id, user_data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/shopping-list/clear', methods=['POST'])
def clear_shopping_list():
    try:
        user_id = get_user_session()
        user_data = storage.load_user_data(user_id)
        user_data['shopping_list'] = []
        storage.save_user_data(user_id, user_data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Daily Nutrition Tracking
@app.route('/api/nutrition/log', methods=['POST'])
def log_meal():
    try:
        data = request.json
        user_id = get_user_session()
        user_data = storage.load_user_data(user_id)
        
        if 'nutrition_logs' not in user_data:
            user_data['nutrition_logs'] = []
        
        log = {
            'id': str(uuid.uuid4()),
            'date': data.get('date', now_aest().strftime('%Y-%m-%d')),
            'meal_type': data['meal_type'],
            'name': data['name'],
            'calories': data['calories'],
            'protein': data.get('protein', 0),
            'carbs': data.get('carbs', 0),
            'fats': data.get('fats', 0),
            'timestamp': now_aest().isoformat()
        }
        user_data['nutrition_logs'].append(log)
        storage.save_user_data(user_id, user_data)
        return jsonify({'success': True, 'log': log})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/nutrition/logs', methods=['GET'])
def get_nutrition_logs():
    try:
        user_id = get_user_session()
        user_data = storage.load_user_data(user_id)
        date = request.args.get('date', now_aest().strftime('%Y-%m-%d'))
        logs = [l for l in user_data.get('nutrition_logs', []) if l['date'] == date]
        return jsonify({'logs': logs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/nutrition/stats', methods=['GET'])
def get_nutrition_stats():
    try:
        user_id = get_user_session()
        user_data = storage.load_user_data(user_id)
        date = request.args.get('date', now_aest().strftime('%Y-%m-%d'))
        health_goal = user_data.get('nutrition_profile', {}).get('healthGoal', '')
        profile = user_data.get('nutrition_profile', {})
        result = calculate_nutrition_stats(
            user_data.get('nutrition_logs', []), date, health_goal,
            age=profile.get('age'), weight_kg=profile.get('weight'),
            height_cm=profile.get('height'), gender=profile.get('gender')
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/nutrition/logs/<log_id>', methods=['DELETE'])
def delete_nutrition_log(log_id):
    try:
        user_id = get_user_session()
        user_data = storage.load_user_data(user_id)
        user_data['nutrition_logs'] = [l for l in user_data.get('nutrition_logs', []) if l['id'] != log_id]
        storage.save_user_data(user_id, user_data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Habit Streaks
@app.route('/api/streaks', methods=['GET'])
def get_streaks():
    try:
        user_id = get_user_session()
        user_data = storage.load_user_data(user_id)
        
        if 'streaks' not in user_data:
            user_data['streaks'] = {'current': 0, 'longest': 0, 'last_login': None}
        
        if update_streak(user_data['streaks']):
            storage.save_user_data(user_id, user_data)
        
        return jsonify({'streaks': user_data['streaks']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/nutrition/analytics', methods=['GET'])
def get_nutrition_analytics():
    try:
        user_id = get_user_session()
        user_data = storage.load_user_data(user_id)
        period = request.args.get('period', 'today')
        result = calculate_period_analytics(user_data.get('nutrition_logs', []), period)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Smart Daily Recommendations
@app.route('/api/recommendations/daily', methods=['GET'])
def get_daily_recommendations():
    try:
        user_id = get_user_session()
        user_data = storage.load_user_data(user_id)
        
        today = now_aest().strftime('%Y-%m-%d')
        logs = [l for l in user_data.get('nutrition_logs', []) if l['date'] == today]
        profile = user_data.get('nutrition_profile', {})
        
        recommendations = generate_daily_recommendations(logs, profile)
        return jsonify({'recommendations': recommendations})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat/stream', methods=['POST'])
def chat_stream():
    user_id = get_user_session()
    user_data = storage.load_user_data(user_id)

    data = request.json
    query = data.get('query', '')

    if not user_data['current_chat']:
        chat_id = str(uuid.uuid4())
        new_chat_obj = {
            'id': chat_id,
            'title': query[:50] if len(query) > 50 else query,
            'created_at': now_aest().isoformat(),
            'messages': []
        }
        user_data['chats'].append(new_chat_obj)
        user_data['current_chat'] = chat_id

    current_chat = next((c for c in user_data['chats'] if c['id'] == user_data['current_chat']), None)

    def generate():
        import json as _json

        def sse(event, data):
            return f"event: {event}\ndata: {_json.dumps(data)}\n\n"

        tool_calls = []

        if not (USE_AWS and bedrock_rag):
            response = get_mock_chat_response(query)
            for word in response.split(' '):
                yield sse('token', {'text': word + ' '})
            yield sse('done', {'tool_calls': []})
            return

        try:
            user_profile = user_data.get('nutrition_profile', {})
            recipes = S3_RECIPES if S3_RECIPES else MOCK_RECIPES

            q_lower = query.lower()
            is_planning = any(w in q_lower for w in ['plan', 'week', 'meal plan', 'shopping'])
            is_nutrition = any(w in q_lower for w in ['calorie', 'macro', 'remaining', 'log', 'track', 'snack', 'how much', 'how many'])

            if is_planning:
                yield sse('status', {'message': '🔍 Searching recipes for your preferences...'})
            elif is_nutrition:
                yield sse('status', {'message': '📊 Calculating your nutrition stats...'})
            else:
                yield sse('status', {'message': '✨ Thinking...'})

            def tool_handler(tool_name, tool_input):
                token_queue.put(('__tool__', tool_name, tool_input))
                try:
                    if tool_name == 'search_recipes':
                        results = bedrock_rag.search_recipes(tool_input.get('query', ''), recipes, tool_input.get('top_k', 3))
                        return {'success': True, 'recipes': [r.get('name', '') for r in results]}
                    elif tool_name == 'add_to_favorites':
                        recipe_name = tool_input.get('recipe_name', '')
                        if 'favorites' not in user_data:
                            user_data['favorites'] = []
                        user_data['favorites'].append({'recipeId': str(uuid.uuid4()), 'recipeName': recipe_name, 'content': tool_input.get('recipe_content', '')})
                        storage.save_user_data(user_id, user_data)
                        return {'success': True, 'message': f"Added '{recipe_name}' to favorites"}
                    elif tool_name == 'add_to_meal_plan':
                        day, meal_name = tool_input.get('day', ''), tool_input.get('meal_name', '')
                        if 'meal_plan' not in user_data:
                            user_data['meal_plan'] = {}
                        user_data['meal_plan'][day] = meal_name
                        storage.save_user_data(user_id, user_data)
                        return {'success': True, 'message': f"Added '{meal_name}' to {day}"}
                    elif tool_name == 'add_to_shopping_list':
                        items = tool_input.get('items', [])
                        if 'shopping_list' not in user_data:
                            user_data['shopping_list'] = []
                        for item in items:
                            user_data['shopping_list'].append({'name': item, 'checked': False})
                        storage.save_user_data(user_id, user_data)
                        return {'success': True, 'message': f"Added {len(items)} items to shopping list"}
                    elif tool_name == 'log_nutrition':
                        if 'nutrition_logs' not in user_data:
                            user_data['nutrition_logs'] = []
                        log = {
                            'id': str(uuid.uuid4()),
                            'date': now_aest().strftime('%Y-%m-%d'),
                            'meal_type': tool_input.get('meal_type', 'snack'),
                            'name': tool_input.get('name', ''),
                            'calories': tool_input.get('calories', 0),
                            'protein': tool_input.get('protein', 0),
                            'carbs': tool_input.get('carbs', 0),
                            'fats': tool_input.get('fats', 0),
                            'timestamp': now_aest().isoformat()
                        }
                        user_data['nutrition_logs'].append(log)
                        storage.save_user_data(user_id, user_data)
                        return {'success': True, 'message': f"Logged {log['name']} ({log['calories']} cal)"}
                    elif tool_name == 'get_nutrition_stats':
                        today = now_aest().strftime('%Y-%m-%d')
                        profile = user_data.get('nutrition_profile', {})
                        stats = calculate_nutrition_stats(
                            user_data.get('nutrition_logs', []), today, profile.get('healthGoal', ''),
                            age=profile.get('age'), weight_kg=profile.get('weight'),
                            height_cm=profile.get('height'), gender=profile.get('gender')
                        )
                        return {'success': True, 'stats': stats, 'meal_plan': user_data.get('meal_plan', {})}
                    return {'success': False, 'error': f'Unknown tool: {tool_name}'}
                except Exception as e:
                    return {'success': False, 'error': str(e)}

            if is_planning:
                yield sse('status', {'message': '📅 Building your weekly meal plan...'})

            import queue, threading
            token_queue = queue.Queue()
            SENTINEL = object()

            def on_token(chunk):
                token_queue.put(chunk)

            def run_agent():
                try:
                    r = bedrock_rag.chat_with_rag_stream(
                        query, recipes, user_profile, tool_handler,
                        current_chat.get('messages', []) if current_chat else [],
                        user_id=user_id, uploads_bucket=S3_BUCKET,
                        meal_plan=user_data.get('meal_plan', {}),
                        token_callback=on_token
                    )
                    token_queue.put(('__result__', r))
                except Exception as exc:
                    token_queue.put(('__error__', exc))
                finally:
                    token_queue.put(SENTINEL)

            thread = threading.Thread(target=run_agent, daemon=True)
            thread.start()

            result = None
            full_streamed = ''
            while True:
                item = token_queue.get()
                if item is SENTINEL:
                    break
                if isinstance(item, tuple) and item[0] == '__result__':
                    result = item[1]
                elif isinstance(item, tuple) and item[0] == '__error__':
                    raise item[1]
                elif isinstance(item, tuple) and item[0] == '__tool__':
                    yield sse('tool_action', {'tool': item[1], 'input': item[2]})
                else:
                    full_streamed += item
                    yield sse('token', {'text': item})

            thread.join()
            # full_streamed contains all coordinator tokens (the actual visible response).
            # result.response may be empty when the final text was fully streamed.
            response_text = full_streamed or (result or {}).get('response', '')
            tool_calls = (result or {}).get('tool_calls', [])

            if not response_text and tool_calls:
                lines = []
                for tc in tool_calls:
                    msg = (tc.get('result') or {}).get('message', '')
                    if msg:
                        lines.append(f"- {msg}")
                response_text = "Here's what I did for you:\n" + "\n".join(lines) if lines else "Done! Check your planner or shopping list for the updates."
                for word in response_text.split(' '):
                    if word:
                        yield sse('token', {'text': word + ' '})
            elif not response_text:
                response_text = "I'm not sure how to respond to that. Could you rephrase?"
                yield sse('token', {'text': response_text})

            if current_chat:
                current_chat['messages'].append({'role': 'user', 'content': query, 'timestamp': now_aest().isoformat()})
                current_chat['messages'].append({'role': 'assistant', 'content': response_text, 'timestamp': now_aest().isoformat(), 'tool_calls': tool_calls})
                if len(current_chat['messages']) == 2:
                    current_chat['title'] = query[:50]
                storage.save_user_data(user_id, user_data)

            yield sse('done', {'tool_calls': tool_calls})

            # Generate follow-up suggestions
            try:
                suggestions_prompt = (
                    f"Given this nutrition assistant response: {response_text[:300]}\n"
                    "Generate exactly 3 short follow-up prompts the user might want to ask next. "
                    "Return ONLY a JSON array of 3 strings, no other text. Example: [\"Add to meal plan\", \"Get shopping list\", \"Show similar recipes\"]"
                )
                import boto3 as _boto3, json as _json2
                br = _boto3.client('bedrock-runtime', region_name='ap-southeast-2')
                sg_resp = br.invoke_model(
                    modelId='anthropic.claude-3-haiku-20240307-v1:0',
                    body=_json2.dumps({"anthropic_version": "bedrock-2023-05-31", "max_tokens": 100,
                                       "messages": [{"role": "user", "content": suggestions_prompt}]}),
                    contentType='application/json', accept='application/json'
                )
                sg_text = _json2.loads(sg_resp['body'].read())['content'][0]['text'].strip()
                suggestions = _json2.loads(sg_text)
                if isinstance(suggestions, list):
                    yield sse('suggestions', {'items': suggestions[:3]})
            except Exception:
                pass

        except Exception as e:
            print(f"Stream error: {e}")
            import traceback; traceback.print_exc()
            yield sse('error', {'message': str(e)})

    return Response(stream_with_context(generate()), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


if __name__ == '__main__':
    mode = "AWS MODE" if USE_AWS else "LOCAL MODE"
    print("\n" + "="*60)
    print(f"🍽️ MealBuddy - {mode}")
    print("="*60)
    if not USE_AWS:
        print("Running without AWS - using mock data")
    print("Visit: http://localhost:5000")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)

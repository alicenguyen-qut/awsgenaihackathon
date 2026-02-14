import json
import boto3
import os
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Import utilities
from utils.responses import get_mock_chat_response
from utils.recommendations import generate_daily_recommendations
from utils.analytics import calculate_nutrition_stats, calculate_period_analytics, update_streak

# AWS clients
bedrock = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'ap-southeast-2'))
s3 = boto3.client('s3', region_name=os.environ.get('AWS_REGION', 'ap-southeast-2'))
BUCKET = os.environ['RECIPES_BUCKET']

# Initialize Bedrock RAG
try:
    from models.bedrock_rag import BedrockRAG
    bedrock_rag = BedrockRAG()
except Exception as e:
    print(f"Bedrock RAG initialization failed: {e}")
    bedrock_rag = None

# User data management
def get_user_data(user_id):
    try:
        obj = s3.get_object(Bucket=BUCKET, Key=f'users/{user_id}.json')
        return json.loads(obj['Body'].read())
    except:
        return {
            'chats': [], 'current_chat': None, 'username': '', 'uploaded_files': [],
            'password_hash': None, 'nutrition_logs': [], 'streaks': {'current': 0, 'longest': 0, 'last_login': ''},
            'favorites': [], 'meal_plan': {}, 'shopping_list': [], 'nutrition_profile': {}
        }

def save_user_data(user_id, data):
    s3.put_object(Bucket=BUCKET, Key=f'users/{user_id}.json', Body=json.dumps(data, indent=2))

def find_user_by_username(username):
    try:
        response = s3.list_objects_v2(Bucket=BUCKET, Prefix='users/')
        for obj in response.get('Contents', []):
            if obj['Key'].endswith('.json'):
                user_data = json.loads(s3.get_object(Bucket=BUCKET, Key=obj['Key'])['Body'].read())
                if user_data.get('username', '').lower() == username.lower():
                    return obj['Key'].replace('users/', '').replace('.json', ''), user_data
    except:
        pass
    return None, None

def get_html():
    try:
        obj = s3.get_object(Bucket=BUCKET, Key='ui/index.html')
        return obj['Body'].read().decode('utf-8')
    except:
        return """<!DOCTYPE html><html><head><title>AI Cooking Assistant</title></head><body><h1>Upload index.html to S3</h1></body></html>"""

def lambda_handler(event, context):
    path = event.get('rawPath', '/')
    method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')
    headers = event.get('headers', {})
    
    # Get session from headers
    session_id = headers.get('x-session-id', str(uuid.uuid4()))
    
    try:
        body = json.loads(event.get('body', '{}')) if event.get('body') else {}
    except:
        body = {}
    
    query_params = event.get('queryStringParameters', {}) or {}
    
    # Serve UI
    if path == '/' and method == 'GET':
        return {'statusCode': 200, 'headers': {'Content-Type': 'text/html'}, 'body': get_html()}
    
    # Authentication
    if path == '/api/login' and method == 'POST':
        username = body.get('username', '').strip()
        password = body.get('password', '').strip()
        
        if not username or not password:
            return {'statusCode': 400, 'body': json.dumps({'error': 'Username and password required'})}
        
        existing_user_id, existing_user_data = find_user_by_username(username)
        
        if existing_user_data:
            if not check_password_hash(existing_user_data.get('password_hash', ''), password):
                return {'statusCode': 401, 'body': json.dumps({'error': 'Invalid password'})}
            session_id = existing_user_id
        else:
            user_data = get_user_data(session_id)
            user_data['username'] = username
            user_data['password_hash'] = generate_password_hash(password)
            user_data['streaks'] = {'current': 1, 'longest': 1, 'last_login': datetime.now().strftime('%Y-%m-%d')}
            save_user_data(session_id, user_data)
        
        return {'statusCode': 200, 'headers': {'x-session-id': session_id}, 'body': json.dumps({'success': True, 'username': username})}
    
    if path == '/api/logout' and method == 'POST':
        return {'statusCode': 200, 'body': json.dumps({'success': True})}
    
    if path == '/api/session' and method == 'GET':
        user_data = get_user_data(session_id)
        return {'statusCode': 200, 'body': json.dumps({
            'user_id': session_id, 'username': user_data.get('username', ''),
            'chats': user_data['chats'], 'current_chat': user_data['current_chat']
        })}
    
    # Nutrition tracking
    if path == '/api/nutrition/log' and method == 'POST':
        user_data = get_user_data(session_id)
        log = {
            'id': str(uuid.uuid4()), 'date': body.get('date', datetime.now().strftime('%Y-%m-%d')),
            'meal_type': body['meal_type'], 'name': body['name'], 'calories': body['calories'],
            'protein': body.get('protein', 0), 'carbs': body.get('carbs', 0), 'fats': body.get('fats', 0),
            'timestamp': datetime.now().isoformat()
        }
        user_data['nutrition_logs'].append(log)
        save_user_data(session_id, user_data)
        return {'statusCode': 200, 'body': json.dumps({'success': True, 'log': log})}
    
    if path == '/api/nutrition/logs' and method == 'GET':
        user_data = get_user_data(session_id)
        date = query_params.get('date', datetime.now().strftime('%Y-%m-%d'))
        logs = [l for l in user_data.get('nutrition_logs', []) if l['date'] == date]
        return {'statusCode': 200, 'body': json.dumps({'logs': logs})}
    
    if path == '/api/nutrition/stats' and method == 'GET':
        user_data = get_user_data(session_id)
        date = query_params.get('date', datetime.now().strftime('%Y-%m-%d'))
        result = calculate_nutrition_stats(user_data.get('nutrition_logs', []), date)
        return {'statusCode': 200, 'body': json.dumps(result)}
    
    if path.startswith('/api/nutrition/logs/') and method == 'DELETE':
        log_id = path.split('/')[-1]
        user_data = get_user_data(session_id)
        user_data['nutrition_logs'] = [l for l in user_data.get('nutrition_logs', []) if l['id'] != log_id]
        save_user_data(session_id, user_data)
        return {'statusCode': 200, 'body': json.dumps({'success': True})}
    
    if path == '/api/nutrition/analytics' and method == 'GET':
        user_data = get_user_data(session_id)
        period = query_params.get('period', 'today')
        result = calculate_period_analytics(user_data.get('nutrition_logs', []), period)
        return {'statusCode': 200, 'body': json.dumps(result)}
    
    if path == '/api/recommendations/daily' and method == 'GET':
        user_data = get_user_data(session_id)
        today = datetime.now().strftime('%Y-%m-%d')
        logs = [l for l in user_data.get('nutrition_logs', []) if l['date'] == today]
        profile = user_data.get('nutrition_profile', {})
        recommendations = generate_daily_recommendations(logs, profile)
        return {'statusCode': 200, 'body': json.dumps({'recommendations': recommendations})}
    
    # Streaks
    if path == '/api/streaks' and method == 'GET':
        user_data = get_user_data(session_id)
        if 'streaks' not in user_data:
            user_data['streaks'] = {'current': 0, 'longest': 0, 'last_login': None}
        if update_streak(user_data['streaks']):
            save_user_data(session_id, user_data)
        return {'statusCode': 200, 'body': json.dumps({'streaks': user_data['streaks']})}
    
    # Favorites
    if path == '/api/favorites' and method == 'POST':
        user_data = get_user_data(session_id)
        if 'favorites' not in user_data:
            user_data['favorites'] = []
        recipe = {'recipeId': body['recipeId'], 'recipeName': body['recipeName'], 'content': body.get('content', '')}
        existing = next((f for f in user_data['favorites'] if f['recipeId'] == recipe['recipeId']), None)
        if existing:
            user_data['favorites'].remove(existing)
            added = False
        else:
            user_data['favorites'].append(recipe)
            added = True
        save_user_data(session_id, user_data)
        return {'statusCode': 200, 'body': json.dumps({'success': True, 'added': added})}
    
    if path == '/api/favorites' and method == 'GET':
        user_data = get_user_data(session_id)
        return {'statusCode': 200, 'body': json.dumps({'favorites': user_data.get('favorites', [])})}
    
    # Meal plan
    if path == '/api/meal-plan' and method == 'GET':
        user_data = get_user_data(session_id)
        return {'statusCode': 200, 'body': json.dumps({'plan': user_data.get('meal_plan', {})})}
    
    if path == '/api/meal-plan' and method == 'POST':
        user_data = get_user_data(session_id)
        user_data['meal_plan'] = body['plan']
        save_user_data(session_id, user_data)
        return {'statusCode': 200, 'body': json.dumps({'success': True})}
    
    # Shopping list
    if path == '/api/shopping-list' and method == 'GET':
        user_data = get_user_data(session_id)
        return {'statusCode': 200, 'body': json.dumps({'items': user_data.get('shopping_list', [])})}
    
    if path == '/api/shopping-list' and method == 'POST':
        user_data = get_user_data(session_id)
        if 'shopping_list' not in user_data:
            user_data['shopping_list'] = []
        user_data['shopping_list'].append({'name': body['name'], 'checked': False})
        save_user_data(session_id, user_data)
        return {'statusCode': 200, 'body': json.dumps({'success': True})}
    
    if path == '/api/shopping-list/clear' and method == 'POST':
        user_data = get_user_data(session_id)
        user_data['shopping_list'] = []
        save_user_data(session_id, user_data)
        return {'statusCode': 200, 'body': json.dumps({'success': True})}
    
    # Profile
    if path == '/api/nutrition-profile' and method == 'POST':
        user_data = get_user_data(session_id)
        user_data['nutrition_profile'] = {
            'dietary': body.get('dietary', []),
            'healthGoal': body.get('healthGoal', ''),
            'allergies': body.get('allergies', [])
        }
        save_user_data(session_id, user_data)
        return {'statusCode': 200, 'body': json.dumps({'success': True})}
    
    if path == '/api/nutrition-profile' and method == 'GET':
        user_data = get_user_data(session_id)
        return {'statusCode': 200, 'body': json.dumps({'profile': user_data.get('nutrition_profile', {})})}
    
    # Chat
    if path == '/chat' and method == 'POST':
        query = body.get('query', '')
        if not query:
            return {'statusCode': 400, 'body': json.dumps({'error': 'Query required'})}
        
        user_data = get_user_data(session_id)
        
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
        
        # Generate response
        if bedrock_rag:
            try:
                from utils.config import MOCK_RECIPES
                user_profile = user_data.get('nutrition_profile', {})
                response = bedrock_rag.chat_with_rag(query, MOCK_RECIPES, user_profile)
            except Exception as e:
                print(f"Bedrock error: {e}")
                response = get_mock_chat_response(query)
        else:
            response = get_mock_chat_response(query)
        
        # Save to chat history
        current_chat = next((c for c in user_data['chats'] if c['id'] == user_data['current_chat']), None)
        if current_chat:
            current_chat['messages'].append({'role': 'user', 'content': query, 'timestamp': datetime.now().isoformat()})
            current_chat['messages'].append({'role': 'assistant', 'content': response, 'timestamp': datetime.now().isoformat()})
            if len(current_chat['messages']) == 2:
                current_chat['title'] = query[:50]
            save_user_data(session_id, user_data)
        
        return {'statusCode': 200, 'body': json.dumps({'response': response})}
    
    # Chat management
    if path == '/api/chat/new' and method == 'POST':
        user_data = get_user_data(session_id)
        chat_id = str(uuid.uuid4())
        new_chat = {'id': chat_id, 'title': 'New Chat', 'created_at': datetime.now().isoformat(), 'messages': []}
        user_data['chats'].append(new_chat)
        user_data['current_chat'] = chat_id
        save_user_data(session_id, user_data)
        return {'statusCode': 200, 'body': json.dumps({'success': True, 'chat_id': chat_id})}
    
    if path.startswith('/api/chat/') and method == 'GET':
        chat_id = path.split('/')[-1]
        user_data = get_user_data(session_id)
        chat = next((c for c in user_data['chats'] if c['id'] == chat_id), None)
        if chat:
            user_data['current_chat'] = chat_id
            save_user_data(session_id, user_data)
            return {'statusCode': 200, 'body': json.dumps(chat)}
        return {'statusCode': 404, 'body': json.dumps({'error': 'Chat not found'})}
    
    if path.startswith('/api/chat/') and method == 'DELETE':
        chat_id = path.split('/')[-1]
        user_data = get_user_data(session_id)
        user_data['chats'] = [c for c in user_data['chats'] if c['id'] != chat_id]
        if user_data['current_chat'] == chat_id:
            user_data['current_chat'] = user_data['chats'][0]['id'] if user_data['chats'] else None
        save_user_data(session_id, user_data)
        return {'statusCode': 200, 'body': json.dumps({'success': True})}
    
    return {'statusCode': 404, 'body': 'Not Found'}

import json
import boto3
import os
import numpy as np
import uuid
from datetime import datetime, timedelta
import base64
from werkzeug.security import generate_password_hash, check_password_hash

bedrock = boto3.client('bedrock-runtime', region_name='ap-southeast-2')
s3 = boto3.client('s3', region_name='ap-southeast-2')
BUCKET = os.environ['RECIPES_BUCKET']

embeddings_cache = None

def load_embeddings():
    global embeddings_cache
    if embeddings_cache is None:
        try:
            obj = s3.get_object(Bucket=BUCKET, Key='embeddings/recipe_embeddings.json')
            embeddings_cache = json.loads(obj['Body'].read())
        except:
            embeddings_cache = []
    return embeddings_cache

def get_embedding(text):
    response = bedrock.invoke_model(
        modelId='amazon.titan-embed-text-v1',
        body=json.dumps({"inputText": text})
    )
    return json.loads(response['body'].read())['embedding']

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

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
    
    # Serve UI
    if path == '/' and method == 'GET':
        return {'statusCode': 200, 'headers': {'Content-Type': 'text/html'}, 'body': get_html()}
    
    # Login API
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
    
    # Session API
    if path == '/api/session' and method == 'GET':
        user_data = get_user_data(session_id)
        return {'statusCode': 200, 'body': json.dumps({
            'user_id': session_id, 'username': user_data.get('username', ''),
            'chats': user_data['chats'], 'current_chat': user_data['current_chat']
        })}
    
    # Profile photo APIs
    if path == '/api/profile-photo' and method == 'POST':
        try:
            user_data = get_user_data(session_id)
            
            # Handle base64 encoded file upload (AWS)
            if 'photo' in body and isinstance(body['photo'], str):
                photo_data = base64.b64decode(body['photo'])
                photo_key = f'photos/{session_id}_profile.jpg'
                s3.put_object(Bucket=BUCKET, Key=photo_key, Body=photo_data, ContentType='image/jpeg')
                user_data['profile_photo'] = f'/api/photo/{session_id}'
            else:
                # This shouldn't happen in Lambda, but handle gracefully
                return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid photo format'})}
            
            save_user_data(session_id, user_data)
            return {'statusCode': 200, 'body': json.dumps({'success': True, 'photoUrl': user_data['profile_photo']})}
        except Exception as e:
            return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}}
    
    if path == '/api/profile-photo' and method == 'GET':
        user_data = get_user_data(session_id)
        return {'statusCode': 200, 'body': json.dumps({'photoUrl': user_data.get('profile_photo', '')})}
    
    # Serve profile photos
    if path.startswith('/api/photo/') and method == 'GET':
        photo_user_id = path.split('/')[-1]
        try:
            obj = s3.get_object(Bucket=BUCKET, Key=f'photos/{photo_user_id}_profile.jpg')
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'image/jpeg'},
                'body': base64.b64encode(obj['Body'].read()).decode('utf-8'),
                'isBase64Encoded': True
            }
        except:
            return {'statusCode': 404, 'body': 'Photo not found'}
    
    # Nutrition APIs
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
    
    if path == '/api/nutrition/stats' and method == 'GET':
        user_data = get_user_data(session_id)
        date = event.get('queryStringParameters', {}).get('date', datetime.now().strftime('%Y-%m-%d')) if event.get('queryStringParameters') else datetime.now().strftime('%Y-%m-%d')
        logs = [l for l in user_data.get('nutrition_logs', []) if l['date'] == date]
        total = {'calories': sum(l['calories'] for l in logs), 'protein': sum(l['protein'] for l in logs),
                 'carbs': sum(l['carbs'] for l in logs), 'fats': sum(l['fats'] for l in logs)}
        return {'statusCode': 200, 'body': json.dumps({'stats': total, 'meal_count': len(logs)})}
    
    # Chat API
    if path == '/chat' and method == 'POST':
        query = body.get('query', '')
        if not query:
            return {'statusCode': 400, 'body': json.dumps({'error': 'Query required'})}
        
        # Simple hardcoded responses for now
        if 'vegan' in query.lower():
            response = "🌱 Vegetarian Buddha Bowl - A colorful bowl with quinoa, chickpeas, sweet potato, and tahini dressing. High in fiber and plant-based protein (520 cal)."
        elif 'protein' in query.lower():
            response = "💪 Grilled Chicken Salad - Mediterranean-style with fresh vegetables. Perfect for muscle growth (380 cal, 42g protein)."
        else:
            response = "Here are some recipe suggestions: Grilled Chicken Salad (380 cal), Vegetarian Buddha Bowl (520 cal), Salmon with Roasted Vegetables (420 cal)"
        
        return {'statusCode': 200, 'body': json.dumps({'response': response})}
    
    return {'statusCode': 404, 'body': 'Not Found'}

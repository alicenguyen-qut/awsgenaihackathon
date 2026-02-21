import json
import os
import boto3
from datetime import datetime
import zoneinfo
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'txt', 'docx', 'pdf'}
AEST = zoneinfo.ZoneInfo('Australia/Sydney')

def now_aest():
    """Current datetime in Australian Eastern time (handles DST automatically)."""
    return datetime.now(AEST)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_user_file(user_id, sessions_folder):
    """Get user data file path"""
    return os.path.join(sessions_folder, f'{user_id}.json')

def load_user_data(user_id, sessions_folder, s3_client=None, s3_bucket=None):
    """Load user data from S3 or local file"""
    if s3_client and s3_bucket:
        # Load from S3
        try:
            response = s3_client.get_object(Bucket=s3_bucket, Key=f'sessions/{user_id}.json')
            return json.loads(response['Body'].read().decode('utf-8'))
        except s3_client.exceptions.NoSuchKey:
            pass
        except Exception as e:
            print(f"S3 load error: {e}")
    
    # Fallback to local file
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

def save_user_data(user_id, data, sessions_folder, s3_client=None, s3_bucket=None):
    """Save user data to S3 or local file"""
    if s3_client and s3_bucket:
        # Save to S3
        try:
            s3_client.put_object(
                Bucket=s3_bucket,
                Key=f'sessions/{user_id}.json',
                Body=json.dumps(data, indent=2),
                ContentType='application/json'
            )
            return
        except Exception as e:
            print(f"S3 save error: {e}, falling back to local")
    
    # Fallback to local file
    filepath = get_user_file(user_id, sessions_folder)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def find_user_by_username(username, sessions_folder, s3_client=None, s3_bucket=None):
    """Find user data by username across all sessions"""
    if s3_client and s3_bucket:
        # Search in S3
        try:
            response = s3_client.list_objects_v2(Bucket=s3_bucket, Prefix='sessions/')
            if 'Contents' in response:
                for obj in response['Contents']:
                    try:
                        data_response = s3_client.get_object(Bucket=s3_bucket, Key=obj['Key'])
                        data = json.loads(data_response['Body'].read().decode('utf-8'))
                        if data.get('username', '').lower() == username.lower():
                            user_id = obj['Key'].replace('sessions/', '').replace('.json', '')
                            return user_id, data
                    except:
                        pass
        except Exception as e:
            print(f"S3 search error: {e}")
    
    # Fallback to local files
    if os.path.exists(sessions_folder):
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

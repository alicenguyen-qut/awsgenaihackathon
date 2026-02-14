# Storage wrapper for S3 or local files
import os
_s3_client = None
_s3_bucket = None
_sessions_folder = None

def init_storage(sessions_folder, s3_client=None, s3_bucket=None):
    """Initialize storage configuration"""
    global _s3_client, _s3_bucket, _sessions_folder
    _sessions_folder = sessions_folder
    _s3_client = s3_client
    _s3_bucket = s3_bucket

def load_user_data(user_id):
    """Load user data using configured storage"""
    from utils.helpers import load_user_data as _load
    return _load(user_id, _sessions_folder, _s3_client, _s3_bucket)

def save_user_data(user_id, data):
    """Save user data using configured storage"""
    from utils.helpers import save_user_data as _save
    return _save(user_id, data, _sessions_folder, _s3_client, _s3_bucket)

def find_user_by_username(username):
    """Find user by username using configured storage"""
    from utils.helpers import find_user_by_username as _find
    return _find(username, _sessions_folder, _s3_client, _s3_bucket)

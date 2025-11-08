# backend/auth.py
import os
import datetime
import jwt
from functools import wraps
from flask import request, jsonify
from models import User

JWT_SECRET = os.environ.get('CSP_JWT_SECRET', 'replace-this-secret')  # change in production
JWT_ALGO = 'HS256'
JWT_EXP_DAYS = 7

def create_token(user):
    payload = {
        'sub': user.id,
        'email': user.email,
        'is_admin': user.is_admin,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=JWT_EXP_DAYS)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)
    # pyjwt may return bytes in some installs
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token

def decode_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except Exception:
        return None

def get_auth_user(db_session):
    auth = request.headers.get('Authorization', None)
    if not auth:
        return None
    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    payload = decode_token(parts[1])
    if not payload:
        return None
    user = db_session.query(User).get(payload['sub'])
    return user

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = get_auth_user(f.__globals__['db'].session if 'db' in f.__globals__ else None)
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs, _auth_user=user)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = get_auth_user(f.__globals__['db'].session if 'db' in f.__globals__ else None)
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        if not user.is_admin:
            return jsonify({'error': 'Admin required'}), 403
        return f(*args, **kwargs, _auth_user=user)
    return wrapper

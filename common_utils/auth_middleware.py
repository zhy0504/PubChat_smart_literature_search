
import os
import redis
import logging
from quart import request, jsonify, g
from functools import wraps

logger = logging.getLogger(__name__)

# Initialize Redis configuration from environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Use a connection pool for better performance
redis_pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def get_redis_client():
    return redis.Redis(connection_pool=redis_pool)

def require_session(func):
    """
    Decorator to validate session_id for API endpoints.
    Checks for session_id in:
    1. JSON Body (for POST/PUT)
    2. Query Parameters (for GET)
    
    If valid, returns the decorated function.
    If invalid, returns 401 error.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        session_id = None
        
        # 1. Check Authorization Header (Bearer scheme)
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith("Bearer "):
            session_id = auth_header.split(" ")[1]
            
        if not session_id:
             return jsonify({
                "success": False,
                "message": {
                    "zh": "无效Token，请登录后重试",
                    "en": "Invalid Token, please log in and try again"
                }
            }), 400

        try:
            redis_client = get_redis_client()
            auth_key = f"user_session:{session_id}"
            user_id = redis_client.get(auth_key)

            if not user_id:
                return jsonify({
                    "success": False,
                    "message": {
                        "zh": "登录信息已过期，请重新登录",
                        "en": "Login information has expired, please log in again"
                    }
                }), 401
                
            # Store user_id in g for the view function to use
            g.user_id = user_id
            g.session_id = session_id
            
        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return jsonify({
                "success": False,
                "message": {
                    "zh": f"系统鉴权错误: {e}",
                    "en": f"System auth error: {e}"
                }
            }), 500

        return await func(*args, **kwargs)

    return wrapper

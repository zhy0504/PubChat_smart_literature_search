import os
import json
import logging
import asyncpg
from urllib.parse import urlparse
from quart import Quart, request, jsonify
from celery import Celery
from common_utils.logger import setup_logging
# Correcting the import based on file content. 
# If require_session_id was intended, it should probably be require_session or aliased.
# Using require_session as alias to match the decorator usage if the previous code used it, 
# but simply importing require_session is safer if we update usage.
# from common_utils.auth_middleware import require_session

setup_logging('search_server')

# Initialize Logger
logger = logging.getLogger(__name__)

# Initialize Quart App
app = Quart(__name__)

# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
celery_app = Celery('search_tasks', broker=CELERY_BROKER_URL)

# Database Connection Config
DB_CONFIG = {
    "database": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"), 
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT")
}


_MODEL_PRESETS = {
    "google_gemini": {
        "provider": "google",
        "model": "gemini-3.1-flash-lite-preview",
    },
    "openrouter_gemini": {
        "provider": "openrouter",
        "base_url": os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        "model": (
            os.getenv("OPENROUTER_MODEL")
            or os.getenv("OPENROUTER_GEMINI_FLASH_MODEL")
            or os.getenv("OPENROUTER_GEMINI_PRO_MODEL")
            or "google/gemini-3.1-flash-lite-preview"
        ),
    },
}

_PROVIDER_ALIASES = {
    "google": "google",
    "gemini": "google",
    "google-gemini": "google",
    "openrouter": "openrouter",
    "openrouter-gemini": "openrouter",
    "openai": "openai-compatible",
    "openai-compatible": "openai-compatible",
    "openai_compatible": "openai-compatible",
    "deepseek": "openai-compatible",
    "qwen": "openai-compatible",
    "siliconflow": "openai-compatible",
    "ollama": "openai-compatible",
    "lmstudio": "openai-compatible",
    "groq": "openai-compatible",
    "together": "openai-compatible",
    "fireworks": "openai-compatible",
    "mistral": "openai-compatible",
    "moonshot": "openai-compatible",
    "kimi": "openai-compatible",
    "glm": "openai-compatible",
    "zhipu": "openai-compatible",
    "anthropic": "anthropic",
    "claude": "anthropic",
    "cohere": "cohere",
}


def _as_string_list(value):
    """Normalize arrays and legacy delimited strings without logging secrets."""
    if value is None:
        return []
    if isinstance(value, str):
        values = value.replace("\r", "\n").replace(";", "\n").replace(",", "\n").split("\n")
    else:
        values = value
    return [str(item).strip() for item in values if str(item).strip()]


def _normalise_llm_config(raw_config):
    """Validate and normalize the public task API's LLM configuration."""
    if raw_config is None:
        raw = {}
    elif isinstance(raw_config, dict):
        raw = dict(raw_config)
    else:
        raise ValueError("llm_config 必须是 JSON 对象")
    model = str(raw.get("model") or "").strip()
    provider = str(raw.get("provider") or "").strip().lower()
    base_url = str(raw.get("base_url") or "").strip().rstrip("/")

    preset = _MODEL_PRESETS.get(model.lower())
    if preset:
        provider = provider or preset["provider"]
        model = str(raw.get("custom_model") or preset["model"]).strip()
        base_url = base_url or str(preset.get("base_url") or "").strip().rstrip("/")

    if model == "__custom__":
        model = str(raw.get("custom_model") or "").strip()

    provider = _PROVIDER_ALIASES.get(provider, provider)
    if not provider:
        provider = "openai-compatible" if base_url else "google"
    if provider not in {"google", "openrouter", "openai-compatible", "anthropic", "cohere"}:
        raise ValueError("不支持的 AI 提供商")

    if not model:
        model_defaults = {
            "google": os.getenv("GOOGLE_GEMINI_MODEL", "gemini-flash-lite-latest"),
            "openrouter": (
                os.getenv("OPENROUTER_MODEL")
                or os.getenv("OPENROUTER_GEMINI_FLASH_MODEL")
                or os.getenv("OPENROUTER_GEMINI_PRO_MODEL")
                or "google/gemini-3.1-flash-lite-preview"
            ),
            "openai-compatible": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "anthropic": os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
            "cohere": os.getenv("COHERE_MODEL", "command-r-plus"),
        }
        model = model_defaults[provider]

    if provider == "openrouter":
        base_url = base_url or os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
    elif provider == "openai-compatible" and not base_url:
        raise ValueError("OpenAI 兼容接口必须填写 base_url")

    if not model:
        raise ValueError("必须填写模型名称")

    if base_url:
        parsed = urlparse(base_url)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("base_url 必须是完整的 http(s) 地址，且不能包含账号、密码或查询参数")
        if len(base_url) > 2048:
            raise ValueError("base_url 过长")

    api_keys = _as_string_list(raw.get("api") or raw.get("api_keys"))
    if not api_keys:
        raise ValueError("至少填写一个 AI API Key")

    return {
        "provider": provider,
        "base_url": base_url or None,
        "model": model,
        "api": api_keys,
        "pubmed_api": _as_string_list(raw.get("pubmed_api") or raw.get("pubmed_api_keys")),
    }


@app.before_serving
async def ensure_task_config_columns():
    """Migrate existing deployments before accepting tasks."""
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        await conn.execute(
            'ALTER TABLE IF EXISTS "userSchema"."tasks" '
            'ADD COLUMN IF NOT EXISTS provider varchar'
        )
        await conn.execute(
            'ALTER TABLE IF EXISTS "userSchema"."tasks" '
            'ADD COLUMN IF NOT EXISTS base_url varchar'
        )
    finally:
        await conn.close()

@app.route('/health', methods=['GET'])
async def health_check():
    logger.info("Health check requested.")
    return jsonify({"status": "literature-search service is running!"}), 200

@app.route('/task', methods=['POST'])
async def create_search_task():
    logger.info("Search requested.")
    # user_id = g.user_id
    try:
        data = await request.get_json()
    except Exception:
        return jsonify({
            "success": False,
            "message": {"zh": "请求体必须是有效的 JSON", "en": "Request body must be valid JSON"},
        }), 400
    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": {"zh": "请求体必须是 JSON 对象", "en": "Request body must be a JSON object"},
        }), 400
    try:
        llm_config = _normalise_llm_config(data.get('llm_config'))
    except ValueError as exc:
        return jsonify({
            "success": False,
            "message": {"zh": str(exc), "en": str(exc)},
        }), 400
    
    conn = None
    redis_client = None
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        async with conn.transaction():
            # 1. Atomic check for user status
            # Use ROW SHARE or FOR UPDATE to lock the user row
            # user_row = await conn.fetchrow(
            #     'SELECT available_times, is_running FROM "userSchema"."users" WHERE id = $1 FOR UPDATE', 
            #     user_id
            # )
            
            # if not user_row:
            #     return jsonify({
            #         "success": False,
            #         "message": {"zh": "用户不存在", "en": "User not found"}
            #     }), 404
                
            # if user_row['is_running']:
            #     return jsonify({
            #         "success": False,
            #         "message": {"zh": "当前有任务正在运行，请稍后重试", "en": "Task is running, please try again later"}
            #     }), 400 # Too Many Requests? Or 400.
            
            # # if user_row['available_times'] <= 0:
            # #     return jsonify({
            # #         "success": False,
            # #         "message": {"zh": "余额已用完", "en": "Balance exhausted"}
            # #     }), 403
            
            # # 2. Update user status to running
            # # Note: We do NOT decrement times here, as per logic "submit task". 
            # # Usually times are decremented on finish or start. 
            # # Assuming just marking as running for now.
            # await conn.execute('UPDATE "userSchema"."users" SET is_running = true WHERE id = $1', user_id)
            
            # 3. Create Task Record
            # Extract fields from nested structures
            s_settings = data.get('search_settings') or {}
            s_filters = data.get('search_filters') or {}
            j_filters = data.get('journal_filters') or {}
            insert_query = """
                INSERT INTO "userSchema"."tasks" (
                    output_language, user_query,
                    max_refinement_attempts, min_study_threshold,
                    time, author, first_author, last_author, affiliation, journal, custom,
                    impact_factor, jcr_zone, cas_zone, provider, base_url, model, api, pubmed_api
                ) VALUES (
                    $1, $2, $3,
                    $4, $5,
                    $6, $7, $8, $9, $10, $11, $12,
                    $13, $14, $15, $16, $17, $18, $19
                ) RETURNING id
            """
            
            task_id = await conn.fetchval(
                insert_query,
                data.get('outputlanguage'),
                data.get('user_query'),
                # Search Settings
                s_settings.get('max_refinement_attempts'),
                s_settings.get('min_study_threshold'),
                # Search Filters
                s_filters.get('time'),
                s_filters.get('author'),
                s_filters.get('first_author'),
                s_filters.get('last_author'),
                s_filters.get('affiliation'),
                s_filters.get('journal'),
                s_filters.get('custom'),
                # Journal Filters
                j_filters.get('impact_factor'),
                j_filters.get('jcr_zone'),
                j_filters.get('cas_zone'),
                # LLM Config
                llm_config['provider'],
                llm_config['base_url'],
                llm_config['model'],
                llm_config['api'],
                llm_config['pubmed_api']
            )
            
            # 4. Push to Celery
            # We send the task_id. The worker will likely need to fetch the task from DB or we pass parameters.
            # Passing just ID is cleaner if worker has DB access.
            async_result = celery_app.send_task('search_workflow.run_search', args=[str(task_id)], queue='search_queue')
            celery_task_id = async_result.id

            # Store celery_task_id in Redis with 30m expiration
            import redis.asyncio as redis
            redis_client = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, db=0, decode_responses=True)
            await redis_client.setex(f"task:{str(task_id)}:celery_id", 1800, celery_task_id)
            
            # Set initial status to Pending
            await redis_client.hset(f"task:{str(task_id)}:info", "status", "Pending")
            await redis_client.expire(f"task:{str(task_id)}:info", 1800)

        return jsonify({
            "success": True,
            "message": {"zh": "任务已提交", "en": "Task submitted"},
            "data": {"search_task_id": str(task_id)}
        }), 200

    except Exception as e:
        logger.error(f"Error creating search task: {e}")
        return jsonify({
            "success": False,
            "message": {"zh": f"任务创建失败，原因为：{e}", "en": f"Failed to create task, reason: {e}"}
        }), 500
    finally:
        if conn:
            await conn.close()
        if redis_client:
            await redis_client.aclose()

@app.route('/task/stop', methods=['POST'])
async def stop_search_task():
    logger.info("Stop task requested.")
    # user_id = g.user_id
    data = await request.get_json()
    task_id = data.get('task_id')
    
    if not task_id:
        return jsonify({"success": False, "message": {"zh": "缺少任务ID", "en": "Missing task ID"}}), 400

    conn = None
    redis_client = None
    try:
        import redis.asyncio as redis
        redis_client = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, db=0, decode_responses=True)
        
        # Get celery_task_id from Redis
        celery_task_id = await redis_client.get(f"task:{task_id}:celery_id")
        
        # 1. Revoke the Celery task
        revoke_id = celery_task_id if celery_task_id else task_id
        celery_app.control.revoke(revoke_id, terminate=True)
        logger.info(f"Task {task_id} (Celery ID: {revoke_id}) revoked.")
        
        # # 2. Update User Status in DB and Task Status
        conn = await asyncpg.connect(**DB_CONFIG)
        # await conn.execute('UPDATE "userSchema"."users" SET is_running = false WHERE id = $1', user_id)
        
        # Update tasks table status if column exists
        try:
            # Assuming 'status' column exists, if not this will fail but caught
            await conn.execute('UPDATE "userSchema"."tasks" SET status = \'stopped\' WHERE id = $1::uuid', task_id)
        except Exception as e:
            logger.warning(f"Could not update status in tasks table (maybe column missing?): {e}")

        # 3. Update Redis status to "Stopped" so frontend reflects it
        await redis_client.hset(f"task:{task_id}:info", "status", "Stopped")

        return jsonify({"success": True, "message": {"zh": "任务已停止", "en": "Task stopped"}}), 200

    except Exception as e:
        logger.error(f"Failed to stop task: {e}")
        return jsonify({"success": False, "message": {"zh": f"停止任务失败: {e}", "en": f"Failed to stop task: {e}"}}), 500
    finally:
        if conn:
            await conn.close()
        if redis_client:
            await redis_client.aclose()

@app.route('/search_status/<string:task_id>', methods=['GET'])
async def get_search_status(task_id):
    logger.info(f"Checking status for task: {task_id}")
    import redis.asyncio as redis
    
    redis_client = None
    try:
        redis_client = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, db=0, decode_responses=True)
        
        info_key = f"task:{task_id}:info"
        retrieval_key = f"task:{task_id}:retrieval"
        articles_key = f"task:{task_id}:articles"

        # 1. 获取基本信息 (Status, Progress)
        info = await redis_client.hgetall(info_key)
        if not info:
             # Redis 中没有，可能任务太久了或ID错误。
            return jsonify({
                "success": False,
                "message": {"zh": "任务不存在或已过期", "en": "Task not found or expired"}
            }), 404

        status = info.get("status", "Pending")
        progress_json = info.get("progress", "{}")
        search_progress = json.loads(progress_json) if progress_json else {}

        # 2. 获取列表数据 (Retrieval, Articles)
        retrieval_list_raw = await redis_client.lrange(retrieval_key, 0, -1)
        articles_list_raw = await redis_client.lrange(articles_key, 0, -1)
        
        retrieval = [json.loads(item) for item in retrieval_list_raw]
        output_review = [json.loads(item) for item in articles_list_raw]

        # 3. 构造返回结构
        response_data = {
            "success": True,
            "status_code": 200,
            "message": {
                "en": "Status retrieved",
                "zh": "状态已获取"
            },
            "data": {
                "search_status": status,
                "download_link": info.get("download_link"),
                "retrieval": retrieval,
                "search_progress": search_progress,
                "output_review": output_review
            }
        }
        
        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Error fetching search status: {e}")
        return jsonify({
            "success": False,
            "message": {"zh": f"获取状态失败: {e}", "en": f"Failed to get status: {e}"}
        }), 500
    finally:
        if redis_client:
            await redis_client.aclose()


@app.route('/documents', methods=['GET'])
async def get_user_documents():
    """Get list of generated documents for the user"""
    # user_id = g.user_id
    
    conn = None
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        # Fetch documents ordered by created_time desc
        rows = await conn.fetch("""
            SELECT *
            FROM "userSchema"."documents" 
            ORDER BY created_time DESC
        """)
        
        # Convert to list of dicts
        documents = []
        for row in rows:
            # Handle potential Decimal type for size
            size_val = row['size']
            if hasattr(size_val, 'real'): # Check if number
                size_val = float(size_val)
                
            # Handle created_time potentially being a string already (depending on driver/DB)
            created_time_val = row['created_time']
            if created_time_val and hasattr(created_time_val, 'isoformat'):
                created_time_str = created_time_val.isoformat()
            else:
                created_time_str = str(created_time_val) if created_time_val else None

            documents.append({
                "id": str(row['id']),
                "task_id": str(row['task_id']) if row['task_id'] else None,
                "size": size_val,
                "user_query": row['user_query'],
                "created_time": created_time_str,
                "download_link": row['download_link']
            })
            
        return jsonify({
            "success": True,
            "data": documents
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to fetch documents: {e}")
        return jsonify({
            "success": False, 
            "message": {"zh": "获取文档列表失败", "en": "Failed to fetch documents"}
        }), 500
    finally:
        if conn:
            await conn.close()


@app.route('/documents/<string:doc_id>', methods=['DELETE'])
async def delete_document(doc_id):
    """Delete a document"""
    # user_id = g.user_id
    
    conn = None
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        
        # Verify ownership and existence
        # row = await conn.fetchrow(
        #     'SELECT user_query, download_link FROM "userSchema"."documents" WHERE id = $1::uuid',
        #     doc_id
        # )
        
        # if not row:
        #     return jsonify({
        #         "success": False,
        #         "message": {"zh": "文档不存在或无权删除", "en": "Document not found or permission denied"}
        #     }), 404
            
        # Delete from DB
        await conn.execute(
            'DELETE FROM "userSchema"."documents" WHERE id = $1::uuid',
            doc_id
        )
        return jsonify({
            "success": True, 
            "message": {"zh": "文档已删除", "en": "Document deleted"}
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        return jsonify({
            "success": False, 
            "message": {"zh": f"删除文档失败: {e}", "en": "Failed to delete document"}
        }), 500
    finally:
        if conn:
            await conn.close()

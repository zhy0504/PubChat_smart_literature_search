# common_utils/logging_config.py
import logging
import sys
import os

def setup_logging(service_name):
    """
    动态配置日志：根据 service_name 生成不同的文件名
    例如：search -> /app/logs/search.log
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 1. Console Handler (所有服务共用，docker logs 可见)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. File Handler (根据服务名动态生成)
    log_dir = "/app/logs"
    log_file_path = os.path.join(log_dir, f"{service_name}.log")
    
    try:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # mode='a' 表示追加模式
        file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Failed to initialize file logging for {service_name}: {e}")

    logging.info(f"🚀 Logging configured for service: {service_name}")
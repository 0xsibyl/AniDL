import os
import logging
from logging.handlers import TimedRotatingFileHandler


def configure_logging(log_directory, log_file_prefix, log_when, log_interval, log_backup_count):
    os.makedirs(log_directory, exist_ok=True)
    log_file_path = os.path.join(log_directory, log_file_prefix)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            TimedRotatingFileHandler(log_file_path, when=log_when, interval=log_interval, backupCount=log_backup_count,
                                     encoding='utf-8', utc=True)
        ]
    )
    logging.info("日志记录已启动.")
    return True


def log_message(message):
    logging.info(message)


# 使用示例
log_directory = 'log'
log_file_prefix = 'data.log'
log_when = 'midnight'  # 每天生成一个新文件
log_interval = 1
log_backup_count = 7  # 保留最近7天的日志

configure_logging(log_directory, log_file_prefix, log_when, log_interval, log_backup_count)
log_message("这是一个测试日志消息。")

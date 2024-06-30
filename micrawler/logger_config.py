import os
import logging
from logging.handlers import RotatingFileHandler


def configure_logging(log_directory, log_file, log_max_bytes, log_backup_count):
    os.makedirs(log_directory, exist_ok=True)
    log_file_path = os.path.join(log_directory, log_file)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            RotatingFileHandler(log_file_path, maxBytes=log_max_bytes, backupCount=log_backup_count)
        ]
    )
    logging.info("日志记录已启动.")
    return True


def log_message(message):
    logging.info(message)

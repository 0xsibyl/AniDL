import os
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime


class CustomTimedRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(self, filename, when='midnight', interval=1, backupCount=0, encoding=None, delay=False, utc=False):
        # 传入 backupCount=0 表示不备份文件
        super().__init__(filename, when, interval, backupCount, encoding, delay, utc)

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None

        current_time = datetime.now()
        base, ext = os.path.splitext(self.baseFilename)
        # 使用日期格式来命名日志文件
        new_filename = f"{base}-{current_time.strftime('%Y-%m-%d')}{ext}"

        # 只重命名文件，且不备份
        if not os.path.exists(new_filename):
            if os.path.exists(self.baseFilename):
                os.rename(self.baseFilename, new_filename)

        if not self.delay:
            self.stream = self._open()


def configure_logging(log_directory, log_file_prefix, log_when, log_interval, log_backup_count=0):
    os.makedirs(log_directory, exist_ok=True)
    log_file_path = os.path.join(log_directory, log_file_prefix)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            CustomTimedRotatingFileHandler(log_file_path, when=log_when, interval=log_interval,
                                           backupCount=log_backup_count, encoding='utf-8', utc=True)
        ]
    )
    logging.info("日志记录已启动.")
    return True

import os
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime


class CustomTimedRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(self, filename, when='midnight', interval=1, backupCount=0, encoding=None, delay=False, utc=False):
        super().__init__(filename, when, interval, backupCount, encoding, delay, utc)

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None
        current_time = datetime.now()
        base, ext = os.path.splitext(self.baseFilename)
        new_filename = f"{base}-{current_time.strftime('%Y-%m-%d')}{ext}"
        if not os.path.exists(self.baseFilename):
            os.rename(self.baseFilename, new_filename)
        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = f"{self.baseFilename}.{i}"
                dfn = f"{self.baseFilename}.{i + 1}"
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            dfn = self.baseFilename + ".1"
            if os.path.exists(dfn):
                os.remove(dfn)
            os.rename(self.baseFilename, dfn)
        if not self.delay:
            self.stream = self._open()


def configure_logging(log_directory, log_file_prefix, log_when, log_interval, log_backup_count):
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

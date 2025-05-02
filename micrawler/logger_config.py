import os
import sys
import logging
from logging.handlers import TimedRotatingFileHandler

def get_application_path():
    """获取应用程序路径，兼容打包后的EXE文件"""
    if getattr(sys, 'frozen', False):
        # 如果是打包后的EXE文件
        return os.path.dirname(sys.executable)
    else:
        # 如果是开发环境
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def configure_logging(log_directory, log_file_prefix, log_when, log_interval, log_backup_count):
    """配置日志记录"""
    # 获取应用程序路径
    app_path = get_application_path()
    
    # 创建日志目录（相对于应用程序路径）
    log_dir = os.path.join(app_path, log_directory)
    os.makedirs(log_dir, exist_ok=True)
    
    # 设置日志文件路径
    log_file = os.path.join(log_dir, f"{log_file_prefix}.log")
    
    # 配置日志记录器
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    
    # 创建文件处理器（按时间轮转）
    file_handler = TimedRotatingFileHandler(
        log_file,
        when=log_when,
        interval=log_interval,
        backupCount=log_backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
    file_handler.setFormatter(file_format)
    
    # 添加处理器到记录器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    logging.info(f"日志配置完成，日志文件：{log_file}")
    return True


def log_video_download(video_id, title, status):
    """记录视频下载信息"""
    status_text = "成功" if status else "开始"
    logging.info(f"视频下载 [{status_text}] - ID: {video_id} - 标题: {title}")


def log_download_error(video_id, error_type, error_message):
    """记录下载错误信息"""
    logging.error(f"视频 {video_id} {error_type}: {error_message}")

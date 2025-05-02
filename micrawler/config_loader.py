import os
import sys
import yaml

def get_application_path():
    """获取应用程序路径，兼容打包后的EXE文件"""
    if getattr(sys, 'frozen', False):
        # 如果是打包后的EXE文件
        return os.path.dirname(sys.executable)
    else:
        # 如果是开发环境
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_config(config_path):
    """加载配置文件"""
    # 获取应用程序路径
    app_path = get_application_path()
    
    # 尝试从应用程序目录加载配置文件
    absolute_config_path = os.path.join(app_path, os.path.basename(config_path))
    
    # 如果应用程序目录下没有配置文件，则尝试从相对路径加载
    if not os.path.exists(absolute_config_path):
        absolute_config_path = os.path.join(app_path, config_path)
    
    # 如果仍然找不到配置文件，则使用默认配置
    if not os.path.exists(absolute_config_path):
        print(f"警告：找不到配置文件 {absolute_config_path}，将使用默认配置")
        return get_default_config()
    
    try:
        with open(absolute_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print(f"已加载配置文件：{absolute_config_path}")
        return config
    except Exception as e:
        print(f"加载配置文件时出错：{e}，将使用默认配置")
        return get_default_config()

def get_default_config():
    """获取默认配置"""
    return {
        'program_info': {
            'name': 'Hanime Crawler',
            'version': '1.0.0',
            'author': 'S^^K'
        },
        'database': {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': 'root',
            'database': 'hanime'
        },
        'crawler': {
            'li_default_url': 'https://hanime1.me/comic?page=',
            'motion_default_url_2d': 'https://hanime1.me/browse?page=',
            'motion_default_url_3d': 'https://hanime1.me/browse/3d?page=',
            'download_path': 'downloads',
            'max_retries': 3
        },
        'log_directory': 'logs',
        'log_file_prefix': 'hanime_crawler',
        'log_when': 'D',
        'log_interval': 1,
        'log_backup_count': 7
    }

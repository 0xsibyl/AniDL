import signal
import json
import os
import time
from colorama import init, Fore, Back, Style
from micrawler.config_loader import load_config
from micrawler.crawler import li_crawling, motion_crawling
from micrawler.logger_config import configure_logging
from micrawler.signal_handler import signal_handler

# 初始化colorama
init(autoreset=True)

# 设置信号处理器
signal.signal(signal.SIGINT, signal_handler)

# 加载配置文件
config = load_config('micrawler/config.yaml')

# 全局配置变量
start_page = 1  # 默认从第一页开始爬取
default_li_url = config['crawler']['li_default_url']
default_2d_url = config['crawler']['motion_default_url_2d']
default_3d_url = config['crawler']['motion_default_url_3d']
crawler_type = None
base_url = None
use_json_db = False  # 是否使用JSON作为数据库
# 在main.py文件中添加以下函数
def get_application_path():
    """获取应用程序路径，兼容打包后的EXE文件"""
    if getattr(sys, 'frozen', False):
        # 如果是打包后的EXE文件
        return os.path.dirname(sys.executable)
    else:
        # 如果是开发环境
        return os.path.dirname(os.path.abspath(__file__))

# 然后修改json_db_path的定义
app_path = get_application_path()
json_db_path = os.path.join(app_path, 'data', 'video_database.json')

def get_display_length(text):
    """计算字符串显示长度，中文字符算2个长度"""
    length = 0
    for char in text:
        if '\u4e00' <= char <= '\u9fff':  # 中文字符范围
            length += 2
        else:
            length += 1
    return length


def print_banner():
    """打印程序横幅"""
    banner_width = 70
    banner = f"""
{Fore.CYAN}{Style.BRIGHT}╔{'═' * (banner_width - 2)}╗
║{' ' * (banner_width - 2)}║
║  {Fore.YELLOW}  _    _                _                {Fore.CYAN}  ___                    {Fore.CYAN}║
║  {Fore.YELLOW} | |  | |              (_)               {Fore.CYAN} / _ \\                   {Fore.CYAN}║
║  {Fore.YELLOW} | |__| | __ _ _ __   _ _ _ __ ___   ___ {Fore.CYAN}| | | |_ __ __ _ _      {Fore.CYAN}║
║  {Fore.YELLOW} |  __  |/ _` | '_ \\ | | | '_ ` _ \\ / _ \\{Fore.CYAN}| | | | '__/ _` | |     {Fore.CYAN}║
║  {Fore.YELLOW} | |  | | (_| | | | || | | | | | | |  __/{Fore.CYAN}| |_| | | | (_| | |     {Fore.CYAN}║
║  {Fore.YELLOW} |_|  |_|\\__,_|_| |_|/ |_|_| |_| |_|\\___|{Fore.CYAN} \\___/|_|  \\__,_|_|     {Fore.CYAN}║
║  {Fore.YELLOW}                   _/ |                  {Fore.CYAN}                         {Fore.CYAN}║
║  {Fore.YELLOW}                  |__/                   {Fore.CYAN}                         {Fore.CYAN}║
║{' ' * (banner_width - 2)}║
║  {Fore.WHITE}版本: {Fore.GREEN}{config['program_info']['version']}{' ' * (banner_width - 15 - len(config['program_info']['version']))}║
║  {Fore.WHITE}作者: {Fore.GREEN}{config['program_info']['author']}{' ' * (banner_width - 15 - len(config['program_info']['author']))}║
║{' ' * (banner_width - 2)}║
╚{'═' * (banner_width - 2)}╝{Style.RESET_ALL}
"""
    print(banner)


def print_menu(selected=None):
    """打印菜单，高亮选中的选项"""
    menu_items = [
        "选择爬取类型",
        "设置起始页",
        "数据存储方式",
        "开始爬取",
        "退出程序"
    ]
    
    menu_width = 70
    
    print(f"\n{Fore.CYAN}╔{'═' * (menu_width - 2)}╗{Style.RESET_ALL}")
    print(f"{Fore.CYAN}║ {Fore.YELLOW}{Style.BRIGHT}主菜单{Style.RESET_ALL}{Fore.CYAN}{' ' * (menu_width - 10)}║{Style.RESET_ALL}")
    print(f"{Fore.CYAN}╠{'═' * (menu_width - 2)}╣{Style.RESET_ALL}")
    
    for i, item in enumerate(menu_items, 1):
        item_display_len = get_display_length(item)
        if selected == i:
            print(f"{Fore.CYAN}║ {Back.BLUE}{Fore.WHITE}{Style.BRIGHT} {i} {Style.RESET_ALL} {Back.BLUE}{Fore.WHITE}{Style.BRIGHT}{item}{' ' * (menu_width - item_display_len - 7)}{Style.RESET_ALL}{Fore.CYAN}║{Style.RESET_ALL}")
        else:
            print(f"{Fore.CYAN}║ {Fore.GREEN} {i} {Style.RESET_ALL} {Fore.WHITE}{item}{' ' * (menu_width - item_display_len - 7)}{Fore.CYAN}║{Style.RESET_ALL}")
    
    print(f"{Fore.CYAN}╠{'═' * (menu_width - 2)}╣{Style.RESET_ALL}")
    
    # 显示当前配置状态
    crawler_status = f"{crawler_type}" if crawler_type else "未设置"
    if crawler_type == 'li':
        crawler_status = "里番"
    elif crawler_type == '2d':
        crawler_status = "2.5D 动画"
    elif crawler_type == '3d':
        crawler_status = "3D 动画"
    
    storage_status = "JSON文件" if use_json_db else "数据库"
    
    print(f"{Fore.CYAN}║ {Fore.YELLOW}当前配置:{' ' * (menu_width - 12)}║{Style.RESET_ALL}")
    
    crawler_display_len = get_display_length(crawler_status)
    print(f"{Fore.CYAN}║ {Fore.WHITE}爬取类型: {Fore.GREEN}{crawler_status}{' ' * (menu_width - crawler_display_len - 14)}║{Style.RESET_ALL}")
    
    page_display_len = get_display_length(str(start_page))
    print(f"{Fore.CYAN}║ {Fore.WHITE}起始页码: {Fore.GREEN}{start_page}{' ' * (menu_width - page_display_len - 14)}║{Style.RESET_ALL}")
    
    storage_display_len = get_display_length(storage_status)
    print(f"{Fore.CYAN}║ {Fore.WHITE}存储方式: {Fore.GREEN}{storage_status}{' ' * (menu_width - storage_display_len - 14)}║{Style.RESET_ALL}")
    
    print(f"{Fore.CYAN}╚{'═' * (menu_width - 2)}╝{Style.RESET_ALL}")


def print_submenu(title, options, selected=None):
    """打印子菜单"""
    menu_width = 70
    
    print(f"\n{Fore.CYAN}╔{'═' * (menu_width - 2)}╗{Style.RESET_ALL}")
    
    title_display_len = get_display_length(title)
    print(f"{Fore.CYAN}║ {Fore.YELLOW}{Style.BRIGHT}{title}{' ' * (menu_width - title_display_len - 4)}║{Style.RESET_ALL}")
    
    print(f"{Fore.CYAN}╠{'═' * (menu_width - 2)}╣{Style.RESET_ALL}")
    
    for i, option in enumerate(options, 1):
        option_display_len = get_display_length(option)
        if selected == i:
            print(f"{Fore.CYAN}║ {Back.BLUE}{Fore.WHITE}{Style.BRIGHT} {i} {Style.RESET_ALL} {Back.BLUE}{Fore.WHITE}{Style.BRIGHT}{option}{' ' * (menu_width - option_display_len - 7)}{Style.RESET_ALL}{Fore.CYAN}║{Style.RESET_ALL}")
        else:
            print(f"{Fore.CYAN}║ {Fore.GREEN} {i} {Style.RESET_ALL} {Fore.WHITE}{option}{' ' * (menu_width - option_display_len - 7)}{Fore.CYAN}║{Style.RESET_ALL}")
    
    print(f"{Fore.CYAN}╚{'═' * (menu_width - 2)}╝{Style.RESET_ALL}")


def print_status(message, status_type="info"):
    """打印状态信息"""
    if status_type == "success":
        color = Fore.GREEN
        icon = "✓"
    elif status_type == "error":
        color = Fore.RED
        icon = "✗"
    elif status_type == "warning":
        color = Fore.YELLOW
        icon = "!"
    else:
        color = Fore.BLUE
        icon = "i"
    
    print(f"{color}[{icon}] {message}{Style.RESET_ALL}")


def print_config_panel(title, config_items):
    """打印配置面板"""
    menu_width = 70
    
    print(f"\n{Fore.CYAN}╔{'═' * (menu_width - 2)}╗{Style.RESET_ALL}")
    
    title_display_len = get_display_length(title)
    print(f"{Fore.CYAN}║ {Fore.YELLOW}{Style.BRIGHT}{title}{' ' * (menu_width - title_display_len - 4)}║{Style.RESET_ALL}")
    
    print(f"{Fore.CYAN}╠{'═' * (menu_width - 2)}╣{Style.RESET_ALL}")
    
    for label, value in config_items:
        label_display_len = get_display_length(label)
        value_display_len = get_display_length(str(value))
        padding = menu_width - label_display_len - value_display_len - 7  # 7 是固定的格式字符数
        print(f"{Fore.CYAN}║ {Fore.WHITE}{label}: {Fore.GREEN}{value}{' ' * padding}║{Style.RESET_ALL}")
    
    print(f"{Fore.CYAN}╚{'═' * (menu_width - 2)}╝{Style.RESET_ALL}")


def load_json_db():
    """加载JSON数据库"""
    if not os.path.exists(json_db_path):
        # 确保目录存在
        os.makedirs(os.path.dirname(json_db_path), exist_ok=True)
        return {}
    
    try:
        with open(json_db_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def save_json_db(data):
    """保存数据到JSON数据库"""
    # 确保目录存在
    os.makedirs(os.path.dirname(json_db_path), exist_ok=True)
    
    try:
        with open(json_db_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print_status(f"保存JSON数据库时出错: {e}", "error")
        return False


def main():
    global start_page, base_url, crawler_type, use_json_db
    
    # 默认开启日志记录
    logging_enabled = configure_logging(
        config['log_directory'],
        config['log_file_prefix'],
        config['log_when'],
        config['log_interval'],
        config['log_backup_count']
    )

    # 初始显示菜单
    print_banner()
    show_menu = True
    
    while True:
        if show_menu:
            print_menu()
        
        choice = input(f"\n{Fore.YELLOW}请选择操作 (1-5): {Style.RESET_ALL}").strip()
        show_menu = False  # 默认不再显示菜单，除非特定情况

        if choice == '1':
            crawler_options = ["里番", "2.5D 动画", "3D 动画"]
            print_submenu("选择爬取类型", crawler_options)
            crawler_choice = input(f"{Fore.YELLOW}请选择 (1-3): {Style.RESET_ALL}").strip()
            
            if crawler_choice == '1':
                base_url = default_li_url
                crawler_type = 'li'
                print_status("已选择: 里番", "success")
            elif crawler_choice == '2':
                base_url = default_2d_url
                crawler_type = '2d'
                print_status("已选择: 2.5D 动画", "success")
            elif crawler_choice == '3':
                base_url = default_3d_url
                crawler_type = '3d'
                print_status("已选择: 3D 动画", "success")
            else:
                print_status("无效选项，请输入1、2或3", "error")
            
            show_menu = True  # 选择完成后显示主菜单
            
        elif choice == '2':
            try:
                print_submenu("设置起始页", [])
                
                start_page = int(input(f"{Fore.YELLOW}请输入起始页码: {Style.RESET_ALL}").strip())
                if start_page < 1:
                    raise ValueError("起始页码必须大于0")
                print_status(f"已设置起始页: {start_page}", "success")
            except ValueError as ve:
                print_status(f"无效输入: {ve}", "error")
            
            show_menu = True  # 设置完成后显示主菜单
            
        elif choice == '3':
            storage_options = ["数据库", "JSON文件"]
            print_submenu("选择数据存储方式", storage_options)
            storage_choice = input(f"{Fore.YELLOW}请选择 (1-2): {Style.RESET_ALL}").strip()
            
            if storage_choice == '1':
                use_json_db = False
                print_status("已选择: 使用数据库存储", "success")
            elif storage_choice == '2':
                use_json_db = True
                print_status("已选择: 使用JSON文件存储", "success")
                # 显示当前JSON数据库状态
                json_db = load_json_db()
                video_count = len(json_db)
                print_status(f"当前JSON数据库中有 {video_count} 条视频记录", "info")
            else:
                print_status("无效选项，请输入1或2", "error")
            
            show_menu = True  # 选择完成后显示主菜单
            
        elif choice == '4':
            if crawler_type is None:
                print_status("请先选择爬取类型", "warning")
                show_menu = True  # 需要先选择爬取类型，重新显示菜单
                continue

            # 使用新的配置面板函数
            crawler_display = "里番" if crawler_type == 'li' else "2.5D 动画" if crawler_type == '2d' else "3D 动画"
            storage_display = "JSON文件" if use_json_db else "数据库"
            download_path = config['crawler']['download_path']
            
            config_items = [
                ("爬取类型", crawler_display),
                ("起始页码", start_page),
                ("存储方式", storage_display),
                ("下载路径", download_path)
            ]
            
            print_config_panel("爬取任务配置", config_items)
            
            confirm = input(f"{Fore.YELLOW}确认开始爬取? (y/n): {Style.RESET_ALL}").strip().lower()
            if confirm != 'y':
                print_status("已取消爬取", "info")
                show_menu = True
                continue
            
            # 显示加载动画
            print_status("正在准备爬取任务...", "info")
            for _ in range(3):
                print(f"{Fore.CYAN}.", end="", flush=True)
                time.sleep(0.3)
            print(Style.RESET_ALL)
            
            # 加载现有的JSON数据库（如果使用JSON）
            json_db = load_json_db() if use_json_db else None
            
            if crawler_type == 'li':
                li_crawling(base_url, start_page, config['database'], config['crawler'], False, None, False, use_json_db, json_db, json_db_path)
            else:
                motion_crawling(base_url, start_page, config['database'], config['crawler'], False, None, crawler_type, False, use_json_db, json_db, json_db_path)
            
            print_status("爬取任务完成", "success")
            show_menu = True  # 爬取完成后重新显示菜单
            
        elif choice == '5':
            print_submenu("感谢使用", [])
            print_status("程序已退出", "info")
            break
        else:
            print_status("无效选项，请输入1-5之间的数字", "error")
            show_menu = True  # 输入无效时重新显示菜单


if __name__ == "__main__":
    main()
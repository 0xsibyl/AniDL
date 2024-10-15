
import signal
from micrawler.config_loader import load_config
from micrawler.crawler import li_crawling, motion_crawling
from micrawler.logger_config import configure_logging
from micrawler.signal_handler import signal_handler

# 设置信号处理器
signal.signal(signal.SIGINT, signal_handler)

# 加载配置文件
config = load_config('micrawler/config.yaml')

# 全局配置变量
logging_enabled = False
write_to_db = False
write_to_es = False
write_to_file = False
start_page = 1  # 默认从第一页开始爬取
default_li_url = config['crawler']['li_default_url']
default_2d_url = config['crawler']['motion_default_url_2d']
default_3d_url = config['crawler']['motion_default_url_3d']
crawler_type = None
base_url = None


def main():
    global logging_enabled, write_to_db, write_to_es, write_to_file, start_page, base_url, crawler_type

    while True:
        print("\n" + "=" * 60)
        print(f"{config['program_info']['name']} - 版本 {config['program_info']['version']}")
        print(f"作者: {config['program_info']['author']}")
        print("=" * 60)
        print("1. 是否开启日志记录")
        print("2. 是否把 video_id 写入数据库")
        print("3. 是否把数据写入 Elasticsearch")
        print("4. 从第几页开始爬取")
        print("5. 选择爬取类型 (1: 里番, 2: 2.5D 动画, 3: 3D 动画)")
        print("6. 开始爬取")
        print("7. 退出")
        print("8. 将 JSON 数据写入文件")
        choice = input("请选择 (1-8): ").strip()

        if choice == '1':
            logging_enabled = configure_logging(
                config['log_directory'],
                config['log_file_prefix'],
                config['log_when'],
                config['log_interval'],
                config['log_backup_count']
            )
        elif choice == '2':
            write_to_db = input("是否把 video_id 写入数据库 (y/n): ").strip().lower() == 'y'
        elif choice == '3':
            write_to_es = input("是否把数据写入 Elasticsearch (y/n): ").strip().lower() == 'y'
        elif choice == '4':
            try:
                start_page = int(input("从第几页开始爬取: ").strip())
                if start_page < 1:
                    raise ValueError("起始页码必须大于0")
            except ValueError as ve:
                print(f"无效输入: {ve}")
        elif choice == '5':
            crawler_choice = input("选择爬取类型 (1: 里番, 2: 2.5D 动画, 3: 3D 动画): ").strip()
            if crawler_choice == '1':
                base_url = default_li_url
                crawler_type = 'li'
            elif crawler_choice == '2':
                base_url = default_2d_url
                crawler_type = '2d'
            elif crawler_choice == '3':
                base_url = default_3d_url
                crawler_type = '3d'
            else:
                print("无效选项，请输入1、2或3。")
        elif choice == '6':
            if crawler_type is None:
                print("请先选择爬取类型。")
                continue

            if crawler_type == 'li':
                li_crawling(base_url, start_page, config['database'], config['crawler'], write_to_es, None,
                            write_to_file)
            else:
                motion_crawling(base_url, start_page, config['database'], config['crawler'], write_to_es, None,
                                crawler_type, write_to_file)

        elif choice == '7':
            print("退出程序.")
            break
        elif choice == '8':
            write_to_file = input("是否将 JSON 数据写入文件 (y/n): ").strip().lower() == 'y'
        else:
            print("无效选项，请输入1-8之间的数字。")


if __name__ == "__main__":
    main()

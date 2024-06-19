import json
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from urllib.parse import urlparse, parse_qs
from time import time
import signal
import sys
import pymysql
import requests
from DrissionPage import ChromiumPage
from DrissionPage._configs.chromium_options import ChromiumOptions
from colorama import Fore, Style, init
from elasticsearch import Elasticsearch
from prettytable import PrettyTable
from pymysql import MySQLError, OperationalError, InterfaceError, IntegrityError
from tqdm import tqdm
import yaml  # 导入 PyYAML

# 初始化 colorama
init(autoreset=True)
# 加载配置文件
with open('config.yaml', 'r', encoding='utf-8') as file:
    config = yaml.safe_load(file)
# 解析配置信息
log_directory = config['log_directory']
log_file_prefix = config['log_file_prefix']
null_log_file_prefix = config['null_log_file_prefix']
log_max_bytes = config['log_max_bytes']
log_backup_count = config['log_backup_count']
database_config = config['database']
es_config = config['elasticsearch']
crawler_config = config['crawler']
program_info = config['program_info']

# 获取当前日期
current_date = datetime.now().strftime('%Y-%m-%d')

# 创建日志目录，如果不存在则创建
os.makedirs(log_directory, exist_ok=True)

# 定义日志文件路径
log_file = os.path.join(log_directory, f'{current_date}_{log_file_prefix}.log')
null_log_file = os.path.join(log_directory, f'{current_date}_{null_log_file_prefix}.log')

# 全局配置变量
logging_enabled = False
write_to_db = False
write_to_es = False
start_page = crawler_config['start_page']
default_url = crawler_config['default_url']

# 程序信息
PROGRAM_NAME = program_info['name']
PROGRAM_VERSION = program_info['version']
AUTHOR = program_info['author']


# 设置信号处理器以便可以通过Ctrl+C来停止程序
def signal_handler(sig, frame):
    print('\n你按下了 Ctrl+C! 程序即将终止.')
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


# 设置日志配置
def configure_logging():
    global logging_enabled
    print("\n" + "=" * 60)
    print("日志记录设置")
    print("=" * 60)
    logging_enabled_input = input("是否开启日志记录 (y/n): ").strip().lower()
    if logging_enabled_input == 'y':
        logging_enabled = True
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),  # 输出到控制台
                RotatingFileHandler(log_file, maxBytes=log_max_bytes, backupCount=log_backup_count)  # 输出到文件
            ]
        )
        logging.info("日志记录已启动.")
    print("=" * 60 + "\n")


# 配置 Elasticsearch 客户端
es = Elasticsearch(
    es_config['host']
)

# 配置 ChromiumPage
co = ChromiumOptions().auto_port()
page = ChromiumPage(co)
page.set.load_mode.eager()
page2 = ChromiumPage(co)
page2.set.load_mode.eager()
page3 = ChromiumPage(co)
page3.set.load_mode.eager()

# 创建一个漂亮表格来展示数据
table = PrettyTable(["番剧名称", "番剧URL", "图片地址"])


def log_message(message):
    if logging_enabled:
        logging.info(message)


def check_and_insert_vide_id(cursor, vide_id):
    try:
        cursor.execute("SELECT COUNT(1) FROM sys_mi WHERE vide_id = %s", (vide_id,))
        if cursor.fetchone()[0]:
            print(f"vide_id {vide_id} 已存在于数据库中，跳过下载。")
            return True
        else:
            return False
    except MySQLError as e:
        print(f"数据库操作时发生错误: {e}")
        log_message(f"数据库操作时发生错误: {e}")
        return True


def insert_vide_id(cursor, vide_id, error_code=1):
    try:
        cursor.execute("INSERT INTO sys_mi (vide_id, error_vide) VALUES (%s, %s)", (vide_id, error_code))
        print(f"vide_id {vide_id} 已插入到数据库中。")
    except MySQLError as e:
        print(f"插入 vide_id 时发生错误: {e}")
        log_message(f"插入 vide_id 时发生错误: {e}")


def log_error_to_db(cursor, vide_id, url, error_message):
    try:
        cursor.execute(
            "INSERT INTO error_log (vide_id, url, error_message) VALUES (%s, %s, %s)",
            (vide_id, url, error_message)
        )
        print(f"记录错误信息到数据库: {error_message}")
    except MySQLError as e:
        print(f"记录错误信息时发生错误: {e}")
        log_message(f"记录错误信息时发生错误: {e}")


def download_video(k, title, vide_id, max_retries=crawler_config['max_retries']):
    save_data = f"{title}{vide_id}.mp4"
    save_path = os.path.join(crawler_config['download_path'], save_data)

    try:
        connection = pymysql.connect(
            host=database_config['host'],
            database=database_config['name'],
            user=database_config['user'],
            password=database_config['password']
        )
        cursor = connection.cursor()

        if check_and_insert_vide_id(cursor, vide_id):
            cursor.close()
            connection.close()
            return

    except (OperationalError, InterfaceError, IntegrityError) as e:
        print(f"数据库连接或操作时发生错误: {e}")
        log_message(f"数据库连接或操作时发生错误: {e}")
        return

    retries = 0
    while retries < max_retries:
        start_time = time()
        try:
            response = requests.get(k.link, stream=True, timeout=10)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP 错误: {e}")
            log_message(f"HTTP 错误: {e}")
            retries += 1
            continue
        except requests.exceptions.ConnectionError as e:
            print(f"连接错误: {e}")
            log_message(f"连接错误: {e}")
            retries += 1
            continue
        except requests.exceptions.Timeout as e:
            print(f"请求超时: {e}")
            log_message(f"请求超时: {e}")
            retries += 1
            continue
        except requests.exceptions.RequestException as e:
            print(f"请求异常: {e}")
            log_message(f"请求异常: {e}")
            retries += 1
            continue

        total_size = int(response.headers.get('content-length', 0))

        try:
            with open(save_path, 'wb') as file, tqdm(
                    desc="Downloading",
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                    ncols=100,
            ) as bar:
                for data in response.iter_content(chunk_size=1024):
                    file.write(data)
                    bar.update(len(data))

                    elapsed_time = time() - start_time
                    if elapsed_time > 1200:
                        print(f"下载时间超过 20 分钟，重新下载...")
                        log_message(f"下载时间超过 20 分钟，重新下载...")
                        file.close()
                        os.remove(save_path)
                        retries += 1
                        break
                else:
                    print(f"视频已成功下载并保存到 {save_path}")
                    log_message(f"视频已成功下载并保存到 {save_path}")

                    try:
                        if not check_and_insert_vide_id(cursor, vide_id):
                            insert_vide_id(cursor, vide_id)
                            connection.commit()
                    except (OperationalError, InterfaceError, IntegrityError) as e:
                        print(f"数据库连接或操作时发生错误: {e}")
                        log_message(f"数据库连接或操作时发生错误: {e}")

                    cursor.close()
                    connection.close()
                    return
        except IOError as e:

            error_message = f"文件写入错误: {e}"

            print(error_message)

            log_message(error_message)

            # Check if the error has already been logged

            try:

                cursor.execute("SELECT COUNT(1) FROM sys_mi WHERE vide_id = %s AND error_vide = 3", (vide_id,))

                if cursor.fetchone()[0]:

                    print(f"vide_id {vide_id} 的文件写入错误已存在于数据库中，跳过记录。")

                else:

                    cursor.execute("INSERT INTO sys_mi (vide_id, error_vide) VALUES (%s, 3)", (vide_id,))

                    connection.commit()

                    print(f"记录文件写入错误到数据库: {error_message}")

            except MySQLError as db_error:

                print(f"记录文件写入错误到数据库时发生错误: {db_error}")

                log_message(f"记录文件写入错误到数据库时发生错误: {db_error}")

            retries += 1


def start_crawling():
    global start_page
    page_number = start_page

    while True:
        url = f'{base_url}&page={page_number}'
        log_message(f'正在访问: {url}')

        page.get(url)
        div1 = page.ele('#home-rows-wrapper')
        if div1:
            div2 = div1.ele('.home-rows-videos-wrapper')
            if div2:
                data = div2.eles('tag:a')
                if not data:
                    log_message(f'第 {page_number} 页没有数据，可能已经是最后一页了。')
                    break

                for i in data:
                    try:
                        img = i('t:img').attr('src')
                        title = i.text
                        link = i.href
                        page2.get(link)
                        hanime1_div = page2.ele('#content-div').ele('#player-div-wrapper')
                        hanime1_div2 = hanime1_div.eles('.video-details-wrapper video-tags-wrapper')
                        author = page2.ele('#content-div').ele(
                            '.video-details-wrapper desktop-inline-mobile-block').ele(
                            '#video-artist-name')
                        print(f'{Fore.YELLOW}作者: {author.text}')

                        for tag in hanime1_div2:
                            print(f'{Fore.YELLOW}番剧标签: {tag.texts()}')

                        parsed_url = urlparse(link)
                        query_params = parse_qs(parsed_url.query)
                        v_value = query_params.get('v', [''])[0]
                        page3.get('https://hanime1.me/download?v=' + v_value)
                        download_url = page3.ele('tag:table').eles('tag:a')  # 我改了一下这里
                        vide_data = {}
                        for k in download_url:
                            if "1080p" in k.link:
                                vide_data['1080P'] = k.link
                                print(f'{Fore.YELLOW}视频下载信息: {vide_data}')
                                download_video(k, title, v_value)
                                break
                            if "720p" in k.link:
                                vide_data['720P'] = k.link
                                print(f'{Fore.YELLOW}视频下载信息: {vide_data}')
                                download_video(k, title, v_value)
                                break
                            if "480p" in k.link:
                                vide_data['480'] = k.link
                                print(f'{Fore.YELLOW}视频下载信息: {vide_data}')
                                download_video(k, title, v_value)
                                break

                        if not vide_data:
                            connection = pymysql.connect(
                                host=database_config['host'],
                                database=database_config['name'],
                                user=database_config['user'],
                                password=database_config['password']
                            )
                            cursor = connection.cursor()
                            print(f"没有找到合适的下载链接，vide_id: {v_value} 插入数据库并记录日志。")
                            try:
                                log_error_to_db(cursor, v_value, link, "没有找到合适的下载链接")
                                connection.commit()
                            except (OperationalError, InterfaceError, IntegrityError) as e:
                                print(f"数据库连接或操作时发生错误: {e}")
                                log_message(f"数据库连接或操作时发生错误: {e}")
                            cursor.close()
                            connection.close()

                        full_title = f"{title} [v={v_value}]"
                        table.add_row([full_title, link, img])

                        print(f'{Fore.GREEN}番剧名称: {full_title}')
                        print(f'{Fore.BLUE}番剧URL: {link}')
                        print(f'{Fore.RED}图片地址: {img}')
                        print(Style.RESET_ALL + '-' * 50)

                        json_data = json.dumps(
                            {"番剧名称": full_title, "作者": author.text, "番剧URL": link, "图片地址": img,
                             "下载地址": vide_data},
                            ensure_ascii=False, indent=5)
                        print(json_data)

                        crawl_time = datetime.now().isoformat()

                        es_data = {
                            'crawl_time': crawl_time,
                            'title': full_title,
                            'url': link,
                            'image_url': img
                        }

                        if write_to_es:
                            es.index(index='anime_data', body=es_data)
                            log_message(f'数据已写入 Elasticsearch: {es_data}')

                    except Exception as e:
                        print(f"获取数据时出错: {e}")
                        log_message(f'获取数据时出错: {e}')
                        try:
                            connection = pymysql.connect(
                                host=database_config['host'],
                                database=database_config['name'],
                                user=database_config['user'],
                                password=database_config['password']
                            )
                            cursor = connection.cursor()
                            log_error_to_db(cursor, v_value, link, str(e))
                            connection.commit()
                            cursor.close()
                            connection.close()
                        except (OperationalError, InterfaceError, IntegrityError) as e:
                            print(f"数据库连接或操作时发生错误: {e}")
                            log_message(f"数据库连接或操作时发生错误: {e}")

            else:
                log_message('找不到 .home-rows-videos-wrapper，可能已经是最后一页了。')
                break
        else:
            log_message('找不到 #home-rows-wrapper，可能已经是最后一页了。')
            break

        page_number += 1

    print(table)
    page.quit()
    page2.quit()
    page3.quit()


def main():
    global write_to_db, write_to_es, start_page, default_url, base_url

    while True:
        print("\n" + "=" * 60)
        print(f"{PROGRAM_NAME} - 版本 {PROGRAM_VERSION}")
        print(f"作者: {AUTHOR}")
        print("=" * 60)
        print("1. 是否开启日志记录")
        print("2. 是否把 vide_id 写入数据库")
        print("3. 是否把数据写入 Elasticsearch")
        print("4. 从第几页开始爬取")
        print("5. 设置爬取的 URL")
        print("6. 开始爬取")
        print("7. 退出")
        choice = input("请选择 (1-7): ").strip()

        if choice == '1':
            configure_logging()
        elif choice == '2':
            write_to_db = input("是否把 vide_id 写入数据库 (y/n): ").strip().lower() == 'y'
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
            custom_url = input(f"使用默认 URL（{default_url}）？ (y/n): ").strip().lower()
            if custom_url == 'y':
                base_url = default_url
            else:
                base_url = input("请输入爬取的 URL: ").strip()
        elif choice == '6':
            print("开始爬取***************************************************************************")
            start_crawling()
        elif choice == '7':
            print("退出程序.")
            break
        else:
            print("无效选项，请输入1-7之间的数字。")


if __name__ == "__main__":
    main()

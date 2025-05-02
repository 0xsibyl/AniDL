import logging
import os
import requests
from tqdm import tqdm
import time
from micrawler.database_utils import DatabaseManager  # 添加这一行导入语句

def download_video(download_link, save_path, vide_id, max_retries=3, use_json_db=False):
    # 初始化日志
    logging.basicConfig(level=logging.INFO)

    # 只有在不使用JSON数据库时才检查数据库状态
    if not use_json_db:
        try:
            # 检查视频是否已经下载完成（状态为 1）
            db_manager = DatabaseManager()
            if db_manager.check_video(vide_id, 1):  # 如果状态为 1，表示已经下载完成
                print(f"视频 {vide_id} 已经下载完成，跳过下载。")
                return True
        except Exception as e:
            logging.error(f"检查数据库时出错: {e}")
            # 继续执行下载，不因数据库错误而中断
    
    # 确保目录存在
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    retries = 0
    while retries < max_retries:
        try:
            # 检查文件是否部分下载过，获取已下载的字节数
            if os.path.exists(save_path):
                file_size = os.path.getsize(save_path)
                if file_size > 0:
                    resume_header = {'Range': f'bytes={file_size}-'}
                else:
                    # 如果文件存在但大小为0，删除它并重新下载
                    os.remove(save_path)
                    resume_header = {}
            else:
                resume_header = {}

            # 发起请求，带上 Range 头实现断点续传
            try:
                response = requests.get(download_link, headers=resume_header, stream=True, timeout=10)
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 416:
                    # 处理 416 Range Not Satisfiable 错误
                    print(f"收到 416 错误，尝试从头开始下载...")
                    # 如果文件存在，先检查是否已完整下载
                    if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                        # 尝试获取文件大小信息
                        head_response = requests.head(download_link, timeout=10)
                        if 'content-length' in head_response.headers:
                            remote_size = int(head_response.headers['content-length'])
                            local_size = os.path.getsize(save_path)
                            if local_size >= remote_size:
                                print(f"文件 {vide_id} 已经完整下载 (本地: {local_size}, 远程: {remote_size})。")
                                return True
                    
                    # 删除可能损坏的文件并重新下载
                    if os.path.exists(save_path):
                        os.remove(save_path)
                    response = requests.get(download_link, stream=True, timeout=10)
                    response.raise_for_status()
                else:
                    raise

            content_length = response.headers.get('content-length')
            total_size = int(content_length) if content_length else 0
            downloaded_size = os.path.getsize(save_path) if os.path.exists(save_path) else 0

            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            with open(save_path, 'ab') as file, tqdm(
                    desc="Downloading",
                    total=total_size,
                    initial=downloaded_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                    ncols=100,
            ) as bar:
                for data in response.iter_content(chunk_size=1024):
                    file.write(data)
                    bar.update(len(data))

            # 在进度条完成后打印下载完成信息
            print(f"视频 {vide_id} 已成功下载并保存到 {save_path}")

            # 只有在不使用JSON数据库时才更新数据库状态
            if not use_json_db:
                try:
                    db_manager = DatabaseManager()
                    db_manager.update_video_status(vide_id, 1)
                except Exception as e:
                    logging.error(f"更新数据库状态时出错: {e}")
            
            return True

        except requests.exceptions.RequestException as e:
            print(f"请求错误: {e}")
            logging.error(f"视频 {vide_id} 请求错误: {e}")
            retries += 1
            continue
        except IOError as e:
            print(f"文件写入错误: {e}")
            logging.error(f"视频 {vide_id} 文件写入错误: {e}")
            retries += 1

    # 如果到达这里，说明下载失败
    print(f"视频 {vide_id} 下载失败。")
    logging.error(f"视频 {vide_id} 下载失败。")
    return False
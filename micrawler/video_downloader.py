import logging
import os

from database_utils import DatabaseManager
import requests
from tqdm import tqdm


def download_video(download_link, save_path, vide_id, max_retries=3):
    # 初始化日志
    logging.basicConfig(level=logging.INFO)

    # 检查视频是否已经下载完成（状态为 1）
    db_manager = DatabaseManager()
    if db_manager.check_video(vide_id, 1):  # 如果状态为 1，表示已经下载完成
        print(f"视频 {vide_id} 已经下载完成，跳过下载。")
        return

    retries = 0
    while retries < max_retries:
        try:
            # 检查文件是否部分下载过，获取已下载的字节数
            if os.path.exists(save_path):
                resume_header = {'Range': f'bytes={os.path.getsize(save_path)}-'}
            else:
                resume_header = {}

            # 发起请求，带上 Range 头实现断点续传
            response = requests.get(download_link, headers=resume_header, stream=True, timeout=10)
            response.raise_for_status()

            content_length = response.headers.get('content-length')
            total_size = int(content_length) if content_length else 0
            downloaded_size = os.path.getsize(save_path) if os.path.exists(save_path) else 0

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

            # 更新视频状态为下载完成（1）
            db_manager.update_video_status(vide_id, 1)
            return

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
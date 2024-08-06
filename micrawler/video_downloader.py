import requests
from tqdm import tqdm

from database_utils import DatabaseManager


def download_video(download_link, save_path, vide_id, max_retries):
    # 检查视频是否已经正常插入，且不在错误日志中
    db_manager = DatabaseManager()
    if db_manager.check_video(vide_id, 1):
        print(f"视频 {vide_id} 已经存在，跳过下载。")
        return

    retries = 0
    while retries < max_retries:
        if not db_manager.check_video(vide_id, 2) or retries > 0:
            try:
                response = requests.get(download_link, stream=True, timeout=10)
                response.raise_for_status()
                content_length = response.headers.get('content-length')
                total_size = int(content_length) if content_length else 0

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
                    print(f"视频已成功下载并保存到 {save_path}")

                    # 更新视频状态
                    db_manager.update_video_status(vide_id, 1)
                    return

            except requests.exceptions.RequestException as e:
                print(f"请求错误: {e}")
                retries += 1
                continue
            except IOError as e:
                print(f"文件写入错误: {e}")
                retries += 1
        else:
            print(f"视频 {id} 在错误日志中，开始重新下载。")
            retries += 1

    # 如果到达这里，说明下载失败
    print(f"视频 {id} 下载失败。")

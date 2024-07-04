import os
import requests
from tqdm import tqdm
from database_utils import check_and_insert_vide_id, insert_vide_id, check_error_log


def download_video(download_link, save_path, vide_id, max_retries, cursor, connection):
    # 检查视频是否已经正常插入，且不在错误日志中
    if check_and_insert_vide_id(cursor, vide_id):
        if not check_error_log(cursor, vide_id):
            print(f"视频 {vide_id} 已存在且没有错误日志记录，跳过下载。")
            cursor.close()
            connection.close()
            return
        else:
            print(f"视频 {vide_id} 在错误日志中有记录，重新下载。")

    retries = 0
    while retries < max_retries:
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

                if not check_and_insert_vide_id(cursor, vide_id):
                    insert_vide_id(cursor, vide_id)
                    connection.commit()
                return

        except requests.exceptions.RequestException as e:
            print(f"请求错误: {e}")
            retries += 1
            continue
        except IOError as e:
            print(f"文件写入错误: {e}")
            retries += 1
    print(f"视频 {vide_id} 下载失败。")

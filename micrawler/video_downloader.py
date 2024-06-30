import os
import requests
from tqdm import tqdm
from database_utils import check_and_insert_vide_id, insert_vide_id


def download_video(k, title, vide_id, crawler_config, connection, cursor):
    save_data = f"{title}{vide_id}.mp4"
    save_path = os.path.join(crawler_config['download_path'], save_data)
    max_retries = crawler_config['max_retries']

    if check_and_insert_vide_id(cursor, vide_id):
        cursor.close()
        connection.close()
        return

    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(k.link, stream=True, timeout=10)
            response.raise_for_status()
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError,
                requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
            print(f"请求错误: {e}")
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
                print(f"视频已成功下载并保存到 {save_path}")

                if not check_and_insert_vide_id(cursor, vide_id):
                    insert_vide_id(cursor, vide_id)
                    connection.commit()
                return
        except IOError as e:
            print(f"文件写入错误: {e}")
            retries += 1

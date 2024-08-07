import os
import json
from datetime import datetime


def write_json_to_file(data, directory, max_size=10 * 1024 * 1024):
    date_str = datetime.now().strftime('%Y-%m-%d')
    base_file_name = f"data_{date_str}"
    extension = ".json"
    file_path = os.path.join(directory, base_file_name + extension)
    counter = 0

    while os.path.exists(file_path) and os.path.getsize(file_path) >= max_size:
        counter += 1
        file_path = os.path.join(directory, f"{base_file_name}-{counter:02d}{extension}")

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"数据已写入文件 {file_path}")

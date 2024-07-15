import json
from datetime import datetime


def write_json_to_file(data):
    date_str = datetime.now().strftime('%Y-%m-%d')
    file_name = f"data_{date_str}.json"
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"数据已写入文件 {file_name}")

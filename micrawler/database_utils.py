import pymysql
from pymysql import MySQLError


def connect_to_db(database_config):
    return pymysql.connect(
        host=database_config['host'],
        database=database_config['name'],
        user=database_config['user'],
        password=database_config['password']
    )


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
        return True


def insert_vide_id(cursor, vide_id, error_code=1):
    try:
        cursor.execute("INSERT INTO sys_mi (vide_id, error_vide) VALUES (%s, %s)", (vide_id, 1))
        print(f"vide_id {vide_id} 已插入到数据库中。")
    except MySQLError as e:
        print(f"插入 vide_id 时发生错误: {e}")


def log_error_to_db(cursor, vide_id, url, error_message):
    try:
        if check_error_log(cursor, vide_id):
            pass
        else:
            cursor.execute(
                "INSERT INTO error_log (vide_id, url, error_message) VALUES (%s, %s, %s)",
                (vide_id, url, error_message)
            )
        print(f"记录错误信息到数据库: {error_message}")
    except MySQLError as e:
        print(f"记录错误信息时发生错误: {e}")


def check_error_log(cursor, vide_id):
    try:
        cursor.execute("SELECT COUNT(1) FROM error_log WHERE vide_id = %s", vide_id)
        if cursor.fetchone()[0]:
            print(f"vide_id {vide_id} 已存在于错误数据库中。")
            return True
        else:
            return False
    except MySQLError as e:
        print(f"数据库操作时发生错误: {e}")
        return True


##这个应该是要写删除代码的
def update_video_status(cursor, vide_id):
    try:
        cursor.execute("INSERT INTO sys_mi (vide_id, error_vide) VALUES (%s, %s)", (vide_id, 2))
        print(f"vide_id {vide_id} 已插入到数据库中。")
    except MySQLError as e:
        print(f"插入 vide_id 时发生错误: {e}")


##这个是写入
def insert_vide_id(cursor, id, title, video_url, thumbnail_url, description, tags, status):
    try:
        cursor.execute(
            "INSERT INTO sys_vide (id, title,video_url,thumbnail_url,description,tags,status) VALUES (%s,%s,%s,%s,%s,%s,%s,)",
            (vide_id, 1))
        if cursor.fetchone()[0]:
            print(f"vide_id {vide_id} 已存在于数据库中，跳过下载。")
            return True
        else:
            return False
    except MySQLError as e:
        print(f"数据库操作时发生错误: {e}")
        return True


##这个是检查的是否为下载     0=未下载 1=已下载 2=下载失败
def check_vide_id(cursor, id):
    try:
        cursor.execute("SELECT COUNT(1) FROM sys_vide WHERE id = %s and status = 1", (id))
        if cursor.fetchone()[0]:
            print(f"vide_id {vide_id} 已存在于数据库中，跳过下载。")
            return True
        else:
            return False
    except MySQLError as e:
        print(f"数据库操作时发生错误: {e}")
        return True


def update_video_status(cursor, id, status):
    try:
        cursor.execute("INSERT INTO sys_vide (id, status) VALUES (%s, %s)", (id, status))
        print(f"vide_id {id} 已插入到数据库中。")
    except MySQLError as e:
        print(f"插入 vide_id 时发生错误: {e}")

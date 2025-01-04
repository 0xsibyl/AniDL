import logging

import pymysql
from pymysql import MySQLError
from contextlib import contextmanager
from micrawler.config_loader import load_config


class DatabaseManager:
    def __init__(self, config_file='micrawler/config.yaml'):
        config = load_config(config_file)
        self.database_config = config['database']

    @contextmanager
    def _get_cursor(self):
        connection = pymysql.connect(
            host=self.database_config['host'],
            database=self.database_config['name'],
            user=self.database_config['user'],
            password=self.database_config['password']
        )
        cursor = connection.cursor()
        try:
            yield cursor
            connection.commit()
        except MySQLError as e:
            connection.rollback()
            logging.error(f"数据库操作时发生错误: {e}")
            raise e
        finally:
            cursor.close()
            connection.close()

    def insert_video(self, id, title, video_url, thumbnail_url, description, tags, status):
        with self._get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO sys_vide (id, title, video_url, thumbnail_url, description, tags, status) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (id, title, video_url, thumbnail_url, description, tags, status)
            )
            if cursor.fetchone() and cursor.fetchone()[0]:
                print(f"vide_id {id} 已存在于数据库中，跳过下载。")
                return True
            return False

    def check_video(self, id, status):
        with self._get_cursor() as cursor:
            cursor.execute("SELECT COUNT(1) FROM sys_vide WHERE id = %s and status = %s", (id, status))
            if cursor.fetchone()[0]:
                print(f"vide_id {id} 已存在于数据库中，跳过下载。")
                return True
            return False

    def update_video_status(self, id, status):
        with self._get_cursor() as cursor:
            cursor.execute("UPDATE sys_vide SET status = %s WHERE id = %s", (status, id))
            print(f"vide_id {id} 的状态已更新为 {status}。")

    def check_video_id(self, id):
        try:
            with self._get_cursor() as cursor:
                cursor.execute("SELECT COUNT(1) FROM sys_vide WHERE id = %s", (id))
                if cursor.fetchone()[0]:
                    print(f"vide_id {id} 已存在于数据库中，无需重新插入。")
                    return True
                return False
        except Exception as e:
            logging.error(f"检查视频 {id} 时出错: {e}")
            return False

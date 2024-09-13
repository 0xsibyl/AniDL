from clickhouse_driver import Client


class ClickHouseClient:
    def __init__(self, host='localhost', port=9000, user='default', password='', database='default'):
        self.client = Client(host=host, port=port, user=user, password=password, database=database)

    def insert(self, table, data):
        """
        插入数据
        :param table: 表名
        :param data: 字典格式的数据，key为列名，value为对应的值
        """
        keys = ', '.join(data.keys())
        values_placeholder = ', '.join(['%s'] * len(data))
        values = tuple(data.values())

        insert_sql = f'INSERT INTO {table} ({keys}) VALUES ({values_placeholder})'
        self.client.execute(insert_sql, [values])

    def select(self, table, columns='*', where_clause=None):
        """
        查询数据
        :param table: 表名
        :param columns: 需要查询的列，默认为所有列
        :param where_clause: 查询条件，可选
        :return: 查询结果
        """
        where_sql = f' WHERE {where_clause}' if where_clause else ''
        select_sql = f'SELECT {columns} FROM {table}{where_sql}'

        return self.client.execute(select_sql)

    def update(self, table, data, where_clause):
        """
        更新数据
        :param table: 表名
        :param data: 字典格式的数据，key为列名，value为对应的值
        :param where_clause: 更新条件
        """
        set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
        values = tuple(data.values())

        update_sql = f'UPDATE {table} SET {set_clause} WHERE {where_clause}'
        self.client.execute(update_sql, values)

    def delete(self, table, where_clause):
        """
        删除数据
        :param table: 表名
        :param where_clause: 删除条件
        """
        delete_sql = f'DELETE FROM {table} WHERE {where_clause}'
        self.client.execute(delete_sql)
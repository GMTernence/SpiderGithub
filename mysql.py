import pymysql
from settings import *


class MYSQL:
    # initialize database
    def __init__(self, host=MYSQL_HOST, username=MYSQL_USER, password=MYSQL_PASSWORD, port=MYSQL_PORT,
                 database=MYSQL_DATABASE):
        try:
            self.db = pymysql.connect(host, username, password, database, charset='utf8', port=port)
            self.cursor = self.db.cursor()
        except pymysql.MySQLError as e:
            print('Database Error')
            print(e.args)

    # insert into data
    def insert(self, table, data):
        keys = ','.join(data.keys())
        values = ','.join(['%s']*len(data))
        sql_query = 'INSERT INTO %s (%s) VALUES (%s)' % (table, keys, values)
        try:
            self.cursor.execute(sql_query, tuple(data.values()))
            self.db.commit()
        except pymysql.MySQLError as e:
            print('Database Error')
            print(e.args)
        self.db.rollback()
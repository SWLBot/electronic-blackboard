import unittest
import os,sys
cur_dir = os.path.dirname(__file__)
par_dir = os.path.dirname(cur_dir)
sys.path.append(par_dir)
from mysql import *

class Mysql(unittest.TestCase):
    def test_connect(self):
        with mysql() as db:
            assert db.connect() == 1
    def test_cmd(self):
        with mysql() as db:
            db.connect()
            sql = 'create table test (id int)'
            assert db.cmd(sql) != -1
            sql = 'drop table test'
            assert db.cmd(sql) != -1

    def test_query(self):
        with mysql() as db:
            db.connect()
            sql = 'show tables'
            assert db.query(sql) != -1

    def test_close(self):
        with mysql() as db:
            db.connect()
            db.close()

if __name__ == '__main__':
    unittest.main()

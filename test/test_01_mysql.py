import unittest
import os,sys
cur_dir = os.path.dirname(__file__)
par_dir = os.path.dirname(cur_dir)
sys.path.append(par_dir)
from mysql import *
import pytest

class Mysql(unittest.TestCase):
    @pytest.mark.run(order=3)
    def test_connect(self):
        with mysql() as db:
            self.assertEqual(db.connect(),1)

    @pytest.mark.run(order=4)
    def test_cmd(self):
        with mysql() as db:
            db.connect()
            sql = 'create table test (id int)'
            self.assertNotEqual(db.cmd(sql),-1)
            sql = 'drop table test'
            self.assertNotEqual(db.cmd(sql),-1)

    @pytest.mark.run(order=5)
    def test_query(self):
        with mysql() as db:
            db.connect()
            sql = 'show tables'
            self.assertNotEqual(db.query(sql),-1)

    @pytest.mark.run(order=6)
    def test_close(self):
        with mysql() as db:
            db.connect()
            db.close()

    @pytest.mark.run(order=7)
    def test_to_list(self):
        tup = ((1,),(2,))
        tup2 = ((3,"str"),(4,"test"))
        self.assertTrue(isinstance(to_list(tup),list))
        self.assertTrue(isinstance(to_list(tup2),list))

if __name__ == '__main__':
    unittest.main()

import unittest
import os,sys
cur_dir = os.path.dirname(__file__)
par_dir = os.path.dirname(cur_dir)
sys.path.append(par_dir)
from mysql import *

class Mysql(unittest.TestCase):
    def test_connect(self):
        with mysql() as db:
            self.assertEqual(db.connect(),1)
    def test_cmd(self):
        with mysql() as db:
            db.connect()
            sql = 'create table test (id int)'
            self.assertNotEqual(db.cmd(sql),-1)
            sql = 'drop table test'
            self.assertNotEqual(db.cmd(sql),-1)

    def test_query(self):
        with mysql() as db:
            db.connect()
            sql = 'show tables'
            self.assertNotEqual(db.query(sql),-1)

    def test_close(self):
        with mysql() as db:
            db.connect()
            db.close()

def suite():
    cases = ['test_connect','test_cmd','test_query','test_close']
    suite = unittest.TestSuite()
    for case in cases:
        suite.addTest(Mysql(case))
    return suite

if __name__ == '__main__':
    unittest.main()

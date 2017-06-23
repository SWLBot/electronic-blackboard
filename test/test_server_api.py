import unittest
import os,sys
cur_dir = os.path.dirname(__file__)
par_dir = os.path.dirname(cur_dir)
sys.path.append(par_dir)
from server_api import *
from mysql import *

class Server_api(unittest.TestCase):
    def test_find_now_schedule(self):
        with mysql() as db:
            db.connect()
            self.assertNotEqual(find_now_schedule(db),-1)

if __name__ == "__main__":
    unittest.main()

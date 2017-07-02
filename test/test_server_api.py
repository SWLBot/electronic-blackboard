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

    def test_check_bluetooth_mode_available(self):
        ret = check_bluetooth_mode_available()
        self.assertNotEqual(ret,-1)

    def test_get_user_birthday(self):
        try:
            user_id = 1
            get_user_birthday(user_id)
        except:
            self.fail("Failed with %s" % traceback.format_exc())

    def test_collect_user_prefer_data(self):
        try:
            user_id = 1
            prefer = [9,10]
            collect_user_prefer_data(user_id, prefer)
        except:
            self.fail("Failed with %s" % traceback.format_exc())

def suite():
    cases = ['test_find_now_schedule','test_check_bluetooth_mode_available','test_get_user_birthday',
        'test_collect_user_prefer_data']
    suite = unittest.TestSuite()
    for case in cases:
        suite.addTest(Server_api(case))

    return suite

if __name__ == "__main__":
    unittest.main()

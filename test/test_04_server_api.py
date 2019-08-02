import unittest
import os,sys
cur_dir = os.path.dirname(__file__)
par_dir = os.path.dirname(cur_dir)
sys.path.append(par_dir)
from server_api import *
from mysql import *

class Server_api(unittest.TestCase):
    def test_find_now_schedule(self):
        self.assertNotEqual(find_now_schedule(),-1)

    def test_check_user_existed_or_signup(self):
        try:
            user_info = {}
            user_info['user_name'] = 'admin'
            user_info['user_password'] = 'admin'
            check_user_existed_or_signup(user_info)
        except:
            self.fail("Failed with %s" % traceback.format_exc())

    def test_check_user_password(self):
        try:
            user_info={}
            user_info['user_name'] = 'admin'
            user_info['user_password'] = 'admin'
            check_user_password(user_info)
        except:
            self.fail("Failed with %s" % traceback.format_exc())

    def test_check_user_level(self):
        ret = check_user_level(1)
        self.assertEqual(ret['result'],'success')

    def test_add_new_data_type(self):
        send_msg = {}
        send_msg["type_name"] = 'test_type'
        ret = add_new_data_type(send_msg)
        self.assertTrue(ret['result']=='success' or ret['error']=='Type name has existed')

if __name__ == "__main__":
    unittest.main()

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

    def test_set_insert_customer_text_msg(self):
        ret = set_insert_customer_text_msg()
        self.assertEqual(ret['result'],'success')

    def test_collect_user_prefer_data(self):
        try:
            user_id = 1
            prefer = [9,10]
            collect_user_prefer_data(user_id, prefer)
        except:
            self.fail("Failed with %s" % traceback.format_exc())

    def test_get_prefer_news(self):
        prefer = [9,10]
        with mysql() as db:
            db.connect()
            self.assertNotEqual(len(get_prefer_news(db,prefer)),0)

    def test_check_bluetooth_id_exist(self):
        with mysql() as db:
            db.connect()
            self.assertNotEqual(check_bluetooth_id_exist(db,'test'),-1)

    def test_Zodiac(self):
        self.assertEqual(Zodiac(12,31),u'摩羯座')

    def test_check_user_existed_or_signup(self):
        try:
            user_info = {}
            user_info['user_name'] = 'admin'
            user_info['user_password'] = 'admin'
            check_user_existed_or_signup(user_info)
        except:
            self.fail("Failed with %s" % traceback.format_exc())

    def test_register_no_right_user(self):
        send_msg = {}
        send_msg["bluetooth_id"] = 'test_bluetooth_id'
        self.assertEqual(register_no_right_user(send_msg),1)

    def test_check_user_password(self):
        try:
            user_info={}
            user_info['user_name'] = 'admin'
            user_info['user_password'] = 'admin'
            check_user_password(user_info)
        except:
            self.fail("Failed with %s" % traceback.format_exc())

if __name__ == "__main__":
    unittest.main()

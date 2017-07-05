import unittest
import os,sys
cur_dir = os.path.dirname(__file__)
par_dir = os.path.dirname(cur_dir)
sys.path.append(par_dir)
from arrange_schedule import *

class Arrange_Schedule(unittest.TestCase):
    def setUp(self):
        # test_read_system_setting
        keys = ['board_py_dir','shutdown','max_db_log','min_db_activity']
        system_setting = read_system_setting()
        for key in keys:
            self.assertTrue(key in system_setting)
        self.system_setting = system_setting

    def test_read_arrange_mode(self):
        keys = ['arrange_sn','arrange_mode','condition']
        receive_msg = read_arrange_mode()
        for key in keys:
            self.assertTrue(key in receive_msg)

    def test_delete_old_cwb_img(self):
        with mysql() as db:
            db.connect()
            server_dir = self.system_setting['board_py_dir']
            user_id = 1
            self.assertEqual(len(delete_old_cwb_img(db,server_dir,user_id)),0)

    def test_crawler_cwb_img(self):
        send_msg = {}
        send_msg['server_dir'] = self.system_setting['board_py_dir']
        send_msg['user_id'] = 1

        receive_msg = crawler_cwb_img(send_msg)
        self.assertEqual(receive_msg['result'],'success')
    
    def test_check_news_QR_code_table(self):
        receive_msg = check_news_QR_code_table()
        self.assertEqual(receive_msg['result'],'success')
    
    def test_crawler_news(self):
        websites = ['inside','techOrange','medium']
        for website in websites:
            receive_msg = crawler_news(website)
            self.assertEqual(receive_msg['result'],'success')

    def test_crawler_ptt_news(self):
        boards = ['joke','StupidClown','Beauty']
        for board in boards:
            receive_msg = crawler_ptt_news(boards)
            self.assertEqual(receive_msg['result'],'success')

    def test_crawler_schedule(self):
        receive_msg = crawler_schedule()
        self.assertEqual(receive_msg['result'],'success')

    def test_check_fortune_table(self):
        receive_msg = check_fortune_table()
        self.assertEqual(receive_msg['result'],'success')

    def test_crawler_constellation_fortune(self):
        receive_msg = crawler_constellation_fortune()
        self.assertEqual(receive_msg['result'], 'success')

    def test_set_schedule_log(self):
        send_msg = {}
        send_msg['board_py_dir'] = self.system_setting['board_py_dir']
        send_msg['max_db_log'] = self.system_setting['max_db_log']
        receive_msg = set_schedule_log(send_msg)
        self.assertEqual(receive_msg['result'],'success')

    def test_expire_data_check(self):
        receive_msg = expire_data_check()
        self.assertEqual(receive_msg['result'],'success')

    def test_find_cwb_type_id(self):
        with mysql() as db:
            db.connect()
            self.assertNotEqual(find_cwb_type_id(db),-1)

    def test_mark_now_activity(self):
        receive_msg = mark_now_activity()
        self.assertEqual(receive_msg['result'], 'success')

if __name__ == "__main__":
    unittest.main()

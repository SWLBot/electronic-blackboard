import unittest
from arrange_schedule import *

class Arrange_Schedule(unittest.TestCase):
    def setUp(self):
        # test_read_system_setting
        keys = ['board_py_dir','shutdown','max_db_log','min_db_activity']
        system_setting = read_system_setting()
        for key in keys:
            assert key in system_setting
        self.system_setting = system_setting

    def test_read_arrange_mode(self):
        keys = ['arrange_sn','arrange_mode','condition']
        receive_msg = read_arrange_mode()
        for key in keys:
            assert key in receive_msg

    def test_crawler_cwb_img(self):
        send_msg = {}
        send_msg['server_dir'] = self.system_setting['board_py_dir']
        send_msg['user_id'] = 1

        receive_msg = crawler_cwb_img(send_msg)
        assert receive_msg['result'] == 'success'

    def test_crawler_news(self):
        websites = ['inside','techOrange','medium']
        for website in websites:
            receive_msg = crawler_news(website)
            assert receive_msg['result'] == 'success'

    def test_crawler_ptt_news(self):
        boards = ['joke','StupidClown','Beauty']
        for board in boards:
            receive_msg = crawler_ptt_news(boards)
            assert receive_msg['result'] == 'success'

    def test_crawler_schedule(self):
        receive_msg = crawler_schedule()
        assert receive_msg['result'] == 'success'

    def test_set_schedule_log(self):
        send_msg = {}
        send_msg['board_py_dir'] = self.system_setting['board_py_dir']
        send_msg['max_db_log'] = self.system_setting['max_db_log']
        receive_msg = set_schedule_log(send_msg)
        assert receive_msg['result'] == 'success'

if __name__ == "__main__":
    unittest.main()

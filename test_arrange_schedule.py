from arrange_schedule import *


def test_crawler_cwb_img(system_setting):
    send_msg = {}
    send_msg['server_dir'] = system_setting['board_py_dir']
    send_msg['user_id'] = 1

    receive_msg = crawler_cwb_img(send_msg)
    assert receive_msg['result'] == 'success'

if __name__ == "__main__":
    system_setting = read_system_setting()
    test_crawler_cwb_img(system_setting)

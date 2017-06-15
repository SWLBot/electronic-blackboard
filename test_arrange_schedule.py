from arrange_schedule import *


def test_read_system_setting():
    keys = ['board_py_dir','shutdown','max_db_log','min_db_activity']
    system_setting = read_system_setting()
    for key in keys:
        assert key in system_setting
    return system_setting

def test_read_arrange_mode():
    keys = ['arrange_sn','arrange_mode','condition']
    receive_msg = read_arrange_mode()
    for key in keys:
        assert key in receive_msg

def test_crawler_cwb_img(system_setting):
    send_msg = {}
    send_msg['server_dir'] = system_setting['board_py_dir']
    send_msg['user_id'] = 1

    receive_msg = crawler_cwb_img(send_msg)
    assert receive_msg['result'] == 'success'

if __name__ == "__main__":
    system_setting = test_read_system_setting()
    test_read_arrange_mode()
    test_crawler_cwb_img(system_setting)
    print("All test passed")

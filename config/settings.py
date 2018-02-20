import os
import binascii
server = dict(
    cookie_secret = binascii.hexlify(os.urandom(24))
)
board = dict(
    cookie_secret = binascii.hexlify(os.urandom(24))
)
arrange_setting = dict(
board_py_dir = os.getcwd() + '/',
shutdown = 0,
max_db_log = 100,
min_db_activity = 10)

bluetooth_enable = True
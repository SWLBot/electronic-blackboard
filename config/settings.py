import os
import binascii
server = dict(
    cookie_secret = binascii.hexlify(os.urandom(24))
)
board = dict(
    cookie_secret = binascii.hexlify(os.urandom(24))
)

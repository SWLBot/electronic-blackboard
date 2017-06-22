import unittest
import os,sys
cur_dir = os.path.dirname(__file__)
par_dir = os.path.dirname(cur_dir)
sys.path.append(par_dir)
from env_init import *

class Env_init(unittest.TestCase):
    def test_env_init(self):
        env_init()

    def test_create_data_type(self):
        create_data_type('test')

if __name__ == "__main__":
    unittest.main()

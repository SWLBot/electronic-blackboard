import unittest
import os,sys
cur_dir = os.path.dirname(__file__)
par_dir = os.path.dirname(cur_dir)
sys.path.append(par_dir)
from env_init import *
import pytest

class Env_init(unittest.TestCase):
    @pytest.mark.run(order=1)
    def test_env_init(self):
        env_init()

    @pytest.mark.run(order=2)
    def test_create_data_type(self):
        create_data_type('test')

if __name__ == "__main__":
    unittest.main()

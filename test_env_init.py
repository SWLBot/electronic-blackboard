import unittest
from env_init import *

class Env_init(unittest.TestCase):
    def test_env_init(self):
        env_init()

    def test_create_data_type(self):
        create_data_type('test')

if __name__ == "__main__":
    unittest.main()

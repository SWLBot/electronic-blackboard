import unittest
import os,sys
cur_dir = os.path.dirname(__file__)
par_dir = os.path.dirname(cur_dir)
sys.path.append(par_dir)
from display_api import *

class Display_api(unittest.TestCase):
    def test_display_image(self):
        user_name = "admin"
        receive_msg = display_image(user_name)
        #return dict type when error occurs
        self.assertEqual(type(receive_msg),list)

    def test_get_user_id(self):
        user_name = "admin"
        receive_msg = get_user_id(user_name)
        #return dict type when error occurs
        self.assertEqual(type(receive_msg),int)

    def test_display_text(self):
        user_name = "admin"
        receive_msg = display_text(user_name)
        #return dict type when error occurs
        self.assertEqual(type(receive_msg),list)

def suite():
    cases = ['test_get_user_id','test_display_image','test_display_text']
    suite = unittest.TestSuite()
    for case in cases:
        suite.addTest(Display_api(case))
    return suite

if __name__ == "__main__":
    unittest.main()

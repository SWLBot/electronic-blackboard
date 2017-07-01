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
    def test_display_data_type(self):
        check = False
        test_type_id = 1
        test_type_name = '圖片'
        test_type_dir = '圖片/'
        test_type_weight = 1
        return_type_id = display_data_type(type_id=test_type_id)
        return_type_name = display_data_type(type_name=test_type_name)
        return_type_dir = display_data_type(type_dir=test_type_dir)
        return_type_weight = display_data_type(type_weight=test_type_weight)
        if type(return_type_id)==list and type(return_type_name)==list and type(return_type_dir)==list and type(return_type_weight)==list:
            check = True
        self.assertTrue(check)

def suite():
    cases = ['test_get_user_id','test_display_image','test_display_text','test_display_data_type']
    suite = unittest.TestSuite()
    for case in cases:
        suite.addTest(Display_api(case))
    return suite

if __name__ == "__main__":
    unittest.main()

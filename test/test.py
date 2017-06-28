from test_mysql import suite as MysqlSuite
from test_env_init import suite as EnvSuite
from test_arrange_schedule import suite as ArrangeSuite
from test_display_api import suite as DisplaySuite
from test_server_api import suite as ServerSuite
import unittest

def main():
    testcases = [EnvSuite,MysqlSuite,ArrangeSuite,DisplaySuite,ServerSuite]
    suite = unittest.TestSuite()
    for case in testcases:
        suite.addTests(case())

    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == "__main__":
    main()

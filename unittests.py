#-------------------------------------------------------------------------------
# Name:        unittests
# Purpose:
#
# Author:      Joos Dominicus
#
# Created:     03-05-2014
#-------------------------------------------------------------------------------

import Database

import unittest
import mock

class test_db_files_exist(unittest.TestCase):
    Database.os.path.isfile = mock.MagicMock(side_effect=[False, False])
    def runTest(self):
        self.assertRaises(Database.DatabaseError, Database.Database, self, "network_path", "local_path", "f_name.db3")

def main():
    unittest.main()

if __name__ == '__main__':
    main()

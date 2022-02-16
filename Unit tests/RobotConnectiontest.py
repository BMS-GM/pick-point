import unittest
import sys

sys.path.append('./..') 

from pyniryo import *

class test_robot(unittest.TestCase):

    def test_robot_connection_positive(self):
        robot = NiryoRobot("10.10.10.10")
    

if __name__ == '__main__':
    unittest.main()
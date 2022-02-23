import unittest
import sys
import os
sys.path.append('./..') 
import main


class test_whole_system(unittest.TestCase):

    def test_main(self):
        os.chdir('..')
        main_thread = main.Main()
        main_thread.main_loop()

if __name__ == '__main__':
    unittest.main()
"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------

listenerConcept.py
Author: Corbin Holz
Date Created: 2/18/2021
Date Last Modified: 2/18/2021
"""

__author__ = 'Blue Marble Security Enterprise'
__version__ = '1.0'

import sys
import math
import time

try:
    command = raw_input()

    command = command.split(" ")
    mySum = (int(command[0]) + int(command[1]))

    time.sleep(11)

    print(mySum)
    print("DONE")

except NiryoOneException as e:
    print (e)

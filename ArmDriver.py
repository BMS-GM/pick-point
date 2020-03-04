#!/usr/bin/env python
"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------

ArmDriver.py
Author: Alek Ertman, Alyssa Hlywa
Date Last Modified: 3/3/2020
"""

__author__ = 'Blue Marble Security Enterprise'
__version__ = '1.0'


from niryo_one_python_api.niryo_one_api import *
import rospy
import time
rospy.init_node('niryo_one_example_python_api')

print "--- Start "

n = NiryoOne()

try:
    # Calibrate robot first
    n.calibrate_auto()
    print "Calibration finished!"

    time.sleep(1)

    # Test learning mode
    # n.activate_learning_mode(False)
    
    n.activate_learning_mode(True)

    # Test digital I/O
    pin = GPIO_1B
    n.pin_mode(pin, PIN_MODE_OUTPUT)
    n.digital_write(pin, PIN_HIGH)
    time.sleep(2)
    n.digital_write(pin, PIN_LOW)
    time.sleep(2)
    n.pin_mode(pin, PIN_MODE_INPUT)

    pin = GPIO_1A
    n.pin_mode(pin, PIN_MODE_INPUT)
    for i in range(0,10):
        print "Read pin GPIO 1_A : " + str(n.digital_read(pin))
        time.sleep(0.2)

    #Begin looking for commands
    instruction = str("")

    while not instruction.equals("quit"):
        instruction = input("Enter Command: ")

        if instruction == "open":
            n.change_tool(TOOL_GRIPPER_3_ID)
			n.open_gripper(TOOL_GRIPPER_3_ID, 300)
			time.sleep(1)

        elif instruction == "close":
            n.change_tool(TOOL_GRIPPER_3_ID)
			n.close_gripper(TOOL_GRIPPER_3_ID, 300)
			time.sleep(1)

        elif instruction == "move":
            n.move_joints()
        
    except NiryoOneException as e:
    print e 
    # handle exception here
    # you can also make a try/except for each command separately

print "--- End"



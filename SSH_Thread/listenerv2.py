"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------
listenerv2.py
Author: Corbin Holz
Date Created: 2/18/2021
Date Last Modified: 2/18/2021
"""

__author__ = 'Blue Marble Security Enterprise'
__version__ = '1.0'

import sys
import math
from niryo_one_python_api.niryo_one_api import *
import rospy

# Initialize the robotic arm
rospy.init_node('niryo_one_example_python_api')
robot = NiryoOne()

# How long to wait during wait calls (seconds)
sleep_time = 1

# Percent of speed
max_velocity = 30

# Speed between 0-1000
max_grip_speed = 300

# Calibrate the Arm
robot.set_arm_max_velocity(max_velocity)

# Set the TOOL ID
"""
TOOL_NONE
TOOL_GRIPPER_1_ID -
TOOL_GRIPPER_2_ID -
TOOL_GRIPPER_3_ID - Adaptive Gripper
TOOL_ELECTROMAGNET_1_ID
TOOL_VACUUM_PUMP_1_ID
"""
robot.change_tool(TOOL_GRIPPER_3_ID)

try:
    # For every loop, wait for commands
    #print("WAIT", file = sys.stdout)
    print("WAIT")
    command = raw_input()

    #print("BUSY", file = sys.stdout)
    print("BUSY")

    # Split the command into partitions
    # ie. [command] [arg1] [arg2] etc.
    command = list(command.split(" "))

    # If move command, collect specified variables and move
    if (command[0] == "MOVE"):
        x_val = float(command[1])
        y_val = float(command[2])
        z_val = float(command[3])
        roll_val = float(command[4])
        pitch_val = float(command[5])
        yaw_val = float(command[6])
        robot.move_pose(x = x_val, y = y_val, z = z_val, roll = roll_val, pitch = pitch_val, yaw = yaw_val)

    # If shift command, shift along specified axis
    elif (command[0] == "SHIFT"):
        spec_axis = command[1]
        shiftBy = 0
        if (spec_axis == "x" or spec_axis == "y" or spec_axis == "z"):
            shiftBy = float(command[2])
            if spec_axis is "x":
                robot.shift_pose(AXIS_X, shiftBy)

            elif spec_axis is "y":
                robot.shift_pose(AXIS_Y, shiftBy)

            elif spec_axis is "z":
                robot.shift_pose(AXIS_Z, shiftBy)

        else:
            shiftBy = float(command[2])
            if spec_axis is "roll":
                robot.shift_pose(ROT_ROLL, shiftBy)

            elif spec_axis is "pitch":
                robot.shift_pose(ROT_PITCH, shiftBy)

            elif spec_axis is "yaw":
                robot.shift_pose(ROT_YAW, shiftBy)

    # If open command, open the effector
    elif (command[0] == "OPEN"):
        robot.open_gripper(TOOL_GRIPPER_3_ID, max_grip_speed)

    # If close command, close the effector
    elif (command[0] == "CLOSE"):
        robot.close_gripper(TOOL_GRIPPER_3_ID, max_grip_speed)

    # If PICK command open the effector, move, and close the effector
    elif (command[0] == "PICK"):
        robot.open_gripper(TOOL_GRIPPER_3_ID, max_grip_speed)

        x_val = float(command[1])
        y_val = float(command[2])
        z_val = float(command[3])
        roll_val = float(command[4])
        pitch_val = float(command[5])
        yaw_val = float(command[6])
        robot.move_pose(x = x_val, y = y_val, z = z_val, roll = roll_val, pitch = pitch_val, yaw = yaw_val)

        robot.close_gripper(TOOL_GRIPPER_3_ID, max_grip_speed)

    # If drop command move arm, open effector, close effector
    elif (command[0] == "DROP"):
        x_val = float(command[1])
        y_val = float(command[2])
        z_val = float(command[3])
        roll_val = float(command[4])
        pitch_val = float(command[5])
        yaw_val = float(command[6])
        robot.move_pose(x = x_val, y = y_val, z = z_val, roll = roll_val, pitch = pitch_val, yaw = yaw_val)

        robot.open_gripper(TOOL_GRIPPER_3_ID, max_grip_speed)
        robot.wait(sleep_time)
        robot.close_gripper(TOOL_GRIPPER_3_ID, max_grip_speed)

    # If SPEED command, update max arm velocity
    elif (command[0] == "SPEED"):
        updated_speed = float(command[1]) * 10

        robot.set_arm_max_velocity(updated_speed)

    # If CALIBRATE, set arm velocity to default/max arm velocity (ran on startup)
    elif command[0] == "CALIBRATE":
        robot.calibrate_auto()
        
    # When Done print to standard out
    #print("DONE", file = sys.stdout)
	print("DONE")

except NiryoOneException as e:
    print (e)
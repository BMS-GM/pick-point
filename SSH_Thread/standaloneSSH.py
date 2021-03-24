"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------
standaloneSSH.py

Code Based on Demo: https://github.com/paramiko/paramiko/

Author: Corbin Holz
Date last modified: 10/2/20
"""

__author__ = 'Blue Marble Security Enterprise'
__version__ = '1.0'

import paramiko
import sys
import time
import os

client = paramiko.SSHClient()

hostname = '10.10.10.10'
user = 'niryo'
userpass = 'robotics'

isManual = 1

# Instantiate command file
command_log = None
# Only read from commands log if manual flag
if (not isManual):
    command_log = open("commands.log", "r")

# Commands read in should be FIFO
command_stack_pos = 0

client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname, username=user, password=userpass)

'''
# Move the listener script
ftp_client = client.open_sftp()
remotepath = '/home'
ftp_client.put('listener.py', remotepath)
ftp_client.close()
'''

# Exec the python script
stdin, stdout, stderr = client.exec_command('source ~/catkin_ws/devel/setup.bash && export PYTHONPATH=${PYTHONPATH}:/home/niryo/catkin_ws/src/niryo_one_python_api/src/niryo_python_api && python listener.py')
print (stdout)
# Write commands
userIn = ""
while (userIn != "QUIT"):
    if (isManual):
        userIn = input("Enter a command to be sent to SSH: ")
        userIn = userIn.upper()
        stdin.write(userIn)
        stdin.flush()
        stdin.channel.shutdown_write()
        print("Sent?")
        time.sleep(10)
        output = "WAIT"
        print("Read output")


        
        # Wait until done is recieved and waiting for next command
        while (output[-1] == "WAIT"):
            # Don't pull as soon as possible for performance
            # Only pull every second
            time.sleep(1)
            output = stdout.readlines()

    # If not manually typing commands go through pipeline
    else:
        # Wait until "WAIT" is recieved
        output = stdout.readlines()
        while (output[-1] != "WAIT"):
            # Don't pull as soon as possible for performance
            # Only pull every second
            time.sleep(1)
            output = stdout.readlines()

        command_list = command_log.readlines()
        # Wait for commands
        while (command_stack_pos >= len(command_list)):
            time.sleep(1)
            command_list = command_log.readlines()

        stdin.write(command_list[command_stack_pos])
        stdin.flush()

        command_stack_pos = command_stack_pos + 1

        
client.close()
command_log.close()
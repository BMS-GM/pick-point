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

hostname = 'colossus.it.mtu.edu'
user = 'username'
userpass = 'password'

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

userIn = ""

while (userIn != "QUIT"):
    if (isManual):
        userIn = input("Enter a command to be sent to SSH: ")
        userIn = userIn.upper()
        if (userIn != "QUIT"):
            # Exec the python script
            stdin, stdout, stderr = client.exec_command('python listenerConcept.py')

            stdin.write(userIn)
            stdin.flush()
            stdin.channel.shutdown_write()

            output = stdout.readlines()

            while (not output or output[-1] != "DONE\n"):
                output = stdout.readlines()

            print(output)

            stdin.close()
            stdout.close()
            stderr.close()


client.close()

"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------
standaloneSSH.py

Code Based on Demo: https://github.com/paramiko/paramiko/

Author: Corbin Holz
Date last modified: 9/16/20
"""

__author__ = 'Blue Marble Security Enterprise'
__version__ = '1.0'

import paramiko
import sys

client = paramiko.SSHClient()

hostname = sys.argv[1]
user = sys.argv[2]
userpass = sys.argv[3]

client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname, username=user, password=userpass)

# Exec the python script
stdin, stdout, stderr = client.exec_command('source ~/catkin_ws/devel/setup.bash && export PYTHONPATH=${PYTHONPATH}:/home/niryo/catkin_ws/src/niryo_one_python_api/src/niryo_python_api && python test.py')

output = stdout.readlines()
print(output)
input("Press Enter to continue...")
client.close()
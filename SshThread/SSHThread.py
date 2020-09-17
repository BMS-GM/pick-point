"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------
SSHThread.py

Code Based on Demo: https://github.com/paramiko/paramiko/

Author: Corbin Holz
Date last modified: 9/16/20
"""

__author__ = 'Blue Marble Security Enterprise'
__version__ = '1.0'

# Import base 64 if using a secure SSH
# import base64
import threading
import time
import paramiko
import sys

class SSHThread(threading.Thread):

    def __init__(self):

        # Create the default variables
        # Define the host, username, and password
        self.client = paramiko.SSHClient()
        self.hostname = 'localhost'
        self.user = 'username'
        self.userpass = 'password'

        # Since SSH allows for secure connections with keys, allow to auto accept keys without passwords
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Otherwise uncomment and add keys
        # key = paramiko.RSAKey(data=base64.b64decode(b'AAA...'))
        # client.get_host_keys().add('ssh.example.com', 'ssh-rsa', key)

    def run(self)
        client.connect(hostname, username=user, password=userpass)
        
        # Exec the python script
        stdin, stdout, stderr = client.exec_command('ls')

        # stdout is where confirmation of completion of task will occur
        output = stdout.readlines()

        # This needs to log.
        print(output)

        client.close()
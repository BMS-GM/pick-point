"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------
SSHThread.py

Code Based on Demo: https://github.com/paramiko/paramiko/

Author: Corbin Holz
Date last modified: 12/1/2020
"""

__author__ = 'Blue Marble Security Enterprise'
__version__ = '1.0'

# Import base 64 if using a secure SSH
# import base64
import threading
import time
import paramiko
import sys
import logging

class SSHThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        # Setup Threading
        super(SSHThread, self).__init__()       # Initialize Thread
        
        # Create the default variables
        # Define the host, username, and password
        self.client = paramiko.SSHClient()
        self.hostname = '10.10.10.10' # Static IP of Arm if device is connected over wifi
        self.user = 'niryo'
        self.userpass = 'robotics'
        self._command_list = []
        
        print("SSH STARTED")
        
        # Since SSH allows for secure connections with keys, allow to auto accept keys without passwords
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Otherwise uncomment and add keys
        # key = paramiko.RSAKey(data=base64.b64decode(b'AAA...'))
        # client.get_host_keys().add('ssh.example.com', 'ssh-rsa', key)

    def run(self):
        self.client.connect(self.hostname, username=self.user, password=self.userpass)
        
        '''
        # Move the listener script
        ftp_client = self.client.open_sftp()
        remotepath = '/home'
        ftp_client.put('listener.py', remotepath)
        ftp_client.close()
        '''

        # Exec the python script
        stdin, stdout, stderr = self.client.exec_command('source ~/catkin_ws/devel/setup.bash && export PYTHONPATH=${PYTHONPATH}:/home/niryo/catkin_ws/src/niryo_one_python_api/src/niryo_python_api && python listener.py')

        # Write commands
        userIn = ""
        while (userIn != "QUIT"):
            # Wait until "WAIT" is recieved
            output = stdout.readlines()
            while (output[-1] != "WAIT"):
                # Don't poll as soon as possible for performance
                # Only poll every second
                time.sleep(1)
                output = stdout.readlines()

            # Wait for commands (loop if empty)
            while (not self._command_list):
                time.sleep(1)

            # FIFO commands
            stdin.write(self._command_list.pop(0))
            stdin.flush()

                
        self.client.close()

    """
    _append_command
    Appends passed command to the command list
    input: new_command
    """
    def _append_command(self, new_command):
        if (new_command not in self._command_list):
            self._command_list.append(new_command)

if __name__ == '__main__':
    # =================================
    # Setup Logging
    # =================================
    # Create master logger and set global log level
    log_dir = "C:\\Users\\jmjerred-adm\\PycharmProjects\\pick-point\\Logs"
    logger = logging.getLogger("GM_Pick_Point")
    logger.setLevel(logging.DEBUG)

    # create log file
    file_handler = logging.FileHandler(log_dir + '\\GUI - %s.log' %
                                       datetime.datetime.now().strftime("%Y.%m.%d-%H.%M.%S"))
    file_handler.setLevel(logging.DEBUG)

    # create console logger
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Format Log
    log_formatter = logging.Formatter('%(levelname)s - %(asctime)s - %(name)s - %(message)s')
    file_handler.setFormatter(log_formatter)
    console_handler.setFormatter(log_formatter)

    # Add outputs to main logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    # =====================================================================

    logger.debug('Stating SSH Thread')
    ssh_thread = SSHThread()
    ssh_thread.start()
    logger.debug('HERE')
    time.sleep(5)
    logger.debug('GOT HERE')
    time.sleep(5)
    ssh_thread.terminate()
    ssh_thread.join()
    logger.debug('Child Thread is Dead')
    # test.set_image("image.PNG")
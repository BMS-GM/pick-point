#!/usr/bin/env python
"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------

Class to create a separate thread to ssh into robotic arm and control arm
"""

__author__ = 'Blue Marble Security Enterprise'
__version__ = '1.0'

import ssh2
import threading
import os
import socket

class RoboticArmDriver(threading.Thread):

    def __init__(self):
        """
        Class Constructor. This also automatically starts the thread
        """
        # Setup Threading
        super(RoboticArmDriver, self).__init__()       # Initialize Thread
        self._ssh_ready_event = threading.Event()
        self._ssh_ready_event.clear()
        self._ssh_returned_event = threading.Event()

        self._result = None

        self.hostname = 'localhost'
        self.user = 'testUser'
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((hostname, 22))
        self.session = ssh2.session.Session()
        self.session.handshake(sock)
        self.session.agent_auth(user)

        self.channel = self.session.open_session()
        channel = session.open_session()
        channel.execute('echo me; exit 2')

        # init the logger
        self._logger = logging.getLogger('GM_Pick_Point.' + self.__class__.__name__)

        self.start()

    def run(self):
        """
        Main Thread Function
        """
        size, data = self.channel.read()
        counter = 0


        while size < 1:
            self.channel.execute('echo Connected')
            size, data = self.channel.read()
            if counter == 20:
                self._logger.warning("SSH could not connect!")
                terminate_thread(self)

        
        

        self._logger.debug("SSH connection is successful... Waiting for commands...")

    def sendInstr(self, instrType, param1, param2, param3, param4, param5, param6):
        self.channel.execute('python {}.py {} {} {} {} {} {}'.format(instrType, param1, param2, param3, param4, param5, param6))
        print("Not Implemented")


    def terminate_thread(self):
        """
        Request the thread to terminate
        """
        # Close Connection
        self.channel.close()
        self._image_returned_event.set()
        self._image_ready_event.set()





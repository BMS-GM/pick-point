#!/usr/bin/env python
"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------

Driver to connect to SQLite database and get jobs and objects from
tables
"""

__author__ = 'Blue Marble Security Enterprise'
__version__ = '1.0'

import sqlite3
import threading
from SQL_Driver import SQLiteDriver


class ObjectDBThread(SQLiteDriver.SQLiteDriver, threading.Thread):
    def __init__(self):
        """
        ObjectDB Constructor
        """
        super(ObjectDBThread, self).__init__()
        self.connection = self.create_connection()
        self._status_lock = threading.Lock()

    @staticmethod
    def create_connection():
        """ create a database connection to the SQLite database
            specified by the db_file
        :return: connection
        """
        conn = None
        try:
            conn = sqlite3.connect("pickpoint.db")
            return conn
        except sqlite3.Error as e:
            print(e)
        return conn

    def get_job_list(self):
        """
        Query all rows in the jobs table
        :return: list of jobs and status
        """
        try:
            cur = self.connection.cursor()
            cur.execute("SELECT * FROM jobs")
            rows = cur.fetchall()
        except sqlite3.Error as e:
            print(e)
            return None

        return rows

    def get_incomplete_job(self):
        """
        Abstract method to return an incomplete job
        :return: an incomplete job
        """
        try:
            cur = self.connection.cursor()
            cur.execute("SELECT * FROM jobs WHERE status == 'Incomplete'")
            job = cur.fetchone()
        except sqlite3.Error as e:
            print(e)
            return None

        return job

    def get_object_list(self, table):
        """
        Query all rows in the objects table
        :param table: name of job
        :return: a list of jobs and statuses for each job
        """
        with self._status_lock:
            try:
                cur = self.connection.cursor()
                cur.execute("SELECT * FROM {0}".format(table))

                rows = cur.fetchall()
            except sqlite3.Error as e:
                print(e)
                return None

        return rows

    def update_job_status(self, job, status):
        """
        Abstract method update the status of a job
        :param job: name of job
        :param status: new status
        :return: N/A
        """
        with self._status_lock:
            try:
                cur = self.connection.cursor()
                cur.execute("UPDATE jobs SET status = '{0}' WHERE name = '{1}'".format(status, job))
                self.connection.commit()
            except sqlite3.Error as e:
                print(e, "update_job_status")

    def reset_job_statuses(self):
        """
        Abstract method reset all job statuses to "Incomplete"
        :return: N/A
        """
        with self._status_lock:
            try:
                cur = self.connection.cursor()
                cur.execute("UPDATE jobs SET status = 'Incomplete'")
                self.connection.commit()
            except sqlite3.Error as e:
                print(e)

    def is_connected(self):
        """
        Check connection to database
        :return: boolean
        """
        if self.connection is None:
            return False
        else:
            return True

    def disconnect(self):
        """ disconnect from database
        :return: N/A
        """
        self.connection.close()
        self.connection = None

    def terminate_thread(self):
        """
        Request Thread Termination
        """
        self._logger.info("Terminating Database Thread...")
        self._terminate_thread_event.set()


if __name__ == '__main__':
    a = ObjectDBThread()

    if not a.is_connected():
        exit(1)

    jobs = a.get_job_list()

    for j in jobs:
        objects = a.get_object_list(j[1])
        print("\nPrinting", j[1], "objects")
        for o in objects:
            print(o)

    print("\nIncomplete job:", a.get_incomplete_job())

    a.update_job_status("cat", "In Progress")
    print("\nIncomplete job:", a.get_incomplete_job())

    a.update_job_status("dog", "Complete")
    print("\nIncomplete job:", a.get_incomplete_job())

    a.update_job_status("bird", "In Progress")
    print("\nIncomplete job:", a.get_incomplete_job())

    for j in a.get_job_list():
        print(j)

    print("\nResetting Statuses\n")
    a.reset_job_statuses()

    for j in a.get_job_list():
        print(j)

    a.disconnect()

    exit(0)

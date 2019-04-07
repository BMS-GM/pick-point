#!/usr/bin/env python
"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------
Abstract class for SQLite drivers
"""

__author__ = 'Blue Marble Security Enterprise'
__version__ = '1.0'


class SQLiteDriver:
    """
    Abstract Class
    """

    def get_object_list(self, table):
        """
        Abstract method to obtain list of objects from database
        :param table: name of job
        :return: a list of objects with corresponding bin
        """
        raise NotImplementedError('Method get_image is not defined')

    def get_job_list(self):
        """
        Abstract method to obtain list of jobs
        :return: a list of jobs and statuses for each job
        """
        raise NotImplementedError('Method get_image is not defined')

    def get_incomplete_job(self):
        """
        Abstract method to return an incomplete job
        :return: an incomplete job
        """
        raise NotImplementedError('Method get_image is not defined')

    def update_job_status(self, job, status):
        """
        Abstract method update the status of a job
        :param job: name of job
        :param status: new status
        :return: N/A
        """
        raise NotImplementedError('Method get_image is not defined')

    def reset_job_statuses(self):
        """
        Abstract method reset all job statuses to "Incomplete"
        :return: N/A
        """
        raise NotImplementedError('Method get_image is not defined')

    def is_connected(self):
        """
        Abstract method to return database connection status
        :return: boolean
        """
        raise NotImplementedError('Method get_image is not defined')

    def disconnect(self):
        """
        Abstract method to disconnect from database
        :return: N/A
        """
        raise NotImplementedError('Method get_image is not defined')



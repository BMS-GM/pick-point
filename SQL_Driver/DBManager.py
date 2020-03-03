#!/usr/bin/env python
"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------

methods for managing SQLite database tables and rows
This is for internal use only to make it easier to edit and
view tables.  Some database management may require you to go into the
terminal and work from there.  The sqlite database file is "pickpoint.db"

DBManager.py
Author: careyes1 [GitHub]
Date Last Modified 4/23/2019
"""

__author__ = 'Blue Marble Security Enterprise'
__version__ = '1.0'

import sqlite3


def connect():
    """
    Connects to the pickpoint.db file
    :return: connection to DB
    """
    try:
        connection = sqlite3.connect("pickpoint.db")
        return connection
    except sqlite3.Error as e:
        print(e)

    return None


def create_table(conn, table):
    """
    Creates a table for a particular job
    :param conn: connection to database
           table: name of table
    :return: N/A
    """
    c = conn.cursor()
    try:
        c.execute("""create table {0}(id integer primary key autoincrement, 
        name varchar(20), destination varchar(20))""".format(table))
        conn.commit()
        print("Table ", table, " created")
    except sqlite3.Error as e:
        print("Table creation failed:\n", e)


def insert_object(conn, name, destination, table, count):
    """
    Inserts a type of object into a job table in the database.
    Can insert multiple of the same part/destination
    :param conn: connection to database
           name: name of the part
           destination: location where part is to be placed
           table: name of table
           count: quantity to be inserted
    :return: N/A
    """
    try:
        for i in range(count):
            conn.execute("insert into {0} values(null, '{1}', '{2}')".format(table, name, destination))
        conn.commit()
    except sqlite3.Error as e:
        print(e, "\n")


def select(conn, table):
    """
    View all contents in table
    :param conn: connection to database
           table: name of table
    :return: N/A
    """
    try:
        table = conn.execute("Select * from {0}".format(table)).fetchall()
        if len(table) == 0:
            print("No objects in table\n")
            return
        for row in table:
            print(row)
    except sqlite3.Error as e:
        print(e)


def delete_row(conn, id, table):
    """
    Deletes a row in table by row ID
    :param conn: connection to database
           id: row ID
           table: name of table
    :return: N/A
    """
    try:
        item = conn.execute("select * from {0} where id = {1}".format(table, id)).fetchone()
        conn.execute("delete from {0} where id = {1}".format(table, id))
        conn.commit()
        print(item, "deleted")
    except sqlite3.Error as e:
        print(e)


def main():
    conn = connect()
    while 1:
        inp = input("table, insert, select, delete, quit\n")
        if inp == "table":
            table = input("Table name: ")
            create_table(conn, table)
        if inp == "insert":
            table = input("Table name: ")
            name = input("Part name: ")
            destination = input("Part destination: ")
            count = int(input("Quantity: "))
            insert_object(conn, name, destination, table, count)
        if inp == "select":
            table = input("Table name: ")
            select(conn, table)
        if inp == "delete":
            table = input("Table name: ")
            part_id = int(input("Part ID: "))
            delete_row(conn, part_id, table)
        if inp == "quit":
            conn.close()
            exit(0)


if __name__ == '__main__':
    main()

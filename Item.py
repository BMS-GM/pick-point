#!/usr/bin/env python
"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------

Generic Item Class
"""

__author__ = 'Blue Marble Security Enterprise'
__version__ = '1.0'


class Item:
    def __init__(self, item_type, placement=None, x=None, y=None, z=None):
        """
        Constructor
        :param item_type: A string containing a SQL compatible name fo the item
        :param placement: A String containing a SQL compatible name for the destination of the object
        :param x: The current X coord
        :param y: The current Y coord
        :param z: The current Z coord
        """
        self.item_type = item_type
        self.placement = placement
        self.x = x
        self.y = y
        self.z = z

    @property
    def tuple(self):
        """
        Property decorated access function to get a tuple version of the Item class

        To Call: item.tuple

        :return: a tuple version of the class
        """
        return self.item_type, self.placement, self.x, self.y, self.z

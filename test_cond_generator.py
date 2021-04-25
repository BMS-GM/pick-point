"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------

test_cond_generator.py
Author: Max Hoglund
Date last modified: 4/20/21
"""

__author__ = 'Blue Marble Security Enterprise'
__version__ = '1.0'

import random

pieces = [ 
    "cat_eyes",
    "cat_body",
    "cat_mouth",
    "cat_ear",
    "cat_food",
    "dog_eyes",
    "dog_body",
    "dog_mouth",
    "dog_ear",
    "dog_food",
    "dog_tail",
    "bird_eyes",
    "bird_body",
    "bird_mouth",
    "bird_wing",
    "bird_food"
    ]
rotation = [
    "0",
    "90"
    ]

#Generate 5 piece / quadrant / rotation combos
for x in range(0,5):
    rng = random.randrange(0,16-x)
    print("{}    {}    {}\n".format(pieces[rng],random.randrange(1,5), rotation[random.randrange(0,2)]))
    pieces.pop(rng)
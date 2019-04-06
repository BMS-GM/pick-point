import numpy as np
import random

part_list = ["bird_eye", "bird_mouth", "bird_wing", "bird_body", "bird_seeds",
                 "cat_eyes", "cat_mouth", "cat_body", "cat_ear", "cat_food",
                 "dog_ear", "dog_eyes", "dog_mouth", "dog_body", "dog_tail", "dog_food"]
part_set = set(part_list)
MAX_BACH_SIZE = len(part_list)


def get_rand_items(num_items=-1):
    if num_items <= 0:
        num_items = random.randint(1, MAX_BACH_SIZE)
    return list(random.sample(part_set, num_items))


def get_rand_items_sorted(num_items=-1):
    result = get_rand_items(num_items)
    result.sort()
    return result


if __name__ == "__main__":

    while True:
        print("\n\nNext Batch:")
        parts = get_rand_items_sorted()
        for part in parts:
            print("\t%s" % part)

        input("Press Enter to Continue...")

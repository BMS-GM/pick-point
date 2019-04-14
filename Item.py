
class Item:
    def __init__(self, item_type, placement=None, x=None, y=None, z=None):
        self.item_type = item_type
        self.placement = placement
        self.x = x
        self.y = y
        self.z = z

    @property
    def tuple(self):
        return self.item_type, self.placement, self.x, self.y, self.z

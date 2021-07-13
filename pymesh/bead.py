import numpy as np

class Bead:
    """
    Class for individual beads
    """

    def __init__(self, x, y, z, r):
        self.x = x
        self.y = y
        self.z = z
        self.r = r

    def pos(self):
        return np.sqrt(self.x**2 + self.y**2)

    def volume(self):
        return 4/3 * np.pi * self.r**3

    def distance(self, other):
        return np.sqrt((self.x-other.x)**2 + (self.y-other.y)**2 + (self.z-other.z)**2)

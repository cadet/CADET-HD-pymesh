import numpy as np
import gmsh

class Bead:
    """
    Class for individual beads
    """

    def __init__(self, x, y, z, r, tag=0):
        self.x = x
        self.y = y
        self.z = z
        self.r = r
        self._tag = tag

    def pos_xy(self):
        return np.sqrt(self.x**2 + self.y**2)

    def volume(self):
        return 4/3 * np.pi * self.r**3

    def distance(self, other):
        return np.sqrt((self.x-other.x)**2 + (self.y-other.y)**2 + (self.z-other.z)**2)

    def generate(self):
        self._tag = gmsh.model.occ.addSphere(self.x, self.y, self.z, self.r)
        return self._tag

    @property
    def tag(self):
        return self._tag

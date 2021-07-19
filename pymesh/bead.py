import gmsh
import numpy as np
from dataclasses import dataclass

@dataclass(init=True, order=True, repr=True, frozen=True)
class Bead:
    """
    Class for individual beads

    Assumes tag is -1 on init, and +ve on generation.

    @note: would have loved to have beads generated on __post_init__(), but
    doing so implies I can't perform transformations beforehand. It's more
    efficient to separate the geometry generation
    """
    x: float
    y: float
    z: float
    r: float
    tag: int = -1

    def generate(self):
        if self.tag == -1:
            object.__setattr__(self, 'tag', gmsh.model.occ.addSphere(self.x, self.y, self.z, self.r))

    def pos_xy(self):
        return np.sqrt(self.x**2 + self.y**2)

    def volume(self):
        return 4/3 * np.pi * self.r**3

    def distance(self, other):
        return np.sqrt((self.x-other.x)**2 + (self.y-other.y)**2 + (self.z-other.z)**2)


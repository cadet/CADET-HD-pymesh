import gmsh
import numpy as np
from dataclasses import dataclass

from pymesh.tools import copy_mesh

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
    ctag: int = -1

    def generate(self):
        if self.tag == -1:
            object.__setattr__(self, 'tag', gmsh.model.occ.addSphere(self.x, self.y, self.z, self.r))

    def copy_mesh(self, m, ntoff, etoff, objectIndex ):
        ntoff, etoff= copy_mesh(
                m, 
                ntoff, etoff, 
                xoff = self.x,
                yoff = self.y,
                zoff = self.z,
                xscale = self.r,
                yscale = self.r,
                zscale = self.r,
                objectIndex = objectIndex
                )
        return ntoff, etoff

    def pos_xy(self):
        return np.sqrt(self.x**2 + self.y**2)

    def volume(self):
        return 4/3 * np.pi * self.r**3

    def surface_area(self):
        return 4 * np.pi * self.r**2

    def distance(self, other):
        return np.sqrt((self.x-other.x)**2 + (self.y-other.y)**2 + (self.z-other.z)**2)

    def copy(self):
        bead_copy = Bead(self.x, self.y, self.z, self.r)
        if self.tag != -1:
            bead_copy.generate()
        return bead_copy

    def translate(self, dx, dy, dz):
        object.__setattr__(self, 'x', self.x + dx)
        object.__setattr__(self, 'y', self.y + dy)
        object.__setattr__(self, 'z', self.z + dz)

        if self.tag != -1:
            gmsh.model.occ.translate([(3,self.tag)], dx, dy, dz)

        return self

    def set_ctag(self, ictag):
        object.__setattr__(self, 'ctag', ictag)

    @property
    def dimTag(self):
        return (3,self.tag)

    @property
    def leftCardinalBounds(self):
        return self.x-self.r, self.y-self.r, self.z-self.r

    @property
    def rightCardinalBounds(self):
        return self.x+self.r, self.y+self.r, self.z+self.r

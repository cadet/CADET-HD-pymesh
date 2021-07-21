"""
Container class.

- Should create a container based on the given config, and created packedBed
- if container.shape is None: don't create
- if container.size == 'auto' or None (default), take bounds from packed bed
- else create container from config
- MUST only have one container entity. Create multiple instances of this class for each linked section.


"""

import gmsh
import sys

from pymesh.log import Logger

factory = gmsh.model.occ

class Container:

    def __init__(self, shape, size, logger=Logger()):
        """
        Container instantiation
        """

        self.shape    = shape
        self.size     = size
        self.logger   = logger

        self.entities = []
        self.generate()

    def generate(self):
        """
        Creates the container geometry
        """
        if self.shape == 'box':
            self.entities.append(factory.addBox(*self.size))
            self.dx = self.size[3]
            self.dy = self.size[4]
            self.dz = self.size[5]
        elif self.shape == 'cylinder':
            self.logger.warn("Support for cylindrical containers is minimal!")
            self.entities.append(factory.addCylinder(*self.size))
            self.dr = self.size[6]
            self.dz = self.size[5]

    @property
    def dimTags(self):
        return [ (3,tag) for tag in self.entities ]

    @property
    def tags(self):
        return self.entities

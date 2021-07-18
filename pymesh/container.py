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

factory = gmsh.model.occ

class Container:

    def __init__(self, shape, size):
        """
        Container instantiation
        """

        self.shape    = shape
        self.size     = size

        self.entities = []
        self.generate()

    def generate(self):
        """
        Creates the container geometry
        """
        if self.shape == 'box':
            if isinstance(self.size, list):
                self.entities.append(factory.addBox(*self.size))
                self.dx = self.size[3]
                self.dy = self.size[4]
                self.dz = self.size[5]
            else:
                print("ERROR: container.size must be a list", file=sys.stderr)
                raise(NotImplementedError)
        else:
            raise(NotImplementedError)

    def asDimTags(self):
        return [ (3,tag) for tag in self.entities ]

    def asTags(self):
        return self.entities

    def asCopyDimTags(self):
        return gmsh.model.occ.copy([ (3,tag) for tag in self.entities ])

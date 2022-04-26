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
from pymesh.tools import store_mesh, copy_mesh

factory = gmsh.model.occ

class Container:

    def __init__(self, shape, size, generate=True, logger=Logger(level=2)):
        """
        Container instantiation
        """

        self.shape    = shape
        self.size     = size
        self.logger   = logger

        self.entities = []
        if generate: 
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

    def copy_mesh(self, nodeTagsOffset, elementTagsOffset): 
        current_model = gmsh.model.getCurrent()

        gmsh.model.add("cylinder")
        self.generate()
        gmsh.model.occ.synchronize()

        s = gmsh.model.getEntities(2)

        self.set_mesh_fields_from_surfaces(s)

        gmsh.model.mesh.generate(2)

        m, _, _ = store_mesh(2)

        gmsh.model.setCurrent(current_model)

        ntoff = nodeTagsOffset
        etoff = elementTagsOffset

        ntoff, etoff = copy_mesh(m, ntoff, etoff)
        gmsh.model.setCurrent('cylinder')
        gmsh.model.remove()

        gmsh.model.setCurrent(current_model)

        s = gmsh.model.getEntities(2)

        l = gmsh.model.geo.addSurfaceLoop([e[1] for e in s])
        gmsh.model.geo.addVolume([l])
        gmsh.model.geo.synchronize()

        self.set_mesh_fields_from_surfaces(s)

        return ntoff, etoff

    def set_mesh_fields_from_surfaces(self, surfaceTags):

        factory = gmsh.model.occ
        field = gmsh.model.mesh.field

        factory.synchronize()

        ## Tags of distance and threshold fields
        dtags = []
        ttags = []

        
        # s = gmsh.model.getEntities(2)

        dtag = field.add('Distance')
        dtags.append(dtag)
        # field.setNumbers(dtag, 'PointsList', [ctag])
        ## TODO
        field.setNumbers(dtag, 'SurfacesList', [s[1] for s in surfaceTags ])

        # distmin = self.mesh_field_threshold_rad_min_factor * 1.0
        # distmax = self.mesh_field_threshold_rad_max_factor * 1.0

        distmin = 0.3
        distmax = 0.3

        ttag = field.add('Threshold')
        ttags.append(ttag)
        field.setNumber(ttag, "InField", dtag);
        field.setNumber(ttag, "SizeMin", 0.08);
        field.setNumber(ttag, "SizeMax", 0.14);
        field.setNumber(ttag, "DistMin", distmin);
        field.setNumber(ttag, "DistMax", distmax);

        ## Set background field
        # backgroundField = 'Min' if self.mesh_field_threshold_size_in <= self.mesh_field_threshold_size_out else 'Max'

        backgroundField = 'Min' 
        bftag = field.add(backgroundField);
        field.setNumbers(bftag, "FieldsList", ttags);
        field.setAsBackgroundMesh(bftag);



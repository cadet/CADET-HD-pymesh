"""
Container class.

- Should create a container based on the given config, and created packedBed
- if container.shape is None: don't create
- if container.size == 'auto' or None (default), take bounds from packed bed
- else create container from config
- MUST only have one container entity. Create multiple instances of this class for each linked section.


"""

import gmsh
from math import pi as PI

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

        if self.shape == 'box':
            self.x, self.y, self.z, self.dx, self.dy, self.dz = self.size
        elif self.shape == 'cylinder':
            self.x, self.y, self.z, self.dx, self.dy, self.dz, self.r = self.size

        self.update_bounds()
        self.logger.print(self.get_bounds())

        self.entities = []
        if generate: 
            self.generate()

    def generate(self):
        """
        Creates the container geometry
        """
        if self.shape == 'box':
            self.entities.append(factory.addBox(*self.size))
        elif self.shape == 'cylinder':
            self.logger.warn("Support for cylindrical containers is minimal!")
            self.entities.append(factory.addCylinder(*self.size))

    @property
    def dimTags(self):
        return [ (3,tag) for tag in self.entities ]

    @property
    def tags(self):
        return self.entities

    def copy_mesh(self, nodeTagsOffset, elementTagsOffset, config): 

        self.logger.warn("Copying container!!")
        current_model = gmsh.model.getCurrent()

        gmsh.model.add("cylinder")
        self.generate()
        gmsh.model.occ.synchronize()

        s = gmsh.model.getEntities(2)

        self.set_mesh_fields_constant(s,config)

        gmsh.model.mesh.generate(2)

        m, _, _ = store_mesh(2)

        gmsh.model.setCurrent(current_model)

        ntoff = nodeTagsOffset
        etoff = elementTagsOffset

        ntoff, etoff = copy_mesh(m, ntoff, etoff, boundaries=True)

        gmsh.model.setCurrent('cylinder')
        gmsh.model.remove()

        gmsh.model.setCurrent(current_model)

        s = gmsh.model.getEntities(2)

        l = gmsh.model.geo.addSurfaceLoop([e[1] for e in s])
        gmsh.model.geo.addVolume([l])
        gmsh.model.geo.synchronize()

        self.set_mesh_fields_from_surfaces(s, config)

        return ntoff, etoff

    def set_mesh_fields_from_surfaces(self, surfaceTags, config):

        factory = gmsh.model.occ
        field = gmsh.model.mesh.field

        factory.synchronize()

        ## Tags of distance and threshold fields
        dtags = []
        ttags = []

        dtag = field.add('Distance')
        dtags.append(dtag)
        field.setNumbers(dtag, 'SurfacesList', [s[1] for s in surfaceTags ])

        distmin = config.get('mesh.field.interstitial_surface_threshold.dist_min', vartype=float)
        distmax = config.get('mesh.field.interstitial_surface_threshold.dist_max', vartype=float)

        sizeon = config.get('mesh.field.interstitial_surface_threshold.size_on', vartype=float)
        sizeaway = config.get('mesh.field.interstitial_surface_threshold.size_away', vartype=float)

        ttag = field.add('Threshold')
        ttags.append(ttag)
        field.setNumber(ttag, "InField", dtag);
        field.setNumber(ttag, "SizeMin", sizeon);
        field.setNumber(ttag, "SizeMax", sizeaway);
        field.setNumber(ttag, "DistMin", distmin);
        field.setNumber(ttag, "DistMax", distmax);

        backgroundField = 'Min' 
        bftag = field.add(backgroundField);
        field.setNumbers(bftag, "FieldsList", ttags);
        field.setAsBackgroundMesh(bftag);


    def set_mesh_fields_constant(self, surfaceTags, config):

        field = gmsh.model.mesh.field
        factory.synchronize()

        ctags = []

        ctag = field.add('Constant')
        ctags.append(ctag)

        sizeon = config.get('mesh.field.interstitial_surface_threshold.size_on', vartype=float)
        sizeaway = config.get('mesh.field.interstitial_surface_threshold.size_away', vartype=float)

        field.setNumbers(ctag, 'SurfacesList', [s[1] for s in surfaceTags ])
        field.setNumber(ctag, 'VIn', sizeon)
        field.setNumber(ctag, 'VOut', sizeaway)

        backgroundField = 'Min' 
        bftag = field.add(backgroundField);
        field.setNumbers(bftag, "FieldsList", ctags);
        field.setAsBackgroundMesh(bftag);

    def update_bounds(self):
        if self.shape == 'box':
            self.xdelta = self.dx
            self.ydelta = self.dy
            self.zdelta = self.dz
            self.volume = self.dx * self.dy * self.dz
            self.cross_section_area = self.dx * self.dy
        elif self.shape == 'cylinder':
            self.xdelta = self.r * 2
            self.ydelta = self.r * 2
            self.zdelta = self.dz
            self.volume = PI * self.r**2 * self.dz
            self.cross_section_area = PI * self.r**2

        self.xmin = min(self.x, self.x + self.dx)
        self.xmax = max(self.x, self.x + self.dx)
        self.ymin = min(self.y, self.y + self.dy)
        self.ymax = max(self.y, self.y + self.dy)
        self.zmin = min(self.z, self.z + self.dz)
        self.zmax = max(self.z, self.z + self.dz)

    def get_bounds(self): 
        return {
            'shape': self.shape,
            'size': self.size,
            'xmin': self.xmin,
            'xmax': self.xmax,
            'ymin': self.ymin,
            'ymax': self.ymax,
            'zmin': self.zmin,
            'zmax': self.zmax,
            'xdelta': self.xdelta,
            'ydelta': self.ydelta,
            'zdelta': self.zdelta,
            'R': self.r,
            'cross_section_area': self.cross_section_area,
            'volume': self.volume,
        }

    def scale(self, factor, cx = 0.0, cy = 0.0, cz = 0.0):
        object.__setattr__(self, 'x', (self.x - cx) * factor)
        object.__setattr__(self, 'y', (self.y - cy) * factor)
        object.__setattr__(self, 'z', (self.z - cz) * factor)
        object.__setattr__(self, 'dx', (self.dx) * factor)
        object.__setattr__(self, 'dy', (self.dy) * factor)
        object.__setattr__(self, 'dz', (self.dz) * factor)
        object.__setattr__(self, 'r', (self.r) * factor)
        self.update_bounds()

        for tag in self.entities:
            # WARNING: Untested
            gmsh.model.occ.dilate([(3, tag)], cx, cy, cz, factor, factor, factor)


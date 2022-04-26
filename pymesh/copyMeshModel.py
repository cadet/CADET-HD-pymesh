"""
New CopyModel class that builds the column using 

contract:
    - must create individual columns given a config
    - must mesh the full model
    - must write output
"""

from pymesh.packedBed import PackedBed
from pymesh.container import Container
from pymesh.column import Column
from pymesh.log import Logger

from pymesh.tools import remove_all_except

import sys

import gmsh
from pathlib import Path

class CopyMeshModel:

    def __init__(self, config, logger=Logger(level=0)):

        self.logger = logger
        self.logger.out("Initializing CopyModel")

        self.container_periodicity = config.container_periodicity
        self.container_linked      = config.container_linked
        self.stack_method          = config.container_stack_method

        self.container_shape       = config.container_shape
        self.container_size        = config.container_size

        self.inlet_length          = config.container_inlet_length
        self.outlet_length         = config.container_outlet_length

        self.fname                 = config.output_filename
        self.mesh_size             = config.mesh_size
        self.mesh_size_method      = config.mesh_size_method
        self.mesh_generate         = config.mesh_generate

        self.fragment_format       = config.output_fragment_format if config.output_fragment_format[0] == '.' else f".{config.output_fragment_format}"

        ntoff = 0
        etoff = 0

        if config.container_shape == 'box': 
            self.logger.die("Box containers not implemented with copymesh.")

        self.packedBed = PackedBed(config, generate=False)
        ntoff, etoff = self.packedBed.copy_mesh(ntoff, etoff)

        if not config.container_shape:
            return

        column_container = Container(self.container_shape, self.container_size, generate=False)
        ntoff, etoff = column_container.copy_mesh(ntoff, etoff, config)
        # container_shell = column_container.generate_shell()

        self.logger.out('Creating central column section')
        self.column = Column(column_container, self.packedBed, fragment=False, copy=False, periodicity='', endFaceSections=config.container_end_face_sections)

        self.column.entities = gmsh.model.getEntities(dim=3)
        self.column.separate_volumes()
        self.column.assign_bounding_surfaces()

    def set_mesh_size(self):
        self.logger.out("Setting mesh size")
        if self.mesh_size_method == 'field':
            self.packedBed.set_mesh_fields()
        elif self.mesh_size_method == 'global':
            modelEntities = gmsh.model.getEntities()
            gmsh.model.mesh.setSize(modelEntities, self.mesh_size)

    def mesh(self):
        gmsh.model.occ.synchronize()
        # self.set_mesh_size()
        self.logger.out("Meshing")
        gmsh.model.mesh.generate(self.mesh_generate)

    def write(self):
        basename = Path(self.fname).stem
        extension = Path(self.fname).suffix

        # # This is almost never used in practice
        # self.logger.out("Writing full mesh")
        # gmsh.write(self.fname)

        if not self.container_shape:
            return

        self.column.write(basename + '_column' + extension, fragmentFormat=self.fragment_format)

        if self.container_linked :
            self.inlet.write(basename + '_inlet' + extension, fragmentFormat=self.fragment_format)
            self.outlet.write(basename + '_outlet' + extension, fragmentFormat=self.fragment_format)


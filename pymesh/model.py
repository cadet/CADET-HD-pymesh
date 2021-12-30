"""
Model class

contract:
    - must create individual columns given a config
    - must mesh the full model
    - must write output
"""

from pymesh.packedBed import PackedBed
from pymesh.container import Container
from pymesh.column import Column
from pymesh.log import Logger

import sys

import gmsh
from pathlib import Path

class Model:

    def __init__(self, config, logger=Logger(level=0)):

        self.logger = logger
        self.logger.out("Initializing Model")

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


        self.packedBed = PackedBed(config)

        if not config.container_shape:
            return

        column_container = Container(self.container_shape, self.container_size)

        ## NOTE: Column periodicity is taken directly from input. If linked=True, ensure that column is periodic in Z
        ## inlet and outlet periodicity ignores Z, always
        column_periodicity = self.container_periodicity + 'z' if self.container_linked and 'z' not in self.container_periodicity else self.container_periodicity
        inout_periodicity = self.container_periodicity.replace('z', '')

        ## Stack beads
        ## NOTE: It does a full 3D stacking of beads intersecting with
        ##      ALL the container walls, regardless of what the periodicity
        ##      actually is, as long as it's not an empty string.
        if column_periodicity:
            self.logger.out('Stacking packed bed')
            if self.stack_method == 'planecut':
                self.packedBed.stack_by_plane_cuts(column_container)
            elif self.stack_method == 'all':
                self.packedBed.stack_all(column_periodicity, column_container.dx, column_container.dy, column_container.dz)
            elif self.stack_method == 'volumecut':
                if self.container_linked:
                    self.logger.die("ConfigError: container.stack_method = volumecut cannot be used with container.linked = True")
                else:
                    self.packedBed.stack_by_volume_cuts(column_container)

        self.packedBed.write('beads_used.xyzd')

        if self.container_linked :
            inlet_size =  [
                self.container_size[0],
                self.container_size[1],
                self.container_size[2] - self.inlet_length,
                self.container_size[3],
                self.container_size[4],
                self.inlet_length
                ]

            self.logger.out('Creating inlet column section')
            inlet_container = Container('box', inlet_size)
            self.inlet = Column(inlet_container, self.packedBed, copy=True, periodicity=inout_periodicity)

            outlet_size = [
               self.container_size[0],
               self.container_size[1],
               self.container_size[2] + self.container_size[5],
               self.container_size[3],
               self.container_size[4],
               self.outlet_length
               ]
            self.logger.out('Creating outlet column section')
            outlet_container = Container('box', outlet_size)
            self.outlet = Column(outlet_container, self.packedBed, copy=True, periodicity=inout_periodicity)

        self.logger.out('Creating central column section')
        self.column = Column(column_container, self.packedBed, copy=False, periodicity=column_periodicity, endFaceSections=config.container_end_face_sections)

    def set_mesh_size(self):
        self.logger.out("Setting mesh size")
        if self.mesh_size_method == 'field':
            self.packedBed.set_mesh_fields()
        elif self.mesh_size_method == 'global':
            modelEntities = gmsh.model.getEntities()
            gmsh.model.mesh.setSize(modelEntities, self.mesh_size)

    def mesh(self):
        gmsh.model.occ.synchronize()
        self.set_mesh_size()
        self.logger.out("Meshing")
        gmsh.model.mesh.generate(self.mesh_generate)

    def write(self):
        basename = Path(self.fname).stem
        extension = Path(self.fname).suffix

        self.logger.out("Writing full mesh")
        gmsh.write(self.fname)

        if not self.container_shape:
            return

        self.column.write(basename + '_column' + extension)

        if self.container_linked :
            self.inlet.write(basename + '_inlet' + extension)
            self.outlet.write(basename + '_outlet' + extension)


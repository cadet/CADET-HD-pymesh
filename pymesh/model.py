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
from pymesh.configHandler import ConfigHandler

import sys

import gmsh
from pathlib import Path

class Model:

    def __init__(self, config):

        self.container_periodicity = config.get('container.periodicity', '')
        self.container_linked      = config.get('container.linked', False)
        self.stack_method          = config.get('container.stack_method', 'planecut')

        self.container_size        = config.get('container.size')

        ## To be used with container.size = auto, or container.linked = True
        self.inlet_length          = config.get('container.inlet_length', 0)
        self.outlet_length         = config.get('container.outlet_length', 0)

        self.fname                 = config.get('output.filename', 'output.vtk')
        self.mesh_size             = config.get('mesh.size', 0.2)
        self.mesh_generate         = config.get('mesh.generate', 3)

        self.packedBed = PackedBed(config)
        column_container = Container(config)

        ## NOTE: Column periodicity is taken directly from input. If linked=True, ensure that column is periodic in Z
        ## inlet and outlet periodicity ignores Z, always
        column_periodicity = self.container_periodicity + 'z' if self.container_linked and 'z' not in self.container_periodicity else self.container_periodicity
        inout_periodicity = self.container_periodicity.replace('z', '')

        ## Stack beads
        ## NOTE: It does a full 3D stacking of beads intersecting with
        ##      ALL the container walls, regardless of what the periodicity
        ##      actually is, as long as it's not an empty string.
        if column_periodicity:
            if self.stack_method == 'planecut':
                self.packedBed.stack_by_plane_cuts(column_container)
            elif self.stack_method == 'volumecut':
                self.packedBed.stack_by_volume_cuts(column_container)
            else:
                print("Config: container.stack_method must be either 'planecut' or 'volumecut'", file=sys.stderr)
                raise(ValueError)

        if self.container_linked :
            inlet_container_config = ConfigHandler().update({
                "container": {
                    "shape": "box",
                    "size" : [
                        self.container_size[0],
                        self.container_size[1],
                        self.container_size[2] - self.inlet_length,
                        self.container_size[3],
                        self.container_size[4],
                        self.inlet_length
                        ]
                    }
                })

            inlet_container = Container(inlet_container_config)
            self.inlet = Column(inlet_container, self.packedBed, copy=True, periodicity=inout_periodicity)

            outlet_container_config = ConfigHandler().update({
                "container": {
                    "shape": "box",
                    "size" : [
                        self.container_size[0],
                        self.container_size[1],
                        self.container_size[2] + self.container_size[5],
                        self.container_size[3],
                        self.container_size[4],
                        self.outlet_length
                        ],
                    }
                })
            outlet_container = Container(outlet_container_config)
            self.outlet = Column(outlet_container, self.packedBed, copy=True, periodicity=inout_periodicity)

        self.column = Column(column_container, self.packedBed, copy=False, periodicity=column_periodicity)

    def set_mesh_size(self):
        modelEntities = gmsh.model.getEntities()
        gmsh.model.mesh.setSize(modelEntities, self.mesh_size)

    def mesh(self):
        gmsh.model.occ.synchronize()
        self.set_mesh_size()
        gmsh.model.mesh.generate()

    def write(self):
        basename = Path(self.fname).stem
        extension = Path(self.fname).suffix

        gmsh.write(self.fname)

        self.column.write(basename + '_column' + extension)

        if self.container_linked :
            self.inlet.write(basename + '_inlet' + extension)
            self.outlet.write(basename + '_outlet' + extension)


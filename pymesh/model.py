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
from pymesh.tools import deep_get

import gmsh
from pathlib import Path

class Model:

    def __init__(self, config):
        self.config = config

        self.container_periodic = deep_get(self.config, 'container.periodic')
        self.container_linked = deep_get(self.config, 'container.linked')

        self.container_size= deep_get(self.config, 'container.size')

        ## To be used with container.size == auto, or container.linked = True
        self.inlet_length = deep_get(self.config, 'container.inlet_length')
        self.outlet_length = deep_get(self.config, 'container.outlet_length')

        self.periodic = deep_get(self.config, 'container.periodic')

        column_container = Container(config)
        self.packedBed = PackedBed(config)

        ## Stack beads
        self.packedBed.stack_by_cut_planes(column_container)

        if self.container_linked :
            inlet_container_config = {
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
            }
            inlet_container = Container(inlet_container_config)
            self.inlet = Column(inlet_container, self.packedBed, copy=True, periodic=True)

            outlet_container_config = {
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
            }
            outlet_container = Container(outlet_container_config)
            self.outlet = Column(outlet_container, self.packedBed, copy=True, periodic=True)

        self.column = Column(column_container, self.packedBed, copy=False, periodic=self.container_periodic)

        # self.mesh()
        # self.write()

    def set_mesh_size(self):
        modelEntities = gmsh.model.getEntities()
        size = deep_get(self.config, 'mesh.size', 0.2)
        gmsh.model.mesh.setSize(modelEntities, size)

    def mesh(self):
        gmsh.model.occ.synchronize()
        self.set_mesh_size()
        gmsh.model.mesh.generate(deep_get(self.config, 'mesh.generate', 3))

    def write(self):
        fname = deep_get(self.config, 'output.filename', 'output.vtk')
        basename = Path(fname).stem
        extension = Path(fname).suffix

        gmsh.write(fname)

        self.column.write(basename + '_column' + extension)

        if self.container_linked :
            self.inlet.write(basename + '_inlet' + extension)
            self.outlet.write(basename + '_outlet' + extension)

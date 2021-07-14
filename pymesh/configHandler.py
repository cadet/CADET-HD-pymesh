"""

ConfigHandler class.

contract:
    - must read and store values from yaml config
    - must provide easy access to deep/nested values (deep_get -> get)
    - must set gmsh default values
    - [TASK] must set dynamic gmsh defaults from config.gmsh
"""
import yaml
import gmsh

from functools import reduce

class ConfigHandler:

    def __init__(self, fname):
        self.config = {}
        with open(fname, 'r') as fp:
            self.config = yaml.load(fp, Loader=yaml.FullLoader)

    def get(self, keys, default=None):
        """
        Simpler syntax to get deep values from a dictionary
        > deep_get(dict, 'key1.key2.key3', defaultValue)
        """
        return reduce(lambda d, key: d.get(key, default) if isinstance(d, dict) else default, keys.split("."), self.config)

    def set_gmsh_defaults(self):

        gmsh.option.setNumber('General.Terminal', 1)

        # 1: MeshAdapt | 2: Auto | 5: Delaunay | 6: Frontal | 7: BAMG | 8: DelQuad
        gmsh.option.setNumber("Mesh.Algorithm", self.get('mesh.algorithm', 5)) # Default = 2
        # 1: Delaunay | 4: Frontal | 5: Frontal Delaunay | 6: Frontal Hex | 7: MMG3D | 9: RTree | 10: HXT
        gmsh.option.setNumber("Mesh.Algorithm3D", self.get('mesh.algorithm3D', 10)) # Default = 1

        if int(gmsh.GMSH_API_VERSION_MAJOR) == 4:
            if int(gmsh.GMSH_API_VERSION_MINOR) >= 9:
                ## Improved bounding box calculations,can slow things down
                gmsh.option.setNumber("Geometry.OCCBoundsUseStl"  , 1)
                gmsh.option.setNumber("Mesh.StlAngularDeflection" , 0.08 )
                gmsh.option.setNumber("Mesh.StlLinearDeflection"  , 0.0005)

        # gmsh.option.setNumber("Geometry.OCCFixDegenerated"  , 1)
        # gmsh.option.setNumber("Geometry.OCCFixSmallEdges"  , 1)
        # gmsh.option.setNumber("Geometry.OCCFixSmallFaces"  , 1)
        # gmsh.option.setNumber("Mesh.MeshSizeFromCurvature"  , 1)

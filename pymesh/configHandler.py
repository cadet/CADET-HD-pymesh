"""

ConfigHandler class.

contract:
    - must read and store values from yaml config
    - must provide easy access to deep/nested values (deep_get -> get)
    - must set gmsh default values
    - [TASK] must set dynamic gmsh defaults from config.gmsh
    - [NOTE] By current design, there are no global defaults for input options.
        Defaults are set within callers.

"""
import yaml
import gmsh

from functools import reduce
from itertools import combinations

from pymesh.log import Logger

class ConfigHandler:

    def __init__(self, logger=None):
        self.logger = logger or Logger()
        self.logger.out('Creating config')
        self.config = {}

    def read(self, fname):
        self.logger.out('Reading config file')
        with open(fname, 'r') as fp:
            self.config = yaml.load(fp, Loader=yaml.FullLoader)
        self.logger.print(self.config)
        self.load()

    def get(self, keys, default=None, vartype=None, choices=[]):
        """
        Simpler syntax to get deep values from a dictionary
        > config.get('key1.key2.key3', defaultValue)

        - typechecking
        - value restriction
        """
        value = reduce(lambda d, key: d.get(key, None) if isinstance(d, dict) else None, keys.split("."), self.config)

        if value == None:
            if default != None:
                self.logger.warn(keys, 'not specified! Defaulting to', str(default) or 'None (empty string)')
                value = default

        if vartype:
            if not isinstance(value, vartype):
                self.logger.die(keys, 'has invalid type!', str(type(value)), 'instead of', str(vartype))

        if choices:
            if value not in choices:
                self.logger.die(keys, 'has invalid value! Must be one of ', str(choices))

        return value

    def load(self):
        """
        Assign values from the loaded dict to the object's attributes
        Centralizes the config value and type checking
        """

        self.logger.out('Loading config values')

        directions = ['x', 'y', 'z']
        periodicity_choices = [ "".join(x) for i in range(0, len(directions)+1) for x in combinations(directions,i) ]
        packing_file_format_choices = [ '<f', '<d', '>f', '>d' ]

        self.packing_file_name                   = self.get('packedbed.packing_file.filename', 'packing.xyzd', str())
        self.packing_file_format                 = self.get('packedbed.packing_file.dataformat', vartype=str(), choices =packing_file_format_choices)
        self.packedbed_nbeads                    = self.get('packedbed.nbeads', 0, int)
        self.packedbed_zbot                      = self.get('packedbed.zbot', 0.0, float)
        self.packedbed_ztop                      = self.get('packedbed.ztop', 0.0, float)
        self.packedbed_scaling_factor            = self.get('packedbed.scaling_factor', 1.0, float)
        self.packedbed_particles_scaling_factor  = self.get('packedbed.particles.scaling_factor', 1.0, float)
        self.packedbed_auto_translate            = self.get('packedbed.auto_translate', False, bool)

        self.container_shape                     = self.get('container.shape', '', vartype=str(), choices = ['box', ''])
        self.container_size                      = self.get('container.size', [], vartype=list)
        self.container_periodicity               = self.get('container.periodicity', '', str(), periodicity_choices)
        self.container_linked                    = self.get('container.linked', False, bool)
        self.container_stack_method              = self.get('container.stack_method', 'planecut', str(), ['planecut', 'volumecut', 'all'])
        self.container_inlet_length              = self.get('container.inlet_length', 0.0, float)
        self.container_outlet_length             = self.get('container.outlet_length', 0.0, float)

        self.mesh_size_method                    = self.get('mesh.size_method', 'global', str(), ['global', 'field'])
        self.mesh_size                           = self.get('mesh.size', 0.2, float)
        self.mesh_field_threshold_size_in        = self.get('mesh.field.threshold.size_in', self.mesh_size, float)
        self.mesh_field_threshold_size_out       = self.get('mesh.field.threshold.size_out', self.mesh_size, float)
        self.mesh_field_threshold_rad_min_factor = self.get('mesh.field.threshold.rad_min_factor', 1.0, float)
        self.mesh_field_threshold_rad_max_factor = self.get('mesh.field.threshold.rad_max_factor', 1.0, float)
        self.mesh_ref_radius                     = self.get('mesh.ref_radius', 'avg', str(), ['avg', 'max', 'min'])
        self.mesh_generate                       = self.get('mesh.generate', 3, int, [0,1,2,3])

        self.output_filename                     = self.get('output.filename', 'output.vtk', str())

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

    def set_gmsh_options(self):
        gmsh_conf = self.get('gmsh', {})

        for option,value in gmsh_conf.items():
            gmsh.option.setNumber(option, value)


class ConfigError(Exception):
    """
    Class to indicate error in input config

    Can potentially be used to invoke logger.die() from within it.
    """
    pass
    # def __init__(self):
    #     print("Please ensure that config is correct and consistent.")

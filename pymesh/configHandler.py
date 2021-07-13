import yaml
import gmsh

from pymesh.tools import deep_get

def load_config(fname):
    config = {}
    with open(fname, 'r') as fp:
        config = yaml.load(fp, Loader=yaml.FullLoader)
    return config

def set_gmsh_defaults(config):
    gmsh.option.setNumber('General.Terminal', 1)

    # gmsh.option.setNumber("Print.GeoLabels", 1) #Default = 1
    # gmsh.option.setNumber('Print.GeoOnlyPhysicals', 1)

    # 1: MeshAdapt | 2: Auto | 5: Delaunay | 6: Frontal | 7: BAMG | 8: DelQuad
    gmsh.option.setNumber("Mesh.Algorithm", deep_get(config, 'mesh.algorithm', 5)) # Default = 2
    # 1: Delaunay | 4: Frontal | 5: Frontal Delaunay | 6: Frontal Hex | 7: MMG3D | 9: RTree | 10: HXT
    gmsh.option.setNumber("Mesh.Algorithm3D", deep_get(config, 'mesh.algorithm3D', 10)) # Default = 1

    ## Improved bounding box calculations
    ## Can slow things down
    gmsh.option.setNumber("Geometry.OCCBoundsUseStl"  , 1)
    gmsh.option.setNumber("Geometry.OCCFixDegenerated"  , 1)
    gmsh.option.setNumber("Geometry.OCCFixSmallEdges"  , 1)
    gmsh.option.setNumber("Geometry.OCCFixSmallFaces"  , 1)
    # gmsh.option.setNumber("Mesh.StlAngularDeflection" , 0.08 )
    # gmsh.option.setNumber("Mesh.StlLinearDeflection"  , 0.0005)
    # gmsh.option.setNumber("Mesh.MeshSizeFromCurvature"  , 1)

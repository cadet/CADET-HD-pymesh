import struct
import itertools
from functools import reduce

import gmsh
import numpy as np

def bin_to_arr(filename, format):
    """
    Read binary data into array
    """

    with(open(filename, 'rb')) as input:
        myiter = struct.iter_unpack(format, input.read())

        arr = []
        for i in myiter:
            arr.append(i[0])

        return arr

def grouper(iterable, n):
    """
    Group binary data into chunks after reading
    """
    it = iter(iterable)
    while True:
       chunk = tuple(itertools.islice(it, n))
       if not chunk:
           return
       yield chunk

def get_volume_normals(entities):
    """
    Given a list of volume entities, calculate all normals for all surfaces
    Return a list of list of normals.
    """
    gmsh.model.occ.synchronize()

    output = []

    for e in entities:
        boundaries = gmsh.model.getBoundary([e], False, False, False)
        normals = get_surface_normals(boundaries)
        output.append(normals)

    return output

def filter_volumes_with_normal(entities, ref_normal):
    """
    Given a list of 3D entities, and reference normal, return a list of entities with surfaces with normals pointing in the reference normal direction.
    """
    gmsh.model.occ.synchronize()

    output_entities = []

    for e in entities:
        boundaries = gmsh.model.getBoundary([e], False, False, False)

        normals = [get_surface_normal_inner(surface) for surface in boundaries]

        for n in normals:
            if np.allclose(n, ref_normal):
                output_entities.append(e)
                break;

    return output_entities


def get_surface_normals(entities):
    """
    Provided a list of 2D dimtags, return a list of normals to the surfaces
    """
    factory = gmsh.model.occ
    factory.synchronize()
    output = [get_surface_normal_inner(surface) for surface in entities]
    return output

def get_surface_normal_inner(surface:tuple):
    points = gmsh.model.getBoundary([surface], False, False, True)
    normals = []
    coord = [x for point in points for x in gmsh.model.getValue(point[0], point[1], []) ]
    pCoord = gmsh.model.getParametrization(surface[0], surface[1], coord)
    curv = gmsh.model.getCurvature(surface[0], surface[1], pCoord)
    if any(curv):
        return np.array([0,0,0])
    normals = gmsh.model.getNormal(surface[1], pCoord)

    # normals = np.array(gmsh.model.getNormal(surface[1], pCoord)).reshape((len(curv), 3))
    ## If normals of all points are the same,
    ## (column-wise check if all numbers are same)
    # if all(np.all(normals == normals[0,:], axis = 0)):

    ## If it's not a curved surface, all points have the same normal
    return normals[0:3]


def testMesh(fname, size=0.2, dim=3):
    factory = gmsh.model.occ
    factory.synchronize()
    ent = gmsh.model.getEntities(0)
    gmsh.model.mesh.setSize(ent, size)
    gmsh.model.mesh.generate(dim)
    gmsh.write(fname)

def remove_all_except(entities):
    factory = gmsh.model.occ
    print(entities)
    dims = [ dim for dim,_ in entities ]
    ## If all dims are same
    if dims.count(dims[0]) == len(dims):
        if dims[0] == 3:
            all = factory.getEntities(dim=3)
            factory.remove([e for e in all if e not in entities], recursive=True)
        elif dims[0] == 2:
            factory.remove(factory.getEntities(dim=3))
            factory.remove([e for e in factory.getEntities(dim=2) if e not in entities], recursive=True)
            factory.remove(factory.getEntities(1))
            factory.remove(factory.getEntities(0))


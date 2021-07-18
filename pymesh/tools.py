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

    NOTE: Unfortunately seems broken. For some reason, gmsh normals aren't that predictable after performing fragmentation with 2D surfaces.
    In my case, beads cut by the z+ plane didn't have a normal pointing in the z+ direction, even though every other direction followed the pattern.
    It might eventually be fixed upstream.
    """
    gmsh.model.occ.synchronize()

    output_entities = []

    for e in entities:
        boundaries = gmsh.model.getBoundary([e], False, False, False)

        for surface in boundaries:
            points = gmsh.model.getBoundary([surface], False, False, True)

            for point in points:
                # coord.extend(gmsh.model.getValue(point[0], point[1], []))
                coord = gmsh.model.getValue(point[0], point[1], [])

                # pCoord = gmsh.model.getParametrization(surface[0], surface[1], coord)
                try:
                    pCoord = gmsh.model.getParametrization(surface[0], surface[1], coord)
                except:
                    print("Some error with getting parametrization.")
                    continue

                curv = gmsh.model.getCurvature(surface[0], surface[1], pCoord)

                ## Don't bother with non-zero curvature surfaces
                if any(curv):
                    break

                normals = gmsh.model.getNormal(surface[1], pCoord)

                # print("Surface: {tag}\nCurv: {curv}\nNormals:{normals}\nRefN:{ref}".format(tag=e[1], curv=curv, normals=normals, ref=np.tile(ref_normals, len(curv))))

                # if np.array_equals(normals, np.tile(ref_normals,len(curv))):
                if np.allclose(normals, np.tile(ref_normal,len(curv))):
                    output_entities.append(e)
                    # print("MATCH")
                    break
                # print("---")

    print("Finished Filtering")
    return output_entities


def get_surface_normals(entities):
    """
    Provided a list of 2D dimtags, return a list of normals to the surfaces
    """
    factory = gmsh.model.occ
    factory.synchronize()
    output = []
    for surface in entities:
        points = gmsh.model.getBoundary([surface], False, False, True)
        normals = []
        for point in points:
            coord  = gmsh.model.getValue(point[0], point[1], [])
            pCoord = gmsh.model.getParametrization(surface[0], surface[1], coord)
            curv = gmsh.model.getCurvature(surface[0], surface[1], pCoord)
            if any(curv):
                # print("get_surface_normal: Detected non-zero curvature to surface", surface[1], ". Setting 0 normal...")
                normals.append([0,0,0])
            else:
                normals.append(gmsh.model.getNormal(surface[1], pCoord))
        normals = np.array(normals)
        # print(normals)
        ## If normals of all points are the same,
        ## (column-wise check if all numbers are same)
        if all(np.all(normals == normals[0,:], axis = 0)):
            output.append(normals[0].tolist())
        else:
            raise(ValueError)

    return output

def testMesh(fname, size=0.2):
    factory = gmsh.model.occ
    factory.synchronize()
    ent = gmsh.model.getEntities(0)
    gmsh.model.mesh.setSize(ent, size)
    gmsh.model.mesh.generate(3)
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


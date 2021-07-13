import struct
import itertools
from functools import reduce

import gmsh
import numpy as np

def bin_to_arr(filename, f):
    """
    Read binary data into array
    """

    with(open(filename, 'rb')) as input:
        myiter = struct.iter_unpack(f, input.read())

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

def deep_get(dictionary, keys, default=None):
    """
    Simpler syntax to get deep values from a dictionary
    > deep_get(dict, 'key1.key2.key3', defaultValue)
    """
    return reduce(lambda d, key: d.get(key, default) if isinstance(d, dict) else default, keys.split("."), dictionary)


def filter_volumes_with_normal(entities, ref_normals):
    print("Started Filtering")

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
                if np.allclose(normals, np.tile(ref_normals,len(curv))):
                    output_entities.append(e)
                    # print("MATCH")
                    break
                # print("---")

    print("Finished Filtering")
    return output_entities

def stackPeriodic(entities, periodic_directions:str, dx, dy, dz):

    factory = gmsh.model.occ

    x_offset_multiplier = [-1, 0, 1]  if 'x' in periodic_directions else [0]
    y_offset_multiplier = [-1, 0, 1]  if 'y' in periodic_directions else [0]
    z_offset_multiplier = [-1, 0, 1]  if 'z' in periodic_directions else [0]

    stacked_entities = entities[:]

    for zom in z_offset_multiplier:
        for yom in y_offset_multiplier:
            for xom in x_offset_multiplier:
                if xom == 0 and yom == 0 and zom == 0: continue
                dummy = factory.copy(entities)
                stacked_entities.extend(dummy)
                factory.translate(dummy, xom * dx, yom * dy, zom * dz)

    return stacked_entities

def get_surface_normals(entities):
    output = []
    for surface in entities:
        points = gmsh.model.getBoundary([surface], False, False, True)
        normals = []
        for point in points:
            coord  = gmsh.model.getValue(point[0], point[1], [])
            pCoord = gmsh.model.getParametrization(surface[0], surface[1], coord)
            curv = gmsh.model.getCurvature(surface[0], surface[1], pCoord)
            # if any(curv):
            #     print("get_surface_normal: Detected non-zero curvature to surface", surface[2], ". Skipping...")
            #     break
            normals.append(gmsh.model.getNormal(surface[1], pCoord))
        normals = np.array(normals)
        # print(normals)
        ## If normals of all points are the same,
        if all(np.all(normals == normals[0,:], axis = 0)):
            output.append(normals[0].tolist())

    return output


            # print(face, ': ', normals)


def stackMinimal(packedBed, container, periodic_directions='xyz'):
    factory = gmsh.model.occ
    fragmented, fmap = factory.fragment(packedBed.asDimTags(), container.asDimTags(), False, False)
    pass










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

    # output = []

    for e in entities:
        boundaries = gmsh.model.getBoundary([e], False, False, False)
        normals = list(get_surface_normals(boundaries))
        yield normals
        # output.append(normals)

    # return output

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

def filter_surfaces_with_normal(entities, ref_normal):
    """
    Given a list of 2D entities and reference normal, return a list of entities with surfaces
    """

    normals = get_surface_normals(entities)

    return [ x[0] for x in filter(lambda z: np.allclose(z[1],ref_normal), zip(entities,normals))]


def get_surface_normals(entities):
    """
    Provided a list of 2D dimtags, return a list of normals to the surfaces
    """
    factory = gmsh.model.occ
    factory.synchronize()
    # output = [get_surface_normal_inner(surface) for surface in entities]
    # output = [get_surface_normal_inner_firstpoint(surface) for surface in entities]
    # return output
    for surface in entities:
        yield get_surface_normal_inner_firstpoint(surface)

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

def get_surface_normal_inner_firstpoint(surface:tuple):
    points = gmsh.model.getBoundary([surface], False, False, True)
    point = points[0]
    coord = gmsh.model.getValue(point[0], point[1], [])
    pCoord = gmsh.model.getParametrization(surface[0], surface[1], coord)
    curv = gmsh.model.getCurvature(surface[0], surface[1], pCoord)
    if any(curv):
        return np.array([0,0,0])
    normal = gmsh.model.getNormal(surface[1], pCoord)
    return normal

def testMesh(fname, size=0.2, dim=3):
    factory = gmsh.model.occ
    factory.synchronize()
    ent = gmsh.model.getEntities(0)
    gmsh.model.mesh.setSize(ent, size)
    gmsh.model.mesh.generate(dim)
    gmsh.write(fname)

def remove_all_except(entities):
    gmsh.model.occ.synchronize()
    gmsh.model.geo.synchronize()
    print(entities)
    dims = [ dim for dim,_ in entities ]
    ## If all dims are same
    if dims.count(dims[0]) == len(dims):
        if dims[0] == 3:
            all = gmsh.model.getEntities(dim=3)
            gmsh.model.removeEntities([e for e in all if e not in entities], recursive=True)
        elif dims[0] == 2:
            gmsh.model.removeEntities(gmsh.model.getEntities(dim=3))
            gmsh.model.removeEntities([e for e in gmsh.model.getEntities(dim=2) if e not in entities], recursive=True)
    gmsh.model.occ.synchronize()
    gmsh.model.geo.synchronize()


def remove_physical_groups(): 
    """
    Needed because for some reason, removing physical groups doesn't remove physical names
    """
    model = gmsh.model
    groups = model.getPhysicalGroups()
    names = [ model.getPhysicalName(x[0], x[1]) for x in groups] 

    for name in names:
        model.removePhysicalName(name)

    model.removePhysicalGroups()


def copy_mesh(m, nodeTagsOffset, elemTagsOffset, xoff=0.0, yoff=0.0, zoff=0.0, xscale=1.0, yscale=1.0, zscale=1.0, boundaries=False): 
    for e in sorted(m):
        coords = np.array(m[e][1][1])

        coords[0::3] *= xscale
        coords[1::3] *= yscale
        coords[2::3] *= zscale

        coords[0::3] += xoff
        coords[1::3] += yoff
        coords[2::3] += zoff

        # Because beads are copied, relying on boundaries is not easy
        # since boundaries do not get automatically moved, and we get wrongly
        # matched volume boundaries
        if boundaries: 
            boundaries_tags = [b[1] for b in m[e][0]] 
        else: 
            boundaries_tags = []

        tag = gmsh.model.addDiscreteEntity(e[0], -1, boundaries_tags)
        gmsh.model.mesh.addNodes(e[0], tag, 
                [ nodeTagsOffset + t for t in m[e][1][0] ], 
                coords.tolist()
                )
        gmsh.model.mesh.addElements(e[0], tag, 
                m[e][2][0], 
                [ elemTagsOffset + t for t in m[e][2][1]] , 
                [ nodeTagsOffset + t for t in m[e][2][2] ] )

    ntoff = nodeTagsOffset + max([ max(v[1][0]) for k,v in m.items() if len( v[1][0] ) != 0 ])
    etoff = elemTagsOffset + max([ max(v[2][1][elemtypeindex]) for k,v in m.items() for elemtypeindex,_ in enumerate(v[2][0]) if  len(v[2][1][elemtypeindex]) != 0 ])

    return ntoff, etoff


def store_mesh(maxDim=-1): 
    m = {}
    entities = []
    for dim in range(maxDim+1) or [-1]: 
        entities.extend(gmsh.model.getEntities(dim)) 
    for e in entities:  
        m[e] = (gmsh.model.getBoundary([e]),
                gmsh.model.mesh.getNodes(e[0], e[1]),
                gmsh.model.mesh.getElements(e[0], e[1]))

    # for k,v in m.items():
    #     for elemtypeindex,elemtype in enumerate(v[2][0]): 
    #         if len(v[2][1][elemtypeindex]) != 0: 
    #             print(max(v[2][1][elemtypeindex]))
    ntoff = max([ max(v[1][0]) for k,v in m.items() if len( v[1][0] ) != 0 ])
    etoff = max([ max(v[2][1][elemtypeindex]) for k,v in m.items() for elemtypeindex,_ in enumerate(v[2][0]) if  len(v[2][1][elemtypeindex]) != 0 ])

    return m, ntoff, etoff

import gmsh
import sys
import numpy as np

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

def remove_all_except(entities):
    factory = gmsh.model.occ
    factory.synchronize()
    gmsh.model.geo.synchronize()
    dims = [ dim for dim,_ in entities ]
    ## If all dims are same
    if dims.count(dims[0]) == len(dims):
        if dims[0] == 3:
            all = gmsh.model.getEntities(dim=3)
            gmsh.model.removeEntities([e for e in all if e not in entities], recursive=True)
        elif dims[0] == 2:
            gmsh.model.removeEntities(gmsh.model.getEntities(dim=3))
            gmsh.model.removeEntities([e for e in gmsh.model.getEntities(dim=2) if e not in entities], recursive=True)
    factory.synchronize()
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


def copy_mesh(m, nodeTagsOffset, elemTagsOffset, xoff=0.0, yoff=0.0, zoff=0.0, xscale=1.0, yscale=1.0, zscale=1.0): 
    for e in sorted(m):
        coords = np.array(m[e][1][1])

        coords[0::3] *= xscale
        coords[1::3] *= yscale
        coords[2::3] *= zscale

        coords[0::3] += xoff
        coords[1::3] += yoff
        coords[2::3] += zoff

        # tag = gmsh.model.addDiscreteEntity(e[0], -1, [b[1] for b in m[e][0]])
        tag = gmsh.model.addDiscreteEntity(e[0])
        gmsh.model.mesh.addNodesCustom(e[0], tag, 
                [ nodeTagsOffset + t for t in m[e][1][0] ], 
                coords.tolist()
                )
        gmsh.model.mesh.destroyMeshCaches()
        gmsh.model.mesh.addElementsCustom(e[0], tag, 
                m[e][2][0], 
                [ elemTagsOffset + t for t in m[e][2][1]] , 
                [ nodeTagsOffset + t for t in m[e][2][2] ] )

    ntoff = nodeTagsOffset + max([ max(v[1][0]) for k,v in m.items() if len( v[1][0] ) != 0 ])
    etoff = elemTagsOffset + max([ max(v[2][1][elemtypeindex]) for k,v in m.items() for elemtypeindex,_ in enumerate(v[2][0]) if  len(v[2][1][elemtypeindex]) != 0 ])

    print("Done copying")

    return ntoff, etoff

def addNodesWrapper(m, nodeTagsOffset, xoff=0.0, yoff=0.0, zoff=0.0, xscale=1.0, yscale=1.0, zscale=1.0): 
    tags = []
    for e in sorted(m):
        coords = np.array(m[e][1][1])

        coords[0::3] *= xscale
        coords[1::3] *= yscale
        coords[2::3] *= zscale

        coords[0::3] += xoff
        coords[1::3] += yoff
        coords[2::3] += zoff

        # tag = gmsh.model.addDiscreteEntity(e[0], -1, [b[1] for b in m[e][0]])
        tag = gmsh.model.addDiscreteEntity(e[0])
        tags.append(tag)
        gmsh.model.mesh.addNodesCustom(e[0], tag, 
                [ nodeTagsOffset + t for t in m[e][1][0] ], 
                coords.tolist()
                )

    ntoff = nodeTagsOffset + max([ max(v[1][0]) for k,v in m.items() if len( v[1][0] ) != 0 ])

    print("Done copying nodes")
    return ntoff, tags

def addElementsWrapper(m, nodeTagsOffset, elemTagsOffset, tags): 
    for e, tag in zip(sorted(m), tags):
        gmsh.model.mesh.addElementsCustom(e[0], tag, 
                m[e][2][0], 
                [ elemTagsOffset + t for t in m[e][2][1]] , 
                [ nodeTagsOffset + t for t in m[e][2][2] ] )

    etoff = elemTagsOffset + max([ max(v[2][1][elemtypeindex]) for k,v in m.items() for elemtypeindex,_ in enumerate(v[2][0]) if  len(v[2][1][elemtypeindex]) != 0 ])
    print("Done fixing elements")
    return etoff

def store_mesh(maxDim=-1): 
    m = {}
    entities = []
    for dim in range(maxDim+1) or [-1]: 
        entities.extend(gmsh.model.getEntities(dim)) 
    for e in entities:  
        m[e] = (gmsh.model.getBoundary([e], combined=False, oriented=False, recursive=False ),
                gmsh.model.mesh.getNodes(e[0], e[1]),
                gmsh.model.mesh.getElements(e[0], e[1]))

    # for k,v in m.items():
    #     for elemtypeindex,elemtype in enumerate(v[2][0]): 
    #         if len(v[2][1][elemtypeindex]) != 0: 
    #             print(max(v[2][1][elemtypeindex]))
    ntoff = max([ max(v[1][0]) for k,v in m.items() if len( v[1][0] ) != 0 ])
    etoff = max([ max(v[2][1][elemtypeindex]) for k,v in m.items() for elemtypeindex,_ in enumerate(v[2][0]) if  len(v[2][1][elemtypeindex]) != 0 ])

    return m, ntoff, etoff

gmsh.initialize()

gmsh.option.setNumber('General.Verbosity', 99)

gmsh.model.add("sphere")
gmsh.model.occ.addSphere(0, 0, 0, 1)
gmsh.model.occ.synchronize()
gmsh.model.mesh.generate(3)

gmsh.model.add("cylinder")
gmsh.model.occ.addCylinder(0, 0, -5, 0, 0, 10, 1.5)
gmsh.model.occ.synchronize()
gmsh.model.mesh.generate(2)

gmsh.model.add('main')

gmsh.model.setCurrent('cylinder')
m_cyl, nt_cyl, et_cyl= store_mesh(2)


gmsh.model.setCurrent('sphere')
m_sph, nt_sph, et_sph= store_mesh()

gmsh.model.setCurrent('main')
ntoff = 0 
etoff = 0
# ntoff, etoff = copy_mesh(m_sph, ntoff, etoff)
# ntoff, etoff = copy_mesh(m_sph, ntoff, etoff, zoff=3.0)

# ntoff1, tags = addNodesWrapper(m_sph, ntoff)
# gmsh.model.mesh.destroyMeshCaches()
# etoff1 = addElementsWrapper(m_sph, ntoff, etoff, tags)
#
# ntoff2, tags2 = addNodesWrapper(m_sph, ntoff1, zoff=3.0)
# gmsh.model.mesh.destroyMeshCaches()
# etoff2 = addElementsWrapper(m_sph, ntoff1, etoff1, tags2)

ntoff1, tags = addNodesWrapper(m_sph, ntoff)
ntoff2, tags2 = addNodesWrapper(m_sph, ntoff1, zoff=3.0)
gmsh.model.mesh.destroyMeshCaches()
etoff1 = addElementsWrapper(m_sph, ntoff, etoff, tags)
etoff2 = addElementsWrapper(m_sph, ntoff1, etoff1, tags2)

ntoff, etoff = copy_mesh(m_cyl, ntoff2, etoff2)

gmsh.model.setCurrent('cylinder')
gmsh.model.remove()
gmsh.model.setCurrent('sphere')
gmsh.model.remove()

gmsh.write('test.vtk')

s = gmsh.model.getEntities(2)

l = gmsh.model.geo.addSurfaceLoop([e[1] for e in s])
vtag = gmsh.model.geo.addVolume([l])

gmsh.model.geo.synchronize()

gmsh.model.mesh.generate(3)
gmsh.write('test_volume.vtk')

gmsh.model.addPhysicalGroup(3, [1], 1)
gmsh.model.setPhysicalName(3, 1, "particles")

gmsh.write('test_volume_particles.vtk')

remove_physical_groups()

gmsh.model.addPhysicalGroup(3, [2], 2)
gmsh.model.setPhysicalName(3, 2, "bulk")
gmsh.write('test_volume_bulk.vtk')

# object boundaries are fucked up
# remove_physical_groups()

# # object boundaries are fucked up
# v = gmsh.model.getEntities(3)
# sa = gmsh.model.getEntities(2)
# s = gmsh.model.getBoundary([(3,2)])
#
# gmsh.model.mesh.generate(3)
# print(list(get_surface_normals(sa)))
#
# # # print(v)
# # print(sa)
# # print(s)
#
# # remove_all_except(sa)
# # gmsh.write('mesh.vtk')
#

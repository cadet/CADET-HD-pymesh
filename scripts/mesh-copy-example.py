import gmsh
import sys
import numpy as np

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

        tag = gmsh.model.addDiscreteEntity(e[0], -1, [b[1] for b in m[e][0]])
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

gmsh.initialize()

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
ntoff, etoff = copy_mesh(m_sph, ntoff, etoff)
ntoff, etoff = copy_mesh(m_sph, ntoff, etoff, zoff=3.0)
ntoff, etoff = copy_mesh(m_cyl, ntoff, etoff)

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

gmsh.model.addPhysicalGroup(3, [1,2], 1)
gmsh.model.setPhysicalName(3, 1, "particles")

gmsh.write('test_volume_particles.vtk')

remove_physical_groups()

gmsh.model.addPhysicalGroup(3, [3], 2)
gmsh.model.setPhysicalName(3, 2, "bulk")
gmsh.write('test_volume_bulk.vtk')


import gmsh
import sys

gmsh.initialize()

# create a model with OCC and mesh it
gmsh.model.add('model1')
# gmsh.model.occ.addBox(0, 0, 0, 1, 1, 1)
gmsh.model.occ.addSphere(0, 0, 0, 1)
gmsh.model.occ.synchronize()
gmsh.model.mesh.generate(3)

# 1) store the mesh
m = {}
for e in gmsh.model.getEntities():
    m[e] = (gmsh.model.getBoundary([e]),
            gmsh.model.mesh.getNodes(e[0], e[1]),
            gmsh.model.mesh.getElements(e[0], e[1]))

# 2) create a new model
gmsh.model.add('model2')

# 3) create discrete entities in the new model and copy the mesh
for e in sorted(m):
    gmsh.model.addDiscreteEntity(e[0], e[1], [b[1] for b in m[e][0]])
    gmsh.model.mesh.addNodes(e[0], e[1], m[e][1][0], m[e][1][1])
    gmsh.model.mesh.addElements(e[0], e[1], m[e][2][0], m[e][2][1], m[e][2][2])


# gmsh.write('test.vtk')

# object boundaries are fucked up
v = gmsh.model.getEntities(3)
s = gmsh.model.getBoundary(v)


mysurfaces = s

gmsh.model.removeEntities(gmsh.model.getEntities(dim=3))
gmsh.model.removeEntities([e for e in gmsh.model.getEntities(dim=2) if e not in mysurfaces], recursive=True)


gmsh.write('test.vtk')

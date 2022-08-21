import gmsh
import argparse

ap = argparse.ArgumentParser()
ap.add_argument('-zc', type=float, help='z-coord center')
ap.add_argument('-R', type=float, help='disk radius')
ap.add_argument('-ms', type=float, help='mesh size')
args = ap.parse_args()

gmsh.initialize()
gmsh.option.setNumber('General.Verbosity', 99)

xc = 0
yc = 0
zc = args.zc
R = args.R
ms = args.ms

rx = R
ry = R

disk_tag = gmsh.model.occ.addDisk(xc, yc, zc, rx, ry)

gmsh.model.occ.synchronize()

gmsh.model.addPhysicalGroup(2, [disk_tag], 1)
gmsh.model.setPhysicalName(2, 1, "disk")

e = gmsh.model.getEntities(0)
gmsh.model.mesh.setSize(e, ms)
gmsh.model.mesh.generate(2)


gmsh.write('disk.msh2')

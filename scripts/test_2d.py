import gmsh
import argparse

ap = argparse.ArgumentParser()
# ap.add_argument('-zc', type=float, help='z-coord center')
# ap.add_argument('-R', type=float, help='disk radius')
ap.add_argument('-ms', type=float, default=0.10, help='mesh size')
args = ap.parse_args()

gmsh.initialize()
gmsh.option.setNumber('General.Verbosity', 99)

xc = 0.0
yc = 0.0
zc = 0.0
R = 1.0

ms = args.ms

rx = R
ry = R

disk_1_tag = gmsh.model.occ.addDisk(0.0, 0.0, 0.0, 0.5, 0.5)
disk_2_tag = gmsh.model.occ.addDisk(1.0, 0.0, 0.0, 0.5, 0.5)
rect_tag = gmsh.model.occ.addRectangle(-1.0, -0.505, 0.0, 3.0, 1.01)

outdimtags, outdimtagsmap = gmsh.model.occ.fragment([(2,rect_tag)], [(2,disk_1_tag), (2,disk_2_tag)])

gmsh.model.occ.synchronize()

gmsh.model.addPhysicalGroup(2, [disk_1_tag], 1)
gmsh.model.setPhysicalName(2, 1, "disk_1")

gmsh.model.addPhysicalGroup(2, [disk_2_tag], 2)
gmsh.model.setPhysicalName(2, 2, "disk_2")

gmsh.model.addPhysicalGroup(2, [rect_tag], 3)
gmsh.model.setPhysicalName(2, 3, "rect")

e = gmsh.model.getEntities(0)
gmsh.model.mesh.setSize(e, ms)
gmsh.model.mesh.generate(2)


gmsh.write(f'test_2d_{args.ms}.vtk')

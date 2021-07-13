"""
Column class

contract:
    - must create necessary columns given Container, PackedBed, and config
    - perform necessary boolean operations on Container and PackedBed entities
    - separate surfaces and volumes
    - setPhysicalNames and Groups
"""

import gmsh

from pymesh.tools import filter_volumes_with_normal, stackPeriodic, get_surface_normals

import numpy as np
from itertools import combinations

class Column:

    def __init__(self, container, packedBed, copy=False, periodic=False):
        ## 1. Operate (fuse/fragment...)
        ## 2. Separate Surfaces
        ## 3. Match Periodic
        ## 4. Set Physical

        self.surfaces = {
                'inlet' : [],
                'outlet' : [],
                'particles': [],
                'walls': []
        }

        self.volumes = {
                'interstitial': [],
                'particles': []
        }

        if periodic:
            # self.operate_periodic(container, packedBed, copy)
            self.operate_periodic_2(container, packedBed, copy)

        self.fragment(container, packedBed, copy)

    def operate_periodic_2(self, container, packedBed, copy=False):
        factory = gmsh.model.occ
        factory.synchronize()

        dx = container.size[3]
        dy = container.size[4]
        dz = container.size[5]

        ## Extract container faces
        container_faces = gmsh.model.getBoundary(container.asDimTags(), combined=False, oriented=False)
        all_beads = packedBed.asDimTags()

        # Dilate container faces to fully cut through particles
        for e in container_faces:
            x,y,z = factory.getCenterOfMass(e[0], e[1])
            factory.dilate([e], x,y,z, 3,3,3)

        face_cutbeads = {}

        ## Find which faces cut which beads
        ##      Done in series because no way currently to say which face cut which bead otherwise
        ##      (Tried filtering beads by cut surfaces, but that seems to be buggy)
        ## Store in dict as {faceDimTag : [cut_beads_dimtags]}
        for face in container_faces:
            fragmented, fmap = factory.fragment(all_beads, [face], removeObject=False, removeTool=True)

            cut_beads =[]
            for e,f in zip(all_beads + [face], fmap):
                # print(e, " -> ", f)
                # if e[0] ==3 and len(f) > 1:
                if len(f) > 1:
                    if e[0] == 3:
                        cut_beads.append(e)
                    # print(f)
                        factory.remove(f, recursive=True)

            for e in fragmented:
                if e[0] == 2:
                    factory.remove([e], recursive=True)

            face_cutbeads.update({face : cut_beads})


        ## Find all cut beads, uniquely
        joined_cut_beads = [x  for face in face_cutbeads.keys() for x in face_cutbeads[face]]
        joined_cut_beads_tags = np.array([x[1] for x in joined_cut_beads])
        joined_cut_beads_tags_unique, joined_cut_beads_counts = np.unique(joined_cut_beads_tags,return_counts=True)

        copied_beads = []

        for bead in joined_cut_beads_tags_unique:
            ## Find all planes of cut
            ## Ex: x0, y0
            cut_planes = []
            for face in face_cutbeads.keys():
                if (3, bead) in face_cutbeads[face]:
                    cut_planes.append(face)

            ## Find all combinations of the cut planes
            ## Ex:[(x0), (y0), (x0,y0)]
            cut_plane_combos = [ x for i in range(1, len(cut_planes)+1) for x in combinations(cut_planes,i) ]


            ## For every combination of the cut planes,
            ##      calculate the combined normal,
            ##      translate a copy of the bead by -dx*normal_dir.
            for combo in cut_plane_combos:
                inormals = get_surface_normals(combo)
                combo_normal = [0, 0, 0]
                for inorm in inormals:
                    combo_normal[0] = combo_normal[0] + inorm[0]
                    combo_normal[1] = combo_normal[1] + inorm[1]
                    combo_normal[2] = combo_normal[2] + inorm[2]
                copied_bead = factory.copy([(3,bead)])
                copied_beads.extend(copied_bead)
                factory.translate(copied_bead, -combo_normal[0] * dx, -combo_normal[1] *dy, -combo_normal[2] * dz)

        allbeads = packedBed.asDimTags() + copied_beads

        fragmented, fmap = factory.fragment(allbeads, container.asDimTags(), removeObject=False, removeTool=False)

        all = factory.getEntities(dim=3)
        for e in all:
            if e not in fmap[-1]:
                factory.remove([e], recursive=True)

        factory.synchronize()

        ent = gmsh.model.getEntities(0)
        gmsh.model.mesh.setSize(ent, 0.2)
        gmsh.model.mesh.generate(2)
        gmsh.write("dilatedboundaries.vtk")

        import sys; sys.exit() ;

    def operate_periodic(self, container, packedBed, copy=False):
        """
        Given a periodic packing and container, create a periodic mesh.

        Note: Periodic packings aren't directly compatible for meshing. They need additional preprocessing.
        """
        factory = gmsh.model.occ

        factory.synchronize()

        container_copy = container.asDimTags()
        container_faces = gmsh.model.getBoundary(container_copy, combined=False, oriented=False)

        for e in container_faces:
            x,y,z = factory.getCenterOfMass(e[0], e[1])
            factory.dilate([e], x,y,z, 3,3,3)

        ## TEST
        allbeads = packedBed.asDimTags()
        fragmented, fmap = factory.fragment(allbeads, container_faces, removeObject=False, removeTool=False)
        # fragmented, fmap = factory.fragment(allbeads, container_boundaries)
        print(len(allbeads))

        fragmented_3D=[]
        for e in fragmented:
            if e[0] == 2:
                factory.remove([e], True)
            else:
                fragmented_3D.append(e)


        print(len(fragmented))
        print(len(fragmented_3D))

        uncut_beads = []
        cut_beads = []
        cut_beads_new_dt = []

        print("before/after fragment relations:")
        for e,f in zip(allbeads + container_faces, fmap):
            # print("parent " + str(e) + " -> child " + str(f))
            print("parent " + str(e) + " -> " + str(len(f)))
            if len(f) > 1 and e[0] == 3:
                cut_beads.append(e)
                # cut_beads_new_dt.extend(e[1])
                factory.remove(f, True)
            elif len(f) == 1:
                uncut_beads.append(e)

        print(gmsh.GMSH_API_VERSION)
        import sys; sys.exit()

        # print(cut_beads_new_dt)
        stacked = stackPeriodic(cut_beads, 'xyz', 4, 4, 4)

        fragmented, fmap = factory.fragment(stacked + uncut_beads, container.asDimTags())

        all = factory.getEntities(dim=3)
        for e in all:
            if e not in fmap[-1]:
                factory.remove([e], recursive=True)

        # for e, f in zip(stacked + uncut_beads, fmap[:-1]):
        #     # print("parent " + str(e) + " -> child " + str(f))
        #     if len(f) == 1 and f[0] not in uncut_beads:
        #         factory.remove(f, recursive=True)
        #     elif len(f) > 1:
        #         print(f)
        #         factory.remove(f, recursive=True)

        # import sys; sys.exit()

        factory.remove(container_faces, recursive=True)
        factory.synchronize()

        ent = gmsh.model.getEntities(0)
        gmsh.model.mesh.setSize(ent, 0.2)
        gmsh.model.mesh.generate(2)
        gmsh.write("dilatedboundaries.vtk")


        # print(cut_beads)
        # print(len(cut_beads))



        import sys; sys.exit()

        container_faces = container_faces[5:]

        for plane in container_faces:

            allbeads = packedBed.asCopyDimTags()
            fragmented, _ = factory.fragment(allbeads, [plane])

            ## remove fragmented cutting planes
            to_delete = [e for e in fragmented if e[0] == 2]
            factory.remove(to_delete, recursive=True)
            cut_beads = [e for e in fragmented if e not in to_delete]

            # cut_beads = fragmented


            ## remove unused cutting planes
            # factory.remove(container_boundaries, recursive=True)

            factory.synchronize()

            ## filter beads
            points = gmsh.model.getBoundary([plane], False, False, True)
            # coord = gmsh.model.getValue(points[0][0], points[0][1], [])
            factory.synchronize()
            coord = []
            for point in points:
                coord.extend(gmsh.model.getValue(point[0], point[1], []))
            pcoord = gmsh.model.getParametrization(plane[0], plane[1], coord)
            normals = gmsh.model.getNormal(plane[1], pcoord)
            n = np.reshape(normals, (len(points), 3))

            if not (n == n[0]).all():
                raise(ValueError)

            print(">> NORMAL:", n[0])
            filtered_beads = filter_volumes_with_normal(cut_beads, n[0])
            print("Beads filtered: ", len(filtered_beads))

            # to_delete = list(set(cut_beads).difference(set(filtered_beads)))
            # for e in to_delete:
            #     factory.remove([e], recursive=True)
            # remaining = [ e for e in cut_beads if e not in to_delete ]

        import sys; sys.exit()

        # factory.remove(container_boundaries, recursive=True)
        factory.remove(container_copy)
        # factory.remove(container.asDimTags(), recursive=True)
        factory.remove(packedBed.asDimTags(), recursive=True)
        # factory.removeAllDuplicates()
        # factory.healShapes(sewFaces=False, makeSolids=False)

        # ent = factory.getEntities(dim=3)
        # for e in ent:
        #     coord = factory.getCenterOfMass(e[0], e[1])
        #     if gmsh.model.isInside(container_copy[0][0], container_copy[0][1], coord, parametric=False):
        #         factory.remove([e], recursive=True)


        # ---

        # factory.remove(packedBed.asDimTags(), recursive=True)
        # factory.remove(container.asDimTags(), recursive=True)


        # for e in container_boundaries:
        #     allbeads = factory.fragment(allbeads,[e])


        factory.synchronize()

        # print(container_boundaries)
        ent = gmsh.model.getEntities()
        gmsh.model.mesh.setSize(ent, 0.15)
        gmsh.model.mesh.generate(2)
        gmsh.write("dilatedboundaries.vtk")

        import sys
        sys.exit(0)

    def fragment(self, container, packedBed, copy=False):
        """
        Given a container and packed bed, perform boolean operations and generate one fragmented column
        """
        factory = gmsh.model.occ

        packedBedDimTags = packedBed.asCopyDimTags() if copy else packedBed.asDimTags()
        fragmented, _ = factory.fragment(container.asDimTags(), packedBedDimTags)

        # Tolerance for bbox.
        eps = 1e-3

        # Also see gmsh options
        #       - Geometry.OCCBoundsUseSTL,
        #       - Mesh.StlAngularDeflection, and
        #       - Mesh.StlLinearDeflection

        size = container.size
        # entitiesInBox = gmsh.model.getEntitiesInBoundingBox(
        entitiesInBox = factory.getEntitiesInBoundingBox(
                size[0]-eps, size[1]-eps, size[2]-eps,
                size[0]+size[3]+eps,
                size[1]+size[4]+eps,
                size[2]+size[5]+eps,
                dim=3
                )

        for e in entitiesInBox:
            fragmented.remove(e)

        factory.remove(fragmented, recursive=True)

        self.entities = entitiesInBox

    def separate_bounding_surfaces(self):
        pass

    def match_periodic_surfaces(self):
        pass

    def set_physical_groups(self):
        gmsh.model.removePhysicalGroups()

        gmsh.model.addPhysicalGroup(2, self.surfaces.get('inlet'), 1)
        gmsh.model.addPhysicalGroup(2, self.surfaces.get('outlet'), 2)
        gmsh.model.addPhysicalGroup(2, self.surfaces.get('walls'), 3)
        gmsh.model.addPhysicalGroup(2, self.surfaces.get('particles'), 4)
        gmsh.model.addPhysicalGroup(3, self.volumes.get('interstitial'), 5)
        gmsh.model.addPhysicalGroup(3, self.volumes.get('particles'), 6)

        gmsh.model.setPhysicalName(2, 1, "inlet")
        gmsh.model.setPhysicalName(2, 2, "outlet")
        gmsh.model.setPhysicalName(2, 3, "walls")
        gmsh.model.setPhysicalName(2, 4, "particles")
        gmsh.model.setPhysicalName(3, 5, "interstitial")
        gmsh.model.setPhysicalName(3, 6, "particles")

    def write(self, fname):
        self.set_physical_groups()
        gmsh.write(fname)


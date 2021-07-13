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
            self.operate_periodic(container, packedBed, copy)
        else:
            self.fragment(packedBed.asDimTags(), container.asDimTags(), copyObject=copy, removeObject=True, removeTool=True, cleanFragments=True)


    def operate_periodic(self, container, packedBed, copy=False):
        """
        Given a periodic packing and container, create a periodic mesh.

        Note: Periodic packings aren't directly compatible for meshing. They need additional preprocessing.
        """
        factory = gmsh.model.occ
        factory.synchronize()

        dx = container.size[3]
        dy = container.size[4]
        dz = container.size[5]

        ## Extract container faces
        container_faces = gmsh.model.getBoundary(container.asDimTags(), combined=False, oriented=False)

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
            fragmented, fmap = factory.fragment(packedBed.asDimTags(), [face], removeObject=False, removeTool=True)

            cut_beads =[]

            ## For every original (e) and fragmented (f) item:
            for e,f in zip(packedBed.asDimTags() + [face], fmap):
                # print(e, " -> ", f)
                # if e[0] ==3 and len(f) > 1:

                if len(f) > 1:                                  ## Particles that were split by the plane
                    if e[0] == 3:                               ## Volumes, not surfaces (plane fragments)
                        cut_beads.append(e)                     ## Save original bead to list
                        factory.remove(f, recursive=True)       ## Remove 3D Fragments

            ## Remove 2D fragments
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

        self.fragment(allbeads, container.asDimTags(), removeObject=True, removeTool=True, copyObject=copy, cleanFragments=True)

    def fragment(self, object, tool, copyObject=False, copyTool=False, removeObject=False, removeTool=False, cleanFragments=False, cleanAll=False):
        """
        Given a container and packed bed, perform boolean operations and generate one fragmented column.
        When the container is the tool, the end of the fmap contains the mapping of the container to the
        many volumes it is fragmented into. This is the only thing that matters in our case, hence we remove
        all other volumes to clean up the model.
        """
        factory = gmsh.model.occ

        object = factory.copy(object) if copyObject else object
        tool = factory.copy(tool) if copyTool else tool

        fragmented, fmap = factory.fragment(object, tool, removeObject=removeObject, removeTool=removeTool)

        if cleanFragments:
            print("Cleaning Fragments")
            factory.remove([e for e in fragmented if e not in fmap[-1]], recursive=True)

        if cleanAll:
            all = factory.getEntities(dim=3)
            factory.remove([e for e in all if e not in fmap[-1]], recursive=True)

        self.entities = fmap[-1][:]

        return self.entities

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


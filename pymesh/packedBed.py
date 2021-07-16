"""
PackedBed class

contract:
    - @input: read config
    - read packing file
    - modify packing (scale, shift, scale-particle-radii)
    - generate geos for particles

"""

from pymesh.tools import bin_to_arr, grouper, get_surface_normals, get_volume_normals
from pymesh.bead import Bead

import numpy as np
import gmsh

from itertools import combinations

class PackedBed:

    config = {}

    def __init__(self, config):

        self.fname                               = config.get('packedbed.packing_file.filename', 'packing.xyzd')
        self.dataformat                          = config.get('packedbed.packing_file.dataformat', '<d')
        self.zBot                                = config.get('packedbed.zbot', 0)
        self.zTop                                = config.get('packedbed.ztop', 0)
        self.nBeads                              = config.get('packedbed.nbeads', 0)
        self.scaling_factor                      = config.get('packedbed.scaling_factor', 1)
        self.particles_scaling_factor            = config.get('packedbed.particles.scaling_factor', 1)

        self.mesh_size                           = config.get('mesh.size', 0.2)
        self.mesh_size_in                        = config.get('mesh.sizein', self.mesh_size)
        self.mesh_size_out                       = config.get('mesh.sizeout', self.mesh_size)
        self.mesh_field_threshold_rad_min_factor = config.get('mesh.field.threshold.rad_min_factor', 1)
        self.mesh_field_threshold_rad_max_factor = config.get('mesh.field.threshold.rad_max_factor', 1)

        self.read_packing()
        if config.get('packing.auto_translate'):
            self.moveBedtoCenter()
        self.generate()
        ## TODO: Fix mesh_fields for copied/stacked beads for periodic problems
        self.set_mesh_fields()

    def read_packing(self):
        # dataformat = "<f" ## For old packings with little endian floating point data. Use <d for new ones
        self.beads = []
        arr = bin_to_arr(self.fname, self.dataformat)
        if self.nBeads < 0:
            for chunk in grouper(arr,4):
                if (chunk[2] >= self.zBot/self.scaling_factor) and (chunk[2] <= self.zTop/self.scaling_factor):
                    x = chunk[0] * self.scaling_factor
                    y = chunk[1] * self.scaling_factor
                    z = chunk[2] * self.scaling_factor
                    r = chunk[3]/2 * self.scaling_factor * self.particles_scaling_factor
                    self.beads.append(Bead(x, y, z, r))
        else:
            for index, chunk in enumerate(grouper(arr,4)):
                if index == self.nBeads:
                    break
                x = chunk[0] * self.scaling_factor
                y = chunk[1] * self.scaling_factor
                z = chunk[2] * self.scaling_factor
                r = chunk[3]/2 * self.scaling_factor * self.particles_scaling_factor
                self.beads.append(Bead(x, y, z, r))


    def asDimTags(self):
        return [ (3,tag) for tag in self.entities ]

    def asCopyDimTags(self):
        return gmsh.model.occ.copy([ (3,tag) for tag in self.entities ])

    def asTags(self):
        return self.entities

    def updateBounds(self):
        """
        Calculate bounding points for the packed bed.
        """

        xpr = []
        xmr = []
        ypr = []
        ymr = []
        zpr = []
        zmr = []
        z = []

        for bead in self.beads:
            xpr.append(bead.x + bead.r)
            xmr.append(bead.x - bead.r)
            ypr.append(bead.y + bead.r)
            ymr.append(bead.y - bead.r)
            zpr.append(bead.z + bead.r)
            zmr.append(bead.z - bead.r)
            z.append(bead.z)

        radList = [ bead.r for bead in self.beads ]
        self.rmax = max(radList)
        self.rmin = min(radList)
        self.ravg = sum(radList)/len(radList)

        self.xmax = max(xpr)
        self.ymax = max(ypr)
        self.ymin = min(ymr)
        self.xmin = min(xmr)
        self.zmax = max(zpr)
        self.zmin = min(zmr)

        self.R = max((self.xmax-self.xmin)/2, (self.ymax-self.ymin)/2) ## Similar to Genmesh
        self.h = self.zmax - self.zmin
        self.CylinderVolume = np.pi * self.R**2 * self.h

    def moveBedtoCenter(self):
        """
        Translate bed center to origin of coordinate system.
        """
        self.updateBounds()
        offsetx = -(self.xmax + self.xmin)/2
        offsety = -(self.ymax + self.ymin)/2
        for bead in self.beads:
            bead.x = bead.x + offsetx
            bead.y = bead.y + offsety
        self.updateBounds()

    def generate(self):
        """
        Create packed bed entities
        """
        factory = gmsh.model.occ
        self.entities = []
        for bead in self.beads:
            self.entities.append(factory.addSphere(bead.x, bead.y, bead.z, bead.r))

    def set_mesh_fields(self):
        factory = gmsh.model.occ
        field = gmsh.model.mesh.field


        self.center_points = []
        for bead in self.beads:
            ctag = factory.addPoint(bead.x, bead.y, bead.z, self.mesh_size_in)
            self.center_points.append(ctag)

            self.dtag = field.add('Distance')
            field.setNumbers(self.dtag, 'PointsList', [self.dtag])

            distmin = self.mesh_field_threshold_rad_min_factor * bead.r
            distmax = self.mesh_field_threshold_rad_max_factor * bead.r

            self.ttag = field.add('Threshold')
            field.setNumber(self.ttag, "InField", self.dtag);
            field.setNumber(self.ttag, "SizeMin", self.mesh_size_in);
            field.setNumber(self.ttag, "SizeMax", self.mesh_size_out);
            field.setNumber(self.ttag, "DistMin", distmin);
            field.setNumber(self.ttag, "DistMax", distmax);

    def stack_by_plane_cuts(self, container):
        """
        Periodic packings need to be stacked to make them meshable
        This method does it via cut planes of the column container.
        1. Extract and Dilate container faces
        2. Fragment serially and find which beads are cut by which faces
        3. Copy and Translate beads based on normal of the cut plane

        [TASK]
        NOTE: This method was used because directly fragmenting objects messes with
        surface normals somehow in gmsh/occt. Ideally, just fragment all at once and
        filter beads by surface normals.
        """
        factory = gmsh.model.occ
        factory.synchronize()

        dx = container.size[3]
        dy = container.size[4]
        dz = container.size[5]

        ## NOTE: Extract ALL container faces, regardless of periodicity directions
        container_faces = gmsh.model.getBoundary(container.asDimTags(), combined=False, oriented=False)

        # Dilate container faces to fully cut through particles
        df = 2          # dilation factor
        for e in container_faces:
            x,y,z = factory.getCenterOfMass(e[0], e[1])
            factory.dilate([e], x,y,z, df, df, df)

        face_cutbeads = {}

        ## Find which faces cut which beads
        ##      Done in series because no way currently to say which face cut which bead otherwise
        ##      (Tried filtering beads by cut surfaces, but that seems to be buggy)
        ## Store in dict as {faceDimTag : [cut_beads_dimtags]}
        for face in container_faces:

            ## Fragment the packedBed, do not delete the original object.
            fragmented, fmap = factory.fragment(self.asDimTags(), [face], removeObject=False, removeTool=True)

            cut_beads =[]

            ## For every original (e) and fragmented (f) item:
            for e,f in zip(self.asDimTags() + [face], fmap):
                # print(e, " -> ", f)
                # if e[0] ==3 and len(f) > 1:

                ## TODO: uniquify f before removing. For some reason, in large case, I get too many split parts for a certain bead
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
            ##      - calculate the combined normal,
            ##      - translate a copy of the bead by -dx*normal_dir.
            for combo in cut_plane_combos:
                inormals = get_surface_normals(combo)
                combo_normal = [sum(i) for i in zip(*inormals)]
                copied_bead = factory.copy([(3,bead)])
                copied_beads.extend(copied_bead)
                factory.translate(copied_bead, -combo_normal[0] * dx, -combo_normal[1] *dy, -combo_normal[2] * dz)
                ## TODO: append to self.beads
                # self.beads.append(Bead(bead.x - combo_normal[0] * dx,
                #     bead.y - combo_normal[1] * dy,
                #     bead.z - combo_normal[2] * dz,
                #     bead.r))

        # allbeads = self.asDimTags() + copied_beads
        self.entities.extend([tag for _, tag in copied_beads])

    def stack_by_volume_cuts(self, container):
        """
        Stack beads by using volume cuts
            - Cut packing with container
            - Filter beads by surface normals
            - Calculate all combinations of normals to copy/translate by
            - Copy+Translate all original beads which are cut
            - [PROB]: Doesn't handle all edge cases:
                - Beads sliced by z+ and the extended edge of x or y planes separately (2 separate clean cuts)
                - fixed by dilation of cut planes, already taken care of by the plane-cut algorithm.
        """
        factory = gmsh.model.occ

        cuts, cmap = factory.cut(self.asDimTags(), container.asDimTags(), removeObject=False, removeTool=False)
        normalss = get_volume_normals(cuts)

        bead_translationNormals = {}

        for vol,normals in zip(cuts, normalss):
            # normals.remove([0,0,0])
            ns = [ n for n in normals if n != [0, 0, 0]]
            nsc = [ x for i in range(1, len(ns)+1) for x in combinations(ns,i) ]
            # print( vol, ' -> ', ns)
            output = []
            for isc in nsc:
                combo_normal = [sum(i) for i in zip(isc)]
                # print(combo_normal)
                output.append(combo_normal)
            index = None
            for i,e in enumerate(cmap):
                if vol in e:
                    index = i
                    break
            if index is None:
                raise(IndexError)
            bead_translationNormals.setdefault(self.asDimTags()[index], [])
            bead_translationNormals[self.asDimTags()[index]].extend(output)
            # print(packedBed.asDimTags()[index], ' -> ', output)

        dx = container.size[3]
        dy = container.size[4]
        dz = container.size[5]

        copied_beads = []

        for bead,translationNormals in bead_translationNormals.items():
            for n in translationNormals:
                copied_bead = factory.copy([bead])
                copied_beads.extend(copied_bead)
                factory.translate(copied_bead, n[0]*dx, n[1]*dy, n[2]*dz)

        self.entities.extend([ x for _,x in copied_beads])
        factory.remove(cuts, recursive=True)

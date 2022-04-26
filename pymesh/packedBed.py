"""
PackedBed class

contract:
    - @input: read config
    - read packing file
    - modify packing (scale, shift, scale-particle-radii)
    - generate geos for particles

"""

from pymesh.tools import bin_to_arr, grouper, get_surface_normals, get_volume_normals, store_mesh
from pymesh.bead import Bead
from pymesh.log import Logger

import struct
import numpy as np
import gmsh

from itertools import combinations

class PackedBed:

    def __init__(self, config, generate=True, logger=Logger(level=2)):

        self.logger = logger

        self.fname                               = config.packing_file_name
        self.dataformat                          = config.packing_file_format
        self.zBot                                = config.packedbed_zbot
        self.zTop                                = config.packedbed_ztop
        self.nBeads                              = config.packedbed_nbeads
        self.scaling_factor                      = config.packedbed_scaling_factor
        self.particles_scaling_factor            = config.packedbed_particles_scaling_factor
        self.auto_translate                      = config.packedbed_auto_translate

        # self.mesh_size                           = config.mesh_size
        self.mesh_field_threshold_size_in        = config.mesh_field_threshold_size_in
        self.mesh_field_threshold_size_out       = config.mesh_field_threshold_size_out
        self.mesh_ref_radius                     = config.mesh_ref_radius
        self.mesh_field_threshold_rad_min_factor = config.mesh_field_threshold_rad_min_factor
        self.mesh_field_threshold_rad_max_factor = config.mesh_field_threshold_rad_max_factor

        self.read_packing()
        if self.auto_translate:
            self.moveBedtoCenter()
        if generate: 
            self.generate()

        # print(*[bead for bead in self.beads], sep='\n')

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

        self.logger.out(f"Found {len(self.beads)} beads")


    @property
    def dimTags(self):
        # return [ (3,tag) for tag in self.entities ]
        return [ (3,b.tag) for b in self.beads ]

    @property
    def tags(self):
        # return self.entities
        return [ b.tag for b in self.beads ]

    def write(self, filename, dataformat='<d'):
        with(open(filename, 'wb')) as output:
            for bead in self.beads:
                output.write(struct.pack(dataformat,bead.x))
                output.write(struct.pack(dataformat,bead.y))
                output.write(struct.pack(dataformat,bead.z))
                output.write(struct.pack(dataformat,bead.r * 2))

    def updateBounds(self):
        """
        Calculate bounding points for the packed bed.
        """

        self.bound_zbot = min( bead.z for bead in self.beads )

        leftCardinalBounds = [bead.leftCardinalBounds for bead in self.beads]
        rightCardinalBounds = [bead.rightCardinalBounds for bead in self.beads]
        self.xmin, self.ymin, self.zmin = [min(c) for c in zip(*leftCardinalBounds)]
        self.xmax, self.ymax, self.zmax = [max(c) for c in zip(*rightCardinalBounds)]

        radList = [ bead.r for bead in self.beads ]
        self.rmax = max(radList)
        self.rmin = min(radList)
        self.ravg = sum(radList)/len(self.beads)

        self.R = max((self.xmax-self.xmin)/2, (self.ymax-self.ymin)/2) ## Similar to Genmesh
        self.h = self.zmax - self.zmin
        self.CylinderVolume = np.pi * self.R**2 * self.h

    def moveBedtoCenter(self):
        """
        Translate bed bottom center to origin of coordinate system.
        """
        self.updateBounds()
        offsetx = -(self.xmax + self.xmin)/2
        offsety = -(self.ymax + self.ymin)/2
        offsetz = -(self.bound_zbot)
        for bead in self.beads:
            bead.translate(offsetx, offsety, offsetz)
        self.updateBounds()

    def generate(self):
        """
        Create packed bed entities
        """
        for bead in self.beads:
            bead.generate()

    def set_mesh_fields(self):
        """
        Set mesh Distance and Threshold fields for every bead
        """
        factory = gmsh.model.occ
        field = gmsh.model.mesh.field

        self.updateBounds()
        if self.mesh_ref_radius == 'avg':
            self.rref = self.ravg
        elif self.mesh_ref_radius == 'max':
            self.rref = self.rmax
        elif self.mesh_ref_radius == 'min':
            self.rref = self.rmin

        ## Tags of distance and threshold fields
        dtags = []
        ttags = []

        ## Create points as an anchor for the distance fields
        for bead in self.beads:

            bead_size_ratio = bead.r/self.rref

            ctag = factory.addPoint(bead.x, bead.y, bead.z, self.mesh_field_threshold_size_in* bead_size_ratio)
            bead.set_ctag(ctag)

        factory.synchronize()

        for bead in self.beads:

            bead_size_ratio = bead.r/self.rref

            dtag = field.add('Distance')
            dtags.append(dtag)
            field.setNumbers(dtag, 'PointsList', [bead.ctag])
            ## TODO
            # field.setNumbers(dtag, 'SurfacesList', [dtag])

            distmin = self.mesh_field_threshold_rad_min_factor * bead.r
            distmax = self.mesh_field_threshold_rad_max_factor * bead.r

            ttag = field.add('Threshold')
            ttags.append(ttag)
            field.setNumber(ttag, "InField", dtag);
            field.setNumber(ttag, "SizeMin", self.mesh_field_threshold_size_in * bead_size_ratio);
            field.setNumber(ttag, "SizeMax", self.mesh_field_threshold_size_out);
            field.setNumber(ttag, "DistMin", distmin);
            field.setNumber(ttag, "DistMax", distmax);

        ## WARNING: The mesh size for SizeMax is not scaled because of the backgroundField issue.
        # Since we have multiple overlapping threshold fields reaching out to
        # infinity, setting a background in both cases of size_in > size_out
        # and size_in < size_out is not easy. 
        # For a finer particle interior, backgroundField == Min
        # For a coarser particle interior, we would have to set backgroundField to Max.
        # This changes things on the particle surface. If we scale the mesh size outside with the bead radius, the max field will set the mesh size of the largest particle on the surface of the smallest.


        ## Set background field
        backgroundField = 'Min' if self.mesh_field_threshold_size_in <= self.mesh_field_threshold_size_out else 'Max'
        bftag = field.add(backgroundField);
        field.setNumbers(bftag, "FieldsList", ttags);
        field.setAsBackgroundMesh(bftag);

        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
        gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)

        factory.synchronize()

    def stack_by_plane_cuts(self, container):
        """
        Periodic packings need to be stacked to make them meshable
        This method does it via cut planes of the column container.
        1. Extract and Dilate container faces
        2. Fragment serially and find which beads are cut by which faces
        3. Copy and Translate beads based on normal of the cut plane

        NOTE: This method was used because directly fragmenting objects messes with
        surface normals somehow in gmsh/occt. Ideally, just fragment all at once and
        filter beads by surface normals.

        [TASK]: Fragment/Filter/Move after each planecut
        """
        factory = gmsh.model.occ
        factory.synchronize()

        dx = container.dx
        dy = container.dy
        dz = container.dz

        ## NOTE: Extracts ALL container faces, regardless of periodicity directions
        container_faces = gmsh.model.getBoundary(container.dimTags, combined=False, oriented=False)

        # Dilate container faces to fully cut through particles
        df = 2          # dilation factor
        for e in container_faces:
            x,y,z = factory.getCenterOfMass(e[0], e[1])
            factory.dilate([e], x,y,z, df, df, df)

        face_cutbeads = {}

        ## Find which faces cut which beads
        ##      Done in series because no way currently to say which face cut which bead otherwise
        ##      (Tried filtering beads by cut surfaces, but that seems to be buggy with fragmenting)
        ## Store in dict as {faceDimTag : [cut_beads_dimtags]}
        for face in container_faces:

            ## Fragment the packedBed, do not delete the original object.
            fragmented, fmap = factory.fragment(self.dimTags, [face], removeObject=False, removeTool=True)

            ## Find beads that are split by the face
            split_beads = list(filter(lambda f: len(f)>1 and f[0][0]==3, fmap))
            split_faces = list(filter(lambda f: f[0]==2, fragmented))

            ## Find the original beads that would be split
            split_beads_orig = list(map(lambda x: self.dimTags[fmap.index(x)], split_beads))

            ## Remove the new split beads and faces
            factory.remove([y for x in split_beads for y in x], recursive=True)
            factory.remove(split_faces, recursive=True)

            face_cutbeads.update({face : split_beads_orig})

        ## Find all cut beads, uniquely
        joined_cut_beads_entities = [x  for face in face_cutbeads.keys() for x in face_cutbeads[face]]
        joined_cut_beads_tags = np.array([x[1] for x in joined_cut_beads_entities])
        joined_cut_beads_tags_unique = np.unique(joined_cut_beads_tags)
        joined_cut_beads = ( bead for bead in self.beads if bead.tag in joined_cut_beads_tags_unique )

        ## For every bead that is cut
        for bead in joined_cut_beads:
            ## Find all planes of cut
            ## Ex: x0, y0
            cut_planes = [ face for face,facecutbeads in face_cutbeads.items() if bead.dimTag in facecutbeads ]
            # cut_planes = list(filter(lambda face: (3,bead.tag) in face_cutbeads[face], face_cutbeads.keys()))

            ## Find all combinations of the cut planes
            ## Ex:[(x0), (y0), (x0,y0)]
            cut_plane_combos = ( x for i in range(1, len(cut_planes)+1) for x in combinations(cut_planes,i) )

            ## For every combination of the cut planes,
            ##      - get surface normals for the constituent wall faces
            ##      - calculate the combined normal,
            ##      - create (generate) a new bead translated in that direction
            for combo in cut_plane_combos:
                inormals = get_surface_normals(combo)
                combo_normal = [sum(i) for i in zip(*inormals)]
                self.beads.append(Bead(bead.x - combo_normal[0] * dx,
                    bead.y - combo_normal[1] * dy,
                    bead.z - combo_normal[2] * dz,
                    bead.r))

        ## Generate the packed bed, i.e., the bead geometries
        self.generate()



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

        cuts, cmap = factory.cut(self.dimTags, container.dimTags, removeObject=False, removeTool=False)
        normalss = get_volume_normals(cuts)

        bead_translationNormals = {}

        for vol,normals in zip(cuts, normalss):

            ## Find flat wall normals for given volumes
            # wall_normals = [ n for n in normals if n != [0,0,0] ]
            normals = np.array(normals)
            wall_normals = normals[np.any(normals != 0, axis=1), :]


            ## Find ALL non-zero lengthed combinations for the flat_normals
            ## Eg. with flat_normals = [ x, y ] ,
            ##          flat_normals_combos = [ x, y, xy ]
            wall_normals_combos = [ x for i in range(1, len(wall_normals)+1) for x in combinations(wall_normals,i) ]

            ## Add up individual normals of the wall_normals_combos
            ## Eg: element xy = [[1, 0, 0] , [0, 1, 0]] -> [1,1,0]
            ## Assemble them into translation_normals (sum all normals in the unrolled tuple)
            translation_normals = map(lambda combo: [sum(i) for i in zip(*combo)], wall_normals_combos)

            ## Find the original bead entities corresponding to the cut beads
            ## Store the mapping in the bead_translationNormals dictionary
            ##### ---------------------------
            ##### index = None
            ##### for i,e in enumerate(cmap):
            #####     if vol in e:
            #####         index = i
            #####         break
            ##### if index is None:
            #####     raise(IndexError)
            ##### ---------------------------
            index = cmap.index(list( filter(lambda e: vol in e, cmap))[0])

            ## Set default to empty list, so that extending is possible
            bead_translationNormals.setdefault(self.dimTags[index], [])
            bead_translationNormals[self.dimTags[index]].extend(translation_normals)
            # print(packedBed.dimTags[index], ' -> ', output)

        dx = container.dx
        dy = container.dy
        dz = container.dz

        for dimTag,translationNormals in bead_translationNormals.items():
            bead = next(filter(lambda x: x.tag == dimTag[1],  self.beads))
            for n in translationNormals:
                self.beads.append(Bead(bead.x + n[0]*dx, bead.y + n[1]*dy, bead.z + n[2]*dz, bead.r))

        self.generate()
        factory.remove(cuts, recursive=True)

    def stack_all(self, stack_directions:str, dx, dy, dz):
        """
        Given entities, stack them in the periodic_directions in combination.
        With xyz periodicity, it should generate 26 * len(entities) new entities

        It's a highly inefficient way to create periodic meshes, but worked as a first attempt.

        @problem: currently doesn't seem to work. Leaving this here for the future.
        """

        self.logger.warn('PackedBed.stack_all:', 'This method is untested and undeveloped. Use planecut instead.')

        factory = gmsh.model.occ

        x_offset_multiplier = [-1, 0, 1]  if 'x' in stack_directions else [0]
        y_offset_multiplier = [-1, 0, 1]  if 'y' in stack_directions else [0]
        z_offset_multiplier = [-1, 0, 1]  if 'z' in stack_directions else [0]

        stacked_beads = []

        for zom in z_offset_multiplier:
            for yom in y_offset_multiplier:
                for xom in x_offset_multiplier:
                    if xom == 0 and yom == 0 and zom == 0: continue

                    # ## Going with bead.copy().translate() for no great reason
                    # for bead in self.beads:
                    #     stacked_beads.append(bead.copy().translate(xom*dx, yom*dy, zom*dz))

                    ## Alternatively append empty beads and then packedBed.generate():
                    ## Probably faster since we don't have to perform a copy and then translate
                    for bead in self.beads:
                        stacked_beads.append(Bead(bead.x + xom*dx, bead.y + yom*dy, bead.z + zom*dz, bead.r))

        self.beads.extend(stacked_beads)
        self.generate()

    def copy_mesh(self, nodeTagsOffset, elementTagsOffset): 
        """
        Generate a reference sphere volume mesh and copy it to create a full packed bed.

        """
        current_model = gmsh.model.getCurrent()

        gmsh.model.add("reference")
        gmsh.model.occ.addSphere(0, 0, 0, 1)

        self.set_threshold_for_reference_mesh()

        gmsh.model.mesh.generate(3)
        m, _, _ = store_mesh(3)

        gmsh.model.setCurrent(current_model)

        ntoff = nodeTagsOffset
        etoff = elementTagsOffset

        for bead in self.beads:
            ntoff, etoff = bead.copy_mesh(m, ntoff, etoff)

        gmsh.model.setCurrent('reference')
        gmsh.model.remove()

        gmsh.model.setCurrent(current_model)
        gmsh.model.geo.synchronize()

        # gmsh.write('test.vtk')
        return ntoff, etoff

    def set_threshold_for_reference_mesh(self): 
        """
        Set a point based threshold mesh field for the reference mesh 
        Implementation is copied from set_mesh_fields() to keep some backward compat
        """

        factory = gmsh.model.occ
        field = gmsh.model.mesh.field

        factory.synchronize()

        self.updateBounds()
        if self.mesh_ref_radius == 'avg':
            self.rref = self.ravg
        elif self.mesh_ref_radius == 'max':
            self.rref = self.rmax
        elif self.mesh_ref_radius == 'min':
            self.rref = self.rmin

        ## Tags of distance and threshold fields
        dtags = []
        ttags = []

        ## Create points as an anchor for the distance fields

        bead_size_ratio = 1.0/self.rref

        ctag = factory.addPoint(0.0, 0.0, 0.0, self.mesh_field_threshold_size_in* bead_size_ratio)

        factory.synchronize()

        bead_size_ratio = 1.0/self.rref

        dtag = field.add('Distance')
        dtags.append(dtag)
        field.setNumbers(dtag, 'PointsList', [ctag])
        ## TODO
        # field.setNumbers(dtag, 'SurfacesList', [dtag])

        distmin = self.mesh_field_threshold_rad_min_factor * 1.0
        distmax = self.mesh_field_threshold_rad_max_factor * 1.0

        ttag = field.add('Threshold')
        ttags.append(ttag)
        field.setNumber(ttag, "InField", dtag);
        field.setNumber(ttag, "SizeMin", self.mesh_field_threshold_size_in * bead_size_ratio);
        field.setNumber(ttag, "SizeMax", self.mesh_field_threshold_size_out * bead_size_ratio);
        field.setNumber(ttag, "DistMin", distmin);
        field.setNumber(ttag, "DistMax", distmax);

        ## Set background field
        backgroundField = 'Min' if self.mesh_field_threshold_size_in <= self.mesh_field_threshold_size_out else 'Max'
        bftag = field.add(backgroundField);
        field.setNumbers(bftag, "FieldsList", ttags);
        field.setAsBackgroundMesh(bftag);

        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
        # gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
        # gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)

        factory.synchronize()


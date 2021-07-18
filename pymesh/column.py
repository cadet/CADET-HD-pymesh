"""
Column class

contract:
    - must create necessary columns given Container, PackedBed, and config
    - perform necessary boolean operations on Container and PackedBed entities
    - separate surfaces and volumes
    - setPhysicalNames and Groups
"""

import gmsh

from pymesh.tools import get_surface_normals, testMesh, remove_all_except

import numpy as np
import numpy.ma as ma
from itertools import combinations

class Column:

    def __init__(self, container, packedBed, copy=False, periodicity:str=''):
        """
        Create a column object given a container and a packedBed
            - Fragment packedBed and container
            - separate volume and surfaces
            - match periodic surfaces
        """
        self.surfaces = {
                'inlet' : [],
                'outlet' : [],
                'particles': [],
                'walls': []
        }

        self.walls = {
            'x-': [], 'x+': [],
            'y-': [], 'y+': [],
            'z-': [], 'z+': [],
        }

        self.volumes = {
                'interstitial': [],
                'particles': []
        }

        self.fragment(packedBed.asDimTags(), container.asDimTags(), copyObject=copy, removeObject=True, removeTool=True, cleanFragments=True)

        self.separate_volumes()
        self.separate_bounding_surfaces()

        if 'x' in periodicity:
            self.match_periodic_surfaces(self.walls.get('x-'), self.walls.get('x+'), 'x', container.dx)

        if 'y' in periodicity:
            self.match_periodic_surfaces(self.walls.get('y-'), self.walls.get('y+'), 'y', container.dy)

        if 'z' in periodicity:
            self.match_periodic_surfaces(self.walls.get('z-'), self.walls.get('z+'), 'z', container.dz)


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

        # fragmented, fmap = factory.fragment(object, tool, removeObject=removeObject, removeTool=removeTool)

        ## NOTE: Intersection preserves normals. This is so stupid.
        ## Direct fragmentation doesn't preserve surface normals
        ## TODO: File an issue with upstream
        obj2, _ = factory.intersect(object, tool, removeObject=True, removeTool=False)
        fragmented, fmap = factory.fragment(obj2, tool, removeObject=removeObject, removeTool=removeTool)


        if cleanFragments:
            print("Cleaning Fragments")
            factory.remove([e for e in fragmented if e not in fmap[-1]], recursive=True)

        if cleanAll:
            all = factory.getEntities(dim=3)
            factory.remove([e for e in all if e not in fmap[-1]], recursive=True)

        self.entities = sorted(fmap[-1][:])

        return self.entities

    def separate_volumes(self):
        self.volumes.update({'interstitial': [ self.entities[-1][1] ]})
        self.volumes.update({'particles': [ tag for _, tag in self.entities[:-1] ]})


    def separate_bounding_surfaces(self):
        """
        Given a fragmented 3D column, extract bounding surfaces and separate them based on their normals in the cardinal directions.
        """
        factory = gmsh.model.occ
        factory.synchronize()

        bounding_surfaces = gmsh.model.getBoundary(self.entities, combined=False, oriented=False, recursive=False)

        normals = get_surface_normals(bounding_surfaces)

        xm = []
        xp = []
        ym = []
        yp = []
        zm = []
        zp = []

        beads = []

        for s,n in zip(bounding_surfaces, normals):

            if np.array_equal(n,[-1,0,0]):
                xm.append(s[1])
            elif np.array_equal(n,[1,0,0]):
                xp.append(s[1])
            elif np.array_equal(n,[0,-1,0]):
                ym.append(s[1])
            elif np.array_equal(n,[0,1,0]):
                yp.append(s[1])
            elif np.array_equal(n,[0,0,-1]):
                zm.append(s[1])
            elif np.array_equal(n,[0,0,1]):
                zp.append(s[1])
            elif np.array_equal(n,[0,0,0]):
                beads.append(s[1])

        self.walls.update({'x-': xm})
        self.walls.update({'x+': xp})
        self.walls.update({'y-': ym})
        self.walls.update({'y+': yp})
        self.walls.update({'z-': zm})
        self.walls.update({'z+': zp})

        self.surfaces.update({'particles': beads})

        self.surfaces.update({'inlet': zm})
        self.surfaces.update({'outlet': zp})
        self.surfaces.update({'walls': xm + xp + ym + yp})


    def match_periodic_surfaces(self, sLeft, sRight, perDir, distance):
        """
        Match surfaces on sleft and sright by bounding box. Then setPeriodic().
        """

        print("Matching periodic in", perDir)
        print( len(sLeft), len(sRight) )

        if len(sLeft) != len(sRight):
            remove_all_except([ (2,tag) for tag in sLeft + sRight])
            testMesh("surfaceMismatch.vtk")
            print(sLeft)
            print(sRight)
            raise(AssertionError)

        affineTranslation = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]

        for s,t in zip(sLeft, sRight):
            print(s, ' -> ', t)

        if perDir == 'x':
            mask = [1, 0, 0 ] * 2
            affineTranslation[3] = distance
        elif perDir == 'y':
            mask = [0, 1, 0 ] * 2
            affineTranslation[7] = distance
        elif perDir == 'z':
            mask = [0, 0, 1 ] * 2
            affineTranslation[11] = distance
        else:
            raise(ValueError)

        ## Terminology: sm = surface-minus, sp = surface-plus
        ## Mask the bounding box in the perDir direction and compare
        for sm in sLeft:
            bboxm = gmsh.model.getBoundingBox(2, sm)
            bboxm_masked = ma.masked_array(bboxm, mask=mask)
            for sp in sRight:
                bboxp = gmsh.model.getBoundingBox(2, sp)
                bboxp_masked = ma.masked_array(bboxp, mask=mask)
                if np.allclose(bboxm_masked, bboxp_masked):
                    gmsh.model.mesh.setPeriodic(2, [sp], [sm], affineTranslation)

    def set_physical_groups(self):
        gmsh.model.removePhysicalGroups()

        print("Setting physical:", self.surfaces.get('inlet'))

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


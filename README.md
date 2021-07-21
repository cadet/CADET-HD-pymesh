# pymesh

Chromatography meshing software built on top of gmsh.

A rewrite of genmesh because python is a bit more flexible and concise for what is essentially a wrapper around gmsh. 

Plus a rewrite helps me reorganize the software at an architectural level. 

# Features roadmap
- [TASK] cylinder container shape
- [TASK] porosity manipulation by bead addition/deletion
- [TASK] bridges, cuts
- [TASK] Move to numpy arrays
- [TASK] check out numba njit
- [TASK] Parallelize

# Known issues:
- [CRIT] setting gmsh.General.NumThreads generates degenerate element surfaces. It's a gmsh issue.
    - observed when used with periodicity and linked mesh
    - In paraview, extract surfaces and then clip to see the degenerate surfaces

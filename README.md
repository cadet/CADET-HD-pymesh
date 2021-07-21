# pymesh

Chromatography meshing software built on top of gmsh.

A rewrite of genmesh because python is a bit more flexible and concise for what is essentially a wrapper around gmsh. 

Plus a rewrite helps me reorganize the software at an architectural level. 

# Install
The best idea is to just use conda, create your environment, install necessary dependencies, install pip in conda, and then do `pip install .`


If gmsh is built from source, ensure that 
    - PYTHONPATH points to $GMSH_ROOT/lib (or wherever the gmsh.py file is)
    - LD_LIBRARY_PATH points to $GMSH_ROOT/lib (or wherever the gmsh{.so,.a} files are)

# Usage

The script in `bin/` should be available in `$PATH` after the install. It is currently called `mesh`. Given the appropriate input file in yaml format, run: `mesh input.yaml`

# Features roadmap
- [PART] cylinder container shape
- [TASK] porosity manipulation by bead addition/deletion
- [TASK] bridges, cuts
- [TASK] Move to numpy arrays
- [TASK] check out numba njit
- [TASK] Parallelize

# Known issues:
- [CRIT] setting gmsh.General.NumThreads generates degenerate element surfaces. It's a gmsh issue.
    - observed when used with periodicity and linked mesh
    - In paraview, extract surfaces and then clip to see the degenerate surfaces
- OpenCASCADE fragment operation doesn't preserve surface normals of cut objects. But intersecting before fragmenting does.
- stack_all() fails (possibly memory issues?) for large packings.

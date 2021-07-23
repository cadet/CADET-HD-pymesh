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
- [NEXT] bridges, cuts
- [TASK] porosity manipulation by bead addition/deletion
- [TASK] Move to numpy arrays?
- [TASK] check out numba njit
- [TASK] Parallelize
- [TASK] Profile stack_all
- [TASK] Debug mode
- [DONE] Timestamp in log filenames
- [TASK] Add JSON support
- [TASK] Consider ruamel_yaml
- [TASK] Geometry save and load

# Known issues:
- [CRIT] setting gmsh.General.NumThreads generates degenerate element surfaces. It's a gmsh issue.
    - observed when used with periodicity and linked mesh
    - In paraview, extract surfaces and then clip to see the degenerate surfaces
- OpenCASCADE fragment operation doesn't preserve surface normals of cut objects. But intersecting before fragmenting does.
- stack_all() fails (possibly memory issues?) for large packings.
- Meshes fail on servers (IBT067 and IBT012) even though the whole toolchain was recompiled. Locally, IBT918, Arch Linux, those same meshes and configs work
    - OCCT 7.5.0-3 (some patches for install location changes in OCCT, but otherwise the same)
    - GMSH 4.8.4 (from git tag gmsh_4_8_4)
    - Fixed by setting the following in input.yaml::gmsh:
        - Geometry.OCCBoundsUseStl: 1
        - Mesh.StlAngularDeflection: 0.08
        - Mesh.StlLinearDeflection: 0.0005
    

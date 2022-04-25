# pymesh

Chromatography meshing software built on top of gmsh.

A rewrite of genmesh because python is a bit more flexible and concise for what is essentially a wrapper around gmsh. 

Plus a rewrite helps me reorganize the software at an architectural level. 

# Install
The best idea is to just use conda, create your environment, install necessary dependencies, install pip in conda, and then do `pip install .`

If gmsh is built from source, ensure that 
    - `PYTHONPATH` points to `$GMSH_ROOT/lib` (or wherever the gmsh.py file is)
    - `LD_LIBRARY_PATH` points to `$GMSH_ROOT/lib` (or wherever the gmsh{.so,.a} files are)

NOTE: I use some weird `git_version()` function in `setup.py`. You might wanna change that.

# Usage

The script in `bin/` should be available in `$PATH` after the install. It is currently called `mesh`. Given the appropriate input file in yaml format, run: `mesh input.yaml`

# Dummy yaml
```yaml
packedbed:
  packing_file:
    filename: packing.xyzd
    dataformat: <d
  nbeads: 4
  scaling_factor: 1.0
  # auto_translate: True
  particles:
    scaling_factor: 0.9997
    # modification: bridge | cut 
    # relative_bridge_radius: ...
container:
  shape: cylinder
  size: [ 0.0, 0.0, -0.5, 0.0, 0.0, 4.0, 0.5 ]
  # size: [-2, -2, 0, 4, 4, 4]
  # periodicity: 
  # linked: True
  # stack_method: planecut
  # inlet_length: 0.0
  # outlet_length: 0.0
mesh:
  # size: 0.15
  size_method: field
  field:
    threshold:
      size_in: 0.06
      size_out: 0.14
      rad_min_factor: 0.4
      rad_max_factor: 0.6
  algorithm: 5
  algorithm3D: 10
  generate: 2
output:
  filename: mesh.vtk
gmsh:
  General.Verbosity: 5
  Geometry.OCCParallel: 1
  Mesh.MaxNumThreads1D: 8
  Mesh.MaxNumThreads2D: 8
  Mesh.MaxNumThreads3D: 8
  Mesh.ScalingFactor: 0.0001
general:
  fragment: True
```

# Notes
- For `shape: cyl`, `size: [x, y, z, dx, dy, dz, r]`
- For `shape: box`, `size: [x, y, z, dx, dy, dz]`
- If `mesh.field.threshold.size_in` and `mesh.field.threshold.size_out` are not given, they default to `mesh.size`
- Set `general.fragment` to `False` to run a quick mesh and manual visual check for correct dimensions and intersecting volumes.
    - Best with `mesh.generate` set to `2`
    - Be aware that this breaks physical groups, matching periodic surfaces etc

# Features roadmap
- [DONE] Timestamp in log filenames
- [DONE] cylinder container shape
- [TASK] porosity manipulation by bead addition/deletion
- [TASK] Documentation
- [NEXT] bridges, cuts
- [TASK] Auto container sizing?
- [TASK] Move to numpy arrays?
- [TASK] check out numba njit
- [TASK] Parallelize
- [TASK] Profile stack_all
- [TASK] Debug mode
- [TASK] Add JSON support
- [TASK] Consider ruamel_yaml
- [TASK] Geometry save and load: stashed
- [TASK] Improve memory usage
    - separate_bounding_surfaces()
- [TASK] Print out information about the column: 
    - length or bed and column
    - porosity of bed and column
    - Particle volumes
    - Particle size distribution: mean

# Known issues:
- [CRIT] setting gmsh.General.NumThreads generates degenerate element surfaces. It's a gmsh issue.
    - observed when used with periodicity and linked mesh
    - In paraview, extract surfaces and then clip to see the degenerate surfaces
- OpenCASCADE fragment operation doesn't preserve surface normals of cut objects. But intersecting before fragmenting does.
- stack_all() fails (possibly memory issues?) for large packings.
- Meshes fail on servers (IBT067 and IBT012) even though the whole toolchain was recompiled. Locally, IBT918, Arch Linux, those same meshes and configs work
    - OCCT 7.5.0-3 (some patches for install location changes in OCCT, but otherwise the same)
    - GMSH 4.8.4 (from git tag gmsh_4_8_4)
    - Fixed (partially) by setting the following in input.yaml::gmsh:
        - Geometry.OCCBoundsUseStl: 1
        - Mesh.StlAngularDeflection: 0.08
        - Mesh.StlLinearDeflection: 0.0005
    - It also seems to be mesh size dependent(???)
- Weird segfaulting with General.NumThreads on IBT012.
    - Crashes at random parts of meshing on _some_ values of General.NumThreads
    - For Delaunay + HXT algos
    - https://nielscautaerts.xyz/debugging-python-in-neovim.html
    - https://stackoverflow.com/questions/10035541/what-causes-a-python-segmentation-fault
    - https://gitlab.onelab.info/gmsh/gmsh/-/issues/1807
    - `munmap_chunk(): invalid pointer`
    - corrupted double-linked list
    - General.Verbosity = 3,4 makes it segfault
    - python3.9: malloc.c:2542: sysmalloc: Assertion `(old_top == initial_top (av) && old_size == 0) || ((unsigned long) (old_size) >= MINSIZE && prev_inuse (old_top) && ((unsigned long) old_end & (pagesize - 1)) == 0)' failed.

    
https://gitlab.onelab.info/gmsh/gmsh/-/issues/1246
https://gitlab.onelab.info/gmsh/gmsh/-/issues/1061
https://gitlab.onelab.info/gmsh/gmsh/-/issues/1330
https://gitlab.onelab.info/gmsh/gmsh/-/issues/1480
https://gitlab.onelab.info/gmsh/gmsh/-/issues/338

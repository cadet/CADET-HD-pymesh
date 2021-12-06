# pymesh

Chromatography meshing software built on top of gmsh.

A rewrite of genmesh because python is a bit more flexible and concise for what is essentially a wrapper around gmsh. 

Plus a rewrite helps me reorganize the software at an architectural level. 

# Install
The best idea is to just use conda, create your environment, install necessary dependencies, install pip in conda, and then do `pip install .`

If gmsh is built from source, ensure that 
    - `PYTHONPATH` points to `$GMSH_ROOT/lib` (or wherever the gmsh.py file is)
    - `LD_LIBRARY_PATH` points to `$GMSH_ROOT/lib` (or wherever the gmsh{.so,.a} files are)

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
```

# Notes
- For `shape: cyl`, `size: [x, y, z, dx, dy, dz, r]`
- For `shape: box`, `size: [x, y, z, dx, dy, dz]`

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
- [TASK] Geometry save and load: stashed
- [TASK] Improve memory usage
    - separate_bounding_surfaces()

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
    
https://gitlab.onelab.info/gmsh/gmsh/-/issues/1246
https://gitlab.onelab.info/gmsh/gmsh/-/issues/1061
https://gitlab.onelab.info/gmsh/gmsh/-/issues/1330
https://gitlab.onelab.info/gmsh/gmsh/-/issues/1480
https://gitlab.onelab.info/gmsh/gmsh/-/issues/338

# pymesh

Chromatography meshing software built on top of gmsh.

A rewrite of genmesh because python is a bit more flexible and concise for what is essentially a wrapper around gmsh. 

Plus a rewrite helps me reorganize the software at an architectural level. 

# Features roadmap
- container shapes
    - [DONE] box
    - [TASK] cylinder
- container sizes
    - [DROP] auto-size
- periodic meshes
    - [DONE] non-stacked workflow
    - [DONE] surface separation
    - [DONE] match and set periodic
- [DONE] linked inlet-column-outlet sections
    - [DONE] actual periodicity pending
- [PART] mesh fields
- [DONE] polydisperse mesh size adaptation
- [TASK] porosity manipulation by bead addition/deletion
- [TASK] bridges

- [ONGO] Consider moving to a more finegrained control over the packing: packedBed -> bead
    - [DONE] each bead also contains the geo tag 
    - [TASK] mesh sizing can be controlled within the bead 
    - [DONE] geometry generation can be given within the bead

- [TASK] Move to numpy
- [TASK] check out numba

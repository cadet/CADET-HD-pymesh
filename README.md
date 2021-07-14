# pymesh

Chromatography meshing software built on top of gmsh.

A rewrite of genmesh because python is a bit more flexible and concise for what is essentially a wrapper around gmsh. 

Plus a rewrite helps me reorganize the software at an architectural level. 

# Features roadmap
- container shapes
    - [DONE] box
    - [TASK] cylinder
- container sizes
    - [TASK] auto-size
- periodic meshes
    - [DONE] non-stacked workflow
    - [DONE] surface separation
    - [DONE] match and set periodic
- [DONE] linked inlet-column-outlet sections
    - [DONE] actual periodicity pending
- [PART] mesh fields
- [TASK] polydisperse mesh size adaptation
- [TASK] porosity manipulation by bead addition/deletion
- [TASK] bridges

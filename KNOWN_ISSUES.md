# Known issues:

- setting gmsh.General.NumThreads generates degenerate element surfaces. It's a gmsh issue.
    - observed when used with periodicity and linked mesh
    - In paraview, extract surfaces and then clip to see the degenerate surfaces
- OpenCASCADE fragment operation doesn't preserve surface normals of cut objects. But intersecting before fragmenting does.
- stack_all() might fails for large packings.
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

from multiprocessing import Process
import gmsh

def f(i):
    gmsh.initialize()
    s = gmsh.model.occ.addRectangle(i,0,0, 1,1)
    gmsh.model.occ.synchronize()
    gmsh.option.setNumber('Mesh.MeshSizeMax', 0.005)
    gmsh.model.mesh.generate(2)
    gmsh.finalize()

if __name__ == '__main__':
    procs = []
    for i in range(5):
        p = Process(target=f, args=(i,))
        p.start()
        procs.append(p)
    for p in procs: p.join()
    print("All done")
    gmsh.initialize()
    gmsh.write('test.vtk')
    gmsh.finalize()

#!/usr/bin/python3

from pymesh.configHandler import load_config, set_gmsh_defaults
from pymesh.model import Model

import argparse
import gmsh

def pymesh():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", help="Input file")
    args = vars(ap.parse_args())

    config = load_config(args['file'])

    gmsh.initialize()
    gmsh.model.add("default")

    set_gmsh_defaults(config)

    defaultModel = Model(config)
    defaultModel.mesh()
    defaultModel.write()

    gmsh.finalize()

if __name__ == "__main__":
    pymesh()

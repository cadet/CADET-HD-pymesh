#!/usr/bin/python3

from pymesh.configHandler import ConfigHandler
from pymesh.model import Model
from pymesh.log import Logger

import argparse
import gmsh


def pymesh():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", help="Input file")
    args = vars(ap.parse_args())

    logger = Logger()

    config = ConfigHandler(logger)
    config.read(args['file'])

    gmsh.initialize()
    gmsh.model.add("default")

    config.set_gmsh_defaults()

    defaultModel = Model(config)
    defaultModel.mesh()
    defaultModel.write()

    gmsh.finalize()

if __name__ == "__main__":
    pymesh()

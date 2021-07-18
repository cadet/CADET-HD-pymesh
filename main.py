#!/usr/bin/python3

from pymesh.configHandler import ConfigHandler
from pymesh.model import Model
from pymesh.log import Logger

import argparse
import gmsh
import subprocess


def pymesh():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", help="Input file")
    args = vars(ap.parse_args())

    logger = Logger()

    githash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).strip().decode('utf8')
    logger.note('GMSH API:', gmsh.GMSH_API_VERSION)
    logger.note('pymesh git hash:', githash)

    config = ConfigHandler(logger)
    config.read(args['file'])

    gmsh.initialize()
    gmsh.model.add("default")

    config.set_gmsh_defaults()
    config.set_gmsh_options()

    defaultModel = Model(config)
    defaultModel.mesh()
    defaultModel.write()

    gmsh.finalize()

    logger.write(config.output_filename)

if __name__ == "__main__":
    pymesh()

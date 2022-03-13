let
  pkgs = import <nixpkgs> {};
in pkgs.mkShell rec {
    name = "pymesh";

    pymesh = pkgs.python3Packages.buildPythonPackage{
        pname = "pymesh";
        version = "0.1";

        src = ./.;

        # ## GMSH override to build and install lib files
        # ## Can also be placed in ~/.nixpkgs/config.nix
        # gmsh = pkgs.gmsh.overrideAttrs (oldAttrs: rec {
        #         cmakeFlags = [
        #         "-DENABLE_BUILD_LIB=1"
        #         "-DENABLE_BUILD_SHARED=1"
        #         "-DENABLE_BUILD_DYNAMIC=1"
        #         ];
        #         });

        propagatedBuildInputs = with pkgs; [
                python39
                python3Packages.numpy
                python3Packages.rich
                python3Packages.ruamel-yaml
                python3Packages.GitPython
                python3Packages.setuptools
                gmsh
            ];

        doCheck = false;
    };

  buildInputs = [
    pymesh
  ];

  shellHook = ''
    # Tells pip to put packages into $PIP_PREFIX instead of the usual locations.
    # See https://pip.pypa.io/en/stable/user_guide/#environment-variables.
    export PIP_PREFIX=$(pwd)/_build/pip_packages
    export PYTHONPATH="$PIP_PREFIX/${pkgs.python3.sitePackages}:$PYTHONPATH"
    export PYTHONPATH="${pkgs.gmsh}/lib:$PYTHONPATH"
    export PATH="$PIP_PREFIX/bin:$PATH"
    unset SOURCE_DATE_EPOCH
  '';

}

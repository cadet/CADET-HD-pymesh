{
  inputs = { nixpkgs.url = "github:nixos/nixpkgs/3eb07eeafb52bcbf02ce800f032f18d666a9498d"; };
  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = { self, nixpkgs, flake-utils }:
  flake-utils.lib.eachDefaultSystem (system:
  let 
    pkgs = nixpkgs.legacyPackages.${system}; 

    # builtins.toString still makes a nix store path for purity
    PROJECT_ROOT = builtins.toString ./.;

    ## GMSH override to build and install lib files
    ## Can also be placed in ~/.nixpkgs/config.nix
    gmsh_with_libs = pkgs.gmsh.overrideAttrs (oldAttrs: rec {

      version = "4.11.0-2ac03e";

      src = pkgs.fetchgit {
        url = "https://gitlab.onelab.info/gmsh/gmsh";
        rev = "2ac03e26721ff5ffe20759ef4ad474da6cbf4b44";
        sha256 = "nwYodyHJIzy5W6FX/D+zfEoNBPQFI0rF6bk/en/3RCQ=";
      };

      patches = [
        ./custom_mesh_copy.patch
      ];

      cmakeFlags = [
        "-DCMAKE_BUILD_TYPE=Release"
        "-DENABLE_BUILD_LIB=1"
        "-DENABLE_BUILD_SHARED=1"
        "-DENABLE_BUILD_DYNAMIC=1"
        "-DENABLE_OPENMP=1"
      ];
    });

      in 
      {

        defaultPackage = pkgs.python3Packages.buildPythonPackage{
          pname = "pymesh";
          version = "0.1";

          src = ./.;

          propagatedBuildInputs = with pkgs; [
            python39
            python3Packages.pip
            python3Packages.numpy
            python3Packages.rich
            python3Packages.ruamel-yaml
            python3Packages.GitPython
            python3Packages.setuptools
            python3Packages.mpmath
            gmsh_with_libs
          ];

          doCheck = false;
        };


        devShell = pkgs.mkShell rec {
          name = "pymesh";

          propagatedBuildInputs = with pkgs; [
            python39
            python3Packages.pip
            python3Packages.numpy
            python3Packages.rich
            python3Packages.ruamel-yaml
            python3Packages.GitPython
            python3Packages.setuptools
            python3Packages.mpmath
            gmsh_with_libs
          ];

          # Allows editing the source code from within the devShell while still having access
          # to libs and scripts in PATHs. PROJECT_ROOT being a variable ensures that we can 
          # run this flake from any directory.
          shellHook = ''
            # Tells pip to put packages into $PIP_PREFIX instead of the usual locations.
            # See https://pip.pypa.io/en/stable/user_guide/#environment-variables.
            export PIP_PREFIX=$HOME/.cache/nix_pip_packages
            export PYTHONPATH="$PIP_PREFIX/${pkgs.python3.sitePackages}:$PYTHONPATH"
            export PYTHONPATH="${gmsh_with_libs}/lib:$PYTHONPATH"
            export PYTHONPATH="'' + PROJECT_ROOT + '':$PYTHONPATH"
            export PATH="$PIP_PREFIX/bin:$PATH"
            export PATH="'' + PROJECT_ROOT + ''/bin:$PATH"
            unset SOURCE_DATE_EPOCH
            '';

          };
        }
        );

      }

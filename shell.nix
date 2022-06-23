# { pkgs ? import <nixpkgs> { } }:
{
  pkgs ? import (builtins.fetchTarball {

      # Descriptive name to make the store path easier to identify
      name = "nixpkgs-unstable-2022-03-17";

      # Commit hash for nixos-unstable as of 2018-09-12
      url = "https://github.com/nixos/nixpkgs/archive/3eb07eeafb52bcbf02ce800f032f18d666a9498d.tar.gz";

      # Hash obtained using `nix-prefetch-url --unpack <url>`
      sha256 = "1ah1fvll0z3w5ykzc6pabqr7mpbnbl1i3vhmns6k67a4y7w0ihrr";

    }) {}

  }:

  let
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
      "-DCMAKE_BUILD_TYPE=Debug"
      "-DENABLE_BUILD_LIB=1"
      "-DENABLE_BUILD_SHARED=1"
      "-DENABLE_BUILD_DYNAMIC=1"
    ];
  });

in pkgs.mkShell rec {
  name = "pymesh";

  pymesh = pkgs.python3Packages.buildPythonPackage{
    pname = "pymesh";
    version = "0.1";

    src = ./.;

    propagatedBuildInputs = with pkgs; [
      python39
      python3Packages.numpy
      python3Packages.rich
      python3Packages.ruamel-yaml
      python3Packages.GitPython
      python3Packages.setuptools
      gmsh_with_libs
    ];

    doCheck = false;
  };

  # buildInputs = [
  #   # pymesh
  # ];

  propagatedBuildInputs = with pkgs; [
    python39
    python3Packages.numpy
    python3Packages.rich
    python3Packages.ruamel-yaml
    python3Packages.GitPython
    python3Packages.setuptools
    gmsh_with_libs
  ];

  shellHook = ''
    # Tells pip to put packages into $PIP_PREFIX instead of the usual locations.
    # See https://pip.pypa.io/en/stable/user_guide/#environment-variables.
    export PIP_PREFIX=$(pwd)/_build/pip_packages
    export PYTHONPATH="$PIP_PREFIX/${pkgs.python3.sitePackages}:$PYTHONPATH"
    export PYTHONPATH="${gmsh_with_libs}/lib:$PYTHONPATH"
    export PYTHONPATH="$(pwd):$PYTHONPATH"
    export PATH="$PIP_PREFIX/bin:$PATH"
    export PATH="$(pwd)/bin:$PATH"
    unset SOURCE_DATE_EPOCH
  '';

}

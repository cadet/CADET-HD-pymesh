with import <nixpkgs> { };

python3Packages.buildPythonPackage{
    pname = "pymesh";
    version = "0.1";

    src = ./.;

propagatedBuildInputs = [
        python39
        python3Packages.numpy
        python3Packages.rich
        python3Packages.ruamel-yaml
        python3Packages.GitPython
        python3Packages.setuptools
        gmsh
    ];


    # checkInputs = with python3Packages; [
    #     pytest
    # ];

    doCheck = false;
    # pythonImportsCheck = [ "pymesh" ];

}

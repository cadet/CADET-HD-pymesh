#!/bin/bash

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
# This is an imperfect script and must be used mostly as a GUIDE to installing the dependencies for genmesh. 
# THIS SCRIPT IS NOT IDEMPOTENT.
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< 

set -xeuo pipefail

BASE_DIR=${PWD}
INSTALL_DIR=${1:-$HOME/local/modules}

TCL_VERSION=8.6.11
TK_VERSION=8.6.11
FREETYPE_VERSION=2.12.0
OCCT_VERSION=7.5.3
GMSH_VERSION=4.10.3

OCCT_GIT_TAG=V${OCCT_VERSION//./_}
GMSH_GIT_TAG=gmsh_${GMSH_VERSION//./_}

OCCT_GIT_BRANCH=$OCCT_GIT_TAG
GMSH_GIT_BRANCH=$GMSH_GIT_TAG

OCCT_DIR_NAME=occt
GMSH_DIR_NAME=gmsh
GMSH_BUILD_TYPE=RelWithDebInfo
NTHREADS=8

TCL_LINK="https://prdownloads.sourceforge.net/tcl/tcl$TCL_VERSION-src.tar.gz"
TK_LINK="https://prdownloads.sourceforge.net/tcl/tk$TK_VERSION-src.tar.gz"
FREETYPE_LINK="https://sourceforge.net/projects/freetype/files/freetype2/$FREETYPE_VERSION/freetype-$FREETYPE_VERSION.tar.xz"
OCCT_GIT_LINK=https://git.dev.opencascade.org/repos/occt.git
GMSH_GIT_LINK=https://gitlab.onelab.info/gmsh/gmsh.git


install_tcl()
{
    mkdir -p "TCL-$TCL_VERSION"
    cd "TCL-$TCL_VERSION"
    wget "$TCL_LINK" -O tcl-src.tar.gz
    tar xf tcl-src.tar.gz --strip-components=1
    cd unix
    ./configure --enable-gcc --enable-shared --enable-threads --prefix=$INSTALL_DIR/tcl/$TCL_VERSION --enable-64bit
    make -j $NTHREADS
    make install
    cd "$BASE_DIR"
}

install_tk()
{
    mkdir -p "TK-$TK_VERSION"
    cd "TK-$TK_VERSION"
    wget "$TK_LINK" -O tk-src.tar.gz
    tar xf tk-src.tar.gz --strip-components=1
    cd unix
    ./configure --enable-gcc --enable-shared --enable-threads --prefix=$INSTALL_DIR/tk/$TK_VERSION --enable-64bit --with-tcl=$INSTALL_DIR/tcl/$TCL_VERSION/lib                           
    make -j $NTHREADS
    make install
    cd "$BASE_DIR"
}

install_freetype2()
{
    mkdir -p "FREETYPE-$FREETYPE_VERSION"
    cd "FREETYPE-$FREETYPE_VERSION"
    wget "$FREETYPE_LINK" -O freetype-src.tar.gz
    tar xf freetype-src.tar.gz --strip-components=1
    ./configure --prefix=$INSTALL_DIR/freetype/$FREETYPE_VERSION CFLAGS='-m64 -fPIC'  CPPFLAGS='-m64 -fPIC'
    make -j $NTHREADS
    make install
    cd "$BASE_DIR"

}

# install_occt()
# {
#     mkdir -p "OCCT-$OCCT_VERSION"
#     tar xf $OCCT_TAR -C "OCCT-$OCCT_VERSION" --strip-components=1
#     cd "OCCT-$OCCT_VERSION"
#     mkdir -p build
#     cd build
#     cmake -DCMAKE_INSTALL_PREFIX=$INSTALL_DIR/$OCCT_DIR_NAME/$OCCT_VERSION -D3RDPARTY_TCL_LIBRARY_DIR=$INSTALL_DIR/tcl/$TCL_VERSION/lib/ -D3RDPARTY_TK_LIBRARY_DIR=$INSTALL_DIR/tk/$TK_VERSION/lib -D3RDPARTY_TK_INCLUDE_DIR=$INSTALL_DIR/tk/$TK_VERSION/include/ -D3RDPARTY_TCL_INCLUDE_DIR=$INSTALL_DIR/tcl/$TCL_VERSION/include/ -D3RDPARTY_FREETYPE_DIR=$INSTALL_DIR/freetype/$FREETYPE_VERSION ..
#     make -j $NTHREADS
#     make install
#     cd "$BASE_DIR"
# }

install_occt_from_git()
{
    # git clone "$OCCT_GIT_LINK" occt
    # cd occt
    # git fetch --all --tags
    # git checkout tags/$OCCT_GIT_TAG

    clone_or_pull "$OCCT_GIT_LINK" occt $OCCT_GIT_BRANCH
    cd occt

    mkdir -p build
    cd build
    cmake -DCMAKE_INSTALL_PREFIX=$INSTALL_DIR/$OCCT_DIR_NAME/$OCCT_VERSION -D3RDPARTY_TCL_LIBRARY_DIR=$INSTALL_DIR/tcl/$TCL_VERSION/lib/ -D3RDPARTY_TK_LIBRARY_DIR=$INSTALL_DIR/tk/$TK_VERSION/lib -D3RDPARTY_TK_INCLUDE_DIR=$INSTALL_DIR/tk/$TK_VERSION/include/ -D3RDPARTY_TCL_INCLUDE_DIR=$INSTALL_DIR/tcl/$TCL_VERSION/include/ -D3RDPARTY_FREETYPE_DIR=$INSTALL_DIR/freetype/$FREETYPE_VERSION ..
    make -j $NTHREADS
    make install
    cd "$BASE_DIR"
}

install_gmsh_from_git()
{
    # git clone "$GMSH_GIT_LINK" gmsh
    # cd gmsh
    # git fetch --all --tags
    # git checkout tags/$GMSH_GIT_TAG

    clone_or_pull "$GMSH_GIT_LINK" gmsh $GMSH_GIT_BRANCH
    cd gmsh
    mkdir -p build
    cd build
    cmake -DCMAKE_BUILD_TYPE=$GMSH_BUILD_TYPE -DCMAKE_PREFIX_PATH=$INSTALL_DIR/$OCCT_DIR_NAME/$OCCT_VERSION -DCMAKE_INSTALL_PREFIX=$INSTALL_DIR/$GMSH_DIR_NAME/$GMSH_VERSION -DENABLE_BUILD_LIB=1 -DENABLE_BUILD_SHARED=1 -DENABLE_BUILD_DYNAMIC=1 -DENABLE_OPENMP=1 ..
    make -j $NTHREADS
    make install
    cd "$BASE_DIR"
}

clone_or_pull()
{
    LINK="$1"
    DIR="$2"
    BRANCH="$3"

    LOCAL_BASE_DIR="$PWD"
    
    if [ -d "$DIR" ]; then
        cd "$DIR"
        if [ -n $BRANCH ]; then
            git checkout $BRANCH
        fi
        ## Don't pull if in detached head, i.e., tagged commits
        if [ $(git rev-parse --symbolic-full-name HEAD) != "HEAD" ]; then 
            git pull
        fi
        cd "$LOCAL_BASE_DIR"
    else
        if [ -n $BRANCH ]; then
            git clone -b $BRANCH $LINK $DIR
        else
            git clone $LINK $DIR
        fi
    fi
}

check_pre()
{
    #TODO: check headers also
    #TODO: exit if not found
    #TODO: Check for opengl headers?
    [[ $(ldconfig -p | grep libXmu.so -c) -gt 1 ]] && echo "Found libXmu"
    [[ $(ldconfig -p | grep libXi.so -c ) -gt 1 ]] && echo "Found libXi"
    [[ $(ldconfig -p | grep libfreetype.so -c) -gt 1 ]] && echo "Found libfreetype"

}

# check_pre
install_tcl
install_tk
install_freetype2
install_occt_from_git
install_gmsh_from_git

# CMake Build


**Please use the Scons build script located in the root of the gaffer repo.**

This is a work in progress CMake build script, which is mainly useful for generating IDE configuration files.

**Create directory for gaffer development**

~~~
mkdir dev-gaffer
cd dev-gaffer
~~~

**Download Gaffer Dependencies**
~~~
wget https://github.com/GafferHQ/dependencies/releases/download/0.48.0.0/gafferDependencies-0.48.0.0-linux.tar.gz
~~~

**Extract**
~~~
tar xvf gafferDependencies-0.48.0.0-linux.tar.gz
~~~

**Set root env var for build**
~~~
export GAFFER_DEPENDENCIES_ROOT=$PWD/gafferDependencies-0.48.0.0-linux

export ILMBASE_ROOT=$GAFFER_DEPENDENCIES_ROOT
export OPENEXR_ROOT=$GAFFER_DEPENDENCIES_ROOT
export FREETYPE_DIR=$GAFFER_DEPENDENCIES_ROOT
export CORTEX_ROOT=$GAFFER_DEPENDENCIES_ROOT
~~~


**Clone git repo and create a directory called .build**

~~~
git clone https://github.com/GafferHQ/gaffer.git
cd gaffer
mkdir .build
cd .build
~~~

**Download and extract Arnold**
~~~
cd $GAFFER_DEPENDENCIES_ROOT
# download arnold here & extract to directory called Arnold-5.1.0.0
~~~

**Run CMake to generate Makefile**
~~~
cmake ../contrib/cmake
-DTBB_INSTALL_DIR=$GAFFER_DEPENDENCIES_ROOT
-DBOOST_ROOT=$GAFFER_DEPENDENCIES_ROOT
-DILMBASE_ROOT=$GAFFER_DEPENDENCIES_ROOT
-DOPENEXR_ROOT=$GAFFER_DEPENDENCIES_ROOT
-DCMAKE_PREFIX_PATH=$GAFFER_DEPENDENCIES_ROOT
-DQt5_DIR=$GAFFER_DEPENDENCIES_ROOT/cmake/Qt5
-DOPENVDB_LOCATION=$GAFFER_DEPENDENCIES_ROOT
-DAPPLESEED_INCLUDE_DIR=$GAFFER_DEPENDENCIES_ROOT/appleseed/include
-DAPPLESEED_LIBRARY=$GAFFER_DEPENDENCIES_ROOT/appleseed/lib/libappleseed.so
-DILMBASE_NAMESPACE_VERSIONING=OFF
-DOPENEXR_NAMESPACE_VERSIONING=OFF
-DARNOLD_ROOT=$GAFFER_DEPENDENCIES_ROOT/arnold-5.1.0.0
-DWITH_IECORE_IMAGE=ON
-DWITH_IECORE_SCENE=ON
-DWITH_IECORE_ALEMBIC=ON
-DWITH_IECORE_USD=OFF
-DCMAKE_INSTALL_PREFIX=$GAFFER_DEPENDENCIES_ROOT
~~~

**Install (using 8 processes)**

~~~
make install -j8
~~~

**Launch Gaffer**

~~~
export PATH=$GAFFER_DEPENDENCIES_ROOT/bin:$PATH
gaffer
~~~

## To Do

- documentation not built

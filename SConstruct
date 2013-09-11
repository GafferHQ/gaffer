##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
#  
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#  
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#  
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#  
#      * Neither the name of John Haddon nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#  
##########################################################################

import os
import re
import sys
import glob
import shutil
import fnmatch
import py_compile
import subprocess

###############################################################################################
# Command line options
###############################################################################################

optionsFile = None

if "GAFFER_OPTIONS_FILE" in os.environ :
	optionsFile = os.environ["GAFFER_OPTIONS_FILE"]
	
if "OPTIONS" in ARGUMENTS :
	optionsFile = ARGUMENTS["OPTIONS"]
	
options = Variables( optionsFile, ARGUMENTS )

options.Add(
	"CXX",
	"The C++ compiler.",
	"g++",
)

options.Add(
	"CXXFLAGS",
	"The extra flags to pass to the C++ compiler during compilation.",
	[ "-pipe", "-Wall", "-Werror", "-O2", "-DNDEBUG", "-DBOOST_DISABLE_ASSERTS" ]
)

options.Add(
        "LINKFLAGS",
        "The extra flags to pass to the C++ linker during compilation.",
        "",
)

options.Add(
	"BUILD_DIR",
	"The destination directory in which the build will be made.",
	"./build/gaffer-${GAFFER_MAJOR_VERSION}.${GAFFER_MINOR_VERSION}.${GAFFER_PATCH_VERSION}-${GAFFER_PLATFORM}",
)

options.Add(
	"BUILD_CACHEDIR",
	"Specify a directory for SCons to cache build results in. This allows the sharing of build results"
	"among multiple developers and can significantly reduce build times, particularly when switching"
	"between multiple compilers and build options.",
	""
)

options.Add(
	"INSTALL_DIR",
	"The destination directory for the installation.",
	"./install/gaffer-${GAFFER_MAJOR_VERSION}.${GAFFER_MINOR_VERSION}.${GAFFER_PATCH_VERSION}-${GAFFER_PLATFORM}",
)

options.Add(
	"PACKAGE_FILE",
	"The file in which the final gaffer file will be created by the package target.",
	"${INSTALL_DIR}.tar.gz",
)

options.Add( 
	BoolVariable( "BUILD_DEPENDENCIES", "Set this to build all the library dependencies gaffer has.", False )
)

# variables related to building all the dependencies for gaffer. these are mutually exclusive
# with the LOCATE_* below, which are about finding the dependencies in existing locations.
# use the BUILD_* options to make a completely standalone package and the other options to
# make a build to integrate into an existing setup where the dependencies have been installed
# somewhere centrally.

options.Add(
	"DEPENDENCIES_SRC_DIR",
	"The location of a directory holding dependencies.",
	"/home/john/dev/gafferDependencies",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_PYTHON", "Set this to build python.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"PYTHON_SRC_DIR",
	"The location of the python source to be used if BUILD_DEPENDENCY_PYTHON is specified.",
	"$DEPENDENCIES_SRC_DIR/Python-2.7.5",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_BOOST", "Set this to build boost.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"BOOST_SRC_DIR",
	"The location of the boost source to be used if BUILD_DEPENDENCY_BOOST is specified.",
	"$DEPENDENCIES_SRC_DIR/boost_1_43_0",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_TBB", "Set this to build tbb.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"TBB_SRC_DIR",
	"The location of the tbb source to be used if BUILD_DEPENDENCY_TBB is specified.",
	"$DEPENDENCIES_SRC_DIR/tbb41_20130613oss",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_OPENEXR", "Set this to build openexr.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"ILMBASE_SRC_DIR",
	"The location of the ilmbase source to be used if BUILD_DEPENDENCY_OPENEXR is specified.",
	"$DEPENDENCIES_SRC_DIR/ilmbase-1.0.3",
)

options.Add(
	"OPENEXR_SRC_DIR",
	"The location of the exr source to be used if BUILD_DEPENDENCY_OPENEXR is specified.",
	"$DEPENDENCIES_SRC_DIR/openexr-1.7.1",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_JPEG", "Set this to build the jpeg library.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"JPEG_SRC_DIR",
	"The location of the jpeg source to be used if BUILD_DEPENDENCY_JPEG is specified.",
	"$DEPENDENCIES_SRC_DIR/jpeg-8c",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_TIFF", "Set this to build the tiff library.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"TIFF_SRC_DIR",
	"The location of the tiff source to be used if BUILD_DEPENDENCY_TIFF is specified.",
	"$DEPENDENCIES_SRC_DIR/tiff-3.8.2",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_PNG", "Set this to build the png library.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"PNG_SRC_DIR",
	"The location of the png source to be used if BUILD_DEPENDENCY_PNG is specified.",
	"$DEPENDENCIES_SRC_DIR/libpng-1.6.3",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_FREETYPE", "Set this to build freetype.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"FREETYPE_SRC_DIR",
	"The location of the freetype source to be used if BUILD_DEPENDENCY_FREETYPE is specified.",
	"$DEPENDENCIES_SRC_DIR/freetype-2.4.12",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_GLEW", "Set this to build GLEW.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"GLEW_SRC_DIR",
	"The location of the glew source to be used if BUILD_DEPENDENCY_GLEW is specified.",
	"$DEPENDENCIES_SRC_DIR/glew-1.7.0",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_OCIO", "Set this to build OCIO", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"OCIO_SRC_DIR",
	"The location of the OCIO source to be used if BUILD_DEPENDENCY_OCIO is specified.",
	"$DEPENDENCIES_SRC_DIR/imageworks-OpenColorIO-8883824",
)

options.Add(
	"OCIO_CONFIG_DIR",
	"The location of the OCIO config files to install with Gaffer.",
	"$DEPENDENCIES_SRC_DIR/imageworks-OpenColorIO-Configs-f931d77/nuke-default",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_OIIO", "Set this to build OIIO.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"OIIO_SRC_DIR",
	"The location of the OIIO source to be used if BUILD_DEPENDENCY_OIIO is specified.",
	"$DEPENDENCIES_SRC_DIR/oiio-Release-1.2.1",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_HDF5", "Set this to build HDF5.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"HDF5_SRC_DIR",
	"The location of the HDF5 source to be used if BUILD_DEPENDENCY_HDF5 is specified.",
	"$DEPENDENCIES_SRC_DIR/hdf5-1.8.11",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_ALEMBIC", "Set this to build Alembic.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"ALEMBIC_SRC_DIR",
	"The location of the Alembic source to be used if BUILD_DEPENDENCY_ALEMBIC is specified.",
	"$DEPENDENCIES_SRC_DIR/Alembic_1.5.0_2013072300",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_CORTEX", "Set this to build cortex.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"CORTEX_SRC_DIR",
	"The location of the boost source to be used if BUILD_DEPENDENCY_CORTEX is specified.",
	"$DEPENDENCIES_SRC_DIR/cortex",
)

options.Add(
	"CORTEX_BUILD_ARGS",
	"Additional arguments to be passed when building Cortex.",
	"",
)

options.Add(
	"CORTEX_POINTDISTRIBUTION_TILESET",
	"The tile set file to be used with the IECore::PointDistribution class.",
	"$DEPENDENCIES_SRC_DIR/tileset_2048.dat",
)

options.Add(
	"RMAN_ROOT",
	"The directory in which your RenderMan renderer is installed. Used to build GafferRenderMan.",
	"",
)

options.Add(
	"ARNOLD_ROOT",
	"The directory in which Arnold is installed. Used to build GafferArnold",
	"",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_PKGCONFIG", "Set this to build the pkgconfig library.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"PKGCONFIG_SRC_DIR",
	"The location of the pkg-config source to be used if BUILD_DEPENDENCY_PKGCONFIG is specified.",
	"$DEPENDENCIES_SRC_DIR/pkg-config-0.23",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_GL", "Set this to build PyOpenGL.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"PYOPENGL_SRC_DIR",
	"The location of the PyOpenGL source to be used if BUILD_DEPENDENCY_GL is specified.",
	"$DEPENDENCIES_SRC_DIR/PyOpenGL-3.0.2",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_QT", "Set this to build QT.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"QT_SRC_DIR",
	"The location of QT.",
	"$DEPENDENCIES_SRC_DIR/qt-everywhere-opensource-src-4.8.5",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_PYSIDE", "Set this to build PySide.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"SHIBOKEN_SRC_DIR",
	"The location of QT.",
	"$DEPENDENCIES_SRC_DIR/shiboken-1.2.0",
)

options.Add(
	"PYSIDE_SRC_DIR",
	"The location of QT.",
	"$DEPENDENCIES_SRC_DIR/pyside-qt4.8+1.2.0",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_PYQT", "Set this to build PyQt.", False )
)

options.Add(
	"SIP_SRC_DIR",
	"The location of SIP.",
	"$DEPENDENCIES_SRC_DIR/sip-4.12.3",
)

options.Add(
	"PYQT_SRC_DIR",
	"The location of SIP.",
	"$DEPENDENCIES_SRC_DIR/PyQt-x11-gpl-4.8.4",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_FONTS", "", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"FONTS_DIR",
	"The location of fonts.",
	"$DEPENDENCIES_SRC_DIR/ttf-bitstream-vera-1.10",
)

# variables to be used when making a build which will use dependencies previously
# installed in some central location. these are mutually exclusive with the BUILD_*
# variables above, which are all about building the dependencies and packaging them
# with gaffer.

options.Add(
	"LOCATE_DEPENDENCY_CPPPATH",
	"Locations on which to search for include files "
	"for the dependencies. These are included with -I.",
	[],
)

options.Add(
	"LOCATE_DEPENDENCY_SYSTEMPATH",
	"Locations on which to search for include files "
	"for the dependencies. These are included with -isystem.",
	[],
)

options.Add(
	"LOCATE_DEPENDENCY_LIBPATH",
	"The locations on which to search for libraries for "
	"the dependencies.",
	"",
)

options.Add(
	"OPENEXR_LIB_SUFFIX",
	"The suffix used when locating the OpenEXR libraries.",
	"",
)

options.Add(
	"BOOST_LIB_SUFFIX",
	"The suffix used when locating the boost libraries.",
	"",
)

options.Add(
	"GLEW_LIB_SUFFIX",
	"The suffix used when locating the glew libraries.",
	"",
)

options.Add(
	"CORTEX_LIB_SUFFIX",
	"The suffix used when locating the cortex libraries.",
	"",
)

options.Add(
	"CORTEX_PYTHON_LIB_SUFFIX",
	"The suffix used when locating the IECorePython library.",
	"",
)

options.Add(
	"OIIO_LIB_SUFFIX",
	"The suffix used when locating the OpenImageIO libraries.",
	"-1",
)

options.Add(
	"OCIO_LIB_SUFFIX",
	"The suffix used when locating the OpenColorIO libraries.",
	"",
)

# general variables

options.Add(
	"ENV_VARS_TO_IMPORT",
	"By default SCons ignores the environment it is run in, to avoid it contaminating the "
	"build process. This can be problematic if some of the environment is critical for "
	"running the applications used during the build. This space separated list of environment "
	"variables is imported to help overcome these problems.",
	"",
)

options.Add(
       "DOXYGEN",
       "Where to find the doxygen binary",
       "doxygen",
)

options.Add(
       "INKSCAPE",
       "Where to find the inkscape binary",
       "inkscape",
)

###############################################################################################
# Basic environment object. All the other environments will be based on this.
###############################################################################################

env = Environment(

	options = options,

	GAFFER_MAJOR_VERSION = "0",
	GAFFER_MINOR_VERSION = "79",
	GAFFER_PATCH_VERSION = "0",

)

for e in env["ENV_VARS_TO_IMPORT"].split() :
	if e in os.environ :
		env["ENV"][e] = os.environ[e]

if env["PLATFORM"] == "darwin" :

	env["ENV"]["MACOSX_DEPLOYMENT_TARGET"] = "10.4"
	env.Append( CXXFLAGS = [ "-D__USE_ISOC99" ] )
	env["GAFFER_PLATFORM"] = "osx"
	
elif env["PLATFORM"] == "posix" :
	
	## We really want to not have the -Wno-strict-aliasing flag, but it's necessary to stop boost
	# python warnings that don't seem to be prevented by including boost via -isystem even. Better to
	# be able to have -Werror but be missing one warning than to have no -Werror.
	## \todo This is probably only necessary for specific gcc versions where -isystem doesn't
	# fully work. Reenable when we encounter versions that work correctly.
	env.Append( CXXFLAGS = [ "-Wno-strict-aliasing" ] )
	env["GAFFER_PLATFORM"] = "linux"
	
if env["BUILD_CACHEDIR"] != "" :
	CacheDir( env["BUILD_CACHEDIR"] )
			
###############################################################################################
# Verify that we're either trying to build and package the dependencies with gaffer, /or/
# trying to build against libraries installed elsewhere, but not both.
###############################################################################################

buildingDependencies = False
locatingDependencies = False
for o in options.options :
	if o.key.startswith( "BUILD_DEPENDENC" ) and str( env.subst( "$" + o.key ) ) != str( env.subst( o.default ) ) :
		buildingDependencies = True
	elif o.key.startswith( "LOCATE_DEPENDENCY" ) and len( env.subst( "$" + o.key ) ) :
		locatingDependencies = True

if buildingDependencies and locatingDependencies :
	raise RuntimeError( "Cannot specify BUILD_DEPENDENCY_* variables and LOCATE_DEPENDENCY* variables." )

###############################################################################################
# Dependencies
# They doesn't fit into the SCons way of things too well so we just build them directly when
# the script runs.
###############################################################################################
			
depEnv = env.Clone()

depEnv["ENV"].update(
	{
		"PATH" : depEnv.subst( "$BUILD_DIR/bin:" + os.environ["PATH"] ),
		"PYTHONPATH" : depEnv.subst( "$BUILD_DIR/python" ),
 		"M4PATH" : depEnv.subst( "$BUILD_DIR/share/aclocal" ),
		"PKG_CONFIG_PATH" : depEnv.subst( "$BUILD_DIR/lib/pkgconfig" ),
		"CMAKE_PREFIX_PATH" : depEnv.subst( "$BUILD_DIR" ),
		"HOME" : os.environ["HOME"],
		"CPPFLAGS" : depEnv.subst( "-I$BUILD_DIR/include" ),
		"LDFLAGS" : depEnv.subst( "-L$BUILD_DIR/lib" ),
	}
)

if depEnv["PLATFORM"]=="darwin" :
	depEnv["ENV"]["DYLD_LIBRARY_PATH"] = depEnv.subst( "/System/Library/Frameworks/ApplicationServices.framework/Versions/A/Frameworks/ImageIO.framework/Resources:$BUILD_DIR/lib" )
	depEnv["ENV"]["DYLD_FALLBACK_FRAMEWORK_PATH"] = depEnv.subst( "$BUILD_DIR/lib" )
else :
	depEnv["ENV"]["LD_LIBRARY_PATH"] = depEnv.subst( "$BUILD_DIR/lib" )

def runCommand( command ) :

	command = depEnv.subst( command )
	sys.stderr.write( command + "\n" )
	subprocess.check_call( command, shell=True, env=depEnv["ENV"] )

if depEnv["BUILD_DEPENDENCY_PKGCONFIG"] :
	runCommand( "cd $PKGCONFIG_SRC_DIR && ./configure --prefix=$BUILD_DIR && make clean && make && make install" )

if depEnv["BUILD_DEPENDENCY_PYTHON"] :
	
	if depEnv["PLATFORM"]=="darwin" :
		runCommand( "cd $PYTHON_SRC_DIR; ./configure --prefix=$BUILD_DIR --enable-framework=$BUILD_DIR/lib --enable-unicode=ucs4 && make clean && make && make install" )
		runCommand( "cd $BUILD_DIR/bin && ln -fsh ../lib/Python.framework/Versions/Current/bin/python python" )
	else :
		runCommand( "cd $PYTHON_SRC_DIR; ./configure --prefix=$BUILD_DIR --enable-shared --enable-unicode=ucs4 && make clean && make -j 4 && make install" )

# get information about the python we just built
pythonVersion = subprocess.Popen( [ "python", "--version" ], env=depEnv["ENV"], stderr=subprocess.PIPE ).stderr.read().strip()
pythonVersion = pythonVersion.split()[1].rpartition( "." )[0]

pythonLinkFlags = ""
try :
	pythonLinkFlags = subprocess.Popen( [ "python-config", "--ldflags" ], env=depEnv["ENV"], stdout=subprocess.PIPE ).stdout.read().strip()
except OSError :
	# this should only occur when building gaffer without an integrated python build, and on linux
	# at least, it's ok to ignore the warning. basically this is just here for ie's funky setup.
	sys.stderr.write( "WARNING : unable to determine python link flags\n" )

pythonLinkFlags = pythonLinkFlags.replace( "Python.framework/Versions/" + pythonVersion + "/Python", "" )
depEnv["PYTHON_LINK_FLAGS"] = pythonLinkFlags
env["PYTHON_LINK_FLAGS"] = pythonLinkFlags
depEnv["PYTHON_VERSION"] = pythonVersion
env["PYTHON_VERSION"] = pythonVersion

if depEnv["BUILD_DEPENDENCY_JPEG"] :
	runCommand( "cd $JPEG_SRC_DIR && ./configure --prefix=$BUILD_DIR && make clean && make && make install" )

if depEnv["BUILD_DEPENDENCY_TIFF"] :
	runCommand( "cd $TIFF_SRC_DIR && ./configure --prefix=$BUILD_DIR && make clean && make && make install" )

if depEnv["BUILD_DEPENDENCY_PNG"] :
	runCommand( "cd $PNG_SRC_DIR && ./configure --prefix=$BUILD_DIR && make clean && make && make install" )
		
if depEnv["BUILD_DEPENDENCY_FREETYPE"] :
	runCommand( "cd $FREETYPE_SRC_DIR && ./configure --prefix=$BUILD_DIR && make clean && make && make install" )
			
if depEnv["BUILD_DEPENDENCY_BOOST"] :
	runCommand( "cd $BOOST_SRC_DIR; ./bootstrap.sh --prefix=$BUILD_DIR --with-python=$BUILD_DIR/bin/python --with-python-root=$BUILD_DIR && ./bjam -d+2 variant=release link=shared threading=multi install" )

if depEnv["BUILD_DEPENDENCY_TBB"] :
	runCommand( "cd $TBB_SRC_DIR; make clean; make" )
	if depEnv["PLATFORM"]=="darwin" :
		runCommand( "cd $TBB_SRC_DIR; cp build/macos_*_release/*.dylib $BUILD_DIR/lib; cp -r include/tbb $BUILD_DIR/include" )
	else :
		runCommand( "cd $TBB_SRC_DIR; cp build/*_release/*.so* $BUILD_DIR/lib; cp -r include/tbb $BUILD_DIR/include" )

if depEnv["BUILD_DEPENDENCY_OPENEXR"] :
	runCommand( "cd $ILMBASE_SRC_DIR && ./configure --prefix=$BUILD_DIR && make clean && make && make install" )
	runCommand( "cd $OPENEXR_SRC_DIR && ./configure --prefix=$BUILD_DIR && make clean && make && make install" )

if depEnv["BUILD_DEPENDENCY_FONTS"] :
	runCommand( "mkdir -p $BUILD_DIR/fonts && cp $FONTS_DIR/*.ttf $BUILD_DIR/fonts" )

if depEnv["BUILD_DEPENDENCY_GLEW"] :
	if depEnv["PLATFORM"]=="posix" :
		runCommand( "mkdir -p $BUILD_DIR/lib64/pkgconfig" )
	runCommand( "cd $GLEW_SRC_DIR && make clean && make install GLEW_DEST=$BUILD_DIR LIBDIR=$BUILD_DIR/lib" )

if depEnv["BUILD_DEPENDENCY_OCIO"] :
	runCommand( "cd $OCIO_SRC_DIR && cmake -DCMAKE_INSTALL_PREFIX=$BUILD_DIR -DOCIO_BUILD_TRUELIGHT=OFF -DOCIO_BUILD_APPS=OFF -DOCIO_BUILD_NUKE=OFF && make clean && make -j 4 && make install" )
	runCommand( "mkdir -p $BUILD_DIR/python" )
	runCommand( "mv $BUILD_DIR/lib/python$PYTHON_VERSION/site-packages/PyOpenColorIO* $BUILD_DIR/python" )
	runCommand( "mkdir -p $BUILD_DIR/openColorIO" )
	runCommand( "cp $OCIO_CONFIG_DIR/config.ocio $BUILD_DIR/openColorIO" )
	runCommand( "cp -r $OCIO_CONFIG_DIR/luts $BUILD_DIR/openColorIO" )

if depEnv["BUILD_DEPENDENCY_OIIO"] :
	runCommand( "cd $OIIO_SRC_DIR && make clean && make THIRD_PARTY_TOOLS_HOME=$BUILD_DIR OCIO_PATH=$BUILD_DIR USE_OPENJPEG=0" )
	if depEnv["PLATFORM"]=="darwin" :
		runCommand( "cd $OIIO_SRC_DIR && cp -r dist/macosx/* $BUILD_DIR" )
		## \todo Come up with something better.
		# move the library to a new name so it doesn't conflict with the libOpenImageIO that arnold uses.
		# Ideally they'd both use the same one but currently Arnold is using a pre-version-1 version.
		runCommand( "mv $BUILD_DIR/lib/libOpenImageIO.dylib $BUILD_DIR/lib/libOpenImageIO-1.dylib" )
	else :
		runCommand( "cd $OIIO_SRC_DIR && cp -r dist/linux64/* $BUILD_DIR" )
		runCommand( "mv $BUILD_DIR/lib/libOpenImageIO.so $BUILD_DIR/lib/libOpenImageIO-1.so" )
	  
if depEnv["BUILD_DEPENDENCY_HDF5"] :
	runCommand( "cd $HDF5_SRC_DIR && ./configure --prefix=$BUILD_DIR --enable-threadsafe --with-pthread=/usr/include && make clean && make -j 4 && make install" )

if depEnv["BUILD_DEPENDENCY_ALEMBIC"] :
	# may need to hand edit build/AlembicBoost.cmake in the alembic distribution to remove Boost_USE_STATIC_LIBS.
	runCommand( "cd $ALEMBIC_SRC_DIR && rm -f CMakeCache.txt && cmake -DCMAKE_INSTALL_PREFIX=$BUILD_DIR -DBoost_NO_SYSTEM_PATHS=TRUE -DBoost_NO_BOOST_CMAKE=TRUE -DBOOST_ROOT=$BUILD_DIR -DILMBASE_ROOT=$BUILD_DIR -DUSE_PYILMBASE=FALSE -DUSE_PYALEMBIC=FALSE && make clean && make -j 4 && make install" )
	runCommand( "mv $BUILD_DIR/alembic-*/include/* $BUILD_DIR/include" )
	runCommand( "mv $BUILD_DIR/alembic-*/lib/static/* $BUILD_DIR/lib" )
	
if depEnv["BUILD_DEPENDENCY_CORTEX"] :
	runCommand( "cd $CORTEX_SRC_DIR && rm -rf .sconsign.dblite .sconf_temp" )
	runCommand(
		"cd $CORTEX_SRC_DIR;"
		"scons install installDoc -j 3 BUILD_CACHEDIR=$BUILD_CACHEDIR "
		"INSTALL_PREFIX=$BUILD_DIR "
		"INSTALL_DOC_DIR=$BUILD_DIR/doc/cortex "
		"INSTALL_RMANPROCEDURAL_NAME=$BUILD_DIR/renderMan/procedurals/iePython "
		"INSTALL_RMANDISPLAY_NAME=$BUILD_DIR/renderMan/displayDrivers/ieDisplay "
		"INSTALL_PYTHON_DIR=$BUILD_DIR/python "
		"INSTALL_ARNOLDPROCEDURAL_NAME=$BUILD_DIR/arnold/procedurals/ieProcedural.so "
		"INSTALL_ARNOLDOUTPUTDRIVER_NAME=$BUILD_DIR/arnold/outputDrivers/ieOutputDriver.so "
		"INSTALL_IECORE_OPS='' "
		"PYTHON_CONFIG=$BUILD_DIR/bin/python-config "
		"BOOST_INCLUDE_PATH=$BUILD_DIR/include/boost "
		"LIBPATH=$BUILD_DIR/lib "
		"BOOST_LIB_SUFFIX='' "
		"OPENEXR_INCLUDE_PATH=$BUILD_DIR/include "
		"FREETYPE_INCLUDE_PATH=$BUILD_DIR/include/freetype2 "
		"RMAN_ROOT=$DELIGHT "
		"WITH_GL=1 "
		"GLEW_INCLUDE_PATH=$BUILD_DIR/include/GL "
		"RMAN_ROOT=$RMAN_ROOT "
		"NUKE_ROOT=$NUKE_ROOT "
		"ARNOLD_ROOT=$ARNOLD_ROOT "
		"OPTIONS='' "
		"DOXYGEN=$DOXYGEN "
		"ENV_VARS_TO_IMPORT='LD_LIBRARY_PATH' "
		"SAVE_OPTIONS=gaffer.options "
		"$CORTEX_BUILD_ARGS"
	)
	runCommand( "mkdir -p $BUILD_DIR/resources/cortex" )
	runCommand( "cp $CORTEX_POINTDISTRIBUTION_TILESET $BUILD_DIR/resources/cortex" )

if depEnv["BUILD_DEPENDENCY_GL"] :
	runCommand( "cd $PYOPENGL_SRC_DIR && python setup.py install --prefix $BUILD_DIR --install-lib $BUILD_DIR/python" )

if depEnv["BUILD_DEPENDENCY_QT"] :
	runCommand(
		"cd $QT_SRC_DIR && ./configure "
		"-prefix $BUILD_DIR "
		"-opensource -confirm-license "
		"-no-rpath -no-declarative -no-gtkstyle -no-qt3support " # these are definitely ok
		"-no-multimedia -no-audio-backend -no-webkit -no-script -no-dbus -no-declarative -no-svg " # these might not be
		"-nomake examples -nomake demos -nomake tools " # i hope these are
		"-I $BUILD_DIR/include -L $BUILD_DIR/lib "
		"&& make -j 4 && make install"
	)
	
if depEnv["BUILD_DEPENDENCY_PYQT"] :
	runCommand( "cd $SIP_SRC_DIR && python configure.py -d $BUILD_DIR/python && make clean && make && make install" )
	runCommand( "cd $PYQT_SRC_DIR && python configure.py -d $BUILD_DIR/python  --confirm-license && make && make install" )

# having MACOS_DEPLOYMENT_TARGET set breaks the pyside build for some reason
if "MACOSX_DEPLOYMENT_TARGET" in depEnv["ENV"] :
	del depEnv["ENV"]["MACOSX_DEPLOYMENT_TARGET"]
if depEnv["BUILD_DEPENDENCY_PYSIDE"] :
	if depEnv["PLATFORM"]=="darwin" :
		runCommand(
			"cd $SHIBOKEN_SRC_DIR && "
			"rm -rf build && mkdir build && cd build && "
			"cmake .. -DCMAKE_BUILD_TYPE=Release -DPYTHON_SITE_PACKAGES=$BUILD_DIR/python -DCMAKE_INSTALL_PREFIX=$BUILD_DIR -DPYTHON_INCLUDE_DIR=$BUILD_DIR/lib/Python.framework/Headers -DPYTHON_EXECUTABLE=$BUILD_DIR/bin/python -DPYTHON_LIBRARY=$BUILD_DIR/Python.framework/Versions/$PYTHON_VERSION/libpython${PYTHON_VERSION}.dylib && "
			"make clean && make -j 4 && make install"
		)
		runCommand(
			"cd $PYSIDE_SRC_DIR && "
			"rm -rf build && mkdir build && cd build && "
			"cmake .. -DCMAKE_BUILD_TYPE=Release -DSITE_PACKAGE=$BUILD_DIR/python -DCMAKE_INSTALL_PREFIX=$BUILD_DIR -DALTERNATIVE_QT_INCLUDE_DIR=$BUILD_DIR/include && "
			"make clean && make -j 4 && make install"
		)
	else :
		runCommand(
			"cd $SHIBOKEN_SRC_DIR && "
			"rm -rf build && mkdir build && cd build && "
			"cmake .. -DCMAKE_BUILD_TYPE=Release -DPYTHON_SITE_PACKAGES=$BUILD_DIR/python -DCMAKE_INSTALL_PREFIX=$BUILD_DIR -DPYTHON_INCLUDE_DIR=$BUILD_DIR/include/python$PYTHON_VERSION && "
			"make clean && make -j 4 && make install"
		)
		runCommand(
			"cd $PYSIDE_SRC_DIR && cmake "
			"-DSITE_PACKAGE=$BUILD_DIR/python -DCMAKE_INSTALL_PREFIX=$BUILD_DIR "
			"&& make clean && make -j 4 && make install"
		)
		
###############################################################################################
# The basic environment for building libraries
###############################################################################################

if buildingDependencies :
	boostLibSuffix = ""
else :
	boostLibSuffix = env["BOOST_LIB_SUFFIX"]

baseLibEnv = env.Clone()

baseLibEnv.Append(

	CPPPATH = [
		"include",
	] + env["LOCATE_DEPENDENCY_CPPPATH"],
	
	CPPFLAGS = [
		"-DBOOST_FILESYSTEM_VERSION=3",
	],
	
	LIBPATH = [
		"./lib",
		"$BUILD_DIR/lib",
		"$LOCATE_DEPENDENCY_LIBPATH",
	],
	
	LIBS = [
		"boost_signals" + boostLibSuffix,
		"boost_iostreams" + boostLibSuffix,
		"boost_filesystem" + boostLibSuffix,
		"boost_date_time" + boostLibSuffix,
		"boost_thread" + boostLibSuffix,
		"boost_wave" + boostLibSuffix,
		"boost_regex" + boostLibSuffix,		
		"boost_system" + boostLibSuffix,
		"tbb",
		"Imath$OPENEXR_LIB_SUFFIX",
		"IlmImf$OPENEXR_LIB_SUFFIX",
		"IECore$CORTEX_LIB_SUFFIX",
	],
	
)

# include 3rd party headers with -isystem rather than -I.
# this should turns off warnings from those headers, allowing us to
# build with -Werror. there are so many warnings from boost
# in particular that this would be otherwise impossible - note that
# we're still having to turn off strict aliasing warnings in the
# default CXXFLAGS because somehow they creep out of boost python
# and past the defences.
for path in [
		"$BUILD_DIR/include",
		"$BUILD_DIR/include/python$PYTHON_VERSION",
		"$BUILD_DIR/include/OpenEXR",
		"$BUILD_DIR/include/GL",
	] + env["LOCATE_DEPENDENCY_SYSTEMPATH"] :
	
	baseLibEnv.Append(
		CXXFLAGS = [ "-isystem", path ]
	)
		
###############################################################################################
# The basic environment for building python modules
###############################################################################################

basePythonEnv = baseLibEnv.Clone()

basePythonEnv.Append(

	CPPFLAGS = [
		"-DBOOST_PYTHON_MAX_ARITY=20",
	],
		
	LIBS = [
		"boost_python" + boostLibSuffix,
		"IECorePython$CORTEX_PYTHON_LIB_SUFFIX",
		"Gaffer",
	],
	
)
	
basePythonEnv.Append(

	CPPFLAGS = os.popen( basePythonEnv.subst( "$BUILD_DIR/bin/python$PYTHON_VERSION-config --includes" ) ).read().split(),

	SHLINKFLAGS = "$PYTHON_LINK_FLAGS",

)

if basePythonEnv["PLATFORM"]=="darwin" :
	basePythonEnv.Append( SHLINKFLAGS = "-single_module" )

###############################################################################################
# Definitions for the libraries we wish to build
###############################################################################################

libraries = {

	"Gaffer" : {
	},
	
	"GafferTest" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "GafferTest", "GafferBindings" ],
		},
		"additionalFiles" : glob.glob( "python/GafferTest/*/*" ) + glob.glob( "python/GafferTest/*/*/*" ),
	},
	
	"GafferUI" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer", "Iex$OPENEXR_LIB_SUFFIX", "IECoreGL$CORTEX_LIB_SUFFIX", "GLEW$GLEW_LIB_SUFFIX" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "IECoreGL$CORTEX_LIB_SUFFIX", "GafferUI", "GafferBindings" ],
		},
	},
	
	"GafferUITest" : {},
	
	"GafferScene" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer", "Iex$OPENEXR_LIB_SUFFIX", "IECoreGL$CORTEX_LIB_SUFFIX", "IECoreAlembic$CORTEX_LIB_SUFFIX", "GafferImage" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "GafferBindings", "GafferScene" ],
		},
		"classStubs" : [
			( "ScriptProcedural", "procedurals/gaffer/script" ),
		],
		"additionalFiles" : glob.glob( "glsl/*.frag" ) + glob.glob( "glsl/*.vert" ),
	},
	
	"GafferSceneTest" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer", "GafferScene" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "Gaffer", "GafferBindings", "GafferScene", "GafferSceneTest" ],
		},
		"additionalFiles" : glob.glob( "python/GafferSceneTest/*/*" ),
	},
	
	"GafferSceneUI" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer", "GafferUI", "GafferScene" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "GafferUI", "GafferSceneUI" ],
		},
	},
	
	"GafferImage" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer", "Iex$OPENEXR_LIB_SUFFIX", "OpenImageIO$OIIO_LIB_SUFFIX", "OpenColorIO$OCIO_LIB_SUFFIX" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "GafferBindings", "GafferImage" ],
		},
		"requiredOptions" : [ "OIIO_SRC_DIR", "OCIO_SRC_DIR" ],
	},
	
	"GafferImageTest" : {},
	
	"GafferImageUITest" : {},
	
	"GafferImageUI" : {
		"envAppends" : {
			"LIBS" : [ "IECoreGL$CORTEX_LIB_SUFFIX", "Gaffer", "GafferImage", "GafferUI", "GLEW$GLEW_LIB_SUFFIX" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "GafferUI", "GafferImageUI" ],
		},
	},
	
	"GafferArnold" : {
		"envAppends" : {
			"CPPPATH" : [ "$ARNOLD_ROOT/include" ],
			"LIBPATH" : [ "$ARNOLD_ROOT/bin" ],
			"LIBS" : [ "Gaffer", "GafferScene", "ai", "IECoreArnold$CORTEX_LIB_SUFFIX" ],
		},
		"pythonEnvAppends" : {
			"CPPPATH" : [ "$ARNOLD_ROOT/include" ],
			"LIBPATH" : [ "$ARNOLD_ROOT/bin" ],
			"LIBS" : [ "Gaffer", "GafferScene", "GafferBindings", "GafferArnold" ],
		},
		"requiredOptions" : [ "ARNOLD_ROOT" ],
	},

	"GafferArnoldTest" : {},

	"GafferArnoldUI" : {},

	"GafferRenderMan" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer", "GafferScene", "IECoreRI$CORTEX_LIB_SUFFIX" ],
			"LIBPATH" : [ "$RMAN_ROOT/lib" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "GafferBindings", "GafferScene", "GafferRenderMan" ],
			"LIBPATH" : [ "$RMAN_ROOT/lib" ],
		},
		"requiredOptions" : [ "RMAN_ROOT" ],
	},

	"GafferRenderManUI" : {},

	"GafferRenderManTest" : {
		"additionalFiles" : glob.glob( "python/GafferRenderManTest/*/*" ),
	},
		
	"apps" : {
		"additionalFiles" : glob.glob( "apps/*/*-1.py" ),
	},
	
	"scripts" : {
		"additionalFiles" : [ "bin/gaffer", "bin/gaffer.py" ],
	},
	
	"startupScripts" : {
		"additionalFiles" : glob.glob( "startup/*/*.py" ),
	},
		
	"misc" : {
		"additionalFiles" : [ "LICENSE" ],
	},
	
	"IECore" : {
				
		"classStubs" : [

			# images
			( "ImageThinner", "ops/image/thinner" ),
			( "Grade", "ops/image/composite" ),
			( "ImagePremultiplyOp", "ops/image/premultiply" ),
			( "ImageUnpremultiplyOp", "ops/image/unpremultiply" ),
			( "Grade", "ops/image/grade" ),
			( "CurveTracer", "ops/image/traceCurves" ),

			# curves
			( "CurveExtrudeOp", "ops/curves/extrude" ),
			( "CurveLineariser", "ops/curves/linearise" ),
			( "CurvesMergeOp", "ops/curves/merge" ),
			( "CurveTangentsOp", "ops/curves/tangents" ),
			
			# meshes
			( "TriangulateOp", "ops/mesh/triangulate" ),
			( "FaceAreaOp", "ops/mesh/faceArea" ),
			( "MeshMergeOp", "ops/mesh/merge" ),
			( "MeshNormalsOp", "ops/mesh/normals" ),
			
			# primitives
			( "TransformOp", "ops/primitive/transform" ),
			( "RenamePrimitiveVariables", "ops/primitive/renameVariables" ),
			
			# files
			( "SequenceLsOp", "ops/files/sequenceLs" ),
			( "SequenceCpOp", "ops/files/sequenceCopy" ),
			( "SequenceMvOp", "ops/files/sequenceMove" ),
			( "SequenceRmOp", "ops/files/sequenceRemove" ),
			( "SequenceRenumberOp", "ops/files/sequenceRenumber" ),
			( "SequenceConvertOp", "ops/files/sequenceConvert" ),
			
			# procedurals
			( "ReadProcedural", "procedurals/read" ), 

		],
		
	},
	
	"IECoreAlembic" : {
			
		"classStubs" : [

			( "ABCToMDC", "ops/files/abcToMDC" ),
			
		],
		
	},

}

# Add on OpenGL libraries to definitions - these vary from platform to platform
for library in ( "GafferUI", "GafferImageUI" ) :
	if env["PLATFORM"] == "darwin" :
		libraries[library]["envAppends"].setdefault( "FRAMEWORKS", [] ).append( "OpenGL" )
	else :
		libraries[library]["envAppends"]["LIBS"].append( "GL" )

###############################################################################################
# The stuff that actually builds the libraries and python modules
###############################################################################################

for libraryName, libraryDef in libraries.items() :

	# skip this library if we don't have the config we need
	
	haveRequiredOptions = True
	for requiredOption in libraryDef.get( "requiredOptions", [] ) :
		if not env[requiredOption] :
			haveRequiredOptions = False
			break
	if not haveRequiredOptions :
		continue

	# environment

	libEnv = baseLibEnv.Clone()
	libEnv.Append( **(libraryDef.get( "envAppends", {} )) )

	# library

	librarySource = sorted( glob.glob( "src/" + libraryName + "/*.cpp" ) + glob.glob( "src/" + libraryName + "/*/*.cpp" ) )
	if librarySource :
	
		library = libEnv.SharedLibrary( "lib/" + libraryName, librarySource )
		libEnv.Default( library )
	
		libraryInstall = libEnv.Install( "$BUILD_DIR/lib", library )
		libEnv.Alias( "build", libraryInstall )
	
	# header install
	
	headers = (
		glob.glob( "include/" + libraryName + "/*.h" ) +
		glob.glob( "include/" + libraryName + "/*.inl" ) +
		glob.glob( "include/" + libraryName + "/*/*.h" ) +
		glob.glob( "include/" + libraryName + "/*/*.inl" )
	)

	for header in headers :
		headerInstall = libEnv.Install(
			"$BUILD_DIR/" + os.path.dirname( header ),
			header
		)
		libEnv.Alias( "build", headerInstall )
		
	# bindings library and binary python modules

	pythonEnv = basePythonEnv.Clone()
	pythonEnv.Append( **(libraryDef.get( "pythonEnvAppends", {} ))  )
	
	bindingsSource = sorted( glob.glob( "src/" + libraryName + "Bindings/*.cpp" ) )
	if bindingsSource :
			
		bindingsLibrary = pythonEnv.SharedLibrary( "lib/" + libraryName + "Bindings", bindingsSource )
		pythonEnv.Default( bindingsLibrary )
		
		bindingsLibraryInstall = pythonEnv.Install( "$BUILD_DIR/lib", bindingsLibrary )
		env.Alias( "build", bindingsLibraryInstall )
				
		# header install
		bindingsHeaderInstall = pythonEnv.Install(
			"$BUILD_DIR/" + "include/" + libraryName + "Bindings",
			glob.glob( "include/" + libraryName + "Bindings/*.h" ) +
			glob.glob( "include/" + libraryName + "Bindings/*.inl" )
		)
		pythonEnv.Alias( "build", bindingsHeaderInstall )

	
	pythonModuleSource = sorted( glob.glob( "src/" + libraryName + "Module/*.cpp" ) )
	if pythonModuleSource :
		
		pythonModuleEnv = pythonEnv.Clone()
		if bindingsSource :
			pythonModuleEnv.Append( LIBS = [ libraryName + "Bindings" ] )
		pythonModuleEnv["SHLIBPREFIX"] = ""
		pythonModuleEnv["SHLIBSUFFIX"] = ".so"
	
		pythonModule = pythonModuleEnv.SharedLibrary( "python/" + libraryName + "/_" + libraryName, pythonModuleSource )
		pythonModuleEnv.Default( pythonModule )
	
		moduleInstall = pythonModuleEnv.Install( "$BUILD_DIR/python/" + libraryName, pythonModule )
		pythonModuleEnv.Default( moduleInstall )
		pythonModuleEnv.Alias( "build", moduleInstall )
	
	# python component of python module

	sedSubstitutions = "s/!GAFFER_MAJOR_VERSION!/$GAFFER_MAJOR_VERSION/g"
	sedSubstitutions += "; s/!GAFFER_MINOR_VERSION!/$GAFFER_MINOR_VERSION/g"
	sedSubstitutions += "; s/!GAFFER_PATCH_VERSION!/$GAFFER_PATCH_VERSION/g"
	
	for pythonFile in glob.glob( "python/" + libraryName + "/*.py" ) :
		pythonFileInstall = env.Command( "$BUILD_DIR/" + pythonFile, pythonFile, "sed \"" + sedSubstitutions + "\" $SOURCE > $TARGET" )
		env.Alias( "build", pythonFileInstall )

	# additional files

	for additionalFile in libraryDef.get( "additionalFiles", [] ) :
		additionalFileInstall = env.InstallAs( "$BUILD_DIR/" + additionalFile, additionalFile )
		env.Alias( "build", additionalFileInstall )
		
	# class stubs
	
	def buildClassStub( target, source, env ) :

		dir = os.path.dirname( str( target[0] ) )
		if not os.path.isdir( dir ) :
			os.makedirs( dir )
		
		classLoadableName = dir.rpartition( "/" )[2]
				
		f = open( str( target[0] ), "w" )
		f.write( "import IECore\n\n" )
		f.write( env.subst( "from $GAFFER_STUB_MODULE import $GAFFER_STUB_CLASS as %s" % classLoadableName ) )
		
	for classStub in libraryDef.get( "classStubs", [] ) :
		stubFileName = "$BUILD_DIR/" + classStub[1] + "/" + classStub[1].rpartition( "/" )[2] + "-1.py"
		stubEnv = env.Clone(
			GAFFER_STUB_MODULE = libraryName,
			GAFFER_STUB_CLASS = classStub[0],
		)
		stub = stubEnv.Command( stubFileName, "", buildClassStub )
		stubEnv.Alias( "build", stub )
	
#########################################################################################################
# Graphics
#########################################################################################################

def buildGraphics( target, source, env ) :

	dir = os.path.dirname( str( target[0] ) )
	if not os.path.isdir( dir ) :
		os.makedirs( dir )
	
	objects, stderr = subprocess.Popen( env["INKSCAPE"] + " --query-all " + str( source[0] ), stdout=subprocess.PIPE, shell=True ).communicate()
	for object in objects.split( "\n" ) :
		tokens = object.split( "," )
		if tokens[0].startswith( "forExport:" ) :
			os.system( env["INKSCAPE"] + " --export-png=%s/%s.png --export-id=%s --export-width=%d --export-height=%d %s --export-background-opacity=0" % (
					dir,
					tokens[0].split( ":" )[-1],
					tokens[0],
					int( round( float( tokens[3] ) ) ), int( round( float( tokens[4] ) ) ),
					str( source[0] ),
				)
			)

graphicsBuild = env.Command( "$BUILD_DIR/graphics/arrowDown10.png", "resources/graphics.svg", buildGraphics )
env.NoCache( graphicsBuild )
env.Alias( "build", graphicsBuild )

#########################################################################################################
# Licenses
#########################################################################################################

if buildingDependencies :

	licenses = [
		( "python", "$PYTHON_SRC_DIR/LICENSE" ),
		( "boost", "$BOOST_SRC_DIR/LICENSE_1_0.txt" ),
		( "cortex", "$CORTEX_SRC_DIR/LICENSE" ),
		( "freetype", "$FREETYPE_SRC_DIR/docs/FTL.TXT" ),
		( "glew", "$GLEW_SRC_DIR/LICENSE.txt" ),
		( "ilmbase", "$ILMBASE_SRC_DIR/COPYING" ),
		( "libjpeg", "$JPEG_SRC_DIR/README" ),
		( "openexr", "$OPENEXR_SRC_DIR/LICENSE" ),
		( "libtiff", "$TIFF_SRC_DIR/COPYRIGHT" ),
		( "libpng", "$PNG_SRC_DIR/LICENSE" ),
		( "tbb", "$TBB_SRC_DIR/COPYING" ),
		( "openColorIO", "$OCIO_SRC_DIR/LICENSE" ),
		( "openImageIO", "$OIIO_SRC_DIR/LICENSE" ),
		( "hdf5", "$HDF5_SRC_DIR/COPYING" ),
		( "alembic", "$ALEMBIC_SRC_DIR/LICENSE.txt" ),
		( "qt", "$QT_SRC_DIR/LICENSE.LGPL" ),
	]
	
	if env["BUILD_DEPENDENCY_PYQT"] :
		licenses.append( ( "pyQt", "$PYQT_SRC_DIR/GPL_EXCEPTION.TXT" ) )
	
	if env["BUILD_DEPENDENCY_PYSIDE"] :
		licenses.append( ( "pySide", "$PYSIDE_SRC_DIR/COPYING" ) )
	
	for l in licenses :

		license = env.InstallAs( "$BUILD_DIR/doc/licenses/" + l[0], l[1] )
		env.Alias( "build", license )
	
#########################################################################################################
# Documentation
#########################################################################################################

def readLinesMinusLicense( f ) :

	if isinstance( f, basestring ) :
		f = open( f, "r" )

	result = []
	skippedLicense = False
	for line in f.readlines() :
	
		if not line.startswith( "#" ) :
			skippedLicense = True
		if skippedLicense :
			result.append( line )
			
	return result

# Builder action that munges a nicely organised python module into a much less nicely organised one
# that doxygen will understand. Otherwise it puts every class implemented in its own file
# into its own namespace and the docs get mighty confusing.
def createDoxygenPython( target, source, env ) :

	target = str( target[0] )
	source = str( source[0] )
	
	if not os.path.isdir( target ) :
		os.makedirs( target )
	
	outFile = open( target + "/__init__.py", "w" )
	
	for line in readLinesMinusLicense( source ) :
	
		outFile.write( line )
	
		if line.startswith( "import" ) :
		
			# copy source file over to target directory
			words = line.split()
			fileName = os.path.dirname( source ) + "/" + words[1] + ".py"
			if os.path.isfile( fileName ) :
				destFile = open( target + "/" + words[1] + ".py", "w" )
				for l in readLinesMinusLicense( fileName ) :
					destFile.write( l )
		
		elif line.startswith( "from" ) :
		
			# cat source file directly into init file
			words = line.split()
			fileName = os.path.dirname( source ) + "/" + words[1] + ".py"
			if os.path.isfile( fileName ) :
				
				outFile.write( "\n" )
				
				for line in readLinesMinusLicense( fileName ) :
					outFile.write( line )
				
				outFile.write( "\n" )
	
docEnv = env.Clone()
docEnv["ENV"]["PATH"] = os.environ["PATH"]
for v in ( "BUILD_DIR", "GAFFER_MAJOR_VERSION", "GAFFER_MINOR_VERSION", "GAFFER_PATCH_VERSION" ) :
	docEnv["ENV"][v] = docEnv[v]

docs = docEnv.Command( "doc/html/index.html", "doc/config/Doxyfile", "$DOXYGEN doc/config/Doxyfile" )
env.NoCache( docs )

for modulePath in ( "python/Gaffer", "python/GafferUI", "python/GafferScene", "python/GafferSceneUI" ) :

	module = os.path.basename( modulePath )
	mungedModule = docEnv.Command( "doc/python/" + module, modulePath + "/__init__.py", createDoxygenPython )
	docEnv.Depends( mungedModule, glob.glob( modulePath + "/*.py" ) )
	docEnv.Depends( docs, mungedModule )
	docEnv.NoCache( mungedModule )

docEnv.Depends( docs, glob.glob( "include/*/*.h" ) + glob.glob( "doc/src/*.dox" ) )

docInstall = docEnv.Install( "$BUILD_DIR/doc/gaffer", "doc/html" )
docEnv.Alias( "build", docInstall )

#########################################################################################################
# Installation
#########################################################################################################

manifest = [

	"bin/gaffer",
	"bin/gaffer.py",
	"bin/python",
	"bin/python*[0-9]", # get the versioned python binaries, but not python-config etc
	
	"LICENSE",

	"apps/*/*-1.py",

	"lib/libboost_signals" + boostLibSuffix + "$SHLIBSUFFIX*",
	"lib/libboost_thread" + boostLibSuffix + "$SHLIBSUFFIX*",
	"lib/libboost_wave" + boostLibSuffix + "$SHLIBSUFFIX*",
	"lib/libboost_regex" + boostLibSuffix + "$SHLIBSUFFIX*",
	"lib/libboost_python" + boostLibSuffix + "$SHLIBSUFFIX*",
	"lib/libboost_date_time" + boostLibSuffix + "$SHLIBSUFFIX*",
	"lib/libboost_filesystem" + boostLibSuffix + "$SHLIBSUFFIX*",
	"lib/libboost_iostreams" + boostLibSuffix + "$SHLIBSUFFIX*",
	"lib/libboost_system" + boostLibSuffix + "$SHLIBSUFFIX*",

	"lib/libIECore*$SHLIBSUFFIX",
	"lib/libGaffer*$SHLIBSUFFIX",
	
	"lib/libIex*$SHLIBSUFFIX*",
	"lib/libHalf*$SHLIBSUFFIX*",
	"lib/libImath*$SHLIBSUFFIX*",
	"lib/libIlmImf*$SHLIBSUFFIX*",
	"lib/libIlmThread*$SHLIBSUFFIX*",
	
	"lib/libtiff*$SHLIBSUFFIX*",
	"lib/libfreetype*$SHLIBSUFFIX*",
	"lib/libjpeg*$SHLIBSUFFIX*",
	"lib/libpng*$SHLIBSUFFIX*",
	
	"lib/libOpenImageIO*$SHLIBSUFFIX*",
	"lib/libOpenColorIO*$SHLIBSUFFIX*",
	
	"lib/libpython*$SHLIBSUFFIX*",
	"lib/Python.framework",
	"lib/python$PYTHON_VERSION",
	
	"lib/libGLEW*$SHLIBSUFFIX*",
	"lib/libtbb*$SHLIBSUFFIX*",
	
	"lib/libhdf5*$SHLIBSUFFIX*",
	
	"lib/libpyside*$SHLIBSUFFIX*",
	"lib/libshiboken*$SHLIBSUFFIX*",
	
	"lib/libQtCore*",
	"lib/libQtGui*",
	"lib/libQtOpenGL*",
	"lib/QtCore.framework",
	"lib/QtGui.framework",
	"lib/QtOpenGL.framework",
	
	"startup/*/*.py",

	"fonts",
	"ops",
	"procedurals",
	"resources",

	"openColorIO",

	"graphics/*.png",
	"glsl/IECoreGL",
	"glsl/*.frag",
	"glsl/*.vert",
	"doc/licenses",
	"doc/gaffer/html",
	"doc/cortex/html",

	"python/IECore*",
	"python/Gaffer*",
	"python/PySide/*.py",
	"python/PySide/QtCore.so",
	"python/PySide/QtGui.so",
	"python/PySide/QtOpenGL.so",
	"python/sip.so",
	"python/PyQt*",
	"python/OpenGL",
	"python/PyOpenColorIO*",

	"include/IECore*",
	"include/Gaffer*",
	"include/boost",
	"include/GL",
	"include/OpenEXR",
	"include/python*",
	"include/tbb",
	
	"renderMan",
	
]

def installer( target, source, env ) :

	def copyTree( src, dst, regex ) :
	
		names = os.listdir( src )
		
		for name in names:
				
			srcName = os.path.join( src, name )
			dstName = os.path.join( dst, name )
						
			if os.path.isdir( srcName ) :
				if regex.match( srcName ) :
					copyTree( srcName, dstName, re.compile( ".*" ) )
				else :
					copyTree( srcName, dstName, regex )
			else :
				if regex.match( srcName ) :
					dstDir = os.path.dirname( dstName )
					if not os.path.isdir( dstDir ) :
						os.makedirs( dstDir )
					if os.path.islink( srcName ) :
						os.symlink( os.readlink( srcName ), dstName )
					else:
						shutil.copy2( srcName, dstName )
	
	regex = re.compile( "|".join( [ fnmatch.translate( env.subst( "$BUILD_DIR/" + m ) ) for m in manifest ] ) )	
	copyTree( str( source[0] ), str( target[0] ), regex )

if env.subst( "$PACKAGE_FILE" ).endswith( ".dmg" ) :
	
	# if the packaging will make a disk image, then build an os x app bundle

	install = env.Command( "$INSTALL_DIR/Gaffer.app/Contents/Resources", "$BUILD_DIR", installer )
	env.AlwaysBuild( install )
	env.NoCache( install )
	env.Alias( "install", install )

	plistInstall = env.Install( "$INSTALL_DIR/Gaffer.app/Contents", "resources/Info.plist" )
	env.Alias( "install", plistInstall )
	
	gafferLink = env.Command( "$INSTALL_DIR/Gaffer.app/Contents/MacOS/gaffer", "", "ln -s ../Resources/bin/gaffer $TARGET" )
	env.Alias( "install", gafferLink )
	
else :

	install = env.Command( "$INSTALL_DIR", "$BUILD_DIR", installer )
	env.AlwaysBuild( install )
	env.NoCache( install )

	env.Alias( "install", install )

#########################################################################################################
# Packaging
#########################################################################################################

def packager( target, source, env ) :

	target = str( target[0] )
	source = str( source[0] )
	b = os.path.basename( source )
	d = os.path.dirname( source )
	
	if target.endswith( ".dmg" ) :
		runCommand( "hdiutil create -volname '%s' -srcfolder '%s' -ov -format UDZO '%s'" % ( os.path.basename( target ), source, target ) )				
	else :
		runCommand( "tar -czf %s -C %s %s" % ( target, d, b ) )
	
package = env.Command( "$PACKAGE_FILE", "$INSTALL_DIR", packager )
env.NoCache( package )
env.Alias( "package", package )

##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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
	[ "-pipe", "-Wall", "-O2", "-DNDEBUG", "-DBOOST_DISABLE_ASSERTS" ]
)

options.Add(
	"BUILD_DIR",
	"The destination directory in which the build will be made.",
	"./build/gaffer-${GAFFER_MAJOR_VERSION}.${GAFFER_MINOR_VERSION}.${GAFFER_PATCH_VERSION}-${PLATFORM}",
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
	"./install/gaffer-${GAFFER_MAJOR_VERSION}.${GAFFER_MINOR_VERSION}.${GAFFER_PATCH_VERSION}-${PLATFORM}",
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
	"$DEPENDENCIES_SRC_DIR/Python-2.6.3",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_BOOST", "Set this to build boost.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"BOOST_SRC_DIR",
	"The location of the boost source to be used if BUILD_DEPENDENCY_BOOST is specified.",
	"$DEPENDENCIES_SRC_DIR/boost_1_42_0",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_TBB", "Set this to build tbb.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"TBB_SRC_DIR",
	"The location of the tbb source to be used if BUILD_DEPENDENCY_TBB is specified.",
	"$DEPENDENCIES_SRC_DIR/tbb22_004oss",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_OPENEXR", "Set this to build openexr.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"ILMBASE_SRC_DIR",
	"The location of the ilmbase source to be used if BUILD_DEPENDENCY_OPENEXR is specified.",
	"$DEPENDENCIES_SRC_DIR/ilmbase-1.0.1",
)

options.Add(
	"OPENEXR_SRC_DIR",
	"The location of the exr source to be used if BUILD_DEPENDENCY_OPENEXR is specified.",
	"$DEPENDENCIES_SRC_DIR/openexr-1.6.1",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_JPEG", "Set this to build the jpeg library.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"JPEG_SRC_DIR",
	"The location of the jpeg source to be used if BUILD_DEPENDENCY_JPEG is specified.",
	"$DEPENDENCIES_SRC_DIR/jpeg-6b",
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
	"$DEPENDENCIES_SRC_DIR/libpng-1.5.2",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_FREETYPE", "Set this to build freetype.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"FREETYPE_SRC_DIR",
	"The location of the freetype source to be used if BUILD_DEPENDENCY_FREETYPE is specified.",
	"$DEPENDENCIES_SRC_DIR/freetype-2.3.9",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_GLEW", "Set this to build GLEW.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"GLEW_SRC_DIR",
	"The location of the glew source to be used if BUILD_DEPENDENCY_GLEW is specified.",
	"$DEPENDENCIES_SRC_DIR/glew-1.5.4",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_CORTEX", "Set this to build cortex.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"CORTEX_SRC_DIR",
	"The location of the boost source to be used if BUILD_DEPENDENCY_CORTEX is specified.",
	"$DEPENDENCIES_SRC_DIR/cortex-vfx/trunk",
)

options.Add(
	"RMAN_ROOT",
	"The directory in which your RenderMan renderer is installed. Used to build IECoreRI.",
	"/usr/local",
)

options.Add(
	"ARNOLD_ROOT",
	"The directory in which Arnold is installed. Used to build IECoreArnold",
	"/usr/local",
)

options.Add(
	"NUKE_ROOT",
	"The directory in which Nuke is installed. Used to build IECoreNuke",
	"/usr/local",
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
	"$DEPENDENCIES_SRC_DIR/PyOpenGL-3.0.0",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_QT", "Set this to build QT.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"QT_SRC_DIR",
	"The location of QT.",
	"$DEPENDENCIES_SRC_DIR/qt-everywhere-opensource-src-4.7.3",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_PYSIDE", "Set this to build PySide.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"APIEXTRACTOR_SRC_DIR",
	"The location of QT.",
	"$DEPENDENCIES_SRC_DIR/apiextractor-0.10.0",
)

options.Add(
	"GENERATORRUNNER_SRC_DIR",
	"The location of QT.",
	"$DEPENDENCIES_SRC_DIR/generatorrunner-0.6.6",
)

options.Add(
	"SHIBOKEN_SRC_DIR",
	"The location of QT.",
	"$DEPENDENCIES_SRC_DIR/shiboken-1.0.0~rc1",
)

options.Add(
	"PYSIDE_SRC_DIR",
	"The location of QT.",
	"$DEPENDENCIES_SRC_DIR/pyside-qt4.7+1.0.0~rc1",
)

options.Add(
	BoolVariable( "BUILD_DEPENDENCY_PYQT", "Set this to build PyQt.", "$BUILD_DEPENDENCIES" )
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
	"The locations on which to search for include files "
	"for the dependencies.",
	"",
)

options.Add(
	"LOCATE_DEPENDENCY_LIBPATH",
	"The locations on which to search for libraries for "
	"the dependencies.",
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
# Basic environment object. All the other environments will be based on this
###############################################################################################

env = Environment(

	options = options,

	GAFFER_MAJOR_VERSION = "0",
	GAFFER_MINOR_VERSION = "29",
	GAFFER_PATCH_VERSION = "0",
	
	PYTHON_VERSION = "2.7", # \todo need some way of getting this magically

)

for e in env["ENV_VARS_TO_IMPORT"].split() :
	if e in os.environ :
		env["ENV"][e] = os.environ[e]

env["ENV"]["MACOSX_DEPLOYMENT_TARGET"] = "10.4"

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
	elif o.key.startswith( "LOCATE_DEPENDENCY" ) and str( env.subst( "$" + o.key ) ) != str( env.subst( o.default ) ) :
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
		"HOME" : os.environ["HOME"],
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

if depEnv["BUILD_DEPENDENCY_TIFF"] :
	runCommand( "cd $TIFF_SRC_DIR && ./configure --prefix=$BUILD_DIR && make clean && make && make install" )

if depEnv["BUILD_DEPENDENCY_JPEG"] :
	runCommand( "cd $JPEG_SRC_DIR && ./configure --prefix=$BUILD_DIR && make clean && make && make install" )

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
	
if depEnv["BUILD_DEPENDENCY_CORTEX"] :
	runCommand( "cd $CORTEX_SRC_DIR; scons install installDoc -j 3 BUILD_CACHEDIR=$BUILD_CACHEDIR INSTALL_DOC_DIR=$BUILD_DIR/doc/cortex INSTALL_PREFIX=$BUILD_DIR INSTALL_PYTHON_DIR=$BUILD_DIR/python PYTHON_CONFIG=$BUILD_DIR/bin/python-config BOOST_INCLUDE_PATH=$BUILD_DIR/include/boost LIBPATH=$BUILD_DIR/lib BOOST_LIB_SUFFIX='' OPENEXR_INCLUDE_PATH=$BUILD_DIR/include FREETYPE_INCLUDE_PATH=$BUILD_DIR/include/freetype2 RMAN_ROOT=$DELIGHT WITH_GL=1 GLEW_INCLUDE_PATH=$BUILD_DIR/include/GL RMAN_ROOT=$RMAN_ROOT NUKE_ROOT=$NUKE_ROOT ARNOLD_ROOT=$ARNOLD_ROOT OPTIONS='' DOXYGEN=$DOXYGEN ENV_VARS_TO_IMPORT='LD_LIBRARY_PATH PATH' SAVE_OPTIONS=gaffer.options" )
	
if depEnv["BUILD_DEPENDENCY_GL"] :
	runCommand( "cd $PYOPENGL_SRC_DIR && python setup.py install --prefix $BUILD_DIR --install-lib $BUILD_DIR/python" )

if depEnv["BUILD_DEPENDENCY_QT"] :
	runCommand( "cd $QT_SRC_DIR && ./configure -prefix $BUILD_DIR -opensource -no-rpath -no-declarative -no-gtkstyle -no-qt3support && make -j 4 && make install" )
	
if depEnv["BUILD_DEPENDENCY_PYQT"] :
	runCommand( "cd $SIP_SRC_DIR && python configure.py -d $BUILD_DIR/python && make clean && make && make install" )
	runCommand( "cd $PYQT_SRC_DIR && python configure.py -d $BUILD_DIR/python  --confirm-license && make && make install" )

# having MACOS_DEPLOYMENT_TARGET set breaks the pyside build for some reason
del depEnv["ENV"]["MACOSX_DEPLOYMENT_TARGET"]
if depEnv["BUILD_DEPENDENCY_PYSIDE"] :
	runCommand( "cd $APIEXTRACTOR_SRC_DIR && cmake -DCMAKE_INSTALL_PREFIX=$BUILD_DIR && make clean && make -j 4 && make install" )
	runCommand( "cd $GENERATORRUNNER_SRC_DIR && cmake -DCMAKE_INSTALL_PREFIX=$BUILD_DIR && make clean && make VERBOSE=1 && make install" )
	if depEnv["PLATFORM"]=="darwin" :
		runCommand( "cd $SHIBOKEN_SRC_DIR && cmake -DSITE_PACKAGE=$BUILD_DIR/python -DCMAKE_INSTALL_PREFIX=$BUILD_DIR -DPYTHON_INCLUDE_DIR=$BUILD_DIR/lib/Python.framework/Headers && make clean && make && make install" )
		runCommand( "cd $PYSIDE_SRC_DIR && cmake -DSITE_PACKAGE=$BUILD_DIR/python -DCMAKE_INSTALL_PREFIX=$BUILD_DIR -DPYTHON_INCLUDE_DIR=$BUILD_DIR/lib/Python.framework/Headers && make VERBOSE=1 && make install" )
	else :
		runCommand( "cd $SHIBOKEN_SRC_DIR && cmake -DCMAKE_INSTALL_PREFIX=$BUILD_DIR -DPYTHON_INCLUDE_DIR=$BUILD_DIR/include/python2.7 -DCMAKE_USE_PYTHON_VERSION=$PYTHON_VERSION && make clean && make && make install" )
		runCommand( "cd $PYSIDE_SRC_DIR && cmake -DSITE_PACKAGE=$BUILD_DIR/python -DCMAKE_INSTALL_PREFIX=$BUILD_DIR && make clean && make VERBOSE=1 && make install" )
		
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
		"$BUILD_DIR/include",
		"$BUILD_DIR/include/python$PYTHON_VERSION",
		"$BUILD_DIR/include/OpenEXR",
		"$BUILD_DIR/include/GL",
		"$LOCATE_DEPENDENCY_CPPPATH",
	],
	
	CPPFLAGS = [
		"-DBOOST_FILESYSTEM_VERSION=2",
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
		"Imath",
		"IECore$CORTEX_LIB_SUFFIX",
	],
	
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

pythonLinkFlags = os.popen( basePythonEnv.subst( "$BUILD_DIR/bin/python$PYTHON_VERSION-config --ldflags" ) ).read().strip()
pythonLinkFlags = pythonLinkFlags.replace( "Python.framework/Versions/" + basePythonEnv["PYTHON_VERSION"] + "/Python", "" )
	
basePythonEnv.Append(

	CPPFLAGS = os.popen( basePythonEnv.subst( "$BUILD_DIR/bin/python$PYTHON_VERSION-config --includes" ) ).read().split(),

	SHLINKFLAGS = pythonLinkFlags,

)

if basePythonEnv["PLATFORM"]=="darwin" :
	basePythonEnv.Append( SHLINKFLAGS = "-single_module" )

###############################################################################################
# Definitions for the libraries we wish to build
###############################################################################################

libraries = {

	"Gaffer" : {},
	
	"GafferTest" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "GafferTest", "GafferBindings" ],
		},
		"additionalFiles" : glob.glob( "python/GafferTest/*/*" )
	},
	
	"GafferScene" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "GafferBindings", "GafferScene", "GafferSceneBindings" ],
		},
	},
	
	"GafferSceneTest" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer", "GafferScene" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "Gaffer", "GafferBindings", "GafferScene", "GafferSceneTest" ],
		},
	},
	
	"GafferSceneUI" : {
	},
	
	"GafferUI" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer", "IECoreGL$CORTEX_LIB_SUFFIX", "GLEW$GLEW_LIB_SUFFIX" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "IECoreGL$CORTEX_LIB_SUFFIX", "GafferUI", "GafferBindings" ],
		},
	},
	
	"GafferUITest" : {},
	
	"apps" : {
		"additionalFiles" : glob.glob( "apps/*/*-1.py" ),
	},
	
	"scripts" : {
		"additionalFiles" : [ "bin/gaffer", "bin/gaffer.py" ],
	},
	
	"startupScripts" : {
		"additionalFiles" : glob.glob( "startup/*/*.py" ),
	},
	
	"shaders" : {
		"additionalFiles" : glob.glob( "shaders/*" ) + glob.glob( "shaders/*/*" ),
	},
	
	"misc" : {
		"additionalFiles" : [ "LICENSE" ],
	},

}

if env["PLATFORM"] == "darwin" :
	libraries["GafferUI"]["envAppends"].setdefault( "FRAMEWORKS", [] ).append( "OpenGL" )
else :
	libraries["GafferUI"]["envAppends"]["LIBS"].append( "GL" )

###############################################################################################
# The stuff that actually builds the libraries and python modules
###############################################################################################

for libraryName, libraryDef in libraries.items() :

	libEnv = baseLibEnv.Clone()
	libEnv.Append( **(libraryDef.get( "envAppends", {} )) )

	# library

	librarySource = glob.glob( "src/" + libraryName + "/*.cpp" )
	if librarySource :
	
		library = libEnv.SharedLibrary( "lib/" + libraryName, librarySource )
		libEnv.Default( library )
	
		libraryInstall = libEnv.Install( "$BUILD_DIR/lib", library )
		libEnv.Alias( "build", libraryInstall )
	
	# header install
	
	headerInstall = libEnv.Install(
		"$BUILD_DIR/" + "include/" + libraryName,
		glob.glob( "include/" + libraryName + "/*.h" ) +
		glob.glob( "include/" + libraryName + "/*.inl" )
	)
	libEnv.Alias( "build", headerInstall )
		
	# bindings library and binary python modules

	pythonEnv = basePythonEnv.Clone()
	pythonEnv.Append( **(libraryDef.get( "pythonEnvAppends", {} ))  )
	
	bindingsSource = glob.glob( "src/" + libraryName + "Bindings/*.cpp" )
	if bindingsSource :
			
		bindingsLibrary = pythonEnv.SharedLibrary( "lib/" + libraryName + "Bindings", bindingsSource )
		pythonEnv.Default( bindingsLibrary )
		
		bindingsLibraryInstall = pythonEnv.Install( "$BUILD_DIR/lib", bindingsLibrary )
		env.Alias( "build", bindingsLibraryInstall )
	
	pythonModuleSource = glob.glob( "src/" + libraryName + "Module/*.cpp" )
	if pythonModuleSource :
		
		pythonModuleEnv = pythonEnv.Clone()
		if bindingsSource :
			pythonModuleEnv.Append( LIBS = [ bindingsLibrary ] )
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
					int( float( tokens[3] ) ), int( float( tokens[4] ) ),
					str( source[0] ),
				)
			)

graphicsBuild = env.Command( "$BUILD_DIR/graphics/arrowDown10.png", "graphics/graphics.svg", buildGraphics )
env.NoCache( graphicsBuild )
env.Alias( "build", graphicsBuild )

#########################################################################################################
# Licenses
#########################################################################################################

if buildingDependencies :

	for l in [
		( "python", "$PYTHON_SRC_DIR/LICENSE" ),
		( "boost", "$BOOST_SRC_DIR/LICENSE_1_0.txt" ),
		( "cortex", "$CORTEX_SRC_DIR/LICENSE" ),
		( "freetype", "$FREETYPE_SRC_DIR/docs/FTL.TXT" ),
		( "glew", "$GLEW_SRC_DIR/LICENSE.txt" ),
		( "ilmbase", "$ILMBASE_SRC_DIR/COPYING" ),
		( "libjpeg", "$JPEG_SRC_DIR/README" ),
		( "openexr", "$OPENEXR_SRC_DIR/LICENSE" ),
		( "libtiff", "$TIFF_SRC_DIR/COPYRIGHT" ),
	] :

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
	
	"lib/libpython*$SHLIBSUFFIX*",
	"lib/Python.framework",
	"lib/python$PYTHON_VERSION",
	
	"lib/libGLEW*$SHLIBSUFFIX*",
	"lib/libtbb*$SHLIBSUFFIX*",
	"lib/libpyside*$SHLIBSUFFIX*",
	"lib/libshiboken*$SHLIBSUFFIX*",
	
	"lib/libQtCore*",
	"lib/libQtGui*",
	"lib/libQtOpenGL*",
	"lib/QtCore.framework",
	"lib/QtGui.framework",
	"lib/QtOpenGL.framework",
	
	"startup/gui/menus.py",
	"startup/gui/layouts.py",
	"startup/gui/graphs.py",

	"shaders",
	"fonts",
	"ops",
	"procedurals",

	"graphics/*.png",
	"glsl/IECoreGL",
	"doc/licenses",
	"doc/gaffer/html",
	"doc/cortex/html",

	"python/IECore*",
	"python/Gaffer*",
	"python/PySide/*.py",
	"python/PySide/QtCore.so",
	"python/PySide/QtGui.so",
	"python/PySide/QtOpenGL.so",
	"python/PyQt*",
	"python/OpenGL",

	"include/IECore*",
	"include/Gaffer*",
	"include/boost",
	"include/GL",
	"include/OpenEXR",
	"include/python*",
	"include/tbb",
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
	copyTree( env.subst( "$BUILD_DIR" ), env.subst( "$INSTALL_DIR" ), regex )
										
install = env.Command( "$INSTALL_DIR", "$BUILD_DIR", installer )
env.AlwaysBuild( install )
env.NoCache( install )

env.Alias( "install", install )

#########################################################################################################
# Packaging
#########################################################################################################

def packager( target, source, env ) :

	installDir = env.subst( "$INSTALL_DIR" )
	b = os.path.basename( installDir )
	d = os.path.dirname( installDir )
	runCommand( env.subst( "tar -czf $PACKAGE_FILE -C %s %s" % ( d, b ) ) )
	
package = env.Command( "$PACKAGE_FILE", install, packager )
env.NoCache( package )
env.Alias( "package", package )

##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
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
import sys
import glob
import shutil
import py_compile
import subprocess

CacheDir( "/home/john/dev/sconsBuildCache" )

###############################################################################################
# Command line options
###############################################################################################

options = Variables( "", ARGUMENTS )

options.Add(
	"BUILD_DIR",
	"The destination directory in which the build will be made.",
	"/home/john/dev/build/gaffer"
)

options.Add(
	"INSTALL_DIR",
	"The destination directory for the installation.",
	"/home/john/dev/install/gaffer-${GAFFER_MAJOR_VERSION}.${GAFFER_MINOR_VERSION}.${GAFFER_PATCH_VERSION}-${PLATFORM}",
)

options.Add(
	"PACKAGE_FILE",
	"The file in which the final gaffer file will be created by the package target.",
	"${INSTALL_DIR}.tar.gz",
)

options.Add( 
	BoolVariable( "BUILD_DEPENDENCIES", "Set this to build all the library dependencies gaffer has.", False )
)

options.Add(
	"DEPENDENCIES_SRC_DIR",
	"The location of a directory holding dependencies.",
	"/home/john/dev/gafferDependencies",
)

options.Add(
	BoolVariable( "BUILD_PYTHON", "Set this to build python.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"PYTHON_SRC_DIR",
	"The location of the python source to be used if BUILD_PYTHON is specified.",
	"$DEPENDENCIES_SRC_DIR/Python-2.6.3",
)

options.Add(
	BoolVariable( "BUILD_BOOST", "Set this to build boost.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"BOOST_SRC_DIR",
	"The location of the boost source to be used if BUILD_BOOST is specified.",
	"$DEPENDENCIES_SRC_DIR/boost_1_42_0",
)

options.Add(
	BoolVariable( "BUILD_TBB", "Set this to build tbb.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"TBB_SRC_DIR",
	"The location of the tbb source to be used if BUILD_TBB is specified.",
	"$DEPENDENCIES_SRC_DIR/tbb22_004oss",
)

options.Add(
	BoolVariable( "BUILD_OPENEXR", "Set this to build openexr.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"ILMBASE_SRC_DIR",
	"The location of the ilmbase source to be used if BUILD_OPENEXR is specified.",
	"$DEPENDENCIES_SRC_DIR/ilmbase-1.0.1",
)

options.Add(
	"OPENEXR_SRC_DIR",
	"The location of the exr source to be used if BUILD_OPENEXR is specified.",
	"$DEPENDENCIES_SRC_DIR/openexr-1.6.1",
)

options.Add(
	BoolVariable( "BUILD_JPEG", "Set this to build the jpeg library.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"JPEG_SRC_DIR",
	"The location of the jpeg source to be used if BUILD_JPEG is specified.",
	"$DEPENDENCIES_SRC_DIR/jpeg-6b",
)

options.Add(
	BoolVariable( "BUILD_TIFF", "Set this to build the tiff library.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"TIFF_SRC_DIR",
	"The location of the tiff source to be used if BUILD_TIFF is specified.",
	"$DEPENDENCIES_SRC_DIR/tiff-3.8.2",
)

options.Add(
	BoolVariable( "BUILD_FREETYPE", "Set this to build freetype.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"FREETYPE_SRC_DIR",
	"The location of the freetype source to be used if BUILD_FREETYPE is specified.",
	"$DEPENDENCIES_SRC_DIR/freetype-2.3.9",
)

options.Add(
	BoolVariable( "BUILD_GLEW", "Set this to build GLEW.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"GLEW_SRC_DIR",
	"The location of the glew source to be used if BUILD_GLEW is specified.",
	"$DEPENDENCIES_SRC_DIR/glew-1.5.4",
)

options.Add(
	BoolVariable( "BUILD_CORTEX", "Set this to build cortex.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"CORTEX_SRC_DIR",
	"The location of the boost source to be used if BUILD_CORTEX is specified.",
	"$DEPENDENCIES_SRC_DIR/cortex-vfx/trunk",
)

options.Add(
	BoolVariable( "BUILD_GTK", "Set this to build gtk.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	BoolVariable( "BUILD_PKGCONFIG", "Set this to build the pkgconfig library.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"PKGCONFIG_SRC_DIR",
	"The location of the pkg-config source to be used if BUILD_GTK is specified.",
	"$DEPENDENCIES_SRC_DIR/pkg-config-0.23",
)

options.Add(
	BoolVariable( "BUILD_GRAPHVIZ", "Set this to build the graphviz library.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"GRAPHVIZ_SRC_DIR",
	"The location of the graphviz source to be used if BUILD_GRAPHVIZ is specified.",
	"$DEPENDENCIES_SRC_DIR/graphviz-2.24.0",
)

options.Add(
	BoolVariable( "BUILD_DOXYGEN", "Set this to build doxygen.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"DOXYGEN_SRC_DIR",
	"The location of the doxygen source to be used if BUILD_DOXYGEN is specified.",
	"$DEPENDENCIES_SRC_DIR/doxygen-1.7.2",
)

options.Add(
	"PYOPENGL_SRC_DIR",
	"The location of the PyOpenGL source to be used if BUILD_GL is specified.",
	"$DEPENDENCIES_SRC_DIR/PyOpenGL-3.0.0",
)

options.Add(
	BoolVariable( "BUILD_GL", "Set this to build PyOpenGL.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	BoolVariable( "BUILD_GOOGLEPERFTOOLS", "Set this to build the google perftools.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"GOOGLEPERFTOOLS_SRC_DIR",
	"The location of the google performance tools source if BUILD_GOOGLEPERFTOOLS is specified.",
	"$DEPENDENCIES_SRC_DIR/google-perftools-1.6",
)

options.Add(
	"LIBUNWIND_SRC_DIR",
	"The location of the libunwind source if BUILD_GOOGLEPERFTOOLS is specified.",
	"$DEPENDENCIES_SRC_DIR/libunwind-0.99-beta",
)

options.Add(
	BoolVariable( "BUILD_QT", "Set this to build QT.", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"QT_SRC_DIR",
	"The location of QT.",
	"$DEPENDENCIES_SRC_DIR/qt-everywhere-opensource-src-4.7.1",
)

options.Add(
	BoolVariable( "BUILD_PYSIDE", "Set this to build PySide.", "$BUILD_DEPENDENCIES" )
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
	BoolVariable( "BUILD_FONTS", "", "$BUILD_DEPENDENCIES" )
)

options.Add(
	"FONTS_DIR",
	"The location of fonts.",
	"$DEPENDENCIES_SRC_DIR/ttf-bitstream-vera-1.10",
)

###############################################################################################
# Dependencies
# They doesn't fit into the SCons way of things too well so we just build them directly when
# the script runs.
###############################################################################################

depEnv = Environment(
	options = options,
)

depEnv["CXX_MAJOR_VERSION"] = depEnv["CXXVERSION"].split( "." )[0]
depEnv["CXX_MINOR_VERSION"] = depEnv["CXXVERSION"].split( "." )[1]
depEnv["DELIGHT"] = os.environ["DELIGHT"]

def runCommand( command ) :

	sys.stderr.write( command + "\n" )
	command = "export PATH=%s DYLD_LIBRARY_PATH= LD_LIBRARY_PATH=%s M4PATH=%s PKG_CONFIG_PATH=%s MACOSX_DEPLOYMENT_TARGET=10.4 && %s " % (
		depEnv.subst( "$BUILD_DIR/bin:/usr/local/bin:/bin:/sbin:/usr/bin:/usr/sbin" ),
		depEnv.subst( "$BUILD_DIR/lib" ),
		depEnv.subst( "$BUILD_DIR/share/aclocal" ),
		depEnv.subst( "$BUILD_DIR/lib/pkgconfig" ),
		depEnv.subst( command )
	)
	status = os.system( command )
	if status :
		raise RuntimeError( "Failed to build dependency" )

if depEnv["BUILD_PKGCONFIG"] :
	runCommand( "cd $PKGCONFIG_SRC_DIR && ./configure --prefix=$BUILD_DIR && make clean && make && make install" )

if depEnv["BUILD_PYTHON"] :
	
	if depEnv["PLATFORM"]=="darwin" :
		runCommand( "cd $PYTHON_SRC_DIR; ./configure --enable-framework=$BUILD_DIR/frameworks --prefix=$BUILD_DIR && make clean && make && make install" )
		runCommand( "cd $BUILD_DIR/bin && ln -fsh python2.6 python" )
	else :
		runCommand( "cd $PYTHON_SRC_DIR; ./configure --prefix=$BUILD_DIR --enable-unicode=ucs4 && make clean && make && make install" )

if depEnv["BUILD_JPEG"] :
	runCommand( "cd $JPEG_SRC_DIR && ./configure --prefix=$BUILD_DIR && make clean && make CFLAGS='-O2 -fPIC' && make install-lib install-headers" )

if depEnv["BUILD_TIFF"] :
	runCommand( "cd $TIFF_SRC_DIR && ./configure --prefix=$BUILD_DIR && make clean && make && make install" )
		
if depEnv["BUILD_FREETYPE"] :
	runCommand( "cd $FREETYPE_SRC_DIR && ./configure --prefix=$BUILD_DIR && make clean && make && make install" )
		
if depEnv["BUILD_GRAPHVIZ"] :
	runCommand( "cd $GRAPHVIZ_SRC_DIR && ./configure --enable-perl=no --prefix=$BUILD_DIR && make clean && make && make install" )

if depEnv["BUILD_DOXYGEN"] :
	runCommand( "cd $DOXYGEN_SRC_DIR && ./configure --prefix $BUILD_DIR && make && make install" )
	
if depEnv["BUILD_BOOST"] :
	runCommand( "cd $BOOST_SRC_DIR; ./bootstrap.sh --prefix=$BUILD_DIR --with-python=$BUILD_DIR/bin/python2.6 --with-python-root=$BUILD_DIR && ./bjam install" )

if depEnv["BUILD_TBB"] :
	runCommand( "cd $TBB_SRC_DIR; make clean; make" )
	if depEnv["PLATFORM"]=="darwin" :
		runCommand( "cd $TBB_SRC_DIR; cp build/macos_intel64_gcc_cc4.2.1_os10.6.2_release/*.dylib $BUILD_DIR/lib; cp -r include/tbb $BUILD_DIR/include" )
	else :
		runCommand( "cd $TBB_SRC_DIR; cp build/linux_intel64_gcc_cc4.4.1_libc2.10.1_kernel2.6.31_release/*.so* $BUILD_DIR/lib; cp -r include/tbb $BUILD_DIR/include" )

if depEnv["BUILD_OPENEXR"] :
	runCommand( "cd $ILMBASE_SRC_DIR && ./configure --prefix=$BUILD_DIR && make clean && make && make install" )
	runCommand( "cd $OPENEXR_SRC_DIR && ./configure --prefix=$BUILD_DIR && make clean && make && make install" )

if depEnv["BUILD_FONTS"] :
	runCommand( "mkdir -p $BUILD_DIR/fonts && cp $FONTS_DIR/*.ttf $BUILD_DIR/fonts" )

if depEnv["BUILD_GLEW"] :
	if depEnv["PLATFORM"]=="posix" :
		runCommand( "mkdir -p $BUILD_DIR/lib64/pkgconfig" )
	runCommand( "cd $GLEW_SRC_DIR && make clean && make install GLEW_DEST=$BUILD_DIR LIBDIR=$BUILD_DIR/lib" )
	
if depEnv["BUILD_CORTEX"] :
	runCommand( "cd $CORTEX_SRC_DIR; scons install -j 3 DOXYGEN=$BUILD_DIR/bin/doxygen INSTALL_DOC_DIR=$BUILD_DIR/doc/cortex INSTALL_PREFIX=$BUILD_DIR INSTALL_PYTHON_DIR=$BUILD_DIR/lib/python2.6/site-packages PYTHON_CONFIG=$BUILD_DIR/bin/python2.6-config BOOST_INCLUDE_PATH=$BUILD_DIR/include/boost LIBPATH=$BUILD_DIR/lib BOOST_LIB_SUFFIX='' OPENEXR_INCLUDE_PATH=$BUILD_DIR/include FREETYPE_INCLUDE_PATH=$BUILD_DIR/include/freetype2 RMAN_ROOT=$DELIGHT WITH_GL=1 GLEW_INCLUDE_PATH=$BUILD_DIR/include/GL" )
	
if depEnv["BUILD_GL"] :
	runCommand( "cd $PYOPENGL_SRC_DIR && python setup.py install" )

if depEnv["BUILD_QT"] :

	runCommand( "cd $QT_SRC_DIR && ./configure -prefix $BUILD_DIR -opensource -no-rpath -no-declarative && make clean && make && make install" )

if depEnv["BUILD_PYSIDE"] :
	runCommand( "cd $APIEXTRACTOR_SRC_DIR && cmake -DCMAKE_INSTALL_PREFIX=$BUILD_DIR && make clean && make && make install" )
	runCommand( "cd $GENERATORRUNNER_SRC_DIR && cmake -DCMAKE_INSTALL_PREFIX=$BUILD_DIR && make clean && make && make install" )
	runCommand( "cd $SHIBOKEN_SRC_DIR && cmake -DCMAKE_INSTALL_PREFIX=$BUILD_DIR && make clean && make && make install" )
	runCommand( "cd $PYSIDE_SRC_DIR && cmake -DCMAKE_INSTALL_PREFIX=$BUILD_DIR && make clean && make && make install" )

if depEnv["BUILD_GOOGLEPERFTOOLS"] :

	runCommand( "cd $LIBUNWIND_SRC_DIR && ./configure --prefix=$BUILD_DIR CFLAGS=-U_FORTIFY_SOURCE && make clean && make && make install" )	
	runCommand( "cd $GOOGLEPERFTOOLS_SRC_DIR && ./configure --prefix=$BUILD_DIR CPPFLAGS=-I$BUILD_DIR/include LDFLAGS=-L$BUILD_DIR/lib && make clean && make && make install" )

###############################################################################################
# Gaffer libraries
###############################################################################################

boostLibSuffix = ""

env = Environment(

	options = options,

	GAFFER_MAJOR_VERSION = "0",
	GAFFER_MINOR_VERSION = "1",
	GAFFER_PATCH_VERSION = "2",

	CPPPATH = [
		"include",
		"$BUILD_DIR/include",
		"$BUILD_DIR/include/boost-1_40",
		"$BUILD_DIR/include/OpenEXR",
	],
	
	CXXFLAGS = [
		"-Wall",
		#"-Werror", # \todo reintroduce when boost sorts itself out
		"-O2",
	],
	
	LIBPATH = [
		"$BUILD_DIR/lib"
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
		"IECore",
	],
	
)

env["ENV"]["MACOSX_DEPLOYMENT_TARGET"] = "10.4"

gafferLibrary = env.SharedLibrary( "lib/Gaffer", glob.glob( "src/Gaffer/*.cpp" ) )
env.Default( gafferLibrary )

gafferLibraryInstall = env.Install( "$BUILD_DIR/lib", gafferLibrary )
env.Alias( "build", gafferLibraryInstall )

uiEnv = env.Clone()
uiEnv.Append(

	LIBS = [ gafferLibrary ],

)
gafferUILibrary = uiEnv.SharedLibrary( "lib/GafferUI", glob.glob( "src/GafferUI/*.cpp" ) )
uiEnv.Default( gafferUILibrary )

gafferUILibraryInstall = env.Install( "$BUILD_DIR/lib", gafferUILibrary )
env.Alias( "build", gafferUILibraryInstall )

###############################################################################################
# Gaffer python modules
###############################################################################################

pythonEnv = env.Clone()

pythonEnv.Append(

	CPPFLAGS = [
		"-DBOOST_PYTHON_MAX_ARITY=20",
	] + os.popen( pythonEnv.subst( "$BUILD_DIR/bin/python2.6-config --includes" ) ).read().split(),
	
	LIBPATH = [ "./lib" ],
	
	LIBS = [
		"boost_python" + boostLibSuffix,
		"IECorePython",
		"Gaffer",
	],
	
	SHLINKFLAGS = os.popen( pythonEnv.subst( "$BUILD_DIR/bin/python2.6-config --ldflags" ) ).read().split(),
)

if pythonEnv["PLATFORM"]=="darwin" :
	pythonEnv.Append( SHLINKFLAGS = "-single_module" )

gafferBindingsLibrary = pythonEnv.SharedLibrary( "lib/GafferBindings", glob.glob( "src/GafferBindings/*.cpp" ) )
pythonEnv.Default( gafferBindingsLibrary )

gafferBindingsLibraryInstall = env.Install( "$BUILD_DIR/lib", gafferBindingsLibrary )
env.Alias( "build", gafferBindingsLibraryInstall )

pythonUIEnv = pythonEnv.Clone()
pythonUIEnv.Append(
	LIBS = [ "GafferUI", "GafferBindings" ],
)
gafferUIBindingsLibrary = pythonUIEnv.SharedLibrary( "lib/GafferUIBindings", glob.glob( "src/GafferUIBindings/*.cpp" ) )
pythonUIEnv.Default( gafferUIBindingsLibrary )

gafferUIBindingsLibraryInstall = env.Install( "$BUILD_DIR/lib", gafferUIBindingsLibrary )
env.Alias( "build", gafferUIBindingsLibraryInstall )

pythonModuleEnv = pythonEnv.Clone()
pythonModuleEnv.Append(

	LIBS = [
		"GafferBindings",
	]

)

pythonModuleEnv["SHLIBPREFIX"] = ""
pythonModuleEnv["SHLIBSUFFIX"] = ".so"

gafferModule = pythonModuleEnv.SharedLibrary( "python/Gaffer/_Gaffer", glob.glob( "src/GafferModule/*.cpp" ) )
pythonModuleEnv.Default( gafferModule )

gafferModuleInstall = env.Install( "$BUILD_DIR/lib/python2.6/site-packages/Gaffer", gafferModule )
sedSubstitutions = "s/!GAFFER_MAJOR_VERSION!/$GAFFER_MAJOR_VERSION/g"
sedSubstitutions += "; s/!GAFFER_MINOR_VERSION!/$GAFFER_MINOR_VERSION/g"
sedSubstitutions += "; s/!GAFFER_PATCH_VERSION!/$GAFFER_PATCH_VERSION/g"

for f in glob.glob( "python/Gaffer/*.py" ) :
	gafferModuleInstall += env.Command( "$BUILD_DIR/lib/python2.6/site-packages/Gaffer/" + os.path.basename( f ), f, "sed \"" + sedSubstitutions + "\" $SOURCE > $TARGET" )

env.Alias( "build", gafferModuleInstall )

pythonUIModuleEnv = pythonModuleEnv.Clone()
pythonUIModuleEnv.Append(
	LIBS = [ "GafferUI", "GafferUIBindings" ],
)
gafferUIModule = pythonUIModuleEnv.SharedLibrary( "python/GafferUI/_GafferUI", glob.glob( "src/GafferUIModule/*.cpp" ) )
pythonUIModuleEnv.Default( gafferUIModule )

gafferUIModuleInstall = env.Install( "$BUILD_DIR/lib/python2.6/site-packages/GafferUI", gafferUIModule )
gafferUIModuleInstall += env.Install( "$BUILD_DIR/lib/python2.6/site-packages/GafferUI", glob.glob( "python/GafferUI/*.py" ) )
env.Alias( "build", gafferUIModuleInstall )

for module in ( "GafferTest", "GafferUITest", "GafferRI", "GafferRIUI" ) :

	moduleInstall = env.Install( "$BUILD_DIR/lib/python2.6/site-packages/" + module, glob.glob( "python/%s/*.py" % module ) )
	env.Alias( "build", moduleInstall ) 

###############################################################################################
# Scripts and apps and stuff
###############################################################################################

scriptsInstall = env.Install( "$BUILD_DIR/bin", [ "bin/gaffer", "bin/gaffer.py" ] )
env.Alias( "build", scriptsInstall )

for app in ( "gui", "view", "test", "cli", "license" ) :
	appInstall = env.Install( "$BUILD_DIR/apps/%s" % app, "apps/%s/%s-1.py" % ( app, app ) )
	env.Alias( "build", appInstall )

startupScriptsInstall = env.Install( "$BUILD_DIR/startup/gui", glob.glob( "startup/gui/*.py" ) )
env.Alias( "build", startupScriptsInstall )

for d in ( "ui", "" ) :
	shaderInstall = env.Install( "$BUILD_DIR/shaders/%s/" % d, glob.glob( "shaders/%s/*" % d ) )
	env.Alias( "build", shaderInstall )

#########################################################################################################
# Graphics
#########################################################################################################

def buildGraphics( target, source, env ) :

	dir = os.path.dirname( str( target[0] ) )
	if not os.path.isdir( dir ) :
		os.makedirs( dir )
	
	objects, stderr = subprocess.Popen( "inkscape --query-all " + str( source[0] ), stdout=subprocess.PIPE, shell=True ).communicate()
	for object in objects.split( "\n" ) :
		tokens = object.split( "," )
		if tokens[0].startswith( "forExport:" ) :
			os.system( "inkscape --export-png=%s/%s.png --export-id=%s --export-width=%d --export-height=%d %s" % (
					dir,
					tokens[0].split( ":" )[-1],
					tokens[0],
					int( float( tokens[3] ) ), int( float( tokens[4] ) ),
					str( source[0] ),
				)
			)

graphicsBuild = env.Command( "$BUILD_DIR/graphics/arrowDown10.png", "graphics/graphics.svg", buildGraphics )
env.Alias( "build", graphicsBuild )
	
#########################################################################################################
# Documentation
#########################################################################################################

def docMunger( target, source, env ) :

	f = open( str( source[0] ) )
	o = open( str( target[0] ), "w" )
	for l in f :
		
		w = l.split()
		if len( w ) < 2 :
			continue
			
		if w[0]=="from" :
			
			if not w[1].startswith( "_" ) :
				ff = open( os.path.dirname( str( source[0] ) ) + "/" + w[1] + ".py" )
				for ll in ff :
					o.write( ll )
					
		elif w[0]=="import" :
			sourceFileName = os.path.dirname( str( source[0] ) ) + "/" + w[1] + ".py"
			if os.path.exists( sourceFileName ) :
				shutil.copyfile( sourceFileName, os.path.dirname( str( target[0] ) ) + "/" + w[1] + ".py" )
	
docEnv = env.Clone()
docEnv["ENV"]["PATH"] = os.environ["PATH"]
for v in ( "BUILD_DIR", "GAFFER_MAJOR_VERSION", "GAFFER_MINOR_VERSION", "GAFFER_PATCH_VERSION" ) :
	docEnv["ENV"][v] = docEnv[v]

gafferMunged = env.Command( "doc/src/Gaffer.py", "python/Gaffer/__init__.py", docMunger )
env.Depends( gafferMunged, glob.glob( "python/Gaffer/*.py" ) )

gafferRIMunged = env.Command( "doc/src/GafferRI.py", "python/GafferRI/__init__.py", docMunger )
env.Depends( gafferRIMunged, glob.glob( "python/GafferRI/*.py" ) )

gafferUIMunged = env.Command( "doc/src/GafferUI.py", "python/GafferUI/__init__.py", docMunger )
env.Depends( gafferUIMunged, glob.glob( "python/GafferUI/*.py" ) )

gafferRIUIMunged = env.Command( "doc/src/GafferRIUI.py", "python/GafferRIUI/__init__.py", docMunger )
env.Depends( gafferRIUIMunged, glob.glob( "python/GafferRIUI/*.py" ) )

docs = docEnv.Command( "doc/html/index.html", "doc/config/Doxyfile", "doxygen doc/config/Doxyfile" )
env.NoCache( docs )
docEnv.Depends( docs, glob.glob( "include/*/*.h" ) + gafferMunged + gafferRIMunged + gafferUIMunged + gafferRIUIMunged + glob.glob( "doc/src/*.dox" ) )

docInstall = docEnv.Install( "$BUILD_DIR/doc/gaffer", "doc/html" )
#docEnv.Alias( "build", docInstall )

#########################################################################################################
# Installation
#########################################################################################################

manifest = [
	"bin/gaffer",
	"bin/gaffer.py",
	"apps/cli/1/cli.py",
	"apps/gui/1/gui.py",
	"apps/test/1/test.py",
	"apps/view/1/view.py",
	"apps/license/1/license.py",
	"lib/libboost_signals" + boostLibSuffix + ".dylib",
	"lib/libboost_thread" + boostLibSuffix + ".dylib",
	"lib/libboost_wave" + boostLibSuffix + ".dylib",
	"lib/libboost_regex" + boostLibSuffix + ".dylib",
	"lib/libboost_python" + boostLibSuffix + ".dylib",
	"lib/libboost_date_time" + boostLibSuffix + ".dylib",
	"lib/libboost_filesystem" + boostLibSuffix + ".dylib",
	"lib/libboost_iostreams" + boostLibSuffix + ".dylib",
	"lib/libboost_system" + boostLibSuffix + ".dylib",
	"lib/libIECore.dylib",
	"lib/libIECoreGL.dylib",
	"lib/libIECoreRI.dylib",
	"lib/libGaffer.dylib",
	"lib/libGafferBindings.dylib",
	"lib/libGafferUI.dylib",
	"lib/libGafferUIBindings.dylib",
	"lib/libIex.6.dylib",
	"lib/libHalf.6.dylib",
	"lib/libImath.6.dylib",
	"lib/libIlmImf.6.dylib",
	"lib/libIlmThread.6.dylib",
	"lib/libtiff.3.dylib",
	"lib/libfreetype.6.dylib",
	"lib/libpyglib-2.0-python.0.dylib",
	"lib/libgobject-2.0.0.dylib",
	"lib/libgthread-2.0.0.dylib",
	"lib/libglib-2.0.0.dylib",
	"lib/libgtk-x11-2.0.0.dylib",
	"lib/libgdk-x11-2.0.0.dylib",
	"lib/libatk-1.0.0.dylib",
	"lib/libgdk_pixbuf-2.0.0.dylib",
	"lib/libgio-2.0.0.dylib",
	"lib/libpangocairo-1.0.0.dylib",
	"lib/libpangoft2-1.0.0.dylib",
	"lib/libcairo.2.dylib",
	"lib/libpixman-1.0.dylib",
	"lib/libpango-1.0.0.dylib",
	"lib/libfontconfig.1.dylib",
	"lib/libexpat.1.dylib",
	"lib/libgmodule-2.0.0.dylib",
	"lib/libgtkglext-x11-1.0.0.dylib",
	"lib/libgdkglext-x11-1.0.0.dylib",
	"lib/libpangox-1.0.0.dylib",
	"lib/libGLEW.1.5.1.dylib",
	"frameworks/Python.framework",
	"startup/gui/menus.py",
	"startup/gui/layouts.py",
	"shaders",
	"glsl/IECoreGL",
	"doc/gaffer/html",
	"doc/cortex/html",
	"lib/python2.6/site-packages/IECore",
	"lib/python2.6/site-packages/IECoreGL",
	"lib/python2.6/site-packages/IECoreRI",
	"lib/python2.6/site-packages/Gaffer/_Gaffer.so",	
	"lib/python2.6/site-packages/GafferTest",	
	"lib/python2.6/site-packages/GafferUI/_GafferUI.so",
	"lib/python2.6/site-packages/GafferUITest",
	"lib/python2.6/site-packages/pygtk.pyc",
	"lib/python2.6/site-packages/gtk-2.0",
	"lib/python2.6/site-packages/cairo",
]

symlinks = [
	# have to symlink python on the mac as the bin/python you get otherwise is just a stub with a hardcoded full
	# path to wherever the framework was built
	( "bin/python", "../frameworks/Python.framework/Versions/2.6/Resources/Python.app/Contents/MacOS/Python" ),
]

pythonSourceToCompile = [
	"lib/python2.6/site-packages/Gaffer/*.py",
	"lib/python2.6/site-packages/GafferRI/*.py",
	"lib/python2.6/site-packages/GafferUI/*.py",
	"lib/python2.6/site-packages/GafferRIUI/*.py",
]

licenses = [
	( "python", "$PYTHON_SRC_DIR/LICENSE" ),
	( "boost", "$BOOST_SRC_DIR/LICENSE_1_0.txt" ),
	( "cortex", "$CORTEX_SRC_DIR/LICENSE" ),
	( "freetype", "$FREETYPE_SRC_DIR/docs/FTL.TXT" ),
	( "glew", "$GLEW_SRC_DIR/LICENSE.txt" ),
	( "glib", "$GLIB_SRC_DIR/COPYING" ),
	( "ilmbase", "$ILMBASE_SRC_DIR/COPYING" ),
	( "libjpeg", "$JPEG_SRC_DIR/README" ),
	( "openexr", "$OPENEXR_SRC_DIR/LICENSE" ),
	( "libtiff", "$TIFF_SRC_DIR/COPYRIGHT" ),
]

def expandSourceFiles( files, env ) :

	result = []
	root = env.subst( "$BUILD_DIR" )
	for f in files :
		for ff in glob.glob( os.path.join( root, f ) ) :
			result.append( ff[len(root)+1:] )
	
	return result

def installer( target, source, env ) :

	shutil.rmtree( env.subst( "$INSTALL_DIR" ), True )
	for f in manifest :

		src = env.subst( os.path.join( "$BUILD_DIR", f ) )
		dst = env.subst( os.path.join( "$INSTALL_DIR", f ) )
		dstDir = os.path.dirname( dst )
		if not os.path.isdir( dstDir ) :
			os.makedirs( dstDir )
				
		if os.path.isdir( src ) :	
			shutil.copytree( src, dst, True )
		else :
			shutil.copy( src, dst )
			
	for s in symlinks :
	
		os.symlink( s[1], env.subst( os.path.join( "$INSTALL_DIR", s[0] ) ) )

	for f in expandSourceFiles( pythonSourceToCompile, env ) :
		
		src = env.subst( os.path.join( "$BUILD_DIR", f ) )
		dst = env.subst( os.path.join( "$INSTALL_DIR", f + "c" ) )
		dstDir = os.path.dirname( dst )
		
		if not os.path.isdir( dstDir ) :
			os.makedirs( dstDir )
		
		py_compile.compile( src, dst, doraise=True )
		
	licenseDir = env.subst( "$INSTALL_DIR/doc/licenses" )
	os.makedirs( licenseDir )
	for l in licenses :
	
		src = env.subst( l[1] )
		dst = os.path.join( licenseDir, l[0] )
		
		shutil.copy( src, dst )
										
install = env.Command( "$INSTALL_DIR/bin/gaffer", "$BUILD_DIR", installer )
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

##########################################################################
#
#  Copyright (c) 2011-2014, John Haddon. All rights reserved.
#  Copyright (c) 2011-2014, Image Engine Design Inc. All rights reserved.
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
import platform
import py_compile
import subprocess

###############################################################################################
# Version
###############################################################################################

gafferMilestoneVersion = 0 # for announcing major milestones - may contain all of the below
gafferMajorVersion = 42 # backwards-incompatible changes
gafferMinorVersion = 0 # new backwards-compatible features
gafferPatchVersion = 0 # bug fixes

# All of the following must be considered when determining
# whether or not a change is backwards-compatible
#
#	- Library ABIs
#	- Python APIs
#	- Node/Plug naming
#	- Application command line arguments

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
	"clang++" if sys.platform == "darwin" else "g++",
)

options.Add(
	"CXXFLAGS",
	"The extra flags to pass to the C++ compiler during compilation.",
	[ "-pipe", "-Wall", "-Werror" ]
)

options.Add(
	BoolVariable( "DEBUG", "Make a debug build", False )
)

options.Add(
	"CXXSTD",
	"The C++ standard to build against. A minimum of C++11 is required.",
	"c++11",
)

options.Add(
	"LINKFLAGS",
	"The extra flags to pass to the C++ linker during compilation.",
	"",
)

options.Add(
	"BUILD_DIR",
	"The destination directory in which the build will be made.",
	"./build/gaffer-${GAFFER_MILESTONE_VERSION}.${GAFFER_MAJOR_VERSION}.${GAFFER_MINOR_VERSION}.${GAFFER_PATCH_VERSION}-${GAFFER_PLATFORM}",
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
	"./install/gaffer-${GAFFER_MILESTONE_VERSION}.${GAFFER_MAJOR_VERSION}.${GAFFER_MINOR_VERSION}.${GAFFER_PATCH_VERSION}-${GAFFER_PLATFORM}",
)

options.Add(
	"PACKAGE_FILE",
	"The file in which the final gaffer file will be created by the package target.",
	"${INSTALL_DIR}.tar.gz",
)

options.Add(
	"DELIGHT_ROOT",
	"The directory in which 3delight is installed. Used to build GafferDelight, an NSI-based"
	"3delight backend.",
	"",
)

options.Add(
	"VTUNE_ROOT",
	"The directory in which VTune is installed.",
	""
)

options.Add(
	"ARNOLD_ROOT",
	"The directory in which Arnold is installed. Used to build GafferArnold",
	"",
)

# Variables to be used when making a build which will use dependencies previously
# installed in some central location, rather than using the precompiled dependencies
# provided by the GafferHQ/dependencies project.

options.Add(
	"APPLESEED_ROOT",
	"The directory in which Appleseed is installed. Used to build Gafferseed",
	"$BUILD_DIR/appleseed",
)

options.Add(
	"OSLHOME",
	"The directory in which OpenShadingLanguage is installed.",
	"$BUILD_DIR",
)

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
	"LOCATE_DEPENDENCY_PYTHONPATH",
	"The locations on which to search for python modules for "
	"the dependencies.",
	"",
)

options.Add(
	"LOCATE_DEPENDENCY_RESOURCESPATH",
	"The path to the resources provided by the gafferResources project. "
	"If you follow the build instructions using the precompiled "
	"dependencies then you will not need this option.",
	"",
)

options.Add(
	"LOCATE_DEPENDENCY_APPLESEED_SEARCHPATH",
	"The paths in which Appleseed resources are installed.",
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
	"",
)

options.Add(
	"OCIO_LIB_SUFFIX",
	"The suffix used when locating the OpenColorIO libraries.",
	"",
)

options.Add(
	"OSL_LIB_SUFFIX",
	"The suffix used when locating the OpenShadingLanguage libraries.",
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
	"INKSCAPE",
	"Where to find the inkscape binary",
	"inkscape",
)

options.Add(
	"SPHINX",
	"Where to find the sphinx-build program",
	"sphinx-build",
)

options.Add(
	"INSTALL_POST_COMMAND",
	"A command which is run following a successful install process. "
	"This could be used to customise installation further for a "
	"particular site.",
	"",
)

###############################################################################################
# Basic environment object. All the other environments will be based on this.
###############################################################################################

env = Environment(

	options = options,

	GAFFER_MILESTONE_VERSION = str( gafferMilestoneVersion ),
	GAFFER_MAJOR_VERSION = str( gafferMajorVersion ),
	GAFFER_MINOR_VERSION = str( gafferMinorVersion ),
	GAFFER_PATCH_VERSION = str( gafferPatchVersion ),

	CPPDEFINES = [
		( "GAFFER_MILESTONE_VERSION", "$GAFFER_MILESTONE_VERSION" ),
		( "GAFFER_MAJOR_VERSION", "$GAFFER_MAJOR_VERSION" ),
		( "GAFFER_MINOR_VERSION", "$GAFFER_MINOR_VERSION" ),
		( "GAFFER_PATCH_VERSION", "$GAFFER_PATCH_VERSION" ),
	],

	CPPPATH = [
		"include",
		"$LOCATE_DEPENDENCY_CPPPATH",
	],

	CPPFLAGS = [
		"-DBOOST_FILESYSTEM_VERSION=3",
		"-DBOOST_FILESYSTEM_NO_DEPRECATED",
		"-DBOOST_SIGNALS_NO_DEPRECATION_WARNING",
	],

	LIBPATH = [
		"./lib",
		"$BUILD_DIR/lib",
		"$LOCATE_DEPENDENCY_LIBPATH",
	],

	FRAMEWORKPATH = "$BUILD_DIR/lib",


)

# include 3rd party headers with -isystem rather than -I.
# this should turn off warnings from those headers, allowing us to
# build with -Werror. there are so many warnings from boost
# in particular that this would be otherwise impossible.
for path in [
		"$BUILD_DIR/include",
		"$BUILD_DIR/include/python$PYTHON_VERSION",
		"$BUILD_DIR/include/OpenEXR",
		"$BUILD_DIR/include/GL",
	] + env["LOCATE_DEPENDENCY_SYSTEMPATH"] :

	env.Append(
		CXXFLAGS = [ "-isystem", path ]
	)

env["BUILD_DIR"] = os.path.abspath( env["BUILD_DIR"] )

# DISPLAY and HOME are essential for running gaffer when generating
# the documentation. TERM is needed to get coloured output from the
# compiler.
for e in env["ENV_VARS_TO_IMPORT"].split() + [ "DISPLAY", "HOME", "TERM" ] :
	if e in os.environ :
		env["ENV"][e] = os.environ[e]

if env["PLATFORM"] == "darwin" :

	env.Append( CXXFLAGS = [ "-D__USE_ISOC99" ] )
	env["GAFFER_PLATFORM"] = "osx"

	osxVersion = [ int( v ) for v in platform.mac_ver()[0].split( "." ) ]
	if osxVersion[0] == 10 and osxVersion[1] > 7 :
		# Fix problems with Boost 1.55 and recent versions of Clang.
		env.Append( CXXFLAGS = [ "-DBOOST_HAS_INT128", "-Wno-unused-local-typedef" ] )

elif env["PLATFORM"] == "posix" :

	if "g++" in os.path.basename( env["CXX"] ) :

		gccVersion = subprocess.Popen( [ env["CXX"], "-dumpversion" ], env=env["ENV"], stdout=subprocess.PIPE ).stdout.read().strip()
		gccVersion = [ int( v ) for v in gccVersion.split( "." ) ]

		# GCC 4.1.2 in conjunction with boost::flat_map produces crashes when
		# using the -fstrict-aliasing optimisation (which defaults to on with -O2),
		# so we turn the optimisation off here, only for that specific GCC version.
		if gccVersion == [ 4, 1, 2 ] :
			env.Append( CXXFLAGS = [ "-fno-strict-aliasing" ] )

		# GCC emits spurious "assuming signed overflow does not occur"
		# warnings, typically triggered by the comparisons in Box3f::isEmpty().
		# Downgrade these back to warning status.
		if gccVersion >= [ 4, 2 ] :
			env.Append( CXXFLAGS = [ "-Wno-error=strict-overflow" ] )

		if gccVersion >= [ 5, 1 ] :
			env.Append( CXXFLAGS = [ "-D_GLIBCXX_USE_CXX11_ABI=0" ] )

	env["GAFFER_PLATFORM"] = "linux"

env.Append( CXXFLAGS = [ "-std=$CXXSTD" ] )

if env["DEBUG"] :
	env.Append( CXXFLAGS = [ "-g", "-O0" ] )
else :
	env.Append( CXXFLAGS = [ "-DNDEBUG", "-DBOOST_DISABLE_ASSERTS" , "-O3" ] )

if env["BUILD_CACHEDIR"] != "" :
	CacheDir( env["BUILD_CACHEDIR"] )

###############################################################################################
# Check for inkscape and sphinx
###############################################################################################

def findOnPath( file, path ) :

	if os.path.isabs( file ) :
		return file if os.path.exists( file ) else None
	else :
		if isinstance( path, basestring ) :
			path = path.split( os.pathsep )
		for p in path :
			f = os.path.join( p, file )
			if os.path.exists( f ) :
				return f

	return None

def checkInkscape(context):
	context.Message('Checking for Inkscape... ')
	result = bool( findOnPath( context.sconf.env['INKSCAPE'], os.environ["PATH"] ) )
	context.Result(result)
	return result

def checkSphinx( context ) :

	context.Message( "Checking for Sphinx..." )
	result = bool( findOnPath( context.sconf.env["SPHINX"], context.sconf.env["ENV"]["PATH"] ) )
	context.Result( result )
	return result

def checkQtVersion( context ) :

	context.Message( "Checking for Qt..." )

	program = """
	#include <iostream>
	#include "QtCore/qconfig.h"

	int main()
	{
#ifdef QT_VERSION_MAJOR
		std::cout << QT_VERSION_MAJOR;
#else
		std::cout << 4;
#endif
		return 0;
	}
	"""

	result = context.TryRun( program, ".cpp" )
	if result[0] :
		context.sconf.env["QT_VERSION"] = result[1]

	context.Result( result[0] )
	return result[0]

conf = Configure(
	env,
	custom_tests = {
		"checkInkscape" : checkInkscape,
		"checkSphinx" : checkSphinx,
		"checkQtVersion" : checkQtVersion,
	}
)

haveInkscape = conf.checkInkscape()
if not haveInkscape and env["INKSCAPE"] != "disableGraphics" :
	sys.stderr.write( "ERROR : Inkscape not found. Check INKSCAPE build variable.\n" )
	Exit( 1 )

if not conf.checkQtVersion() :
	sys.stderr.write( "Qt not found\n" )
	Exit( 1 )

###############################################################################################
# An environment for running commands with access to the applications we've built
###############################################################################################

def split( stringOrList, separator = ":" ) :

	if isinstance( stringOrList, list ) :
		return stringOrList
	else :
		return stringOrList.split( separator )

commandEnv = env.Clone()
commandEnv["ENV"]["PATH"] = commandEnv.subst( "$BUILD_DIR/bin:" ) + commandEnv["ENV"]["PATH"]

if commandEnv["PLATFORM"]=="darwin" :
	commandEnv["ENV"]["DYLD_LIBRARY_PATH"] = commandEnv.subst( ":".join( [ "$BUILD_DIR/lib" ] + split( commandEnv["LOCATE_DEPENDENCY_LIBPATH"] ) ) )
else :
	commandEnv["ENV"]["LD_LIBRARY_PATH"] = commandEnv.subst( ":".join( [ "$BUILD_DIR/lib" ] + split( commandEnv["LOCATE_DEPENDENCY_LIBPATH"] ) ) )

commandEnv["ENV"]["PYTHONPATH"] = commandEnv.subst( ":".join( split( commandEnv["LOCATE_DEPENDENCY_PYTHONPATH"] ) ) )

def runCommand( command ) :

	command = commandEnv.subst( command )
	sys.stderr.write( command + "\n" )
	subprocess.check_call( command, shell=True, env=commandEnv["ENV"] )

###############################################################################################
# Determine python version
###############################################################################################

pythonVersion = subprocess.Popen( [ "python", "--version" ], env=commandEnv["ENV"], stderr=subprocess.PIPE ).stderr.read().strip()
pythonVersion = pythonVersion.split()[1].rpartition( "." )[0]

env["PYTHON_VERSION"] = pythonVersion

###############################################################################################
# The basic environment for building libraries
###############################################################################################

baseLibEnv = env.Clone()

baseLibEnv.Append(

	LIBS = [
		"boost_signals$BOOST_LIB_SUFFIX",
		"boost_iostreams$BOOST_LIB_SUFFIX",
		"boost_filesystem$BOOST_LIB_SUFFIX",
		"boost_date_time$BOOST_LIB_SUFFIX",
		"boost_thread$BOOST_LIB_SUFFIX",
		"boost_wave$BOOST_LIB_SUFFIX",
		"boost_regex$BOOST_LIB_SUFFIX",
		"boost_system$BOOST_LIB_SUFFIX",
		"boost_chrono$BOOST_LIB_SUFFIX",
		"tbb",
		"Imath$OPENEXR_LIB_SUFFIX",
		"IlmImf$OPENEXR_LIB_SUFFIX",
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
		"boost_python$BOOST_LIB_SUFFIX",
		"IECorePython$CORTEX_PYTHON_LIB_SUFFIX",
		"Gaffer",
	],

)

if basePythonEnv["PLATFORM"]=="darwin" :

	basePythonEnv.Append(
		CPPPATH = [ "$BUILD_DIR/lib/Python.framework/Versions/$PYTHON_VERSION/include/python$PYTHON_VERSION" ],
		LIBPATH = [ "$BUILD_DIR/lib/Python.framework/Versions/$PYTHON_VERSION/lib/python$PYTHON_VERSION/config" ],
		LIBS = [ "python$PYTHON_VERSION" ],
	)

else :

	basePythonEnv.Append(
		CPPPATH = [ "$BUILD_DIR/include/python$PYTHON_VERSION" ]
	)

###############################################################################################
# Definitions for the libraries we wish to build
###############################################################################################

vTuneRoot = env.subst("$VTUNE_ROOT")

gafferLib = {}

if os.path.exists( vTuneRoot ):
	gafferLib = {
		"envAppends" : {
			"CXXFLAGS" : [ "-isystem", "$VTUNE_ROOT/include", "-DGAFFER_VTUNE"],
			"LIBPATH" : [ "$VTUNE_ROOT/lib64" ],
			"LIBS" : [ "ittnotify" ]
		},
		"pythonEnvAppends" : {
			"CXXFLAGS" : [ "-DGAFFER_VTUNE"]
		}
	}

libraries = {

	"Gaffer" : gafferLib,

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
			"LIBS" : [ "Gaffer", "Iex$OPENEXR_LIB_SUFFIX", "IECoreGL$CORTEX_LIB_SUFFIX", "IECoreImage$CORTEX_LIB_SUFFIX", "IECoreScene$CORTEX_LIB_SUFFIX" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "IECoreImage$CORTEX_LIB_SUFFIX", "IECoreScene$CORTEX_LIB_SUFFIX", "IECoreGL$CORTEX_LIB_SUFFIX", "GafferUI", "GafferBindings" ],
			 # Prevent Qt clashing with boost::signals - we can remove
			 # this if we move to boost::signals2.
			 "CXXFLAGS" : [ "-DQT_NO_KEYWORDS" ],
		},
	},

	"GafferUITest" : {},

	"GafferDispatch" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "GafferBindings", "GafferDispatch" ],
		},
	},

	"GafferDispatchTest" : {

		"additionalFiles" : glob.glob( "python/GafferDispatchTest/*/*" ) + glob.glob( "python/GafferDispatchTest/*/*/*" ),

	},

	"GafferDispatchUI" : {},

	"GafferDispatchUITest" : {},

	"GafferCortex" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer", "GafferDispatch" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "GafferBindings", "GafferCortex", "GafferDispatch" ],
		},
	},

	"GafferCortexTest" : {
		"additionalFiles" : glob.glob( "python/GafferCortexTest/*/*" ) + glob.glob( "python/GafferCortexTest/*/*/*" ) + glob.glob( "python/GafferCortexTest/images/*" ),
	},

	"GafferCortexUI" : {},

	"GafferCortexUITest" : {},

	"GafferScene" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer", "Iex$OPENEXR_LIB_SUFFIX", "IECoreGL$CORTEX_LIB_SUFFIX", "IECoreAlembic$CORTEX_LIB_SUFFIX", "IECoreImage$CORTEX_LIB_SUFFIX",  "IECoreScene$CORTEX_LIB_SUFFIX", "GafferImage", "GafferDispatch" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "GafferBindings", "GafferScene", "GafferDispatch", "IECoreScene$CORTEX_LIB_SUFFIX" ],
		},
		"additionalFiles" : glob.glob( "glsl/*.frag" ) + glob.glob( "glsl/*.vert" ),
	},

	"GafferSceneTest" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer", "GafferDispatch", "GafferScene", "IECoreScene$CORTEX_LIB_SUFFIX" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "Gaffer", "GafferDispatch", "GafferBindings", "GafferScene", "GafferSceneTest" ],
		},
		"additionalFiles" : glob.glob( "python/GafferSceneTest/*/*" ),
	},

	"GafferSceneUI" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer", "GafferUI", "GafferImage", "GafferImageUI", "GafferScene", "Iex$OPENEXR_LIB_SUFFIX", "IECoreGL$CORTEX_LIB_SUFFIX", "IECoreImage$CORTEX_LIB_SUFFIX", "IECoreScene$CORTEX_LIB_SUFFIX" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "IECoreGL$CORTEX_LIB_SUFFIX", "GafferBindings", "GafferScene", "GafferUI", "GafferImageUI", "GafferSceneUI" ],
		},
	},

	"GafferSceneUITest" : {},

	"GafferImage" : {
		"envAppends" : {
			"CPPPATH" : [ "$BUILD_DIR/include/freetype2" ],
			"LIBS" : [ "Gaffer", "GafferDispatch", "Iex$OPENEXR_LIB_SUFFIX", "IECoreImage$CORTEX_LIB_SUFFIX", "OpenImageIO$OIIO_LIB_SUFFIX", "OpenColorIO$OCIO_LIB_SUFFIX", "freetype" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "GafferBindings", "GafferImage", "GafferDispatch", "IECoreImage$CORTEX_LIB_SUFFIX", ],
		},
	},

	"GafferImageTest" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer", "GafferImage", "OpenImageIO$OIIO_LIB_SUFFIX",  ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "GafferImageTest", "GafferImage" ],
		},
		"additionalFiles" : glob.glob( "python/GafferImageTest/scripts/*" ) + glob.glob( "python/GafferImageTest/images/*" ) + glob.glob( "python/GafferImageTest/openColorIO/luts/*" ) + glob.glob( "python/GafferImageTest/openColorIO/*" ),
	},

	"GafferImageUITest" : {},

	"GafferImageUI" : {
		"envAppends" : {
			"LIBS" : [ "IECoreGL$CORTEX_LIB_SUFFIX", "Gaffer", "GafferImage", "GafferUI" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "GafferUI", "GafferImage", "GafferImageUI" ],
		},
	},

	"GafferArnold" : {
		"envAppends" : {
			"CPPPATH" : [ "$ARNOLD_ROOT/include" ],
			"LIBPATH" : [ "$ARNOLD_ROOT/bin" ],
			"LIBS" : [ "Gaffer", "GafferScene", "GafferDispatch", "ai", "GafferVDB", "openvdb",  "IECoreScene$CORTEX_LIB_SUFFIX", "IECoreArnold$CORTEX_LIB_SUFFIX", "GafferOSL" ],
		},
		"pythonEnvAppends" : {
			"CPPPATH" : [ "$ARNOLD_ROOT/include" ],
			"LIBPATH" : [ "$ARNOLD_ROOT/bin" ],
			"LIBS" : [ "Gaffer", "GafferScene", "GafferBindings", "GafferVDB", "GafferDispatch", "GafferArnold", "GafferOSL" ],
		},
		"requiredOptions" : [ "ARNOLD_ROOT" ],
		"additionalFiles" : [ "arnold/plugins/gaffer.mtd" ],
	},

	"GafferArnoldTest" : {
		"additionalFiles" : glob.glob( "python/GafferArnoldTest/volumes/*" ) + glob.glob( "python/GafferArnoldTest/metadata/*" ),
	},

	"GafferArnoldUI" : {
		"envAppends" : {
			"LIBS" : [ "IECoreScene$CORTEX_LIB_SUFFIX", "IECoreGL$CORTEX_LIB_SUFFIX", "GafferOSL", "GafferSceneUI" ],
			},
		"pythonEnvAppends" : {
			"LIBS" : [ "GafferArnoldUI", "GafferSceneUI" ],
		},
	},

	"GafferArnoldUITest" : {},

	"GafferOSL" : {
		"envAppends" : {
			"CPPPATH" : [ "$OSLHOME/include/OSL" ],
			"LIBS" : [ "Gaffer", "GafferScene", "GafferImage", "OpenImageIO$OIIO_LIB_SUFFIX", "oslquery$OSL_LIB_SUFFIX", "oslexec$OSL_LIB_SUFFIX", "Iex$OPENEXR_LIB_SUFFIX", "IECoreImage$CORTEX_LIB_SUFFIX", "IECoreScene$CORTEX_LIB_SUFFIX" ],
		},
		"pythonEnvAppends" : {
			"CPPPATH" : [ "$OSLHOME/include/OSL" ],
			"LIBS" : [ "GafferBindings", "GafferScene", "GafferImage", "GafferOSL", "Iex$OPENEXR_LIB_SUFFIX" ],
		},
		"oslHeaders" : glob.glob( "shaders/*/*.h" ),
		"oslShaders" : glob.glob( "shaders/*/*.osl" ),
	},

	"GafferOSLUI" : {},

	"GafferOSLTest" : {
		"additionalFiles" : glob.glob( "python/GafferOSLTest/*/*" ),
	},

	"GafferOSLUITest" : {},

	"GafferDelight" : {
		"envAppends" : {
			"CPPPATH" : [ "$DELIGHT_ROOT/include" ],
			"LIBS" : [ "Gaffer", "GafferScene", "GafferDispatch", "IECoreScene$CORTEX_LIB_SUFFIX", "3delight" ],
			"LIBPATH" : [ "$DELIGHT_ROOT/lib" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "GafferBindings", "GafferScene", "GafferDispatch", "GafferDelight" ],
			"LIBPATH" : [ "$DELIGHT_ROOT/lib" ],
		},
		"requiredOptions" : [ "DELIGHT_ROOT" ],
	},

	"GafferDelightTest" : {},

	"GafferDelightUI" : {},

	"GafferDelightUITest" : {},

	"GafferAppleseed" : {
		"envAppends" : {
			"CXXFLAGS" : [ "-isystem", "$APPLESEED_ROOT/include", "-DAPPLESEED_ENABLE_IMATH_INTEROP", "-DAPPLESEED_USE_SSE" ],
			"LIBPATH" : [ "$APPLESEED_ROOT/lib" ],
			"LIBS" : [ "Gaffer", "GafferDispatch", "GafferScene", "appleseed",  "IECoreScene$CORTEX_LIB_SUFFIX", "IECoreAppleseed$CORTEX_LIB_SUFFIX", "OpenImageIO$OIIO_LIB_SUFFIX", "oslquery$OSL_LIB_SUFFIX" ],
		},
		"pythonEnvAppends" : {
			"CXXFLAGS" : [ "-isystem", "$APPLESEED_ROOT/include", "-DAPPLESEED_ENABLE_IMATH_INTEROP", "-DAPPLESEED_USE_SSE" ],
			"LIBPATH" : [ "$APPLESEED_ROOT/lib" ],
			"LIBS" : [ "Gaffer", "GafferDispatch", "GafferScene", "GafferBindings", "GafferAppleseed" ],
		},
		"requiredOptions" : [ "APPLESEED_ROOT" ],
	},

	"GafferAppleseedTest" : {
		"additionalFiles" : glob.glob( "python/GafferAppleseedTest/*/*" ),
	},

	"GafferAppleseedUI" : {},

	"GafferAppleseedUITest" : {},

	"GafferTractor" : {},

	"GafferTractorTest" : {},

	"GafferTractorUI" : {},

	"GafferTractorUITest" : {},

	"GafferVDB" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer", "GafferScene", "Half", "openvdb", "IECoreScene$CORTEX_LIB_SUFFIX" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "GafferScene", "GafferVDB", "openvdb", "IECoreScene$CORTEX_LIB_SUFFIX"],
		}
	},

	"GafferVDBTest" : {
		"additionalFiles" : glob.glob( "python/GafferVDBTest/*/*" ),
	},

	"GafferVDBUI" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer", "GafferScene", "GafferSceneUI", "IECoreScene$CORTEX_LIB_SUFFIX", "IECoreGL$CORTEX_LIB_SUFFIX", "GafferVDB", "openvdb" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "GafferScene", "GafferVDB", "GafferVDBUI", "openvdb" ],
		}
	},

	"GafferVDBUITest" : {
		"additionalFiles" : glob.glob( "python/GafferVDBUITest/*/*" ),
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

			# files
			( "SequenceLsOp", "ops/files/sequenceLs" ),
			( "SequenceCpOp", "ops/files/sequenceCopy" ),
			( "SequenceMvOp", "ops/files/sequenceMove" ),
			( "SequenceRmOp", "ops/files/sequenceRemove" ),
			( "SequenceRenumberOp", "ops/files/sequenceRenumber" ),
			( "SequenceConvertOp", "ops/files/sequenceConvert" ),

		],

	},

	"IECoreScene" : {

		"classStubs" : [

			( "ReadProcedural", "procedurals/read" ),

		],

	},

}

# Add on OpenGL libraries to definitions - these vary from platform to platform
for library in ( "GafferUI", "GafferScene", "GafferSceneUI", "GafferImageUI" ) :
	if env["PLATFORM"] == "darwin" :
		libraries[library]["envAppends"].setdefault( "FRAMEWORKS", [] ).append( "OpenGL" )
	else :
		libraries[library]["envAppends"]["LIBS"].append( "GL" )
	libraries[library]["envAppends"]["LIBS"].append( "GLEW$GLEW_LIB_SUFFIX" )

# Add on Qt libraries to definitions - these vary from platform to platform

def addQtLibrary( library, qtLibrary ) :

	if env["PLATFORM"] == "darwin" :
		libraries[library]["pythonEnvAppends"].setdefault( "FRAMEWORKS", [] ).append( "Qt" + qtLibrary )
	else :
		prefix = "Qt" if int( env["QT_VERSION"] ) < 5 else "Qt${QT_VERSION}"
		libraries[library]["pythonEnvAppends"]["LIBS"].append( prefix + qtLibrary )

for library in ( "GafferUI", ) :
	addQtLibrary( library, "Core" )
	addQtLibrary( library, "Gui" )
	addQtLibrary( library, "OpenGL" )
	if int( env["QT_VERSION"] ) > 4 :
		addQtLibrary( library, "Widgets" )


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

	sedSubstitutions = "s/!GAFFER_MILESTONE_VERSION!/$GAFFER_MILESTONE_VERSION/g"
	sedSubstitutions += "; s/!GAFFER_MAJOR_VERSION!/$GAFFER_MAJOR_VERSION/g"
	sedSubstitutions += "; s/!GAFFER_MINOR_VERSION!/$GAFFER_MINOR_VERSION/g"
	sedSubstitutions += "; s/!GAFFER_PATCH_VERSION!/$GAFFER_PATCH_VERSION/g"

	headers = (
		glob.glob( "include/" + libraryName + "/*.h" ) +
		glob.glob( "include/" + libraryName + "/*.inl" ) +
		glob.glob( "include/" + libraryName + "/*/*.h" ) +
		glob.glob( "include/" + libraryName + "/*/*.inl" )
	)

	for header in headers :
		headerInstall = env.Command( "$BUILD_DIR/" + header, header, "sed \"" + sedSubstitutions + "\" $SOURCE > $TARGET" )
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
		if pythonModuleEnv["PLATFORM"] == "darwin" :
			# On OSX, we must build Python modules with the ".so"
			# prefix rather than the ".dylib" you might expect.
			# This is done by changing the SHLIBSUFFIX variable.
			# But this causes a problem with SCons' automatic
			# scanning for the library dependencies of those modules,
			# because by default it expects the libraries to end in
			# "$SHLIBSUFFIX". So we must also explicitly add
			# the original value of SHLIBSUFFIX (.dylib) to the
			# LIBSUFFIXES variable used by the library scanner.
			pythonModuleEnv["LIBSUFFIXES"].append( pythonModuleEnv.subst( "$SHLIBSUFFIX" ) )
			pythonModuleEnv["SHLIBSUFFIX"] = ".so"

		pythonModule = pythonModuleEnv.SharedLibrary( "python/" + libraryName + "/_" + libraryName, pythonModuleSource )
		pythonModuleEnv.Default( pythonModule )

		moduleInstall = pythonModuleEnv.Install( "$BUILD_DIR/python/" + libraryName, pythonModule )
		pythonModuleEnv.Alias( "build", moduleInstall )

	# python component of python module

	pythonFiles = glob.glob( "python/" + libraryName + "/*.py" ) + glob.glob( "python/" + libraryName + "/*/*.py" )
	for pythonFile in pythonFiles :
		pythonFileInstall = env.Command( "$BUILD_DIR/" + pythonFile, pythonFile, "sed \"" + sedSubstitutions + "\" $SOURCE > $TARGET" )
		env.Alias( "build", pythonFileInstall )

	# additional files

	for additionalFile in libraryDef.get( "additionalFiles", [] ) :
		if additionalFile in pythonFiles :
			continue
		additionalFileInstall = env.InstallAs( "$BUILD_DIR/" + additionalFile, additionalFile )
		env.Alias( "build", additionalFileInstall )

	# osl headers

	for oslHeader in libraryDef.get( "oslHeaders", [] ) :
		oslHeaderInstall = env.InstallAs( "$BUILD_DIR/" + oslHeader, oslHeader )
		env.Alias( "oslHeaders", oslHeaderInstall )
		env.Alias( "build", oslHeaderInstall )

	# osl shaders

	def buildOSL( target, source, env ) :

		subprocess.check_call( [ "oslc", "-I./shaders", "-o", str( target[0] ), str( source[0] ) ], env = env["ENV"] )

	for oslShader in libraryDef.get( "oslShaders", [] ) :
		oslShaderInstall = env.InstallAs( "$BUILD_DIR/" + oslShader, oslShader )
		env.Alias( "build", oslShader )
		compiledFile = commandEnv.Command( os.path.splitext( str( oslShaderInstall[0] ) )[0] + ".oso", oslShader, buildOSL )
		env.Depends( compiledFile, "oslHeaders" )
		env.Alias( "build", compiledFile )

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

	svgFileName = os.path.abspath( str( source[0] ) )

	dir = os.path.dirname( os.path.abspath( str( target[0] ) ) )
	if not os.path.isdir( dir ) :
		os.makedirs( dir )

	queryCommand = env["INKSCAPE"] + " --query-all \"" + svgFileName + "\""
	inkscape = subprocess.Popen( queryCommand, stdout=subprocess.PIPE, shell=True )
	objects, stderr = inkscape.communicate()
	if inkscape.returncode :
		raise subprocess.CalledProcessError( inkscape.returncode, queryCommand )

	for object in objects.split( "\n" ) :
		tokens = object.split( "," )
		if tokens[0].startswith( "forExport:" ) :
			subprocess.check_call(
				env["INKSCAPE"] + " --export-png=%s/%s.png --export-id=%s --export-width=%d --export-height=%d %s --export-background-opacity=0" % (
					dir,
					tokens[0].split( ":" )[-1],
					tokens[0],
					int( round( float( tokens[3] ) ) ), int( round( float( tokens[4] ) ) ),
					svgFileName,
				),
				shell = True,
			)

if haveInkscape :

	for source, target in (
		( "resources/graphics.svg", "arrowDown10.png" ),
		( "resources/GafferLogo.svg", "GafferLogo.png" ),
		( "resources/GafferLogoMini.svg", "GafferLogoMini.png" ),
	) :

		graphicsBuild = env.Command( os.path.join( "$BUILD_DIR/graphics/", target ), source, buildGraphics )
		env.NoCache( graphicsBuild )
		env.Alias( "build", graphicsBuild )

else :

	sys.stderr.write( "WARNING : Inkscape not found - not building graphics. Check INKSCAPE build variable.\n" )

#########################################################################################################
# Resources
#########################################################################################################

resources = None
if commandEnv.subst( "$LOCATE_DEPENDENCY_RESOURCESPATH" ) :
	resources = commandEnv.Install( "$BUILD_DIR", "$LOCATE_DEPENDENCY_RESOURCESPATH" )
	commandEnv.NoCache( resources )
	commandEnv.Alias( "build", resources )

#########################################################################################################
# Documentation
#########################################################################################################

def buildDocs( target, source, env ) :

	# This is a little bit tricky. We need Gaffer itself to build the
	# docs, because we autogenerate the node reference from the node metadata.
	# And we also need sphinx, but `sphinx_build` starts with `#!/usr/bin/python`,
	# which may not be compatible with Gaffer's built-in python. So, we locate
	# the modules sphinx needs upfront, and make sure they're on the PYTHONPATH,
	# then we use `gaffer env python` to launch Gaffer's python, and generate
	# all the docs in that environment.

	for module in ( "sphinx", "markupsafe", "CommonMark", "pytz" ) :
		if not findOnPath( module, env["ENV"]["PYTHONPATH"] ) :
			try :
				m = __import__( module )
				env["ENV"]["PYTHONPATH"] = env["ENV"]["PYTHONPATH"] + ":" + os.path.dirname( m.__path__[0] )
			except ImportError :
				pass

	# Ensure that Arnold, Appleseed and 3delight are available in the documentation
	# environment.

	libraryPathEnvVar = "DYLD_LIBRARY_PATH" if commandEnv["PLATFORM"]=="darwin" else "LD_LIBRARY_PATH"

	if env.subst( "$ARNOLD_ROOT" ) :
		env["ENV"]["PATH"] += ":" + env.subst( "$ARNOLD_ROOT/bin" )
		env["ENV"]["PYTHONPATH"] += ":" + env.subst( "$ARNOLD_ROOT/python" )
		env["ENV"][libraryPathEnvVar] += ":" + env.subst( "$ARNOLD_ROOT/bin" )

	if env.subst( "$APPLESEED_ROOT" ) and env["APPLESEED_ROOT"] != "$BUILD_DIR/appleseed" :
		env["ENV"]["PATH"] += ":" + env.subst( "$APPLESEED_ROOT/bin" )
		env["ENV"][libraryPathEnvVar] += ":" + env.subst( "$APPLESEED_ROOT/lib" )
		env["ENV"]["OSLHOME"] = env.subst( "$OSLHOME" )
		env["ENV"]["OSL_SHADER_PATHS"] = env.subst( "$APPLESEED_ROOT/shaders/gaffer" )
		env["ENV"]["APPLESEED_SEARCHPATH"] = env.subst( "$APPLESEED_ROOT/shaders/gaffer:$LOCATE_DEPENDENCY_APPLESEED_SEARCHPATH" )

	# Run any python scripts we find in the document source tree. These are
	# used to autogenerate source files for processing by sphinx.

	for root, dirs, files in os.walk( str( source[0] ) ) :
		for f in files :
			ext = os.path.splitext( f )[1]
			command = []
			if ext == ".py" :
				command = [ "gaffer", "env", "python", f ]
			elif ext == ".sh" :
				command = [ "gaffer", "env", "./" + f ]
			if command :
				sys.stdout.write( "Running {0}\n".format( os.path.join( root, f ) ) )
				subprocess.check_call( command, cwd = root, env = env["ENV"] )

	# Run sphinx to generate the final documentation.

	subprocess.check_call(
		[
			"gaffer", "env", "python",
			findOnPath( env.subst( "$SPHINX" ), env["ENV"]["PATH"] ),
			"-b", "html",
			str( source[0] ), os.path.dirname( str( target[0] ) )
		],
		env = env["ENV"]
	)

if conf.checkSphinx() :

	docs = commandEnv.Command( "$BUILD_DIR/doc/gaffer/html/index.html", "doc/source", buildDocs )
	commandEnv.Depends( docs, "build" )
	if resources is not None :
		commandEnv.Depends( docs, resources )
	commandEnv.AlwaysBuild( docs )
	commandEnv.NoCache( docs )
	commandEnv.Alias( "docs", docs )

else :

	sys.stderr.write( "WARNING : Sphinx not found - not building docs. Check SPHINX build variable.\n" )

#########################################################################################################
# Installation
#########################################################################################################

def installer( target, source, env ) :

	shutil.copytree( str( source[0] ), str( target[0] ), symlinks=True )

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

	if env["INSTALL_POST_COMMAND"] != "" :
		# this is the only way we could find to get a post action to run for an alias
		env.Alias( "install", install, "$INSTALL_POST_COMMAND" )

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

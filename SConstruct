##########################################################################
#
#  Copyright (c) 2011-2014, John Haddon. All rights reserved.
#  Copyright (c) 2011-2014, Image Engine Design Inc. All rights reserved.
#  Copyright 2019, Hypothetical Inc. All rights reserved.
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
import locale
import platform
import shutil
import subprocess
import distutils.dir_util

EnsureSConsVersion( 3, 0, 2 ) # Substfile is a default builder as of 3.0.2

if locale.getpreferredencoding() != "UTF-8" :
	# The `Substfile` builder uses `open()` without specifying an encoding, and
	# so gets Python's default encoding. Unless this is `UTF-8`, any `.py` files
	# containing unicode characters will be corrupted during installation.
	sys.stderr.write( "ERROR : Preferred encoding must be 'UTF-8'. Set PYTHONUTF8 environment variable before running `scons`.\n" )
	Exit( 1 )

###############################################################################################
# Version
###############################################################################################

gafferMilestoneVersion = 1 # for announcing major milestones - may contain all of the below
gafferMajorVersion = 2 # backwards-incompatible changes
gafferMinorVersion = 2 # new backwards-compatible features
gafferPatchVersion = 0 # bug fixes
gafferVersionSuffix = "" # used for alpha/beta releases : "a1", "b2", etc.

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
	{"darwin" : "clang++", "win32" : "cl"}.get(sys.platform, "g++")
)

options.Add(
	"CXXFLAGS",
	"The extra flags to pass to the C++ compiler during compilation.",
	# We want `-Wextra` because some of its warnings are useful, and further useful
	# warnings may be added in future. But it does introduce warnings we find unhelpful - see
	# the compiler sections below where we turn them back off again.
	[ "-pipe", "-Wall", "-Wextra" ] if Environment()["PLATFORM"] != "win32" else [],
)

options.Add(
	EnumVariable(
		"BUILD_TYPE",
		"Optimisation and debug symbol configuration",
		"RELEASE",
		allowed_values = ('RELEASE', 'DEBUG', 'RELWITHDEBINFO')
	)
)

options.Add(
	"CXXSTD",
	"The C++ standard to build against. A minimum of C++17 is required.",
	"c++17",
)

options.Add(
	BoolVariable( "WARNINGS_AS_ERRORS", "Treat compiler and linker warnings as errors.", True )
)

options.Add(
	"LINKFLAGS",
	"The extra flags to pass to the C++ linker during compilation.",
	""
)

options.Add(
	BoolVariable( "ASAN", "Enable ASan when compiling with clang++", False)
)

options.Add(
	"BUILD_DIR",
	"The destination directory in which the build will be made.",
	os.path.join( ".", "build", "gaffer-${GAFFER_MILESTONE_VERSION}.${GAFFER_MAJOR_VERSION}.${GAFFER_MINOR_VERSION}.${GAFFER_PATCH_VERSION}${GAFFER_VERSION_SUFFIX}-${GAFFER_PLATFORM}" ),
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
	os.path.join( ".", "install", "gaffer-${GAFFER_MILESTONE_VERSION}.${GAFFER_MAJOR_VERSION}.${GAFFER_MINOR_VERSION}.${GAFFER_PATCH_VERSION}${GAFFER_VERSION_SUFFIX}-${GAFFER_PLATFORM}" ),
)

options.Add(
	"PACKAGE_FILE",
	"The file in which the final gaffer file will be created by the package target.",
	"${INSTALL_DIR}.tar.gz" if sys.platform != "win32" else "${INSTALL_DIR}.zip",
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
	os.path.join( "$BUILD_DIR", "appleseed" ),
)

options.Add(
	"CYCLES_ROOT",
	"The directory in which Cycles is installed. Used to build GafferCycles",
	os.path.join( "$BUILD_DIR", "cycles" ),
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
	"BOOST_PYTHON_LIB_SUFFIX",
	"The suffix appended to the names of the python boost libraries. "
	"You can modify this so that the correct python library name is used, "
	"likely related to the specific python version.",
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

options.Add(
	"VDB_LIB_SUFFIX",
	"The suffix used when locating the OpenVDB libraries.",
	"",
)

options.Add(
	"USD_LIB_PREFIX",
	"The prefix to prepend to the names of the USD libraries. You can modify this "
	"to link against libraries installed with non-default names. "
	"Should match the USD build option PXR_LIB_PREFIX",
	"usd_"
)

# general variables

options.Add(
	BoolVariable(
		"GAFFERCORTEX",
		"Builds and installs the GafferCortex modules. These are deprecated and will "
		"be removed completely in a future version.",
		False
	)
)

options.Add(
	BoolVariable(
		"GAFFERUSD",
		"Builds and installs the GafferUSD modules.",
		True
	)
)

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
	"PYBIND11",
	"The directory in which pybind11 is installed."
	"",
)

options.Add(
	"INSTALL_POST_COMMAND",
	"A command which is run following a successful install process. "
	"This could be used to customise installation further for a "
	"particular site.",
	"",
)

options.Add( "GAFFER_MILESTONE_VERSION", "Milestone version", str( gafferMilestoneVersion ) )
options.Add( "GAFFER_MAJOR_VERSION", "Major version", str( gafferMajorVersion ) )
options.Add( "GAFFER_MINOR_VERSION", "Minor version", str( gafferMinorVersion ) )
options.Add( "GAFFER_PATCH_VERSION", "Patch version", str( gafferPatchVersion ) )
options.Add( "GAFFER_VERSION_SUFFIX", "Version suffix", str( gafferVersionSuffix ) )

###############################################################################################
# Basic environment object. All the other environments will be based on this.
###############################################################################################

###########################################################################################
# All platforms
###########################################################################################

env = Environment(

	options = options,

	CPPDEFINES = [
		( "BOOST_FILESYSTEM_VERSION", "3" ),
		"BOOST_FILESYSTEM_NO_DEPRECATED",
		# Boost has deprecated `boost/bind.hpp` in favour of
		# `boost/bind/bind.hpp`, and we have updated our code accordingly. But
		# `boost::python` and others are still using the deprecated header,
		# so we define BOOST_BIND_GLOBAL_PLACEHOLDERS to silence the reams of
		# warnings triggered by that.
		"BOOST_BIND_GLOBAL_PLACEHOLDERS",
	],

	CPPPATH = [
		"include",
		"$LOCATE_DEPENDENCY_CPPPATH",
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

systemIncludeArgument = "/external:I" if env[ "PLATFORM" ] == "win32" else "-isystem"

for path in [
		"$BUILD_DIR/include",
		"$BUILD_DIR/include/OpenEXR",
		"$BUILD_DIR/include/GL",
	] + env["LOCATE_DEPENDENCY_SYSTEMPATH"] :

	env.Append(
		CXXFLAGS = [ systemIncludeArgument, path ]
	)

env["BUILD_DIR"] = os.path.abspath( env["BUILD_DIR"] )

for e in env["ENV_VARS_TO_IMPORT"].split() :
	if e in os.environ :
		env["ENV"][e] = os.environ[e]

###########################################################################################
# POSIX configuration
###########################################################################################

if env["PLATFORM"] != "win32" :

	# DISPLAY and HOME are essential for running gaffer when generating
	# the documentation. TERM is needed to get coloured output from the
	# compiler.
	for e in [ "DISPLAY", "HOME", "TERM" ] :
		if e in os.environ :
			env["ENV"][e] = os.environ[e]

	# Platform-specific config

	if env["PLATFORM"] == "darwin" :

		env.Append( CXXFLAGS = [ "-D__USE_ISOC99" ] )
		env["GAFFER_PLATFORM"] = "macos"

	else :

		env["GAFFER_PLATFORM"] = "linux"

	# Compiler-specific config

	if "clang++" in os.path.basename( env["CXX"] ) :

		env.Append(
			CXXFLAGS = [ "-Wno-unused-local-typedef" ]
		)

		# Turn off the parts of `-Wextra` that we don't like.
		env.Append( CXXFLAGS = [ "-Wno-unused-parameter" ] )

	elif "g++" in os.path.basename( env["CXX"] ) :

		# Get GCC version.
		gccVersion = subprocess.check_output( [ env["CXX"], "-dumpversion" ], env=env["ENV"], universal_newlines=True ).strip()
		if "." not in gccVersion :
			# GCC 7 onwards requires `-dumpfullversion` to get minor/patch, but this
			# flag does not exist on earlier GCCs, where minor/patch was provided by `-dumpversion`.
			gccVersion = subprocess.check_output( [ env["CXX"], "-dumpfullversion" ], env=env["ENV"], universal_newlines=True ).strip()
		gccVersion = [ int( v ) for v in gccVersion.split( "." ) ]

		# GCC emits spurious "assuming signed overflow does not occur"
		# warnings, typically triggered by the comparisons in Box3f::isEmpty().
		# Downgrade these back to warning status.
		if gccVersion >= [ 4, 2 ] :
			env.Append( CXXFLAGS = [ "-Wno-error=strict-overflow" ] )

		if gccVersion >= [ 5, 1 ] and gccVersion < [ 11, 2 ] :
			env.Append( CXXFLAGS = [ "-D_GLIBCXX_USE_CXX11_ABI=0" ] )

		if gccVersion >= [ 9, 2 ] :
			env.Append( CXXFLAGS = [ "-Wsuggest-override" ] )

		# Turn off the parts of `-Wextra` that we don't like.
		env.Append( CXXFLAGS = [ "-Wno-cast-function-type", "-Wno-unused-parameter" ] )

		env.Append(
			CXXFLAGS = [ "-pthread" ],
			SHLINKFLAGS = [ "-pthread", "-Wl,--no-undefined" ],
		)

	# Shared config

	env.Append( CXXFLAGS = [ "-std=$CXXSTD", "-fvisibility=hidden" ] )

	if env["BUILD_TYPE"] == "DEBUG" :
		env.Append( CXXFLAGS = ["-g", "-O0", "-DTBB_USE_DEBUG=1"] )
	elif env["BUILD_TYPE"] == "RELEASE" :
		env.Append( CXXFLAGS = ["-DNDEBUG", "-DBOOST_DISABLE_ASSERTS", "-O3"] )
	elif env["BUILD_TYPE"] == "RELWITHDEBINFO" :
		env.Append( CXXFLAGS = ["-DNDEBUG", "-DBOOST_DISABLE_ASSERTS", "-O3", "-g", "-fno-omit-frame-pointer"] )

	if env["WARNINGS_AS_ERRORS"] :
		env.Append(
			CXXFLAGS = [ "-Werror" ],
			SHLINKFLAGS = [ "-Wl,-fatal_warnings" ],
		)

###########################################################################################
# Windows configuration
###########################################################################################

else:
	env.Append(
		CXXFLAGS = [
			"/nologo",  # Suppress startup banner
			"/DOPENEXR_DLL",  # Link to dynamic OpenEXR library
			"/DNOMINMAX",  # Suppress compiler definition of `min` and `max`
			"/D__PRETTY_FUNCTION__=__FUNCSIG__",
			"/DBOOST_ALL_DYN_LINK",
			"/DBOOST_ALL_NO_LIB",
			"/W4",  # Warning level 4, one level less than all warnings
			"/experimental:external",  # Allow use of /external:I
			"/external:W0",  # Suppress warnings for headers included with /external:I
			"/Zc:inline", # Remove unreferenced function or data if it is COMDAT or has internal linkage only
			"/GR", # Enable RTTI
			"/TP", # Treat all files as c++ (vs C)
			"/FC", # Display full paths in diagnostics
			"/EHsc", # Catch c++ exceptions only
			"/MP",  # Enable multiprocessing of builds
			"/permissive-", # Disable permissive mode, which also enables standard compliant two phase name lookup
			"/D_USE_MATH_DEFINES",  # Required when permissive mode is off, for defining constants like M_PI used by OpenVDB
			"/std:$CXXSTD",
			"/DHAVE_SNPRINTF",  # Fix a legacy issue for MSVC versions < 2019
		]
	)

	if env["WARNINGS_AS_ERRORS"] :
		env.Append(
			CXXFLAGS = [
				"/WX",  # Treat warnings as errors
				"/wd4100",  # Suppress warning about unused parameters
				"/wd4706",	# Suppress warning about using assignment in conditionals
				"/wd4267",  # Suppress warning about conversion from int to size_t
				"/wd4244",  # Suppress warning about possible loss of data in type conversion
				"/wd4305",  # Suppress warning about conversion from double to float
				"/D_CRT_SECURE_NO_WARNINGS",  # Suppress warnings about getenv and similar
			],
		)

	if env["BUILD_TYPE"] == "DEBUG" :
		env.Append(
			CXXFLAGS =
			[
				"/O0",
				"/Zi",
				"/MDd",
				"/DBOOST_DISABLE_ASSERTS",
				"/bigobj",
			],
			CCPDBFLAGS=
			[
				"/Zi",
				"/Fd${TARGET}.pdb",
			],
		)
	elif env["BUILD_TYPE"] == "RELEASE" :
		env.Append(
			CXXFLAGS =
			[
				"/DNDEBUG",
				"/MD",	# create multithreaded DLL
				"/DBOOST_DISABLE_ASSERTS",
				"/O2",
				# /Og optimization (included via /O2) generates lots of unreachable
				# code warnings from boost::intrusive_ptr. Disabled in release build only.
				"/wd4702"
			]
		)
	elif env["BUILD_TYPE"] == "RELWITHDEBINFO" :
		env.Append(
			CXXFLAGS =
			[
				"/DNDEBUG",
				"/MD",
				"/bigobj",
				"/DBOOST_DISABLE_ASSERTS",
				"/Zi",
			],
			LINKFLAGS =
			[
				"/DEBUG",
			],
			CCPDBFLAGS=
			[
				"/Zi",
				"/Fd${TARGET}.pdb",
			],
		)


if env["BUILD_CACHEDIR"] != "" :
	CacheDir( env["BUILD_CACHEDIR"] )

###############################################################################################
# Check for inkscape and sphinx
###############################################################################################

def findOnPath( file, path ) :

	if os.path.isabs( file ) :
		return file if os.path.exists( file ) else None
	else :
		if isinstance( path, str ) :
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

inkscapeHelp = subprocess.check_output( [ env["INKSCAPE"], "--help" ], universal_newlines=True )
env["INKSCAPE_USE_EXPORT_FILENAME"] = True if "--export-filename" in inkscapeHelp else False

haveSphinx = conf.checkSphinx()

if not conf.checkQtVersion() :
	sys.stderr.write( "Qt not found\n" )
	Exit( 1 )

if env["ASAN"] :
	env.Append(
		CXXFLAGS = [ "-fsanitize=address" ],
		LINKFLAGS = [ "-fsanitize=address" ],
	)
	if "clang++" in os.path.basename( env["CXX"] ) :
		env.Append(
			CXXFLAGS = [ "-shared-libasan" ],
			LINKFLAGS = [ "-shared-libasan" ],
		)

###############################################################################################
# An environment for running commands with access to the applications we've built
###############################################################################################

def split( stringOrList, separator = os.path.pathsep ) :

	if isinstance( stringOrList, list ) :
		return stringOrList
	else :
		return stringOrList.split( separator )

commandEnv = env.Clone()
commandEnv["ENV"]["PATH"] = commandEnv.subst( "$BUILD_DIR/bin" + os.path.pathsep ) + commandEnv["ENV"]["PATH"]
if env["PLATFORM"] == "win32" :
	commandEnv["ENV"]["PATH"] = commandEnv.subst( "$BUILD_DIR/lib" + os.path.pathsep ) + commandEnv["ENV"]["PATH"]

if commandEnv["PLATFORM"]=="darwin" :
	commandEnv["ENV"]["DYLD_LIBRARY_PATH"] = commandEnv.subst( ":".join(
		[ "/System/Library/Frameworks/ImageIO.framework/Resources", "$BUILD_DIR/lib" ] +
		split( commandEnv["LOCATE_DEPENDENCY_LIBPATH"] )
	) )
elif commandEnv["PLATFORM"] == "win32" :
	commandEnv["ENV"]["PATH"] = commandEnv.subst( ";".join( [ "$BUILD_DIR/lib" ] + split( commandEnv[ "LOCATE_DEPENDENCY_LIBPATH" ] ) + [ commandEnv["ENV"]["PATH"] ] ) )
else:
	commandEnv["ENV"]["LD_LIBRARY_PATH"] = commandEnv.subst( ":".join( [ "$BUILD_DIR/lib" ] + split( commandEnv["LOCATE_DEPENDENCY_LIBPATH"] ) ) )

commandEnv["ENV"]["PYTHONPATH"] = commandEnv.subst( os.path.pathsep.join( split( commandEnv["LOCATE_DEPENDENCY_PYTHONPATH"] ) ) )

# SIP on MacOS prevents DYLD_LIBRARY_PATH being passed down so we make sure
# we also pass through to gaffer the other base vars it uses to populate paths
# for third-party support.
for v in ( 'ARNOLD_ROOT', 'DELIGHT_ROOT' ) :
	commandEnv["ENV"][ v ] = commandEnv[ v ]

def runCommand( command ) :

	command = commandEnv.subst( command )
	sys.stderr.write( command + "\n" )
	return subprocess.check_output( command, shell=True, env=commandEnv["ENV"], universal_newlines=True )

###############################################################################################
# The basic environment for building libraries
###############################################################################################

baseLibEnv = env.Clone()

baseLibEnv.Append(

	LIBS = [
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

# Determine boost version

boostVersionHeader = baseLibEnv.FindFile(
	"boost/version.hpp",
	[ "$BUILD_DIR/include" ] +
	baseLibEnv["LOCATE_DEPENDENCY_SYSTEMPATH"] +
	baseLibEnv["LOCATE_DEPENDENCY_CPPPATH"]
)

if not boostVersionHeader :
	sys.stderr.write( "ERROR : unable to find \"boost/version.hpp\".\n" )
	Exit( 1 )

with open( str( boostVersionHeader ) ) as f :
	for line in f.readlines() :
		m = re.match( "^#define BOOST_LIB_VERSION \"(.*)\"\s*$", line )
		if m :
			boostVersion = m.group( 1 )
			m = re.match( "^([0-9]+)_([0-9]+)(?:_([0-9]+)|)$", boostVersion )
			baseLibEnv["BOOST_MAJOR_VERSION"] = m.group( 1 )
			baseLibEnv["BOOST_MINOR_VERSION"] = m.group( 2 )

if "BOOST_MAJOR_VERSION" not in baseLibEnv :
	sys.stderr.write( "ERROR : unable to determine boost version from \"{}\".\n".format(  boostVersionHeader ) )
	Exit( 1 )

###############################################################################################
# The basic environment for building python modules
###############################################################################################

basePythonEnv = baseLibEnv.Clone()

pythonExecutable = shutil.which( "python", path = commandEnv["ENV"]["PATH"] )
basePythonEnv["PYTHON_VERSION"] = subprocess.check_output(
	[ pythonExecutable, "-c", "import sys; print( '{}.{}'.format( *sys.version_info[:2] ) )" ],
	env=commandEnv["ENV"], universal_newlines=True
).strip()

if basePythonEnv["PLATFORM"] == "win32" :
	basePythonEnv["PYTHON_VERSION"] = basePythonEnv["PYTHON_VERSION"].replace( ".", "" )

basePythonEnv["PYTHON_ABI_VERSION"] = basePythonEnv["PYTHON_VERSION"]
basePythonEnv["PYTHON_ABI_VERSION"] += subprocess.check_output(
	[ pythonExecutable, "-c", "import sysconfig; print( sysconfig.get_config_var( 'abiflags' ) or '' )" ],
	env=commandEnv["ENV"], universal_newlines=True
).strip()

# if BOOST_PYTHON_LIB_SUFFIX is provided, use it
boostPythonLibSuffix = basePythonEnv.get( "BOOST_PYTHON_LIB_SUFFIX", None )
if boostPythonLibSuffix is None :
	basePythonEnv["BOOST_PYTHON_LIB_SUFFIX"] = basePythonEnv["BOOST_LIB_SUFFIX"]
	if ( int( basePythonEnv["BOOST_MAJOR_VERSION"] ), int( basePythonEnv["BOOST_MINOR_VERSION"] ) ) >= ( 1, 67 ) :
		basePythonEnv["BOOST_PYTHON_LIB_SUFFIX"] = basePythonEnv["PYTHON_VERSION"].replace( ".", "" ) + basePythonEnv["BOOST_PYTHON_LIB_SUFFIX"]

basePythonEnv.Append(

	CPPDEFINES = [
		( "BOOST_PYTHON_MAX_ARITY", "20" ),
	],

	LIBS = [
		"boost_python$BOOST_PYTHON_LIB_SUFFIX",
		"IECorePython$CORTEX_PYTHON_LIB_SUFFIX",
		"Gaffer",
		"python$PYTHON_ABI_VERSION",
	],

)

if basePythonEnv["PLATFORM"]=="darwin" :

	basePythonEnv.Append(
		CPPPATH = [ "$BUILD_DIR/lib/Python.framework/Versions/$PYTHON_VERSION/include/python$PYTHON_VERSION" ],
		LIBS = [ "python$PYTHON_VERSION" ],
		LIBPATH = [ "$BUILD_DIR/lib/Python.framework/Versions/$PYTHON_VERSION/lib" ]
	)

else :

	basePythonEnv.Append(
		CPPPATH = [ "$BUILD_DIR/include/python$PYTHON_ABI_VERSION" ]
	)

	if basePythonEnv["PLATFORM"] == "win32" :

		basePythonEnv.Append( LIBPATH = "$BUILD_DIR/libs" )

###############################################################################################
# Arnold configuration
###############################################################################################

arnoldInstallRoot = ""
if env["ARNOLD_ROOT"] :

	# Version

	arnoldHeader = env.subst( "$ARNOLD_ROOT/include/ai_version.h" )
	if not os.path.exists( arnoldHeader ) :
		sys.stderr.write( "ERROR : unable to find \"{}\".\n".format( arnoldHeader ) )
		Exit( 1 )

	arnoldVersions = {}
	for line in open( arnoldHeader ) :
		m = re.match( "^#define AI_VERSION_(ARCH|MAJOR)_NUM\s*([0-9]+)", line )
		if m :
			arnoldVersions[m.group(1)] = m.group( 2 )

	if set( arnoldVersions.keys() ) != { "ARCH", "MAJOR" } :
		sys.stderr.write( "ERROR : unable to parse \"{}\".\n".format( arnoldHeader ) )
		Exit( 1 )

	# Install root

	arnoldInstallRoot = "${{BUILD_DIR}}/arnold/{ARCH}.{MAJOR}".format( **arnoldVersions )

	# Metadata. Our `arnoldPlugins/gaffer.mtd` contains metadata for all the Arnold
	# nodes we know about, in all Arnold versions. We need to filter this down
	# to only the nodes in _this_ Arnold version during installation. Arnold emits
	# warnings if we attempt to register metadata for nodes that don't exist.

	def filterMetadata( target, source, env ) :

		# Get set of built-in nodes

		kickEnv = env["ENV"].copy()
		kickEnv["PATH"] = os.pathsep.join( [ os.path.join( env["ARNOLD_ROOT"], "bin" ), kickEnv["PATH"] ] )
		kickOutput = subprocess.check_output(
			"kick -nodes",
			env = kickEnv,
			universal_newlines = True,
			shell = True
		)

		nodeDefRegex = re.compile( r"\s*([a-zA-Z0-9_]+)\s+(driver|color_manager|driver|filter|light|operator|options|override|shader|shape)" )
		nodes = set()
		for line in kickOutput.split( "\n" ) :
			m = nodeDefRegex.match( line )
			if m :
				nodes.add( m.group( 1 ) )

		# Filter the input metadata file so that we only include metadata
		# for nodes that exist.

		newNodeRegex = re.compile( r"^\[node ([a-zA-Z_0-9]+)\]" )
		with open( str( source[0] ) ) as inFile :
			with open( str( target[0] ), "w" ) as outFile :
				omit = False
				for line in inFile.readlines() :
					m = newNodeRegex.match( line )
					if m :
						nodeName = m.group( 1 )
						omit = nodeName not in nodes
						if omit :
							sys.stderr.write( "Omitting non-existent node {}\n".format( nodeName ) )
					if not omit :
						outFile.write( line )

	metadataInstall = env.Command(
		os.path.join( arnoldInstallRoot, "arnoldPlugins/gaffer.mtd" ),
		"arnoldPlugins/gaffer.mtd",
		filterMetadata
	)
	env.Alias( "build", metadataInstall )

###############################################################################################
# Definitions for the libraries we wish to build
###############################################################################################

libraries = {

	"Gaffer" : {
		"envAppends" : {
			"LIBS" : [ "Half", "fmt" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "fmt" ],
		}
	},

	"GafferTest" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "GafferTest", "GafferBindings" ],
		},
		"additionalFiles" : glob.glob( "python/GafferTest/*/*" ) + glob.glob( "python/GafferTest/*/*/*" ),
		"apps" : [ "cli", "env", "license", "python", "stats", "test" ],
	},

	"GafferUI" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer", "Iex$OPENEXR_LIB_SUFFIX", "IECoreGL$CORTEX_LIB_SUFFIX", "IECoreImage$CORTEX_LIB_SUFFIX", "IECoreScene$CORTEX_LIB_SUFFIX" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "IECoreImage$CORTEX_LIB_SUFFIX", "IECoreScene$CORTEX_LIB_SUFFIX", "IECoreGL$CORTEX_LIB_SUFFIX", "GafferUI", "GafferBindings" ],
		},
		"mocSourceFiles" : [
			"src/GafferUIModule/PathListingWidgetBinding.cpp",
		],
		"apps" : [ "browser", "gui", "screengrab", "view" ],
	},

	"GafferUITest" : {

		"additionalFiles" : glob.glob( "python/GafferUITest/scripts/*.gfr" ),

	},

	"GafferDispatch" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "GafferBindings", "GafferDispatch" ],
		},
		"apps" : [ "execute" ],
	},

	"GafferDispatchTest" : {

		"additionalFiles" : glob.glob( "python/GafferDispatchTest/*/*" ) + glob.glob( "python/GafferDispatchTest/*/*/*" ),

	},

	"GafferDispatchUI" : {
		"apps" : [ "dispatch" ],
	},

	"GafferDispatchUITest" : {},

	"GafferCortex" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer", "GafferDispatch" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "GafferBindings", "GafferCortex", "GafferDispatch" ],
		},
		"requiredOptions" : [ "GAFFERCORTEX" ],
	},

	"GafferCortexTest" : {
		"additionalFiles" : glob.glob( "python/GafferCortexTest/*/*" ) + glob.glob( "python/GafferCortexTest/*/*/*" ) + glob.glob( "python/GafferCortexTest/images/*" ),
		"requiredOptions" : [ "GAFFERCORTEX" ],
	},

	"GafferCortexUI" : {
		"apps" : [ "op" ],
		"requiredOptions" : [ "GAFFERCORTEX" ],
	},

	"GafferCortexUITest" : {
		"requiredOptions" : [ "GAFFERCORTEX" ],
	},

	"GafferScene" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer", "Iex$OPENEXR_LIB_SUFFIX", "IECoreGL$CORTEX_LIB_SUFFIX", "IECoreImage$CORTEX_LIB_SUFFIX",  "IECoreScene$CORTEX_LIB_SUFFIX", "GafferImage", "GafferDispatch", "Half", "fmt" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "GafferBindings", "GafferScene", "GafferDispatch", "GafferImage", "IECoreScene$CORTEX_LIB_SUFFIX", "IECoreGL$CORTEX_LIB_SUFFIX" ],
		},
		"additionalFiles" : glob.glob( "glsl/*.frag" ) + glob.glob( "glsl/*.vert" ) + glob.glob( "include/GafferScene/Private/IECore*Preview/*.h" )
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
			"LIBS" : [ "IECoreGL$CORTEX_LIB_SUFFIX", "GafferBindings", "GafferScene", "GafferUI", "GafferImageUI", "GafferSceneUI", "IECoreScene$CORTEX_LIB_SUFFIX" ],
		},
	},

	"GafferSceneUITest" : {},

	"GafferImage" : {
		"envAppends" : {
			"CPPPATH" : [ "$BUILD_DIR/include/freetype2" ],
			"LIBS" : [ "Gaffer", "GafferDispatch", "Iex$OPENEXR_LIB_SUFFIX", "IECoreImage$CORTEX_LIB_SUFFIX", "OpenImageIO$OIIO_LIB_SUFFIX", "OpenImageIO_Util$OIIO_LIB_SUFFIX", "OpenColorIO$OCIO_LIB_SUFFIX", "freetype", "fmt" ],
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
			"LIBS" : [ "GafferImage", "GafferImageTest" ],
		},
		"additionalFiles" :
			glob.glob( "python/GafferImageTest/scripts/*" ) + glob.glob( "python/GafferImageTest/images/*" ) +
			glob.glob( "python/GafferImageTest/openColorIO/luts/*" ) + glob.glob( "python/GafferImageTest/openColorIO/*.ocio" ) +
			glob.glob( "python/GafferImageTest/openColorIO/looks/*" ),
	},

	"GafferImageUITest" : {},

	"GafferImageUI" : {
		"envAppends" : {
			"LIBS" : [ "IECoreGL$CORTEX_LIB_SUFFIX", "Gaffer", "GafferImage", "GafferUI", "OpenColorIO$OCIO_LIB_SUFFIX", "IECoreScene$CORTEX_LIB_SUFFIX", "Iex$OPENEXR_LIB_SUFFIX" ],
		},
		"pythonEnvAppends" : {
			"CPPPATH" : [ "$PYBIND11/include" ],
			"LIBS" : [ "GafferBindings", "GafferUI", "GafferImage", "GafferImageUI" ],
		},
	},

	"IECoreArnold" : {
		"envAppends" : {
			"LIBPATH" : [ "$ARNOLD_ROOT/bin" ] if env["PLATFORM"] != "win32" else [ "$ARNOLD_ROOT/bin", "$ARNOLD_ROOT/lib" ],
			## \todo Remove GafferScene. We need it at present to get access to `IECoreScenePreview::Renderer`,
			# but IECoreArnold must never depend on Gaffer code; logically it is in the layer below Gaffer.
			"LIBS" : [ "GafferScene", "ai", "IECoreScene$CORTEX_LIB_SUFFIX", "IECoreVDB$CORTEX_LIB_SUFFIX", "openvdb$VDB_LIB_SUFFIX" ],
			"CXXFLAGS" : [ "-DAI_ENABLE_DEPRECATION_WARNINGS" ],
			"CPPPATH" : [ "$ARNOLD_ROOT/include" ],
		},
		"pythonEnvAppends" : {
			"LIBPATH" : [ "$ARNOLD_ROOT/bin" ] if env["PLATFORM"] != "win32" else [ "$ARNOLD_ROOT/bin", "$ARNOLD_ROOT/lib" ],
			"LIBS" : [ "IECoreScene$CORTEX_LIB_SUFFIX", "IECoreArnold" ],
			"CXXFLAGS" : [ "-DAI_ENABLE_DEPRECATION_WARNINGS" ],
			"CPPPATH" : [ "$ARNOLD_ROOT/include" ],
		},
		"requiredOptions" : [ "ARNOLD_ROOT" ],
		"installRoot" : arnoldInstallRoot,
	},

	"IECoreArnoldTest" : {
		"additionalFiles" : glob.glob( "python/IECoreArnoldTest/metadata/*" ) + glob.glob( "python/IECoreArnoldTest/assFiles/*" ),
		"requiredOptions" : [ "ARNOLD_ROOT" ],
		"installRoot" : arnoldInstallRoot,
	},

	"GafferArnold" : {
		"envAppends" : {
			"LIBPATH" : [ "$ARNOLD_ROOT/bin" ] if env["PLATFORM"] != "win32" else [ "$ARNOLD_ROOT/bin", "$ARNOLD_ROOT/lib" ],
			"LIBS" : [ "Gaffer", "GafferScene", "GafferDispatch", "ai", "GafferVDB", "openvdb$VDB_LIB_SUFFIX",  "IECoreScene$CORTEX_LIB_SUFFIX", "IECoreVDB$CORTEX_LIB_SUFFIX", "IECoreArnold", "GafferOSL", "fmt" ],
			"CXXFLAGS" : [ "-DAI_ENABLE_DEPRECATION_WARNINGS" ],
			"CPPPATH" : [ "$ARNOLD_ROOT/include" ],
		},
		"pythonEnvAppends" : {
			"LIBPATH" : [ "$ARNOLD_ROOT/bin" ] if env["PLATFORM"] != "win32" else [ "$ARNOLD_ROOT/bin", "$ARNOLD_ROOT/lib" ],
			"LIBS" : [ "Gaffer", "GafferScene", "GafferBindings", "GafferVDB", "GafferDispatch", "GafferArnold", "GafferOSL", "IECoreScene$CORTEX_LIB_SUFFIX", "IECoreArnold", "fmt" ],
			"CXXFLAGS" : [ "-DAI_ENABLE_DEPRECATION_WARNINGS" ],
			"CPPPATH" : [ "$ARNOLD_ROOT/include" ],
		},
		"requiredOptions" : [ "ARNOLD_ROOT" ],
		"installRoot" : arnoldInstallRoot,
	},

	"GafferArnoldTest" : {
		"additionalFiles" : glob.glob( "python/GafferArnoldTest/volumes/*" ) + glob.glob( "python/GafferArnoldTest/metadata/*" ) + glob.glob( "python/GafferArnoldTest/images/*" ),
		"requiredOptions" : [ "ARNOLD_ROOT" ],
		"installRoot" : arnoldInstallRoot,
	},

	"GafferArnoldUI" : {
		"envAppends" : {
			"LIBPATH" : [ "$ARNOLD_ROOT/bin" ] if env["PLATFORM"] != "win32" else [ "$ARNOLD_ROOT/bin", "$ARNOLD_ROOT/lib" ],
			"LIBS" : [ "IECoreScene$CORTEX_LIB_SUFFIX", "IECoreGL$CORTEX_LIB_SUFFIX", "OpenImageIO$OIIO_LIB_SUFFIX", "OpenImageIO_Util$OIIO_LIB_SUFFIX", "oslquery$OSL_LIB_SUFFIX", "Gaffer", "GafferScene", "GafferOSL", "GafferSceneUI", "ai" ],
			"CXXFLAGS" : [ "-DAI_ENABLE_DEPRECATION_WARNINGS" ],
			"CPPPATH" : [ "$ARNOLD_ROOT/include" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "GafferArnoldUI", "GafferSceneUI", "IECoreScene$CORTEX_LIB_SUFFIX" ],
		},
		"requiredOptions" : [ "ARNOLD_ROOT" ],
		"installRoot" : arnoldInstallRoot,
	},

	"GafferArnoldUITest" : {
		"additionalFiles" : glob.glob( "python/GafferArnoldUITest/metadata/*" ),
		"requiredOptions" : [ "ARNOLD_ROOT" ],
		"installRoot" : arnoldInstallRoot,
	},

	"GafferArnoldPlugin" : {
		"envAppends" : {
			"LIBPATH" : [ "$ARNOLD_ROOT/bin" ] if env["PLATFORM"] != "win32" else [ "$ARNOLD_ROOT/bin", "$ARNOLD_ROOT/lib" ],
			"LIBS" : [ "IECoreArnold", "ai", "IECoreImage$CORTEX_LIB_SUFFIX" ],
			"CXXFLAGS" : [ "-DAI_ENABLE_DEPRECATION_WARNINGS" ],
			"CPPPATH" : [ "$ARNOLD_ROOT/include" ],
		},
		"envReplacements" : {
			"SHLIBPREFIX" : "",
		},
		"installName" : "arnoldPlugins/Gaffer",
		"requiredOptions" : [ "ARNOLD_ROOT" ],
		"installRoot" : arnoldInstallRoot,
	},

	"GafferOSL" : {
		"envAppends" : {
			"CPPPATH" : [ "$OSLHOME/include/OSL" ],
			"LIBS" : [ "Gaffer", "GafferScene", "GafferImage", "OpenImageIO$OIIO_LIB_SUFFIX", "OpenImageIO_Util$OIIO_LIB_SUFFIX", "oslquery$OSL_LIB_SUFFIX", "oslexec$OSL_LIB_SUFFIX", "Iex$OPENEXR_LIB_SUFFIX", "IECoreImage$CORTEX_LIB_SUFFIX", "IECoreScene$CORTEX_LIB_SUFFIX" ],
		},
		"pythonEnvAppends" : {
			"CPPPATH" : [ "$OSLHOME/include/OSL" ],
			"LIBS" : [ "GafferBindings", "GafferScene", "GafferImage", "GafferOSL", "Iex$OPENEXR_LIB_SUFFIX", "IECoreScene$CORTEX_LIB_SUFFIX" ],
		},
		"oslHeaders" : glob.glob( "shaders/*/*.h" ),
		"oslShaders" : glob.glob( "shaders/*/*.osl" ),
	},

	"GafferOSLUI" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer", "GafferUI", "GafferOSL" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "IECoreGL$CORTEX_LIB_SUFFIX", "GafferBindings", "GafferScene", "GafferUI", "GafferImageUI", "GafferOSLUI" ],
		},
	},

	"GafferOSLTest" : {
		"additionalFiles" : glob.glob( "python/GafferOSLTest/*/*" ),
	},

	"GafferOSLUITest" : {},

	"IECoreDelight" : {
		"envAppends" : {
			"CPPPATH" : [ "$DELIGHT_ROOT/include" ],
			"LIBPATH" : [ "$DELIGHT_ROOT/lib" ],
			## \todo Remove GafferScene. We need it at present to get access to `IECoreScenePreview::Renderer`,
			# but IECoreDelight must never depend on Gaffer code; logically it is in the layer below Gaffer.
			"LIBS" : [ "GafferScene", "3delight", "IECoreImage$CORTEX_LIB_SUFFIX", "IECoreScene$CORTEX_LIB_SUFFIX" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "IECoreScene$CORTEX_LIB_SUFFIX", "IECoreDelight" ],
		},
		"requiredOptions" : [ "DELIGHT_ROOT" ],
	},

	"IECoreDelightTest" : {
		"requiredOptions" : [ "DELIGHT_ROOT" ],
	},

	"GafferDelight" : {
		"envAppends" : {
			"CPPPATH" : [ "$DELIGHT_ROOT/include" ],
			"LIBS" : [ "Gaffer", "GafferScene", "GafferDispatch", "IECoreScene$CORTEX_LIB_SUFFIX", "IECoreDelight" ],
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
			"CXXFLAGS" : [ systemIncludeArgument, "$APPLESEED_ROOT/include", "-DAPPLESEED_ENABLE_IMATH_INTEROP" ],
			"LIBPATH" : [ "$APPLESEED_ROOT/lib" ],
			"LIBS" : [ "Gaffer", "GafferDispatch", "GafferScene", "appleseed",  "IECoreScene$CORTEX_LIB_SUFFIX", "IECoreAppleseed$CORTEX_LIB_SUFFIX", "OpenImageIO$OIIO_LIB_SUFFIX", "OpenImageIO_Util$OIIO_LIB_SUFFIX", "oslquery$OSL_LIB_SUFFIX", "fmt" ],
			"CPPDEFINES" : [ "APPLESEED_USE_SSE" ] if platform.machine() != "arm64" else [],
		},
		"pythonEnvAppends" : {
			"CXXFLAGS" : [ systemIncludeArgument, "$APPLESEED_ROOT/include", "-DAPPLESEED_ENABLE_IMATH_INTEROP" ],
			"LIBPATH" : [ "$APPLESEED_ROOT/lib" ],
			"LIBS" : [ "Gaffer", "GafferDispatch", "GafferScene", "GafferBindings", "GafferAppleseed" ],
			"CPPDEFINES" : [ "APPLESEED_USE_SSE" ] if platform.machine() != "arm64" else [],
		},
		"requiredOptions" : [ "APPLESEED_ROOT" ],
	},

	"GafferAppleseedTest" : {
		"additionalFiles" : glob.glob( "python/GafferAppleseedTest/*/*" ),
	},

	"GafferAppleseedUI" : {},

	"GafferAppleseedUITest" : {},

	"GafferCycles" : {
		"envAppends" : {
			"LIBPATH" : [ "$CYCLES_ROOT/lib" ],
			"LIBS" : [
				"IECoreScene$CORTEX_LIB_SUFFIX", "IECoreImage$CORTEX_LIB_SUFFIX", "IECoreVDB$CORTEX_LIB_SUFFIX",
				"Gaffer", "GafferScene", "GafferDispatch", "GafferOSL",
				"cycles_session", "cycles_scene", "cycles_graph", "cycles_bvh", "cycles_device", "cycles_kernel", "cycles_kernel_osl",
				"cycles_integrator", "cycles_util", "cycles_subd", "extern_sky",
				"OpenImageIO$OIIO_LIB_SUFFIX", "OpenImageIO_Util$OIIO_LIB_SUFFIX", "oslexec$OSL_LIB_SUFFIX", "oslquery$OSL_LIB_SUFFIX",
				"openvdb$VDB_LIB_SUFFIX", "Alembic", "osdCPU", "OpenColorIO$OCIO_LIB_SUFFIX", "embree3", "Iex",
			],
			"CXXFLAGS" : [ systemIncludeArgument, "$CYCLES_ROOT/include" ],
			"CPPDEFINES" : [
				( "CCL_NAMESPACE_BEGIN", "namespace ccl {" ),
				( "CCL_NAMESPACE_END", "}" ),
				( "WITH_OSL", "1" ),
			],
			"FRAMEWORKS" : [ "Foundation", "Metal", "IOKit" ],
		},
		"pythonEnvAppends" : {
			"LIBPATH" : [ "$CYCLES_ROOT/lib" ],
			"LIBS" : [
				"Gaffer", "GafferScene", "GafferDispatch", "GafferBindings", "GafferCycles",
				"cycles_session", "cycles_scene", "cycles_graph", "cycles_bvh", "cycles_device", "cycles_kernel", "cycles_kernel_osl",
				"cycles_integrator", "cycles_util", "cycles_subd", "extern_sky",
				"OpenImageIO$OIIO_LIB_SUFFIX", "OpenImageIO_Util$OIIO_LIB_SUFFIX", "oslexec$OSL_LIB_SUFFIX", "openvdb$VDB_LIB_SUFFIX",
				"oslquery$OSL_LIB_SUFFIX", "Alembic", "osdCPU", "OpenColorIO$OCIO_LIB_SUFFIX", "embree3", "Iex",
			],
			"CXXFLAGS" : [ systemIncludeArgument, "$CYCLES_ROOT/include" ],
			"CPPDEFINES" : [
				( "CCL_NAMESPACE_BEGIN", "namespace ccl {" ),
				( "CCL_NAMESPACE_END", "}" ),
			],
		},
		"requiredOptions" : [ "CYCLES_ROOT" ],
	},

	"GafferCyclesTest" : { "requiredOptions" : [ "CYCLES_ROOT" ], },

	"GafferCyclesUI" : { "requiredOptions" : [ "CYCLES_ROOT" ], },

	"GafferCyclesUITest" : { "requiredOptions" : [ "CYCLES_ROOT" ], },

	"GafferTractor" : {},

	"GafferTractorTest" : {},

	"GafferTractorUI" : {},

	"GafferTractorUITest" : {},

	"GafferUSD" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer", "GafferDispatch", "GafferScene", "IECoreScene$CORTEX_LIB_SUFFIX" ] + [ "${USD_LIB_PREFIX}" + x for x in [ "sdf", "arch", "tf", "vt" ] ],
			# USD includes "at least one deprecated or antiquated header", so we
			# have to drop our usual strict warning levels.
			"CXXFLAGS" : [ "-Wno-deprecated" if env["PLATFORM"] != "win32" else "/wd4996" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "GafferUSD", "GafferScene", "GafferDispatch", "GafferBindings" ],
		},
		# USD's Python bindings are intrusive to the main library.
		"libraryDependsOnPython" : True,
		"requiredOptions" : [ "GAFFERUSD" ],
	},

	"GafferUSDTest" : {
		"requiredOptions" : [ "GAFFERUSD" ],
	},

	"GafferUSDUI" : {
		"requiredOptions" : [ "GAFFERUSD" ],
	},

	"GafferUSDUITest" : {
		"requiredOptions" : [ "GAFFERUSD" ],
	},

	"GafferVDB" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer", "GafferScene", "Half", "openvdb$VDB_LIB_SUFFIX", "IECoreVDB$CORTEX_LIB_SUFFIX", "IECoreScene$CORTEX_LIB_SUFFIX" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "GafferBindings", "GafferScene", "GafferVDB", "openvdb$VDB_LIB_SUFFIX", "IECoreVDB$CORTEX_LIB_SUFFIX", "IECoreScene$CORTEX_LIB_SUFFIX"],
		}
	},

	"GafferVDBTest" : {
		"additionalFiles" : glob.glob( "python/GafferVDBTest/*/*" ),
	},

	"GafferVDBUI" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer", "GafferScene", "GafferSceneUI", "IECoreVDB$CORTEX_LIB_SUFFIX", "IECoreScene$CORTEX_LIB_SUFFIX", "IECoreGL$CORTEX_LIB_SUFFIX", "GafferVDB", "openvdb$VDB_LIB_SUFFIX" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "GafferScene", "GafferVDB", "GafferVDBUI", "openvdb$VDB_LIB_SUFFIX" ],
		}
	},

	"GafferVDBUITest" : {
		"additionalFiles" : glob.glob( "python/GafferVDBUITest/*/*" ),
	},

	"scripts" : {
		"additionalFiles" : [ "bin/__gaffer.py" ],
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

}

libraries["scripts"]["additionalFiles"].append( "bin/gaffer.cmd" if env["PLATFORM"] == "win32" else "bin/gaffer" )

# Add on OpenGL libraries to definitions - these vary from platform to platform
for library in ( "GafferUI", "GafferScene", "GafferSceneUI", "GafferImageUI" ) :
	if env["PLATFORM"] == "darwin" :
		libraries[library]["envAppends"].setdefault( "FRAMEWORKS", [] ).append( "OpenGL" )
	elif env["PLATFORM"] == "win32" :
		libraries[library]["envAppends"]["LIBS"].append( "opengl32" )
	else :
		libraries[library]["envAppends"]["LIBS"].append( [ "GL", "GLX" ] )
		libraries[library]["pythonEnvAppends"]["LIBS"].append( [ "GL", "GLX" ] )
	libraries[library]["envAppends"]["LIBS"].append( "GLEW$GLEW_LIB_SUFFIX" )

# Add on Qt libraries to definitions - these vary from platform to platform

def addQtLibrary( library, qtLibrary, pythonOnly = True ) :

	if env["PLATFORM"] == "darwin" :
		libraries[library]["pythonEnvAppends"].setdefault( "FRAMEWORKS", [] ).append( "Qt" + qtLibrary )
		if not pythonOnly:
			libraries[library]["envAppends"].setdefault( "FRAMEWORKS", [] ).append( "Qt" + qtLibrary )
	else :
		libraries[library]["pythonEnvAppends"]["LIBS"].append( "Qt${QT_VERSION}" + qtLibrary )
		if not pythonOnly:
			libraries[library]["envAppends"]["LIBS"].append( "Qt${QT_VERSION}" + qtLibrary )

for library in ( "GafferUI", ) :
	addQtLibrary( library, "Core", False )
	addQtLibrary( library, "Gui" )
	addQtLibrary( library, "OpenGL" )
	addQtLibrary( library, "Test" )
	addQtLibrary( library, "Widgets" )

# Add required libraries for Windows

if env["PLATFORM"] == "win32" :

	for library in ( "Gaffer", ) :

		libraries[library].setdefault( "envAppends", {} )
		libraries[library]["envAppends"].setdefault( "LIBS", [] ).extend( [ "Advapi32" ] )

# Optionally add vTune requirements

if os.path.exists( env.subst("$VTUNE_ROOT") ):

	for library in ( "Gaffer", ) :

		libraries[library].setdefault( "envAppends", {} )
		libraries[library]["envAppends"].setdefault( "CXXFLAGS", [] ).extend(
			[ systemIncludeArgument, "$VTUNE_ROOT/include", "-DGAFFER_VTUNE" ]
		)
		libraries[library]["envAppends"].setdefault( "LIBPATH", [] ).extend( [ "$VTUNE_ROOT/lib64" ] )
		libraries[library]["envAppends"].setdefault( "LIBS", [] ).extend( [ "ittnotify", "dl" ] )

		libraries[library].setdefault( "pythonEnvAppends", {} )
		libraries[library]["pythonEnvAppends"].setdefault( "CXXFLAGS", [] ).extend( [ "-DGAFFER_VTUNE" ] )

#########################################################################################################
# Repair Symlinks on Windows
#########################################################################################################

# Windows does not support symlinks except with special (non-default)
# privileges. When cloning the repository, git will create symlink source files
# as a text file with the symlink target as its content. We override the
# `Install()` builder to detect such files and install the target instead.

if env["PLATFORM"] == "win32" :

	def customInstaller( dest, source, env ) :

		if os.path.isdir( source ) or os.path.isdir( dest ) :
			raise RuntimeError( "Cannot copy {} to {}. Source and destination cannot be directories.".format( source, dest ) )

		fileInfo = runCommand( "git ls-files -s {}".format( source ) ).split()

		if len( fileInfo ) == 4 or len( fileInfo ) == 5:

			# ls-files output format: [<tag> ]<mode> <object> <stage> <file>
			# The magic code for symlinks in git is file mode 120000

			fileMode = fileInfo[1] if len( fileInfo ) == 5 else fileInfo[0]
			filePath = fileInfo[4] if len( fileInfo ) == 5 else fileInfo[3]
			filePath = filePath.replace( "/", "\\" )  # filePath comes in from git with /

			if fileMode == "120000" and os.path.exists( filePath ):

				with open( filePath, "r" ) as f :

					sourceFile = f.readline().replace( "/", "\\" )

					linkSource = os.path.abspath(
						os.path.join(
							os.getcwd(),
							os.path.dirname(filePath ),
							sourceFile
						)
					)

					# If running with privileges that allow symlinks, the file content will
					# already be correct (`linkSource` will likely be the first line of
					# the license). Don't copy those files by checking if the linked file exists.
					if os.path.isfile( linkSource ) :
						source = os.path.abspath( os.path.join( os.path.dirname( linkSource ), sourceFile )  )

						# Make the source relative to the current directory as SCons expects
						source = source.replace( os.getcwd(), "" ).lstrip( os.path.sep )

						shutil.copy2( source, dest )

						return

		shutil.copy2( source, dest )

	env["INSTALL"] = customInstaller

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
	if libraryDef.get( "libraryDependsOnPython" ) :
		libEnv = basePythonEnv.Clone()

	libEnv.Append( CXXFLAGS = "-D{0}_EXPORTS".format( libraryName ) )
	libEnv.Append( **(libraryDef.get( "envAppends", {} )) )
	libEnv.Replace( **(libraryDef.get( "envReplacements", {} )) )

	installRoot = libraryDef.get( "installRoot", "$BUILD_DIR" )

	# library

	librarySource = sorted( glob.glob( "src/" + libraryName + "/*.cpp" ) + glob.glob( "src/" + libraryName + "/*/*.cpp" ) + glob.glob( "src/" + libraryName + "/*/*/*.cpp" ) )
	if librarySource :

		libraryInstallName = libraryDef.get( "installName", "lib/" + libraryName )
		library = libEnv.SharedLibrary( libraryInstallName, librarySource )
		libEnv.Default( library )

		libraryInstall = libEnv.Install(
			os.path.join( installRoot, os.path.dirname( libraryInstallName ) ),
			library
		)
		libEnv.Alias( "build", libraryInstall )

	# header install

	fileSubstitutions = {
		"!GAFFER_MILESTONE_VERSION!" : libEnv.subst( "$GAFFER_MILESTONE_VERSION" ),
		"!GAFFER_MAJOR_VERSION!" : libEnv.subst( "$GAFFER_MAJOR_VERSION" ),
		"!GAFFER_MINOR_VERSION!" : libEnv.subst( "$GAFFER_MINOR_VERSION" ),
		"!GAFFER_PATCH_VERSION!" : libEnv.subst( "$GAFFER_PATCH_VERSION" ),
		"!GAFFER_VERSION_SUFFIX!" : libEnv.subst( "$GAFFER_VERSION_SUFFIX" ),
	}

	def processHeaders( env, libraryName ) :

		headers = (
			glob.glob( "include/" + libraryName + "/*.h" ) +
			glob.glob( "include/" + libraryName + "/*.inl" ) +
			glob.glob( "include/" + libraryName + "/*/*.h" ) +
			glob.glob( "include/" + libraryName + "/*/*.inl" )
		)

		for headerIn in glob.glob( "include/" + libraryName + "/*.h.in" ) :
			header = env.Substfile(
				os.path.splitext( headerIn )[0],
				headerIn,
				SUBST_DICT = fileSubstitutions
			)
			headers.append( str( header[0] ) )

		for header in headers :
			headerInstall = env.InstallAs(
				os.path.join( installRoot, header ),
				header
			)
			env.Alias( "build", headerInstall )

	processHeaders( libEnv, libraryName )

	# bindings library

	pythonEnv = basePythonEnv.Clone()
	pythonEnv.Append( **(libraryDef.get( "pythonEnvAppends", {} ))  )

	bindingsEnv = pythonEnv.Clone()
	bindingsEnv.Append( CXXFLAGS = "-D{0}Bindings_EXPORTS".format( libraryName ) )

	bindingsSource = sorted( glob.glob( "src/" + libraryName + "Bindings/*.cpp" ) )
	if bindingsSource :

		bindingsLibrary = bindingsEnv.SharedLibrary( "lib/" + libraryName + "Bindings", bindingsSource )
		bindingsEnv.Default( bindingsLibrary )

		bindingsLibraryInstall = bindingsEnv.Install( os.path.join( installRoot, "lib" ), bindingsLibrary )
		env.Alias( "build", bindingsLibraryInstall )

	# bindings header install

	processHeaders( bindingsEnv, libraryName + "Bindings" )

	# python module binary component

	pythonModuleSource = sorted( glob.glob( "src/" + libraryName + "Module/*.cpp" ) )
	if pythonModuleSource :

		pythonModuleEnv = pythonEnv.Clone()
		if bindingsSource :
			pythonModuleEnv.Append( LIBS = [ libraryName + "Bindings" ] )

		pythonModuleEnv["SHLIBPREFIX"] = ""
		if pythonModuleEnv["PLATFORM"] == "darwin" :
			# On MacOS, we must build Python modules with the ".so"
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
		elif pythonModuleEnv["PLATFORM"] == "win32" :
			pythonModuleEnv["SHLIBSUFFIX"] = ".pyd"

		pythonModule = pythonModuleEnv.SharedLibrary( "python/" + libraryName + "/_" + libraryName, pythonModuleSource )
		pythonModuleEnv.Default( pythonModule )

		moduleInstall = pythonModuleEnv.Install( os.path.join( installRoot, "python", libraryName ), pythonModule )
		pythonModuleEnv.Alias( "build", moduleInstall )

	# Moc preprocessing, for QObject derived classes. SCons does include a "qt" tool that
	# can scan files automatically for the Q_OBJECT macro, but it hasn't been updated for Qt 5.
	# We don't need `moc` for many files, so we just list them manually and emit the `moc`
	# command ourselves.

	for sourceFile in libraryDef.get( "mocSourceFiles", [] ) :
		mocOutput = commandEnv.Command( os.path.splitext( sourceFile )[0] + ".moc", sourceFile, "moc $SOURCE -o $TARGET" )
		# Somehow the above leads to a circular dependency between `mocOutput` and itself.
		# Tell SCons not to worry. The official SCons tool does the same.
		env.Ignore( mocOutput, mocOutput )

	# python component of python module

	pythonFiles = glob.glob( "python/" + libraryName + "/*.py" ) + glob.glob( "python/" + libraryName + "/*/*.py" ) + glob.glob( "python/" + libraryName + "/*/*/*.py" )
	for pythonFile in pythonFiles :
		pythonFileInstall = env.Substfile(
			os.path.join( installRoot, pythonFile ),
			pythonFile,
			SUBST_DICT = fileSubstitutions
		)
		env.Alias( "build", pythonFileInstall )

	# apps

	for app in libraryDef.get( "apps", [] ) :
		appInstall = env.InstallAs( os.path.join( installRoot, "apps", app, "{app}-1.py".format( app=app ) ), "apps/{app}/{app}-1.py".format( app=app ) )
		env.Alias( "build", appInstall )

	# startup files

	for startupDir in libraryDef.get( "apps", [] ) + [ libraryName ] :
		for startupFile in glob.glob( "startup/{startupDir}/*.py".format( startupDir=startupDir ) ) + glob.glob( "startup/{startupDir}/*.gfr".format( startupDir=startupDir ) ) :
			startupFileInstall = env.InstallAs( os.path.join( installRoot, startupFile ), startupFile )
			env.Alias( "build", startupFileInstall )

	# additional files

	for additionalFile in libraryDef.get( "additionalFiles", [] ) :
		if additionalFile in pythonFiles :
			continue
		additionalFileInstall = env.InstallAs( os.path.join( installRoot, additionalFile ), additionalFile )
		env.Alias( "build", additionalFileInstall )

	# osl headers

	for oslHeader in libraryDef.get( "oslHeaders", [] ) :
		oslHeaderInstall = env.InstallAs( os.path.join( installRoot, oslHeader ), oslHeader )
		env.Alias( "oslHeaders", oslHeaderInstall )
		env.Alias( "build", oslHeaderInstall )

	# osl shaders

	def buildOSL( target, source, env ) :
		subprocess.check_call(
			[
				shutil.which( "oslc", path = env["ENV"]["PATH"] ) if env["PLATFORM"] == "win32" else "oslc",
				"-I./shaders",
				"-o",
				str( target[0] ), str( source[0] )
			],
			env = env["ENV"]
		)

	for oslShader in libraryDef.get( "oslShaders", [] ) :
		env.Alias( "build", oslShader )
		compiledFile = commandEnv.Command( os.path.join( installRoot, os.path.splitext( oslShader )[0] + ".oso" ), oslShader, buildOSL )
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
		stubFileName = os.path.join( installRoot, classStub[1], classStub[1].rpartition( "/" )[2] + "-1.py" )
		stubEnv = env.Clone(
			GAFFER_STUB_MODULE = libraryName,
			GAFFER_STUB_CLASS = classStub[0],
		)
		stub = stubEnv.Command( stubFileName, "", buildClassStub )
		stubEnv.Alias( "build", stub )

#########################################################################################################
# Graphics
#########################################################################################################

def buildImageCommand( source, target, env ) :

	# Requires env to have buildImageOptions set, containing, at minimum:
	#	- id : The svg object id to export.

	svgFilename = str( source[0] )
	filename = str( target[0] )

	substitutions = validateAndFlattenImageOptions( env["buildImageOptions"], svgFilename )

	outputDirectory = os.path.dirname( filename )
	if not os.path.isdir( outputDirectory ) :
		os.makedirs( outputDirectory )

	args = [
		env["INKSCAPE"],
		"--export-id={}".format( substitutions["id"] ),
		"--export-width={:d}".format( substitutions["width"] ),
		"--export-height={:d}".format( substitutions["height"] ),
		"--export-background-opacity=0"
	]
	if env["INKSCAPE_USE_EXPORT_FILENAME"] :
		args += [
			"--export-filename={}".format( os.path.abspath( filename ) ),
			"--export-overwrite",
		]
	else :
		args.append( "--export-png={}".format( os.path.abspath( filename ) ) )
	args.append( os.path.abspath( svgFilename ) )

	subprocess.check_call( args )

def validateAndFlattenImageOptions( imageOptions, svg ) :

	id_ = imageOptions["id"]

	svgObjectInfo = svgQuery( svg, id_ )
	if svgObjectInfo is None :
		raise RuntimeError( "Object with id '%s' not found" % id_ )

	width = int( round( svgObjectInfo["width"] ) )
	height = int( round( svgObjectInfo["height"] ) )

	# Ensure images are properly pixel aligned and optionally, a specific size.
	# Transparent container objects should be used where the artwork is of a shape that precludes this.

	if imageOptions.get( "validatePixelAlignment", True ):
		if width != svgObjectInfo["width"] or height != svgObjectInfo["height"] :
			raise RuntimeError(
				"Object with id '%s' is not aligned to pixel boundaries w: %s h: %s" %
					( id_, svgObjectInfo["width"], svgObjectInfo["height"] )
			)

	# Optional exact dimension validation

	vw = imageOptions.get( "requiredWidth", None )
	vh = imageOptions.get( "requiredHeight", None )
	if ( vw and width != vw ) or ( vh and height != vh ) :
		raise RuntimeError( "Object '%s' is %dx%d must be %dx%d" % ( id_, width, height, vw, vh ) )

	return {
		"id" : id_,
		"width" : width,
		"height" : height
	}

# svgQuery is relatively slow as it requires running inkscape, which can be ~1s on macOS.
# As we know any given svg is constant during a build and we can retrieve all object info
# in one go, we cache per file.
__svgQueryCache = {}

def svgQuery( svgFile, id_ ) :

	filepath = os.path.abspath( svgFile )

	objects = __svgQueryCache.get( svgFile, None )
	if objects is None :

		objects = {}

		output = subprocess.check_output( [ env["INKSCAPE"], "--query-all", filepath ], universal_newlines=True )
		for line in output.split( "\n" ) :
			tokens = line.split( "," )
			# <id>,<x>,<y>,<width>,<height>
			if len(tokens) != 5 :
				continue
			objects[ tokens[0] ] = {
				"width" : float( tokens[3] ),
				"height" : float( tokens[4] )
			}

		__svgQueryCache[ svgFile ] = objects

	return objects.get( id_, None )

def imagesToBuild( definitionFile ) :

	with open( definitionFile ) as f :
		exports = eval( f.read() )

	toBuild = []

	# For each image, we must, at the very least, define:
	#   id  : The svg object id
	#   filename : The target filename

	def searchWalk( root, parentOptions ) :

		rootOptions = parentOptions.copy()
		rootOptions.update( root.get( "options", {} ) )

		for i in root.get( "ids", [] ) :
			imageOptions = rootOptions.copy()
			imageOptions["id"] = i
			imageOptions["filename"] = i + ".png"
			toBuild.append( imageOptions )

		for definition in root.get( "groups", {} ).values() :
			searchWalk( definition, rootOptions )

	searchWalk( exports, {} )

	return toBuild

# Bitmaps can be generated from inkscape compatible svg files, using the
# `graphicsCommands` helper.  In order to build images, you need two things:
#
#   - An svg file with one or more well-known object IDs
#   - A sidecar python definitions file that lists the IDs to build. This must
#     live next to the svg, with the same name.
#
# You can then add in a graphics builds as follows (output directories will be
# made for you):
#
#	cmds = graphicsCommands( env, <svgPath>, <outputDirectory> )
#	env.Alias( "build", cmds )
#
# The definition file must be `eval`able to define a single `exports`
# dictionary, structured as follows:
#
#	{
#		# Required (unless "groups" are provided)
#			"ids" : [ <id str>, ... ],
#		# Optional
#			"options" = { ... },
#			# Each entry in this dict follows the same structure as the outer dict
#			# to allow different options to be set for groups of images. The keys are
#			# purely for organisational purposes, and don't affect image generation.
#			"groups" : { ... }
#	}
#
# Options :
#
#	- requiredWidth [int] : If set error if images are not of the supplied width.
#	- requiredHeight [int] : If set error if images are not of the supplied height.
#	- validatePixelAlignment [bool] : If True (default), error if objects aren't aligned to the pixel grid.
#
def graphicsCommands( env, svg, outputDirectory ) :

	commands = []

	definitionFile = svg.replace( ".svg", ".py" )

	try :

		# Manually construct the Action so we can hash in the build options
		buildAction = Action( buildImageCommand, "Exporting '$TARGET' from '$SOURCE'", varlist=[ "buildImageOptions" ] )

		for options in imagesToBuild( definitionFile ) :
			targetPath = os.path.join( outputDirectory, options["filename"] )
			buildEnv = env.Clone( buildImageOptions = options )
			commands.append( buildEnv.Command( targetPath, svg, buildAction ) )

	except Exception as e :
		raise RuntimeError( "%s: %s" % ( svg, e ) )

	return commands

def buildQtResourceFile( source, target, env ) :

	# Make `.qrc` file specifying what to include.
	qrcFileName = os.path.splitext( str( target[0] ) )[0] + ".qrc"

	with open( qrcFileName, "w" ) as qrcFile :
		qrcFile.write( "<!DOCTYPE RCC><RCC version=\"1.0\">\n<qresource>\n" )
		for s in source :
			qrcFile.write( "\t<file>{}</file>\n".format( os.path.basename( str( s ) ) ) )
		qrcFile.write( "</qresource>\n</RCC>\n" )

	# Run `rcc` on that to generate the resource file, and then clean up.
	subprocess.check_call(
		[ shutil.which( "rcc", path = env["ENV"]["PATH"] ), qrcFileName, "--binary", "-o", str( target[0] ) ],
		env = env["ENV"]
	)
	os.remove( qrcFileName )

# Gaffer UI Images

if haveInkscape :

	for source in ( "resources/graphics.svg", "resources/GafferLogo.svg", "resources/GafferLogoMini.svg" ) :
		env.Alias( "build", graphicsCommands( env, source, "$BUILD_DIR/graphics" ) )

	resourceGraphics = set()
	with open( "python/GafferUI/_StyleSheet.py" ) as styleSheet :
		for line in styleSheet.readlines() :
			m = re.search( r"^[^#]*url\((.*)\)", line )
			if m :
				url = m.group( 1 )
				if not url.startswith( ":/" ) :
					sys.stderr.write( "ERROR : URL \"{}\" does not point to a Qt resource file.\n".format( url ) )
					Exit( 1 )
				resourceGraphics.add( "$BUILD_DIR/graphics/{}".format( url[2:] ) )

	env.Alias( "build", commandEnv.Command( "$BUILD_DIR/graphics/resources.rcc", sorted( resourceGraphics ), buildQtResourceFile ) )

else :

	sys.stderr.write( "WARNING : Inkscape not found - not building graphics. Check INKSCAPE build variable.\n" )

#########################################################################################################
# Resources
#########################################################################################################

resources = None
if commandEnv.subst( "$LOCATE_DEPENDENCY_RESOURCESPATH" ) :

	resources = []
	resourceRoot = commandEnv.subst( "$LOCATE_DEPENDENCY_RESOURCESPATH" )
	for root, dirs, files in os.walk( resourceRoot ) :
		for f in files :
			fullPath = os.path.join( root, f )
			resources.append( commandEnv.Command( fullPath.replace( resourceRoot, "$BUILD_DIR/resources/", 1 ), fullPath, Copy( "$TARGET", "$SOURCE" ) ) )

	commandEnv.NoCache( resources )
	commandEnv.Alias( "build", resources )

#########################################################################################################
# Documentation
#########################################################################################################

def generateDocs( target, source, env ) :

	# Run a script in the document source tree. These are used to
	# autogenerate source files for processing by sphinx.

	root = os.path.dirname( str(source[0]) )
	localFile = os.path.basename( str(source[0]) )

	ext = os.path.splitext( localFile )[1]
	command = []
	if localFile == "screengrab.py" :
		command = [ "gaffer", "screengrab", "-commandFile", localFile ]
	elif ext == ".py" :
		command = [ "gaffer", "env", "python", localFile ]
	elif ext == ".sh" :
		command = [ "gaffer", "env", "./" + localFile ]
	if command :
		sys.stdout.write( "Running {0}\n".format( os.path.join( root, localFile ) ) )
		subprocess.check_call( command, cwd = root, env = env["ENV"] )

def locateDocs( docRoot, env ) :

	# Locate files in the document source tree which are used by
	# sphinx to generate the final html.

	commands = []
	sources = [ docRoot ]

	for root, dirs, files in os.walk( docRoot ) :
		for f in files :
			sourceFile = os.path.join( root, f )
			sources.append( sourceFile )
			ext = os.path.splitext( f )[1]
			if ext in ( ".py", ".sh" ) :
				with open( sourceFile ) as s :
					line = s.readline()
					# the first line in a shell script is the language
					# specifier so we need the second line
					if ext == ".sh" :
						line = s.readline()
					targets = []
					dependencies = []
					while line.startswith( ( "# BuildTarget:", "# BuildDependency:" ) ) :
						if line.startswith( "# BuildTarget:" ) :
							targets.extend( [ os.path.join( root, x ) for x in line.partition( "# BuildTarget:" )[-1].strip( " \n" ).split( " " ) ] )
						elif line.startswith( "# BuildDependency:" ) :
							dependencies.extend( [ os.path.join( root, x ) for x in line.partition( "# BuildDependency:" )[-1].strip( " \n" ).split( " " ) ] )
						line = s.readline()
					if targets :
						command = env.Command( targets, sourceFile, generateDocs )
						env.Depends( command, "build" )
						if dependencies :
							env.Depends( command, dependencies )
						if line.startswith( "# UndeclaredBuildTargets" ) :
							env.NoCache( command )
						# Force the commands to run serially, in case the doc generation
						# has been run in parallel. Otherwise we can get overlapping
						# screengrabs from the commands that launch Gaffer UIs.
						if commands :
							env.Depends( command, commands[-1] )
						commands.append( command )
						sources.extend( targets )

	return sources, commands

def buildDocs( target, source, env ) :

	# Run sphinx to generate the final documentation.

	subprocess.check_call(
		[
			findOnPath( env.subst( "$SPHINX" ), env["ENV"]["PATH"] ),
			"-b", "html",
			str( source[0] ), os.path.dirname( str( target[0] ) )
		],
		env = env["ENV"]
	)

if haveSphinx and haveInkscape :

	# We build docs in the standard environment rather than commandEnv, so we can
	# use host python to avoid needing a matrix of sphinx versions to match Gaffer's
	# bundled python version.
	docEnv = env.Clone()
	docEnv["ENV"]["PYTHONPATH"] = ":".join( sys.path )

	# Since we don't copy the docs reference scripts, the screengrab
	# scripts must read them from the source, so we use the reference
	# env var. We also extend startup paths to include any config
	# we need for the docs to build correctly.
	docCommandEnv = commandEnv.Clone()
	docCommandEnv["ENV"]["GAFFER_REFERENCE_PATHS"] = os.path.abspath( "doc/references" )
	docCommandEnv["ENV"]["GAFFER_STARTUP_PATHS"] = os.path.abspath( "doc/startup" )

	# Ensure that Arnold, Appleseed and 3delight are available in the documentation
	# environment.

	libraryPathEnvVar = "DYLD_LIBRARY_PATH" if docEnv["PLATFORM"]=="darwin" else "LD_LIBRARY_PATH"

	if docCommandEnv.subst( "$ARNOLD_ROOT" ) :
		docCommandEnv["ENV"]["PATH"] += ":" + docCommandEnv.subst( "$ARNOLD_ROOT/bin" )
		docCommandEnv["ENV"]["PYTHONPATH"] += ":" + docCommandEnv.subst( "$ARNOLD_ROOT/python" )
		docCommandEnv["ENV"][libraryPathEnvVar] = docCommandEnv["ENV"].get( libraryPathEnvVar, "" ) + ":" + docCommandEnv.subst( "$ARNOLD_ROOT/bin" )

	if docCommandEnv.subst( "$APPLESEED_ROOT" ) and docCommandEnv["APPLESEED_ROOT"] != "$BUILD_DIR/appleseed" :
		docCommandEnv["ENV"]["PATH"] += ":" + docCommandEnv.subst( "$APPLESEED_ROOT/bin" )
		docCommandEnv["ENV"][libraryPathEnvVar] = docCommandEnv["ENV"].get( libraryPathEnvVar, "" ) + ":" + docCommandEnv.subst( "$APPLESEED_ROOT/lib" )
		docCommandEnv["ENV"]["OSLHOME"] = docCommandEnv.subst( "$OSLHOME" )
		docCommandEnv["ENV"]["OSL_SHADER_PATHS"] = docCommandEnv.subst( "$APPLESEED_ROOT/shaders/appleseed" )
		docCommandEnv["ENV"]["APPLESEED_SEARCHPATH"] = docCommandEnv.subst( "$APPLESEED_ROOT/shaders/appleseed:$LOCATE_DEPENDENCY_APPLESEED_SEARCHPATH" )

	#  Docs graphics generation
	docGraphicsCommands = graphicsCommands( docEnv, "resources/docGraphics.svg", "$BUILD_DIR/doc/gaffer/graphics" )
	docEnv.Alias( "docs", docGraphicsCommands )
	docSource, docGenerationCommands = locateDocs( "doc/source", docCommandEnv )
	docs = docEnv.Command( "$BUILD_DIR/doc/gaffer/html/index.html", docSource, buildDocs )
	# SCons doesn't know about the assorted outputs of sphinx, so only index.html ends up in the cache
	docEnv.NoCache( docs )
	docEnv.Depends( docGenerationCommands, docGraphicsCommands )
	docEnv.Depends( docs, docGraphicsCommands )
	docEnv.Depends( docs, "build" )
	docVars = docCommandEnv.Command( "doc/source/gafferVars.json", "doc/source/gafferVars.py", generateDocs )
	# Always build gafferVars otherwise an incorrect version could be retrieved from the cache
	docEnv.AlwaysBuild( docVars )
	docEnv.NoCache( docVars )
	docEnv.Depends( docs, docVars )
	if resources is not None :
		docEnv.Depends( docs, resources )
	docEnv.Alias( "docs", docs )

else :

	if not haveSphinx :
		sys.stderr.write( "WARNING : Sphinx not found - not building docs. Check SPHINX build variable.\n" )

	if not haveInkscape :
		sys.stderr.write( "WARNING : Inkscape not found - not building docs. Check INKSCAPE build variable.\n" )

#########################################################################################################
# Example files
#########################################################################################################

exampleFiles = []
for ext in ( 'gfr', 'grf', 'png' ) :
	exampleFiles += glob.glob( "doc/examples/*.%s" % ext )
	exampleFiles += glob.glob( "doc/examples/*/*.%s" % ext )
	exampleFiles += glob.glob( "doc/examples/*/*/*.%s" % ext )

for f in exampleFiles :
	fileInstall = env.Command( f.replace( "doc/", "$BUILD_DIR/resources/", 1 ), f, Copy( "$TARGET", "$SOURCE" ) )
	env.Alias( "build", fileInstall )

#########################################################################################################
# Installation
#########################################################################################################

def installer( target, source, env ) :

	distutils.dir_util.copy_tree( str( source[0] ), str( target[0] ), preserve_symlinks=True, update=True )

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
	elif target.endswith( ".zip" ) :
		shutil.make_archive( os.path.splitext( target )[0], "zip", root_dir=d, base_dir=b )
	else :
		runCommand( "tar -czf %s -C %s %s" % ( target, d, b ) )

package = env.Command( "$PACKAGE_FILE", "$INSTALL_DIR", packager )
env.NoCache( package )
env.Alias( "package", package )

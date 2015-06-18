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
import py_compile
import subprocess

###############################################################################################
# Version
###############################################################################################

gafferMilestoneVersion = 0 # for announcing major milestones - may contain all of the below
gafferMajorVersion = 14 # backwards-incompatible changes
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
	"g++",
)

options.Add(
	"CXXFLAGS",
	"The extra flags to pass to the C++ compiler during compilation.",
	[ "-pipe", "-Wall", "-Werror", "-O3", "-DNDEBUG", "-DBOOST_DISABLE_ASSERTS" ]
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
	"APPLESEED_INCLUDE_PATH",
	"The path to the appleseed include directory. Used to build Gafferseed",
	"$BUILD_DIR/appleseed/include",
)

options.Add(
	"APPLESEED_LIB_PATH",
	"The path to the appleseed lib directory. Used to build Gafferseed",
	"$BUILD_DIR/appleseed/lib",
)

# variables to be used when making a build which will use dependencies previously
# installed in some central location, rather than using the precompiled dependencies
# provided by the gafferDependencies project.

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

	GAFFER_MILESTONE_VERSION = str( gafferMilestoneVersion ),
	GAFFER_MAJOR_VERSION = str( gafferMajorVersion ),
	GAFFER_MINOR_VERSION = str( gafferMinorVersion ),
	GAFFER_PATCH_VERSION = str( gafferPatchVersion ),

	CPPDEFINES = [
		( "GAFFER_MILESTONE_VERSION", "$GAFFER_MILESTONE_VERSION" ),
		( "GAFFER_MAJOR_VERSION", "$GAFFER_MAJOR_VERSION" ),
		( "GAFFER_MINOR_VERSION", "$GAFFER_MINOR_VERSION" ),
		( "GAFFER_PATCH_VERSION", "$GAFFER_PATCH_VERSION" ),
	]

)

for e in env["ENV_VARS_TO_IMPORT"].split() :
	if e in os.environ :
		env["ENV"][e] = os.environ[e]

if env["PLATFORM"] == "darwin" :

	env["ENV"]["MACOSX_DEPLOYMENT_TARGET"] = "10.4"
	env.Append( CXXFLAGS = [ "-D__USE_ISOC99" ] )
	env["GAFFER_PLATFORM"] = "osx"

elif env["PLATFORM"] == "posix" :

	# gcc 4.1.2 in conjunction with boost::flat_map produces crashes when
	# using the -fstrict-aliasing optimisation (which defaults to on with -O2),
	# so we turn the optimisation off here, only for that specific gcc version.
	if "g++" in os.path.basename( env["CXX"] ) :
		gccVersion = subprocess.Popen( [ env["CXX"], "-dumpversion" ], env=env["ENV"], stdout=subprocess.PIPE ).stdout.read().strip()
		if gccVersion == "4.1.2" :
			env.Append( CXXFLAGS = [ "-fno-strict-aliasing" ] )

	env["GAFFER_PLATFORM"] = "linux"

if env["BUILD_CACHEDIR"] != "" :
	CacheDir( env["BUILD_CACHEDIR"] )

###############################################################################################
# An environment for running commands with access to the applications we've built
###############################################################################################

commandEnv = env.Clone()
commandEnv["ENV"]["PATH"] = commandEnv.subst( "$BUILD_DIR/bin:" ) + commandEnv["ENV"]["PATH"]

if commandEnv["PLATFORM"]=="darwin" :
	commandEnv["ENV"]["DYLD_LIBRARY_PATH"] = commandEnv.subst( "$BUILD_DIR/lib" )
else :
	commandEnv["ENV"]["LD_LIBRARY_PATH"] = commandEnv.subst( "$BUILD_DIR/lib" )

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

	CPPPATH = [
		"include",
	] + env["LOCATE_DEPENDENCY_CPPPATH"],

	CPPFLAGS = [
		"-DBOOST_FILESYSTEM_VERSION=3",
		"-DBOOST_SIGNALS_NO_DEPRECATION_WARNING",
	],

	LIBPATH = [
		"./lib",
		"$BUILD_DIR/lib",
		"$LOCATE_DEPENDENCY_LIBPATH",
	],

	LIBS = [
		"boost_signals$BOOST_LIB_SUFFIX",
		"boost_iostreams$BOOST_LIB_SUFFIX",
		"boost_filesystem$BOOST_LIB_SUFFIX",
		"boost_date_time$BOOST_LIB_SUFFIX",
		"boost_thread$BOOST_LIB_SUFFIX",
		"boost_wave$BOOST_LIB_SUFFIX",
		"boost_regex$BOOST_LIB_SUFFIX",
		"boost_system$BOOST_LIB_SUFFIX",
		"tbb",
		"Imath$OPENEXR_LIB_SUFFIX",
		"IlmImf$OPENEXR_LIB_SUFFIX",
		"IECore$CORTEX_LIB_SUFFIX",
	],

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
			 # Prevent Qt clashing with boost::signals - we can remove
			 # this if we move to boost::signals2.
			 "CXXFLAGS" : [ "-DQT_NO_KEYWORDS" ],
		},
	},

	"GafferUITest" : {},

	"GafferCortex" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "GafferBindings", "GafferCortex" ],
		},
	},

	"GafferCortexTest" : {
		"additionalFiles" : glob.glob( "python/GafferTest/*/*" ) + glob.glob( "python/GafferCortexTest/*/*/*" ),
	},

	"GafferCortexUI" : {},

	"GafferCortexUITest" : {},

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
			"LIBS" : [ "Gaffer", "GafferUI", "GafferScene", "IECoreGL$CORTEX_LIB_SUFFIX", "GLEW$GLEW_LIB_SUFFIX" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "IECoreGL$CORTEX_LIB_SUFFIX", "GafferScene", "GafferUI", "GafferSceneUI" ],
		},
	},

	"GafferSceneUITest" : {},

	"GafferImage" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer", "Iex$OPENEXR_LIB_SUFFIX", "OpenImageIO$OIIO_LIB_SUFFIX", "OpenColorIO$OCIO_LIB_SUFFIX" ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "GafferBindings", "GafferImage" ],
		},
	},

	"GafferImageTest" : {
		"envAppends" : {
			"LIBS" : [ "Gaffer", "GafferImage", "OpenImageIO$OIIO_LIB_SUFFIX",  ],
		},
		"pythonEnvAppends" : {
			"LIBS" : [ "GafferImageTest", "GafferImageBindings" ],
		},
	},

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

	"GafferArnoldUITest" : {},

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

	"GafferRenderManUITest" : {},

	"GafferOSL" : {
		"envAppends" : {
			"CPPPATH" : [ "$BUILD_DIR/include/OSL" ],
			"LIBS" : [ "Gaffer", "GafferScene", "GafferImage", "OpenImageIO$OIIO_LIB_SUFFIX", "oslquery$OSL_LIB_SUFFIX", "oslexec$OSL_LIB_SUFFIX" ],
		},
		"pythonEnvAppends" : {
			"CPPPATH" : [ "$BUILD_DIR/include/OSL" ],
			"LIBS" : [ "GafferBindings", "GafferScene", "GafferImage", "GafferOSL" ],
		},
		"oslHeaders" : glob.glob( "shaders/*/*.h" ),
		"oslShaders" : glob.glob( "shaders/*/*.osl" ),
	},

	"GafferOSLUI" : {},

	"GafferOSLTest" : {
		"additionalFiles" : glob.glob( "python/GafferOSLTest/*/*" ),
	},

	"GafferOSLUITest" : {},

	"GafferAppleseed" : {
		"envAppends" : {
			"CPPPATH" : [ "$APPLESEED_INCLUDE_PATH" ],
			"LIBPATH" : [ "$APPLESEED_LIB_PATH" ],
			"LIBS" : [ "Gaffer", "GafferScene", "appleseed", "IECoreAppleseed$CORTEX_LIB_SUFFIX" ],
		},
		"pythonEnvAppends" : {
			"CPPPATH" : [ "$APPLESEED_INCLUDE_PATH" ],
			"LIBPATH" : [ "$APPLESEED_LIB_PATH" ],
			"LIBS" : [ "Gaffer", "GafferScene", "GafferBindings", "GafferAppleseed" ],
		},
		"requiredOptions" : [ "APPLESEED_INCLUDE_PATH", "APPLESEED_LIB_PATH" ],
	},

	"GafferAppleseedTest" : {},

	"GafferAppleseedUI" : {},

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
			( "ImagePremultiplyOp", "ops/image/premultiply" ),
			( "ImageUnpremultiplyOp", "ops/image/unpremultiply" ),
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
for library in ( "GafferUI", "GafferSceneUI", "GafferImageUI" ) :
	if env["PLATFORM"] == "darwin" :
		libraries[library]["envAppends"].setdefault( "FRAMEWORKS", [] ).append( "OpenGL" )
	else :
		libraries[library]["envAppends"]["LIBS"].append( "GL" )

# Add on Qt libraries to definitions - these vary from platform to platform
for library in ( "GafferUI", ) :
	if env["PLATFORM"] == "darwin" :
		libraries[library]["pythonEnvAppends"].setdefault( "FRAMEWORKPATH", [] ).append( "$BUILD_DIR/lib" )
		libraries[library]["pythonEnvAppends"].setdefault( "FRAMEWORKS", [] ).append( "QtCore" )
		libraries[library]["pythonEnvAppends"].setdefault( "FRAMEWORKS", [] ).append( "QtGui" )
	else :
		libraries[library]["pythonEnvAppends"]["LIBS"].append( "QtCore" )
		libraries[library]["pythonEnvAppends"]["LIBS"].append( "QtGui" )
		

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
		pythonModuleEnv["SHLIBSUFFIX"] = ".so"

		pythonModule = pythonModuleEnv.SharedLibrary( "python/" + libraryName + "/_" + libraryName, pythonModuleSource )
		pythonModuleEnv.Default( pythonModule )

		moduleInstall = pythonModuleEnv.Install( "$BUILD_DIR/python/" + libraryName, pythonModule )
		pythonModuleEnv.Alias( "build", moduleInstall )

	# python component of python module

	for pythonFile in glob.glob( "python/" + libraryName + "/*.py" ) :
		pythonFileInstall = env.Command( "$BUILD_DIR/" + pythonFile, pythonFile, "sed \"" + sedSubstitutions + "\" $SOURCE > $TARGET" )
		env.Alias( "build", pythonFileInstall )

	# additional files

	for additionalFile in libraryDef.get( "additionalFiles", [] ) :
		additionalFileInstall = env.InstallAs( "$BUILD_DIR/" + additionalFile, additionalFile )
		env.Alias( "build", additionalFileInstall )

	# osl headers

	for oslHeader in libraryDef.get( "oslHeaders", [] ) :
		oslHeaderInstall = env.InstallAs( "$BUILD_DIR/" + oslHeader, oslHeader )
		env.Alias( "oslHeaders", oslHeaderInstall )
		env.Alias( "build", oslHeaderInstall )

	# osl shaders

	for oslShader in libraryDef.get( "oslShaders", [] ) :
		oslShaderInstall = env.InstallAs( "$BUILD_DIR/" + oslShader, oslShader )
		env.Alias( "build", oslShader )
		compiledFile = commandEnv.Command( os.path.splitext( str( oslShaderInstall[0] ) )[0] + ".oso", oslShader, "oslc -I./shaders -o $TARGET $SOURCE" )
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

for source, target in (
	( "resources/graphics.svg", "arrowDown10.png" ),
	( "resources/GafferLogo.svg", "GafferLogo.png" ),
	( "resources/GafferLogoMini.svg", "GafferLogoMini.png" ),
) :

	graphicsBuild = env.Command( os.path.join( "$BUILD_DIR/graphics/", target ), source, buildGraphics )
	env.NoCache( graphicsBuild )
	env.Alias( "build", graphicsBuild )

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
for v in ( "BUILD_DIR", "GAFFER_MILESTONE_VERSION", "GAFFER_MAJOR_VERSION", "GAFFER_MINOR_VERSION", "GAFFER_PATCH_VERSION" ) :
	docEnv["ENV"][v] = docEnv[v]

docs = docEnv.Command( "doc/html/index.html", "doc/config/Doxyfile", "$DOXYGEN doc/config/Doxyfile" )
env.NoCache( docs )

for modulePath in ( "python/Gaffer", "python/GafferUI", "python/GafferScene", "python/GafferSceneUI" ) :

	module = os.path.basename( modulePath )
	mungedModule = docEnv.Command( "doc/python/" + module, modulePath + "/__init__.py", createDoxygenPython )
	docEnv.Depends( mungedModule, glob.glob( modulePath + "/*.py" ) )
	docEnv.Depends( docs, mungedModule )
	docEnv.NoCache( mungedModule )

docEnv.Depends( docs, glob.glob( "include/*/*.h" ) + glob.glob( "doc/doxygenPages/*.md" ) )

docInstall = docEnv.Install( "$BUILD_DIR/doc/gaffer", "doc/html" )
docEnv.Alias( "build", docInstall )

#########################################################################################################
# Installation
#########################################################################################################

## \todo I'm not convinced we need this manifest anymore. If everyone will be using
# the gafferDependencies project to seed their builds, then BUILD_DIR will only contain
# files from gafferDependencies (which has its own manifest) and files we explicitly
# built and definitely want packaged.
dependenciesManifest = [

	"bin/python",
	"bin/python*[0-9]", # get the versioned python binaries, but not python-config etc

	"bin/maketx",
	"bin/oslc",
	"bin/oslinfo",

	"lib/libboost_signals$BOOST_LIB_SUFFIX$SHLIBSUFFIX*",
	"lib/libboost_thread$BOOST_LIB_SUFFIX$SHLIBSUFFIX*",
	"lib/libboost_wave$BOOST_LIB_SUFFIX$SHLIBSUFFIX*",
	"lib/libboost_regex$BOOST_LIB_SUFFIX$SHLIBSUFFIX*",
	"lib/libboost_python$BOOST_LIB_SUFFIX$SHLIBSUFFIX*",
	"lib/libboost_date_time$BOOST_LIB_SUFFIX$SHLIBSUFFIX*",
	"lib/libboost_filesystem$BOOST_LIB_SUFFIX$SHLIBSUFFIX*",
	"lib/libboost_iostreams$BOOST_LIB_SUFFIX$SHLIBSUFFIX*",
	"lib/libboost_system$BOOST_LIB_SUFFIX$SHLIBSUFFIX*",
	"lib/libboost_chrono$BOOST_LIB_SUFFIX$SHLIBSUFFIX*",

	"lib/libIECore*$SHLIBSUFFIX",

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

	"lib/libLLVM*$SHLIBSUFFIX*",
	"lib/libosl*",

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

	"lib/libxerces-c*$SHLIBSUFFIX",

	"fonts",
	"ops",
	"procedurals",
	"resources",
	"shaders",

	"openColorIO",

	"glsl/IECoreGL",
	"glsl/*.frag",
	"glsl/*.vert",

	"doc/licenses",
	"doc/cortex/html",
	"doc/osl*",

	"python/IECore*",
	"python/shiboken.so",
	"python/PySide/*.py",
	"python/PySide/QtCore.so",
	"python/PySide/QtGui.so",
	"python/PySide/QtOpenGL.so",
	"python/sip.so",
	"python/PyQt*",
	"python/OpenGL",
	"python/PyOpenColorIO*",

	"include/IECore*",
	"include/boost",
	"include/GL",
	"include/OpenEXR",
	"include/python*",
	"include/tbb",
	"include/OSL",
	"include/OpenImageIO",
	"include/OpenColorIO",
	"include/QtCore",
	"include/QtGui",
	"include/QtOpenGL",

	"renderMan",
	"arnold",
	"appleseed",
	"appleseedDisplays",

]

gafferManifest = dependenciesManifest + [

	"bin/gaffer",
	"bin/gaffer.py",

	"LICENSE",

	"apps/*/*-1.py",

	"lib/libGaffer*$SHLIBSUFFIX",

	"startup/*/*.py",

	"graphics/*.png",

	"doc/gaffer/html",

	"python/Gaffer*",

	"include/Gaffer*",

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

	regex = re.compile( "|".join( [ fnmatch.translate( os.path.normpath( env.subst( "$BUILD_DIR/" + m ) ) ) for m in env["MANIFEST"] ] ) )
	copyTree( str( source[0] ), str( target[0] ), regex )

if env.subst( "$PACKAGE_FILE" ).endswith( ".dmg" ) :

	# if the packaging will make a disk image, then build an os x app bundle

	install = env.Command( "$INSTALL_DIR/Gaffer.app/Contents/Resources", "$BUILD_DIR", installer, MANIFEST=gafferManifest )
	env.AlwaysBuild( install )
	env.NoCache( install )
	env.Alias( "install", install )

	plistInstall = env.Install( "$INSTALL_DIR/Gaffer.app/Contents", "resources/Info.plist" )
	env.Alias( "install", plistInstall )

	gafferLink = env.Command( "$INSTALL_DIR/Gaffer.app/Contents/MacOS/gaffer", "", "ln -s ../Resources/bin/gaffer $TARGET" )
	env.Alias( "install", gafferLink )

else :

	install = env.Command( "$INSTALL_DIR", "$BUILD_DIR", installer, MANIFEST=gafferManifest )
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

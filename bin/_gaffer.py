##########################################################################
#
#  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

# This script is private and should not be called directly. Use the `gaffer`
# command to launch Gaffer (`gaffer.cmd` on Windows).
import os
import pathlib
import re
import sys

# Utilities
# =========

libraryPath = {
	"linux" : "LD_LIBRARY_PATH",
	"darwin" : "DYLD_LIBRARY_PATH",
	"win32" : "PATH",
}.get( sys.platform )

def appendToPath( pathToAppend, envVar ) :

	pathToAppend = str( pathToAppend )

	path = os.environ.get( envVar )
	path = path.split( os.pathsep ) if path else []

	if pathToAppend not in path :
		path.append( pathToAppend )

	os.environ[envVar] = os.pathsep.join( path )

def prependToPath( pathToPrepend, envVar ) :

	pathToPrepend = str( pathToPrepend )

	path = os.environ.get( envVar )
	path = path.split( os.pathsep ) if path else []

	if pathToPrepend not in path :
		path.insert( 0, pathToPrepend )

	os.environ[envVar] = os.pathsep.join( path )

gafferRoot = pathlib.Path( __file__ ).resolve().parents[1]

# Cortex Setup
# ============

prependToPath( gafferRoot / "glsl", "IECOREGL_SHADER_PATHS" )
prependToPath( gafferRoot / "glsl", "IECOREGL_SHADER_INCLUDE_PATHS" )
prependToPath( gafferRoot / "fonts", "IECORE_FONT_PATHS" )
prependToPath( gafferRoot / "ops", "IECORE_OP_PATHS" )
prependToPath( pathlib.Path.home() / "gaffer" / "ops", "IECORE_OP_PATHS" )
prependToPath( pathlib.Path.home() / "gaffer" / "opPresets", "IECORE_OP_PRESET_PATHS" )
prependToPath( pathlib.Path.home() / "gaffer" / "startup", "CORTEX_STARTUP_PATHS" )
appendToPath( gafferRoot / "startup", "CORTEX_STARTUP_PATHS" )

if "CORTEX_POINTDISTRIBUTION_TILESET" not in os.environ :
	os.environ["CORTEX_POINTDISTRIBUTION_TILESET"] = str( gafferRoot / "resources" / "cortex" / "tileset_2048.dat" )

if sys.platform in ( "linux", "darwin" ) :
	# Stop Cortex from making all Python modules load with RTLD_GLOBAL.
	os.environ["IECORE_RTLD_GLOBAL"] = "0"

# Load USD PointInstancer prototypes as relative paths by default. This allows
# the _PointInstancerAdaptor to function even when the instancers are reparented
# in the Gaffer hierarchy.
if "IECOREUSD_POINTINSTANCER_RELATIVE_PROTOTYPES" not in os.environ :
	os.environ["IECOREUSD_POINTINSTANCER_RELATIVE_PROTOTYPES"] = "1"

# Work around https://github.com/ImageEngine/cortex/issues/1338, which causes
# bad serialisations in certain locales.
os.environ["LC_NUMERIC"] = "C"

# Core Gaffer Setup
# =================

## \todo Do we really need `as_posix()` here? We use '\' separators
# for all the other paths on Windows.
os.environ["GAFFER_ROOT"] = gafferRoot.as_posix()

prependToPath( gafferRoot / "apps", "GAFFER_APP_PATHS" )
prependToPath( pathlib.Path.home() / "gaffer" / "apps", "GAFFER_APP_PATHS" )
prependToPath( pathlib.Path.home() / "gaffer" / "startup", "GAFFER_STARTUP_PATHS" )
appendToPath( gafferRoot / "startup", "GAFFER_STARTUP_PATHS" )
prependToPath( gafferRoot / "graphics", "GAFFERUI_IMAGE_PATHS" )
prependToPath( gafferRoot / "python", "PYTHONPATH" )
prependToPath( gafferRoot / "lib", libraryPath )
prependToPath( gafferRoot / "bin", "PATH" )

if sys.platform == "darwin" :
	prependToPath( gafferRoot / "lib", "DYLD_FRAMEWORK_PATH" )
elif sys.platform == "win32" :
	appendToPath( gafferRoot / "lib", "IECORE_DLL_DIRECTORIES" )

# OSL Setup
# =========

if ( gafferRoot / "bin" / "oslc" ).exists() :
	os.environ["OSLHOME"] = str( gafferRoot )

## \todo Should we rename these to "osl" to match our "glsl" folder?
prependToPath( gafferRoot / "shaders", "OSL_SHADER_PATHS" )
prependToPath( pathlib.Path.home() / "gaffer" / "shaders", "OSL_SHADER_PATHS" )

if "GAFFEROSL_CODE_DIRECTORY" not in os.environ :
	os.environ["GAFFEROSL_CODE_DIRECTORY"] = str( pathlib.Path.home() / "gaffer" / "oslCode" )
	appendToPath( os.environ["GAFFEROSL_CODE_DIRECTORY"], "OSL_SHADER_PATHS" )

# USD Setup
# =========

prependToPath( gafferRoot / "resources" / "IECoreUSD", "PXR_PLUGINPATH_NAME" )
prependToPath( gafferRoot / "materialX", "PXR_MTLX_STDLIB_SEARCH_PATHS" )

if sys.platform == "win32" and "PXR_USD_WINDOWS_DLL_PATH" not in os.environ :
	# Prevent USD from adding entries from `PATH` to Python binary search paths.
	os.environ["PXR_USD_WINDOWS_DLL_PATH"] = ""

# Cycles Setup
# ============

def setUpCycles() :

	if "CYCLES_ROOT" in os.environ :
		cyclesRoot = pathlib.Path( os.environ["CYCLES_ROOT"] )
	else :
		cyclesRoot = gafferRoot / "cycles"
		if not cyclesRoot.exists() :
			return
		os.environ["CYCLES_ROOT"] = str( cyclesRoot )

	prependToPath( cyclesRoot / "bin", "PATH" )

setUpCycles()

# Arnold Setup
# ============

def setUpArnold() :

	# Determine Arnold version.

	if "ARNOLD_ROOT" not in os.environ :
		return

	arnoldRoot = pathlib.Path( os.environ.get( "ARNOLD_ROOT" ) )
	versionHeader = pathlib.Path( arnoldRoot / "include" / "ai_version.h" )
	if not versionHeader.exists() :
		sys.stderr.write( "ERROR : unable to find \"{}\".\n".format( versionHeader ) )
		return

	arnoldVersions = {}
	for line in open( versionHeader ) :
		m = re.match( r"^#define AI_VERSION_(ARCH|MAJOR)_NUM\s*([0-9]+)", line )
		if m :
			arnoldVersions[m.group(1)] = m.group( 2 )
			if len( arnoldVersions ) == 2 :
				break

	if set( arnoldVersions.keys() ) != { "ARCH", "MAJOR" } :
		sys.stderr.write( "ERROR : unable to parse \"{}\".\n".format( versionHeader ) )
		return

	# Put GafferArnold on the appropriate paths.

	arnoldPluginVersion = "{ARCH}.{MAJOR}".format( **arnoldVersions )
	pluginRoot = gafferRoot / "arnold" / arnoldPluginVersion

	if pluginRoot.exists() :
		prependToPath( pluginRoot, "GAFFER_EXTENSION_PATHS" )
		prependToPath( pluginRoot / "arnoldPlugins", "ARNOLD_PLUGIN_PATH" )
	else :
		sys.stderr.write( "WARNING : GafferArnold extension not available for Arnold {}\n".format( arnoldPluginVersion ) )
		return

	# Put Arnold's own libs and binaries on the appropriate paths.

	appendToPath( arnoldRoot / "bin", libraryPath )
	appendToPath( arnoldRoot / "bin", "PATH" )
	appendToPath( arnoldRoot / "python", "PYTHONPATH" )
	prependToPath( arnoldRoot / "plugins", "ARNOLD_PLUGIN_PATH" )

	# Disable Autodesk Analytics, unless it is being explicitly managed already
	# by setting `ARNOLD_ADP_OPTIN` or `ARNOLD_ADP_DISABLE`.
	if "ARNOLD_ADP_OPTIN" not in os.environ and "ARNOLD_ADP_DISABLE" not in os.environ :
		os.environ["ARNOLD_ADP_DISABLE"] = "1"

setUpArnold()

# 3Delight Setup
# ==============

def setUp3Delight() :

	if "DELIGHT" not in os.environ :
		return

	delight = pathlib.Path( os.environ["DELIGHT"] )

	appendToPath( delight / "lib", libraryPath )
	appendToPath( delight / "bin", "PATH" )
	appendToPath( delight / "python", "PYTHONPATH" )
	appendToPath( delight / "osl", "OSL_SHADER_PATHS" )
	# For backwards compatibility - can be removed when users have had time to
	# update to `$DELIGHT/osl` pathed shaders.
	appendToPath( delight, "OSL_SHADER_PATHS" )

setUp3Delight()

# ONNX Setup
# ==========

def setUpONNX() :

	if "ONNX_ROOT" not in os.environ :
		return

	onnxRoot = pathlib.Path( os.environ.get( "ONNX_ROOT" ) )
	appendToPath( onnxRoot / "lib", libraryPath )

setUpONNX()

# RenderMan Setup
# ===============

def setUpRenderMan() :

	# Determine RenderMan version.

	if "RMANTREE" not in os.environ or os.environ.get( "GAFFERRENDERMAN_FEATURE_PREVIEW", "0" ) != "1" :
		return

	rmanTree = pathlib.Path( os.environ.get( "RMANTREE" ) )
	renderManHeader = pathlib.Path( rmanTree / "include" / "prmanapi.h" )
	if not renderManHeader.exists() :
		sys.stderr.write( "ERROR : unable to find \"{}\".\n".format( renderManHeader ) )
		return

	renderManVersions = {}
	for line in open( renderManHeader ) :
		m = re.match( r"^#define _PRMANAPI_VERSION_(MAJOR|MINOR)_\s*([0-9]+)", line )
		if m :
			renderManVersions[m.group(1)] = m.group( 2 )
			if len( renderManVersions ) == 2 :
				break

	if set( renderManVersions.keys() ) != { "MAJOR", "MINOR" } :
		sys.stderr.write( "ERROR : unable to parse \"{}\".\n".format( renderManHeader ) )
		return

	renderManPluginVersion = "{MAJOR}.{MINOR}".format( **renderManVersions )

	# Set up paths.

	pluginRoot = gafferRoot / "renderMan" / renderManPluginVersion
	prependToPath( pluginRoot, "GAFFER_EXTENSION_PATHS" )

	appendToPath( rmanTree / "lib", libraryPath )
	appendToPath( rmanTree / "bin", "PATH" )
	appendToPath( rmanTree / "bin", "PYTHONPATH" )
	appendToPath( rmanTree / "lib" / "plugins", "RMAN_RIXPLUGINPATH" )
	appendToPath( rmanTree / "lib" / "shaders", "OSL_SHADER_PATHS" )
	appendToPath( pluginRoot / "plugins", "RMAN_DISPLAYS_PATH" )

	if sys.platform == "win32" :
		appendToPath( rmanTree / "bin", "IECORE_DLL_DIRECTORIES" )
		appendToPath( rmanTree / "lib", "IECORE_DLL_DIRECTORIES" )

setUpRenderMan()

# 3rd Party Extension Setup
# =========================

def setUp3rdPartyExtensions() :

	paths = os.environ.get( "GAFFER_EXTENSION_PATHS" )
	if not paths :
		return

	for path in paths.split( os.pathsep ) :

		extensionRoot = pathlib.Path( path )
		appendToPath( extensionRoot / "lib", libraryPath )
		appendToPath( extensionRoot / "bin", "PATH" )
		appendToPath( extensionRoot / "python", "PYTHONPATH" )
		appendToPath( extensionRoot / "apps", "GAFFER_APP_PATHS" )
		appendToPath( extensionRoot / "graphics", "GAFFERUI_IMAGE_PATHS" )
		appendToPath( extensionRoot / "glsl", "IECOREGL_SHADER_PATHS" )
		appendToPath( extensionRoot / "glsl", "IECOREGL_SHADER_INCLUDE_PATHS" )
		appendToPath( extensionRoot / "shaders", "OSL_SHADER_PATHS" )
		prependToPath( extensionRoot / "startup", "GAFFER_STARTUP_PATHS" )

		if sys.platform == "win32" :
			appendToPath( extensionRoot / "lib", "IECORE_DLL_DIRECTORIES" )

setUp3rdPartyExtensions()

# Qt Setup
# ========

os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str( gafferRoot / "qt" / "plugins" )

# Work around issue with Qt 5.12+ when using a wacom tablet on linux.
#   See https://bugreports.qt.io/browse/QTBUG-77826
# This can hopefully be removed once this patch is in:
#   https://codereview.qt-project.org/c/qt/qtbase/+/284141
os.environ["QT_XCB_TABLET_LEGACY_COORDINATES"] = "1"

if sys.platform == "win32" :
	os.environ["QT_OPENGL"] = "desktop"

# JEMalloc Setup
# ==============

if sys.platform == "linux" :
	if os.environ.get( "GAFFER_JEMALLOC", "1" ) != "0" :
		appendToPath( gafferRoot / "lib" / "libjemalloc.so", "LD_PRELOAD" )

# OIIO Setup
# ==========

if sys.platform == "win32" :
	os.environ["OIIO_LOAD_DLLS_FROM_PATH"] = "0"
elif sys.platform == "darwin" :
	# Not strictly OIIO-related, but works around clashes between our image
	# libraries and the system ones.
	prependToPath( "/System/Library/Frameworks/ApplicationServices.framework/Versions/A/Frameworks/ImageIO.framework/Resources", "DYLD_LIBRARY_PATH" )

# OCIO Setup
# ==========

if not os.environ.get( "OCIO" ) :
	os.environ["OCIO"] = "ocio://studio-config-v1.0.0_aces-v1.3_ocio-v2.1"

# Python Setup
# ============

if "PYTHONNOUSERSITE" not in os.environ :
	# Prevent Python automatically adding a user-level `site-packages`
	# directory to the `sys.path`. These frequently contain modules which
	# conflict with our own. Users who know what they are doing can set
	# `PYTHONNOUSERSITE=0` before running Gaffer if they want to use
	# the user directory.
	os.environ["PYTHONNOUSERSITE"] = "1"

# Exec `__gaffer.py`
# ==================

args = [
	sys.executable,
	str( pathlib.Path( sys.argv[0] ).with_name( "__gaffer.py" ) )
] + sys.argv[1:]

if sys.platform != "win32" :
	os.execv( sys.executable, args )
else :
	# On Windows, Python emulates `execv()` badly by launching another process
	# (rather than replacing this one) and not even waiting for it to finish.
	# Use `subprocess.run()` so we can at least wait and pass on the return
	# value.
	import subprocess
	sys.exit( subprocess.run( args ).returncode )

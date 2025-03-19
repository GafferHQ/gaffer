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

gafferRoot = pathlib.Path( os.environ["GAFFER_ROOT"] )

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

	appendToPath( rmanTree / "lib", libraryPath )
	appendToPath( pluginRoot / "lib", libraryPath )

	appendToPath( rmanTree / "bin", "PATH" )
	appendToPath( rmanTree / "bin", "PYTHONPATH" )
	appendToPath( pluginRoot / "python", "PYTHONPATH" )
	appendToPath( rmanTree / "lib" / "plugins", "RMAN_RIXPLUGINPATH" )
	appendToPath( pluginRoot / "plugins", "RMAN_DISPLAYS_PATH" )
	appendToPath( rmanTree / "lib" / "shaders", "OSL_SHADER_PATHS" )

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

setUp3rdPartyExtensions()

# JEMalloc Setup
# ==============

if sys.platform == "linux" :
	if os.environ.get( "GAFFER_JEMALLOC", "1" ) != "0" :
		appendToPath( gafferRoot / "lib" / "libjemalloc.so", "LD_PRELOAD" )

# OCIO Setup
# ==========

if not os.environ.get( "OCIO" ) :
	os.environ["OCIO"] = "ocio://studio-config-v1.0.0_aces-v1.3_ocio-v2.1"

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

##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2012-2015, Image Engine Design Inc. All rights reserved.
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
import traceback
import functools

import IECore

import Gaffer
import GafferScene
import GafferUI
import GafferSceneUI

# ScriptWindow menu
##########################################################################

scriptWindowMenu = GafferUI.ScriptWindow.menuDefinition( application )

GafferUI.ApplicationMenu.appendDefinitions( scriptWindowMenu, prefix="/Gaffer" )
GafferUI.FileMenu.appendDefinitions( scriptWindowMenu, prefix="/File" )
GafferUI.EditMenu.appendDefinitions( scriptWindowMenu, prefix="/Edit" )
GafferUI.LayoutMenu.appendDefinitions( scriptWindowMenu, name="/Layout" )
GafferUI.DispatcherUI.appendMenuDefinitions( scriptWindowMenu, prefix="/Execute" )
GafferUI.LocalDispatcherUI.appendMenuDefinitions( scriptWindowMenu, prefix="/Execute" )

## Help menu
###########################################################################

for menuItem, url in [
		( "User Guide", "$GAFFER_ROOT/doc/gaffer/html/index.html" ),
		( "Node Reference", "$GAFFER_ROOT/doc/gaffer/html/Reference/NodeReference/index.html" ),
		( "License", "$GAFFER_ROOT/doc/gaffer/html/Appendices/License/index.html" ),
		( "LocalDocsDivider", None ),
		( "Forum", "https://groups.google.com/forum/#!forum/gaffer-dev" ),
		( "Issue Tracker", "https://github.com/GafferHQ/gaffer/issues" ),
		( "CoreDocsDivider", None ),
	] :

	if url and "://" not in url :
		url = os.path.expandvars( url )
		url = "file://" + url if os.path.isfile( url ) else ""

	scriptWindowMenu.append(
		"/Help/" + menuItem,
		{
			"divider" : url is None,
			"command" : functools.partial( GafferUI.showURL, url ),
			"active" : bool( url )
		}
	)

## Node creation menu
###########################################################################

moduleSearchPath = IECore.SearchPath( os.environ["PYTHONPATH"], ":" )

nodeMenu = GafferUI.NodeMenu.acquire( application )

# Arnold nodes

if moduleSearchPath.find( "arnold" ) :

	try :

		import GafferArnold
		import GafferArnoldUI

		GafferArnoldUI.ShaderMenu.appendShaders( nodeMenu.definition() )

		nodeMenu.append( "/Arnold/Displacement", GafferArnold.ArnoldDisplacement, searchText = "ArnoldDisplacement"  )
		nodeMenu.append( "/Arnold/VDB", GafferArnold.ArnoldVDB, searchText = "ArnoldVDB"  )
		nodeMenu.append( "/Arnold/Options", GafferArnold.ArnoldOptions, searchText = "ArnoldOptions" )
		nodeMenu.append( "/Arnold/Attributes", GafferArnold.ArnoldAttributes, searchText = "ArnoldAttributes" )
		nodeMenu.append(
			"/Arnold/Render", GafferArnold.ArnoldRender,
			plugValues = {
				"fileName" : "${project:rootDirectory}/asses/${script:name}/${script:name}.####.ass",
			},
			searchText = "ArnoldRender"
		)
		nodeMenu.append( "/Arnold/Interactive Render", GafferArnold.InteractiveArnoldRender, searchText = "InteractiveArnoldRender" )
		nodeMenu.append( "/Arnold/Shader Ball", GafferArnold.ArnoldShaderBall, searchText = "ArnoldShaderBall" )

		GafferArnoldUI.CacheMenu.appendDefinitions( scriptWindowMenu, "/Tools/Arnold" )

	except Exception, m :

		stacktrace = traceback.format_exc()
		IECore.msg( IECore.Msg.Level.Error, "startup/gui/menus.py", "Error loading Arnold module - \"%s\".\n %s" % ( m, stacktrace ) )

# RenderMan nodes

if "DELIGHT" in os.environ :

	try :

		import GafferRenderMan
		import GafferRenderManUI

		GafferRenderManUI.ShaderMenu.appendShaders( nodeMenu.definition() )

		nodeMenu.append( "/RenderMan/Attributes", GafferRenderMan.RenderManAttributes, searchText = "RenderManAttributes" )
		nodeMenu.append( "/RenderMan/Options", GafferRenderMan.RenderManOptions, searchText = "RenderManOptions" )
		nodeMenu.append(
			"/RenderMan/Render", GafferRenderMan.RenderManRender,
			plugValues = {
				"ribFileName" : "${project:rootDirectory}/ribs/${script:name}/${script:name}.####.rib",
			},
			searchText = "RenderManRender"
		)
		nodeMenu.append( "/RenderMan/Interactive Render", GafferRenderMan.InteractiveRenderManRender, searchText = "InteractiveRenderManRender" )
		nodeMenu.append( "/RenderMan/Shader Ball", GafferRenderMan.RenderManShaderBall, searchText = "RenderManShaderBall" )

		scriptWindowMenu.append(
			"/Help/3Delight/User Guide",
			{
				"command" : functools.partial( GafferUI.showURL, os.path.expandvars( "$DELIGHT/doc/3Delight-UserManual.pdf" ) ),
			}
		)

	except Exception, m :

		stacktrace = traceback.format_exc()
		IECore.msg( IECore.Msg.Level.Error, "startup/gui/menus.py", "Error loading RenderMan module - \"%s\".\n %s" % ( m, stacktrace ) )

# appleseed nodes

if "APPLESEED" in os.environ :

	try :

		import GafferAppleseed
		import GafferAppleseedUI
		import GafferOSL
		import GafferOSLUI

		def __shaderNodeCreator( nodeName, shaderName ) :

			node = GafferOSL.OSLShader( nodeName )
			node.loadShader( shaderName )

			return node

		GafferSceneUI.ShaderUI.appendShaders(
			nodeMenu.definition(), "/Appleseed/Shader",
			os.environ["APPLESEED_SEARCHPATH"].split( ":" ),
			[ "oso" ],
			__shaderNodeCreator,
			# Show only the OSL shaders from the Appleseed shader
			# library.
			matchExpression = re.compile( "(^|.*/)as_[^/]*$")
		)

		GafferAppleseedUI.LightMenu.appendLights( nodeMenu.definition() )

		nodeMenu.append( "/Appleseed/Attributes", GafferAppleseed.AppleseedAttributes, searchText = "AppleseedAttributes" )
		nodeMenu.append( "/Appleseed/Options", GafferAppleseed.AppleseedOptions, searchText = "AppleseedOptions" )
		nodeMenu.append(
			"/Appleseed/Render", GafferAppleseed.AppleseedRender,
			plugValues = {
				"fileName" : "${project:rootDirectory}/appleseeds/${script:name}/${script:name}.####.appleseed",
			},
			searchText = "AppleseedRender"
		)
		nodeMenu.append( "/Appleseed/Interactive Render", GafferAppleseed.InteractiveAppleseedRender, searchText = "InteractiveAppleseedRender" )
		nodeMenu.append( "/Appleseed/Shader Ball", GafferAppleseed.AppleseedShaderBall, searchText = "AppleseedShaderBall" )

		scriptWindowMenu.append(
			"/Help/Appleseed/User Docs",
			{
				"command" : functools.partial( GafferUI.showURL, "https://github.com/appleseedhq/appleseed/wiki" ),
			}
		)

	except Exception, m :

		stacktrace = traceback.format_exc()
		IECore.msg( IECore.Msg.Level.Error, "startup/gui/menus.py", "Error loading Appleseed module - \"%s\".\n %s" % ( m, stacktrace ) )

# Scene nodes

nodeMenu.append( "/Scene/File/Reader", GafferScene.SceneReader, searchText = "SceneReader" )
nodeMenu.append( "/Scene/File/Writer", GafferScene.SceneWriter, searchText = "SceneWriter" )
nodeMenu.append( "/Scene/File/Alembic", GafferScene.AlembicSource, searchText = "AlembicSource" )
nodeMenu.append( "/Scene/Source/Object To Scene", GafferScene.ObjectToScene, searchText = "ObjectToScene" )
nodeMenu.append( "/Scene/Source/Camera", GafferScene.Camera )
nodeMenu.append( "/Scene/Source/Coordinate System", GafferScene.CoordinateSystem, searchText = "CoordinateSystem" )
nodeMenu.append( "/Scene/Source/Clipping Plane", GafferScene.ClippingPlane, searchText = "ClippingPlane" )
nodeMenu.append( "/Scene/Source/External Procedural", GafferScene.ExternalProcedural, searchText = "ExternalProcedural" )
nodeMenu.append( "/Scene/Source/Grid", GafferScene.Grid )
nodeMenu.append( "/Scene/Source/Primitive/Cube", GafferScene.Cube )
nodeMenu.append( "/Scene/Source/Primitive/Plane", GafferScene.Plane )
nodeMenu.append( "/Scene/Source/Primitive/Sphere", GafferScene.Sphere )
nodeMenu.append( "/Scene/Source/Primitive/Text", GafferScene.Text )
nodeMenu.append( "/Scene/Source/Seeds", GafferScene.Seeds )
nodeMenu.append( "/Scene/Source/Instancer", GafferScene.Instancer )
nodeMenu.append( "/Scene/Object/Primitive Variables", GafferScene.PrimitiveVariables, searchText = "PrimitiveVariables" )
nodeMenu.append( "/Scene/Object/Delete Primitive Variables", GafferScene.DeletePrimitiveVariables, searchText = "DeletePrimitiveVariables" )
nodeMenu.append( "/Scene/Object/Mesh Type", GafferScene.MeshType, searchText = "MeshType" )
nodeMenu.append( "/Scene/Object/Points Type", GafferScene.PointsType, searchText = "PointsType" )
nodeMenu.append( "/Scene/Object/Mesh To Points", GafferScene.MeshToPoints, searchText = "MeshToPoints" )
nodeMenu.append( "/Scene/Object/Light To Camera", GafferScene.LightToCamera, searchText = "LightToCamera" )
nodeMenu.append( "/Scene/Object/Map Projection", GafferScene.MapProjection, searchText = "MapProjection" )
nodeMenu.append( "/Scene/Object/Map Offset", GafferScene.MapOffset, searchText = "MapOffset"  )
nodeMenu.append( "/Scene/Object/Parameters", GafferScene.Parameters )
nodeMenu.append( "/Scene/Attributes/Shader Assignment", GafferScene.ShaderAssignment, searchText = "ShaderAssignment" )
nodeMenu.append( "/Scene/Attributes/Shader Switch", GafferScene.ShaderSwitch, searchText = "ShaderSwitch" )
nodeMenu.append( "/Scene/Attributes/Standard Attributes", GafferScene.StandardAttributes, searchText = "StandardAttributes" )
nodeMenu.append( "/Scene/Attributes/Custom Attributes", GafferScene.CustomAttributes, searchText = "CustomAttributes" )
nodeMenu.append( "/Scene/Attributes/Delete Attributes", GafferScene.DeleteAttributes, searchText = "DeleteAttributes" )
nodeMenu.append( "/Scene/Attributes/Attribute Visualiser", GafferScene.AttributeVisualiser, searchText = "AttributeVisualiser" )
nodeMenu.append( "/Scene/Attributes/Light Tweaks", GafferScene.LightTweaks, searchText = "LightTweaks" )
nodeMenu.append( "/Scene/Filters/Set Filter", GafferScene.SetFilter, searchText = "SetFilter" )
nodeMenu.append( "/Scene/Filters/Path Filter", GafferScene.PathFilter, searchText = "PathFilter" )
nodeMenu.append( "/Scene/Filters/Union Filter", GafferScene.UnionFilter, searchText = "UnionFilter" )
nodeMenu.append( "/Scene/Filters/FilterSwitch", GafferScene.FilterSwitch, searchText = "FilterSwitch" )
nodeMenu.append( "/Scene/Hierarchy/Group", GafferScene.Group )
nodeMenu.append( "/Scene/Hierarchy/Parent", GafferScene.Parent )
nodeMenu.append( "/Scene/Hierarchy/Duplicate", GafferScene.Duplicate )
nodeMenu.append( "/Scene/Hierarchy/SubTree", GafferScene.SubTree ) #\todo - rename to 'Subtree' (node needs to change too)
nodeMenu.append( "/Scene/Hierarchy/Prune", GafferScene.Prune )
nodeMenu.append( "/Scene/Hierarchy/Isolate", GafferScene.Isolate )
nodeMenu.append( "/Scene/Hierarchy/Switch", GafferScene.SceneSwitch, searchText = "SceneSwitch" )
nodeMenu.append( "/Scene/Transform/Transform", GafferScene.Transform )
nodeMenu.append( "/Scene/Transform/Freeze Transform", GafferScene.FreezeTransform, searchText = "FreezeTransform" )
nodeMenu.append( "/Scene/Transform/Point Constraint", GafferScene.PointConstraint, searchText = "PointConstraint" )
nodeMenu.append( "/Scene/Transform/Aim Constraint", GafferScene.AimConstraint, searchText = "AimConstraint" )
nodeMenu.append( "/Scene/Transform/Parent Constraint", GafferScene.ParentConstraint, searchText = "ParentConstraint" )
nodeMenu.append( "/Scene/Context/Time Warp", GafferScene.SceneTimeWarp, searchText = "SceneTimeWarp" )
nodeMenu.append( "/Scene/Context/Variables", GafferScene.SceneContextVariables, searchText = "SceneContextVariables" )
nodeMenu.append( "/Scene/Context/Loop", GafferScene.SceneLoop, searchText = "SceneLoop"  )
nodeMenu.append( "/Scene/Globals/Outputs", GafferScene.Outputs )
nodeMenu.append( "/Scene/Globals/Delete Outputs", GafferScene.DeleteOutputs, searchText = "DeleteOutputs" )
nodeMenu.append( "/Scene/Globals/Delete Sets", GafferScene.DeleteSets, searchText = "DeleteSets" )
nodeMenu.append( "/Scene/Globals/Standard Options", GafferScene.StandardOptions, searchText = "StandardOptions" )
nodeMenu.append( "/Scene/Globals/Custom Options", GafferScene.CustomOptions, searchText = "CustomOptions" )
nodeMenu.append( "/Scene/Globals/Delete Options", GafferScene.DeleteOptions, searchText = "DeleteOptions" )
nodeMenu.append( "/Scene/Globals/Copy Options", GafferScene.CopyOptions, searchText = "CopyOptions" )
nodeMenu.append( "/Scene/Globals/Set", GafferScene.Set )
nodeMenu.append( "/Scene/OpenGL/Attributes", GafferScene.OpenGLAttributes, searchText = "OpenGLAttributes" )
nodeMenu.definition().append( "/Scene/OpenGL/Shader", { "subMenu" : GafferSceneUI.OpenGLShaderUI.shaderSubMenu } )
nodeMenu.append( "/Scene/OpenGL/Render", GafferScene.OpenGLRender, searchText = "OpenGLRender" )

# Image nodes

import GafferImage
import GafferImageUI

nodeMenu.append( "/Image/Source/Display", GafferImage.Display )
nodeMenu.append( "/Image/Source/Reader", GafferImage.ImageReader, searchText = "ImageReader" )
nodeMenu.append( "/Image/Source/Writer", GafferImage.ImageWriter, searchText = "ImageWriter" )
nodeMenu.append( "/Image/Shape/Text", GafferImage.Text, postCreator = GafferImageUI.TextUI.postCreate )
nodeMenu.append( "/Image/Color/Clamp", GafferImage.Clamp )
nodeMenu.append( "/Image/Color/Constant", GafferImage.Constant )
nodeMenu.append( "/Image/Color/Grade", GafferImage.Grade )
nodeMenu.append( "/Image/Color/CDL", GafferImage.CDL )
nodeMenu.append( "/Image/Color/ColorSpace", GafferImage.ColorSpace )
nodeMenu.append( "/Image/Color/DisplayTransform", GafferImage.DisplayTransform )
nodeMenu.append( "/Image/Color/LUT", GafferImage.LUT )
nodeMenu.append( "/Image/Color/Premultiply", GafferImage.Premultiply )
nodeMenu.append( "/Image/Color/Unpremultiply", GafferImage.Unpremultiply )
nodeMenu.append( "/Image/Filter/Blur", GafferImageUI.BlurUI.nodeMenuCreateCommand )
nodeMenu.append( "/Image/Filter/Median", GafferImageUI.MedianUI.nodeMenuCreateCommand )
nodeMenu.append( "/Image/Merge/Merge", GafferImage.Merge )
nodeMenu.append( "/Image/Merge/Mix", GafferImage.Mix )
nodeMenu.append( "/Image/Merge/Switch", GafferImage.ImageSwitch, searchText = "ImageSwitch" )
nodeMenu.append( "/Image/Transform/Resize", GafferImage.Resize )
nodeMenu.append( "/Image/Transform/Transform", GafferImage.ImageTransform, searchText = "ImageTransform" )
nodeMenu.append( "/Image/Transform/Crop", GafferImage.Crop, postCreator = GafferImageUI.CropUI.postCreate )
nodeMenu.append( "/Image/Transform/Offset", GafferImage.Offset )
nodeMenu.append( "/Image/Transform/Mirror", GafferImage.Mirror )
nodeMenu.append( "/Image/Warp/VectorWarp", GafferImage.VectorWarp )
nodeMenu.append( "/Image/Channels/Shuffle", GafferImageUI.ShuffleUI.nodeMenuCreateCommand, searchText = "Shuffle" )
nodeMenu.append( "/Image/Channels/Copy", GafferImage.CopyChannels, searchText = "CopyChannels" )
nodeMenu.append( "/Image/Channels/Delete", GafferImage.DeleteChannels, searchText = "DeleteChannels" )
nodeMenu.append( "/Image/Context/Time Warp", GafferImage.ImageTimeWarp, searchText = "ImageTimeWarp" )
nodeMenu.append( "/Image/Context/Variables", GafferImage.ImageContextVariables, searchText = "ImageContextVariables"  )
nodeMenu.append( "/Image/Context/Loop", GafferImage.ImageLoop, searchText = "ImageLoop"  )
nodeMenu.append( "/Image/Utility/Metadata", GafferImage.ImageMetadata, searchText = "ImageMetadata" )
nodeMenu.append( "/Image/Utility/Delete Metadata", GafferImage.DeleteImageMetadata, searchText = "DeleteImageMetadata" )
nodeMenu.append( "/Image/Utility/Copy Metadata", GafferImage.CopyImageMetadata, searchText = "CopyImageMetadata" )
nodeMenu.append( "/Image/Utility/Stats", GafferImage.ImageStats, searchText = "ImageStats", postCreator = GafferImageUI.ImageStatsUI.postCreate  )
nodeMenu.append( "/Image/Utility/Sampler", GafferImage.ImageSampler, searchText = "ImageSampler" )

# OSL nodes

if moduleSearchPath.find( "GafferOSL" ) :

	import GafferOSL
	import GafferOSLUI

	def __shaderNodeCreator( nodeName, shaderName ) :

		node = GafferOSL.OSLShader( nodeName )
		node.loadShader( shaderName )

		return node

	GafferSceneUI.ShaderUI.appendShaders(
		nodeMenu.definition(), "/OSL/Shader",
		os.environ["OSL_SHADER_PATHS"].split( ":" ),
		[ "oso" ],
		__shaderNodeCreator,
		# Appleseed comes with a library of OSL shaders which we put
		# on the OSL_SHADER_PATHS, but we don't want to show them in
		# this menu, because we show them in the Appleseed menu instead.
		#
		# The OSLCode node also generates a great many shaders behind
		# the scenes that we don't want to place in the menus. Typically
		# these aren't on the OSL_SHADER_PATHS anyway because they are
		# given to the renderer via absolute paths, but at the time of
		# writing it is necessary to place them on the OSL_SHADER_PATHS
		# in order to use them in Arnold. We don't enable this by default
		# because it causes Arnold to potentially load a huge number of
		# shader plugins at startup, but we hide any oslCode shaders here
		# in case someone else enables it.
		#
		# This match expression filters both categories of shader out :
		#
		# - (^|.*/) matches any number (including zero) of directory
		#   names preceding the shader name.
		# - (?!as_|oslCode) is a negative lookahead, asserting that the shader
		#   name does not start with "as_", the prefix for all
		#   Appleseed shaders, or "oslCode", the prefix for all OSLCode
		#   shaders.
		# - [^/]*$ matches the rest of the shader name, ensuring it
		#   doesn't include any directory separators.
		matchExpression = re.compile( "(^|.*/)(?!as_|oslCode)[^/]*$"),
		searchTextPrefix = "osl",
	)

	nodeMenu.append( "/OSL/Code", GafferOSL.OSLCode, searchText = "OSLCode" )
	nodeMenu.append( "/OSL/Image", GafferOSL.OSLImage, searchText = "OSLImage" )
	nodeMenu.append( "/OSL/Object", GafferOSL.OSLObject, searchText = "OSLObject" )

	oslDocs = os.path.expandvars( "$GAFFER_ROOT/doc/osl-languagespec.pdf" )
	scriptWindowMenu.append(
		"/Help/Open Shading Language/Language Reference",
		{
			"active" : os.path.exists( oslDocs ),
			"command" : functools.partial( GafferUI.showURL, oslDocs ),
		}
	)

# Dispatch nodes

import GafferDispatch
import GafferDispatchUI

nodeMenu.append( "/Dispatch/System Command", GafferDispatch.SystemCommand, searchText = "SystemCommand" )
nodeMenu.append( "/Dispatch/Python Command", GafferDispatch.PythonCommand, searchText = "PythonCommand" )
nodeMenu.append( "/Dispatch/Task List", GafferDispatch.TaskList, searchText = "TaskList" )
nodeMenu.append( "/Dispatch/Task Switch", GafferDispatch.TaskSwitch, searchText = "TaskSwitch" )
nodeMenu.append( "/Dispatch/Wedge", GafferDispatch.Wedge )
nodeMenu.append( "/Dispatch/Variables", GafferDispatch.TaskContextVariables, searchText = "TaskContextVariables" )

# Utility nodes

nodeMenu.append( "/Utility/Expression", Gaffer.Expression )
nodeMenu.append( "/Utility/Node", Gaffer.Node )
nodeMenu.append( "/Utility/Random", Gaffer.Random )
nodeMenu.append( "/Utility/Box", GafferUI.BoxUI.nodeMenuCreateCommand )
nodeMenu.append( "/Utility/BoxIn", Gaffer.BoxIn )
nodeMenu.append( "/Utility/BoxOut", Gaffer.BoxOut )
nodeMenu.append( "/Utility/Reference", GafferUI.ReferenceUI.nodeMenuCreateCommand )
nodeMenu.definition().append( "/Utility/Backdrop", { "command" : GafferUI.BackdropUI.nodeMenuCreateCommand } )
nodeMenu.append( "/Utility/Dot", Gaffer.Dot )
nodeMenu.append( "/Utility/Switch", functools.partial( Gaffer.SwitchComputeNode, "Switch" ) )

## Miscellaneous UI
###########################################################################

GafferUI.DotUI.connect( application.root() )

with IECore.IgnoredExceptions( ImportError ) :

	import GafferTractorUI

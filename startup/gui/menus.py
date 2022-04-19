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
import GafferDispatchUI
import GafferSceneUI

# ScriptWindow menu
##########################################################################

scriptWindowMenu = GafferUI.ScriptWindow.menuDefinition( application )

GafferUI.ApplicationMenu.appendDefinitions( scriptWindowMenu, prefix="/Gaffer" )
GafferUI.FileMenu.appendDefinitions( scriptWindowMenu, prefix="/File" )
GafferUI.EditMenu.appendDefinitions( scriptWindowMenu, prefix="/Edit" )
GafferUI.LayoutMenu.appendDefinitions( scriptWindowMenu, name="/Layout" )
GafferDispatchUI.DispatcherUI.appendMenuDefinitions( scriptWindowMenu, prefix="/Execute" )
GafferDispatchUI.LocalDispatcherUI.appendMenuDefinitions( scriptWindowMenu, prefix="/Execute" )
GafferUI.GraphBookmarksUI.appendScriptWindowMenuDefinitions( scriptWindowMenu, prefix="/Edit" )

# Turn on backups by default, so they are supported by the open functions
# in the file menu. They can be turned off again in the preferences menu.
GafferUI.Backups.acquire( application )

## Help menu
###########################################################################

def addHelpMenuItems( items ) :

	for menuItem, url in items:

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

addHelpMenuItems( [
		( "User Guide", "$GAFFER_ROOT/doc/gaffer/html/index.html" ),
		( "Node Reference", "$GAFFER_ROOT/doc/gaffer/html/Reference/NodeReference/index.html" )
] )

GafferUI.Examples.appendExamplesSubmenuDefinition( scriptWindowMenu, "/Help/Examples" )

addHelpMenuItems( [
		( "License", "$GAFFER_ROOT/doc/gaffer/html/Appendices/License/index.html" ),
		( "LocalDocsDivider", None ),
		( "Forum", "https://groups.google.com/forum/#!forum/gaffer-dev" ),
		( "Issue Tracker", "https://github.com/GafferHQ/gaffer/issues" ),
		( "CoreDocsDivider", None )
] )


## Node creation menu
###########################################################################

moduleSearchPath = IECore.SearchPath( os.environ["PYTHONPATH"] )

nodeMenu = GafferUI.NodeMenu.acquire( application )

# Arnold nodes

if moduleSearchPath.find( "arnold" ) :

	try :

		import GafferArnold
		import GafferArnoldUI
		import arnold

		GafferArnoldUI.ShaderMenu.appendShaders( nodeMenu.definition() )

		nodeMenu.append( "/Arnold/Globals/Options", GafferArnold.ArnoldOptions, searchText = "ArnoldOptions" )
		nodeMenu.append( "/Arnold/Globals/Atmosphere", GafferArnold.ArnoldAtmosphere, searchText = "ArnoldAtmosphere" )
		nodeMenu.append( "/Arnold/Globals/Background", GafferArnold.ArnoldBackground, searchText = "ArnoldBackground" )
		nodeMenu.append( "/Arnold/Globals/AOVShader", GafferArnold.ArnoldAOVShader, searchText = "ArnoldAOVShader" )
		nodeMenu.append( "/Arnold/Globals/Imager", GafferArnold.ArnoldImager, searchText = "ArnoldImager" )
		nodeMenu.append( "/Arnold/Displacement", GafferArnold.ArnoldDisplacement, searchText = "ArnoldDisplacement"  )
		nodeMenu.append( "/Arnold/CameraShaders", GafferArnold.ArnoldCameraShaders, searchText = "ArnoldCameraShaders"  )
		nodeMenu.append( "/Arnold/VDB", GafferArnold.ArnoldVDB, searchText = "ArnoldVDB"  )
		nodeMenu.append( "/Arnold/Attributes", GafferArnold.ArnoldAttributes, searchText = "ArnoldAttributes" )
		nodeMenu.append( "/Arnold/Render", GafferArnold.ArnoldRender, searchText = "ArnoldRender" )
		nodeMenu.append( "/Arnold/Interactive Render", GafferArnold.InteractiveArnoldRender, searchText = "InteractiveArnoldRender" )
		nodeMenu.append( "/Arnold/Shader Ball", GafferArnold.ArnoldShaderBall, searchText = "ArnoldShaderBall" )
		nodeMenu.append( "/Arnold/Arnold Texture Bake", GafferArnold.ArnoldTextureBake, searchText = "ArnoldTextureBake" )

		GafferArnoldUI.CacheMenu.appendDefinitions( scriptWindowMenu, "/Tools/Arnold" )

		scriptWindowMenu.append(
			"/Tools/Arnold/Populate GPU Cache",
			{
				"command" : GafferArnoldUI.GPUCache.populateGPUCache,
			}
		)

	except Exception as m :

		stacktrace = traceback.format_exc()
		IECore.msg( IECore.Msg.Level.Error, "startup/gui/menus.py", "Error loading Arnold module - \"%s\".\n %s" % ( m, stacktrace ) )

# 3delight nodes

if moduleSearchPath.find( "nsi.py" ) and moduleSearchPath.find( "GafferDelight" ) :

	try :

		import GafferOSL
		import GafferDelight
		import GafferDelightUI

		def __shaderNodeCreator( nodeName, shaderName ) :

			node = GafferOSL.OSLShader( nodeName )
			node.loadShader( "maya/osl/" + shaderName )

			return node

		for label, shader in [
			( "Standard", "material3Delight" ),
			( "Glass", "material3DelightGlass" ),
			( "Metal", "material3DelightMetal" ),
			( "Skin", "material3DelightSkin" ),
			( "Hair", "materialHairAndFur" ),
		] :

			nodeMenu.append(
				"/3Delight/Shader/" + label,
				functools.partial( __shaderNodeCreator, label, shader ),
				searchText = "dl" + label
			)

		GafferSceneUI.ShaderUI.appendShaders(
			nodeMenu.definition(), "/3Delight/Shader/Maya",
			[ os.path.join( os.environ["DELIGHT"], "maya", "osl" ) ],
			[ "oso" ],
			__shaderNodeCreator,
			matchExpression = re.compile( "^[^_].*$"),
			searchTextPrefix = "maya"
		)

		def __lightCreator( nodeName, shaderName, shape ) :

			node = GafferOSL.OSLLight( nodeName )
			node.loadShader( shaderName )

			if isinstance( shape, node.Shape ) :
				node["shape"].setValue( shape )
			else  :
				node["shape"].setValue( node.Shape.Geometry )
				node["geometryType"].setValue( "dl:environment" )
				Gaffer.Metadata.registerValue( node["geometryType"], "plugValueWidget:type", "" )
				Gaffer.Metadata.registerValue( node["geometryBound"], "plugValueWidget:type", "" )
				Gaffer.Metadata.registerValue( node["geometryParameters"], "plugValueWidget:type", "" )

				if shape == "distant" :
					node["geometryParameters"].addChild( Gaffer.NameValuePlug( "angle", 0.0, name = "angle", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

			Gaffer.Metadata.registerValue( node["shape"], "plugValueWidget:type", "" )

			visibilityPlug = Gaffer.NameValuePlug( "dl:visibility.camera", False, "cameraVisibility", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
			node["attributes"].addChild( visibilityPlug )
			Gaffer.Metadata.registerValue( visibilityPlug, "nameValuePlugPlugValueWidget:ignoreNamePlug", True )
			Gaffer.MetadataAlgo.setReadOnly( visibilityPlug["name"], True )

			return node

		for label, shader, shape in [
			[ "PointLight", "maya/osl/pointLight", GafferOSL.OSLLight.Shape.Sphere ],
			[ "SpotLight", "maya/osl/spotLight", GafferOSL.OSLLight.Shape.Disk ],
			[ "DistantLight", "maya/osl/distantLight", "distant" ],
			[ "EnvironmentLight", "maya/osl/environmentLight", "environment" ],
		] :
			nodeMenu.append(
				"/3Delight/Light/" + label,
				functools.partial( __lightCreator, label, shader, shape ),
				searchText = "dl" + label
			)

		nodeMenu.append( "/3Delight/Attributes", GafferDelight.DelightAttributes, searchText = "DelightAttributes"  )
		nodeMenu.append( "/3Delight/Options", GafferDelight.DelightOptions, searchText = "DelightOptions"  )
		nodeMenu.append( "/3Delight/Render", GafferDelight.DelightRender, searchText = "DelightRender"  )
		nodeMenu.append( "/3Delight/Interactive Render", GafferDelight.InteractiveDelightRender, searchText = "InteractiveDelightRender"  )

	except Exception as m :

		stacktrace = traceback.format_exc()
		IECore.msg( IECore.Msg.Level.Error, "startup/gui/menus.py", "Error loading Delight module - \"%s\".\n %s" % ( m, stacktrace ) )

# appleseed nodes

if "APPLESEED" in os.environ :

	try :

		import GafferAppleseed
		import GafferAppleseedUI
		import GafferOSL
		import GafferOSLUI

		if os.environ.get( "GAFFERAPPLESEED_HIDE_UI", "" ) != "1" :

			GafferAppleseedUI.ShaderMenu.appendShaders( nodeMenu.definition() )

			GafferAppleseedUI.LightMenu.appendLights( nodeMenu.definition() )

			nodeMenu.append( "/Appleseed/Attributes", GafferAppleseed.AppleseedAttributes, searchText = "AppleseedAttributes" )
			nodeMenu.append( "/Appleseed/Options", GafferAppleseed.AppleseedOptions, searchText = "AppleseedOptions" )
			nodeMenu.append( "/Appleseed/Render", GafferAppleseed.AppleseedRender, searchText = "AppleseedRender" )
			nodeMenu.append( "/Appleseed/Interactive Render", GafferAppleseed.InteractiveAppleseedRender, searchText = "InteractiveAppleseedRender" )
			nodeMenu.append( "/Appleseed/Shader Ball", GafferAppleseed.AppleseedShaderBall, searchText = "AppleseedShaderBall" )

			scriptWindowMenu.append(
				"/Help/Appleseed/User Docs",
				{
					"command" : functools.partial( GafferUI.showURL, "https://github.com/appleseedhq/appleseed/wiki" ),
				}
			)

	except Exception as m :

		stacktrace = traceback.format_exc()
		IECore.msg( IECore.Msg.Level.Error, "startup/gui/menus.py", "Error loading Appleseed module - \"%s\".\n %s" % ( m, stacktrace ) )

# Scene nodes

nodeMenu.append( "/Scene/File/Reader", GafferScene.SceneReader, searchText = "SceneReader" )
nodeMenu.append( "/Scene/File/Writer", GafferScene.SceneWriter, searchText = "SceneWriter" )
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
nodeMenu.append( "/Scene/Source/MotionPath", GafferScene.MotionPath )
nodeMenu.append( "/Scene/Object/Primitive Variables", GafferScene.PrimitiveVariables, searchText = "PrimitiveVariables" )
nodeMenu.append( "/Scene/Object/Copy Primitive Variables", GafferScene.CopyPrimitiveVariables, searchText = "CopyPrimitiveVariables" )
nodeMenu.append( "/Scene/Object/Delete Primitive Variables", GafferScene.DeletePrimitiveVariables, searchText = "DeletePrimitiveVariables" )
nodeMenu.append( "/Scene/Object/Shuffle Primitive Variables", GafferScene.ShufflePrimitiveVariables, searchText = "ShufflePrimitiveVariables" )
nodeMenu.append( "/Scene/Object/Resample Primitive Variables", GafferScene.ResamplePrimitiveVariables, searchText = "ResamplePrimitiveVariables" )
nodeMenu.append( "/Scene/Object/Collect Primitive Variables", GafferScene.CollectPrimitiveVariables, searchText = "CollectPrimitiveVariables" )
nodeMenu.append( "/Scene/Object/Orientation", GafferScene.Orientation )
nodeMenu.append( "/Scene/Object/Mesh Type", GafferScene.MeshType, searchText = "MeshType" )
nodeMenu.append( "/Scene/Object/Points Type", GafferScene.PointsType, searchText = "PointsType" )
nodeMenu.append( "/Scene/Object/Mesh To Points", GafferScene.MeshToPoints, searchText = "MeshToPoints" )
nodeMenu.append( "/Scene/Object/Wireframe", GafferScene.Wireframe )
nodeMenu.append( "/Scene/Object/Light To Camera", GafferScene.LightToCamera, searchText = "LightToCamera" )
nodeMenu.append( "/Scene/Object/Map Projection", GafferScene.MapProjection, searchText = "MapProjection" )
nodeMenu.append( "/Scene/Object/Map Offset", GafferScene.MapOffset, searchText = "MapOffset"  )
nodeMenu.append( "/Scene/Object/Parameters", GafferScene.Parameters )
nodeMenu.append( "/Scene/Object/Mesh Tangents", GafferScene.MeshTangents, searchText = "MeshTangents", postCreator = GafferSceneUI.MeshTangentsUI.postCreate )
nodeMenu.append( "/Scene/Object/Delete Faces", GafferScene.DeleteFaces, searchText = "DeleteFaces" )
nodeMenu.append( "/Scene/Object/Delete Curves", GafferScene.DeleteCurves, searchText = "DeleteCurves" )
nodeMenu.append( "/Scene/Object/Delete Points", GafferScene.DeletePoints, searchText = "DeletePoints" )
nodeMenu.append( "/Scene/Object/Delete Object", GafferScene.DeleteObject, searchText = "DeleteObject" )
nodeMenu.append( "/Scene/Object/Reverse Winding", GafferScene.ReverseWinding, searchText = "ReverseWinding" )
nodeMenu.append( "/Scene/Object/Mesh Distortion", GafferScene.MeshDistortion, searchText = "MeshDistortion" )
nodeMenu.append( "/Scene/Object/Camera Tweaks", GafferScene.CameraTweaks, searchText = "CameraTweaks" )
nodeMenu.append( "/Scene/Object/Curve Sampler", GafferScene.CurveSampler, searchText = "CurveSampler" )
nodeMenu.append( "/Scene/Object/Closest Point Sampler", GafferScene.ClosestPointSampler, searchText = "ClosestPointSampler" )
nodeMenu.append( "/Scene/Object/UV Sampler", GafferScene.UVSampler, searchText = "UVSampler" )
nodeMenu.append( "/Scene/Attributes/Shader Assignment", GafferScene.ShaderAssignment, searchText = "ShaderAssignment" )
nodeMenu.append( "/Scene/Attributes/Shader Tweaks", GafferScene.ShaderTweaks, searchText = "ShaderTweaks" )
nodeMenu.append( "/Scene/Attributes/Standard Attributes", GafferScene.StandardAttributes, searchText = "StandardAttributes" )
nodeMenu.append( "/Scene/Attributes/Custom Attributes", GafferScene.CustomAttributes, searchText = "CustomAttributes" )
nodeMenu.append( "/Scene/Attributes/Delete Attributes", GafferScene.DeleteAttributes, searchText = "DeleteAttributes" )
nodeMenu.append( "/Scene/Attributes/Shuffle Attributes", GafferScene.ShuffleAttributes, searchText = "ShuffleAttributes" )
nodeMenu.append( "/Scene/Attributes/Localise Attributes", GafferScene.LocaliseAttributes, searchText = "LocaliseAttributes" )
nodeMenu.append( "/Scene/Attributes/Attribute Visualiser", GafferScene.AttributeVisualiser, searchText = "AttributeVisualiser" )
nodeMenu.append( "/Scene/Attributes/Attribute Tweaks", GafferScene.AttributeTweaks, searchText = "AttributeTweaks" )
nodeMenu.append( "/Scene/Attributes/Copy Attributes", GafferScene.CopyAttributes, searchText = "CopyAttributes" )
nodeMenu.append( "/Scene/Attributes/Collect Transforms", GafferScene.CollectTransforms, searchText = "CollectTransforms" )
nodeMenu.append( "/Scene/Filters/Set Filter", GafferScene.SetFilter, searchText = "SetFilter" )
nodeMenu.append( "/Scene/Filters/Path Filter", GafferScene.PathFilter, searchText = "PathFilter" )
nodeMenu.append( "/Scene/Filters/Union Filter", GafferScene.UnionFilter, searchText = "UnionFilter" )
nodeMenu.append( "/Scene/Hierarchy/Group", GafferScene.Group )
nodeMenu.append( "/Scene/Hierarchy/Parent", GafferScene.Parent )
nodeMenu.append( "/Scene/Hierarchy/Merge", GafferScene.MergeScenes, searchText = "MergeScenes" )
nodeMenu.append( "/Scene/Hierarchy/Duplicate", GafferScene.Duplicate )
nodeMenu.append( "/Scene/Hierarchy/SubTree", GafferScene.SubTree ) #\todo - rename to 'Subtree' (node needs to change too)
nodeMenu.append( "/Scene/Hierarchy/Prune", GafferScene.Prune )
nodeMenu.append( "/Scene/Hierarchy/Isolate", GafferScene.Isolate )
nodeMenu.append( "/Scene/Hierarchy/Collect", GafferScene.CollectScenes, searchText = "CollectScenes" )
nodeMenu.append( "/Scene/Hierarchy/Encapsulate", GafferScene.Encapsulate )
nodeMenu.append( "/Scene/Hierarchy/Unencapsulate", GafferScene.Unencapsulate )
nodeMenu.append( "/Scene/Transform/Transform", GafferScene.Transform )
nodeMenu.append( "/Scene/Transform/Freeze Transform", GafferScene.FreezeTransform, searchText = "FreezeTransform" )
nodeMenu.append( "/Scene/Transform/Point Constraint", GafferScene.PointConstraint, searchText = "PointConstraint" )
nodeMenu.append( "/Scene/Transform/Aim Constraint", GafferScene.AimConstraint, searchText = "AimConstraint" )
nodeMenu.append( "/Scene/Transform/Parent Constraint", GafferScene.ParentConstraint, searchText = "ParentConstraint" )
nodeMenu.append( "/Scene/Globals/Outputs", GafferScene.Outputs )
nodeMenu.append( "/Scene/Globals/Delete Outputs", GafferScene.DeleteOutputs, searchText = "DeleteOutputs" )
nodeMenu.append( "/Scene/Globals/Delete Sets", GafferScene.DeleteSets, searchText = "DeleteSets" )
nodeMenu.append( "/Scene/Globals/Standard Options", GafferScene.StandardOptions, searchText = "StandardOptions" )
nodeMenu.append( "/Scene/Globals/Custom Options", GafferScene.CustomOptions, searchText = "CustomOptions" )
nodeMenu.append( "/Scene/Globals/Delete Options", GafferScene.DeleteOptions, searchText = "DeleteOptions" )
nodeMenu.append( "/Scene/Globals/Copy Options", GafferScene.CopyOptions, searchText = "CopyOptions" )
nodeMenu.append( "/Scene/Globals/Set", GafferScene.Set )
nodeMenu.append( "/Scene/Globals/Set Visualiser", GafferScene.SetVisualiser, searchText = "SetVisualiser" )
nodeMenu.append( "/Scene/OpenGL/Attributes", GafferScene.OpenGLAttributes, searchText = "OpenGLAttributes" )
nodeMenu.definition().append( "/Scene/OpenGL/Shader", { "subMenu" : GafferSceneUI.OpenGLShaderUI.shaderSubMenu } )
nodeMenu.append( "/Scene/OpenGL/Render", GafferScene.OpenGLRender, searchText = "OpenGLRender" )
nodeMenu.append( "/Scene/Utility/Filter Query", GafferScene.FilterQuery, searchText = "FilterQuery" )
nodeMenu.append( "/Scene/Utility/Transform Query", GafferScene.TransformQuery, searchText = "TransformQuery" )
nodeMenu.append( "/Scene/Utility/Bound Query", GafferScene.BoundQuery, searchText = "BoundQuery" )
nodeMenu.append( "/Scene/Utility/Existence Query", GafferScene.ExistenceQuery, searchText = "ExistenceQuery" )
nodeMenu.append( "/Scene/Utility/Attribute Query", GafferScene.AttributeQuery, searchText = "AttributeQuery" )
nodeMenu.append( "/Scene/Utility/Shader Query", GafferScene.ShaderQuery, searchText = "ShaderQuery" )

# Image nodes

import GafferImage
import GafferImageUI

nodeMenu.append( "/Image/File/Reader", GafferImage.ImageReader, searchText = "ImageReader" )
nodeMenu.append( "/Image/File/Writer", GafferImage.ImageWriter, searchText = "ImageWriter" )
nodeMenu.append( "/Image/Shape/Rectangle", GafferImage.Rectangle, postCreator = GafferImageUI.RectangleUI.postCreate )
nodeMenu.append( "/Image/Shape/Text", GafferImage.Text, postCreator = GafferImageUI.TextUI.postCreate )
nodeMenu.append( "/Image/Pattern/Constant", GafferImage.Constant )
nodeMenu.append( "/Image/Pattern/Checkerboard", GafferImageUI.CheckerboardUI.nodeMenuCreateCommand )
nodeMenu.append( "/Image/Pattern/Ramp", GafferImage.Ramp, postCreator = GafferImageUI.RampUI.postCreate)
nodeMenu.append( "/Image/Color/Clamp", GafferImage.Clamp )
nodeMenu.append( "/Image/Color/Grade", GafferImage.Grade )
nodeMenu.append( "/Image/Color/CDL", GafferImage.CDL )
nodeMenu.append( "/Image/Color/ColorSpace", GafferImage.ColorSpace )
nodeMenu.append( "/Image/Color/DisplayTransform", GafferImage.DisplayTransform )
nodeMenu.append( "/Image/Color/LUT", GafferImage.LUT )
nodeMenu.append( "/Image/Color/Premultiply", GafferImage.Premultiply )
nodeMenu.append( "/Image/Color/Unpremultiply", GafferImage.Unpremultiply )
nodeMenu.append( "/Image/Color/Saturation", GafferImage.Saturation )
nodeMenu.append( "/Image/Filter/Blur", GafferImageUI.BlurUI.nodeMenuCreateCommand )
nodeMenu.append( "/Image/Filter/Median", GafferImageUI.MedianUI.nodeMenuCreateCommand )
nodeMenu.append( "/Image/Filter/Erode", GafferImageUI.ErodeUI.nodeMenuCreateCommand )
nodeMenu.append( "/Image/Filter/Dilate", GafferImageUI.DilateUI.nodeMenuCreateCommand )
nodeMenu.append( "/Image/Filter/BleedFill", GafferImage.BleedFill )
nodeMenu.append( "/Image/Matte/Cryptomatte", GafferScene.Cryptomatte, searchText = "Cryptomatte" )
nodeMenu.append( "/Image/Merge/Merge", GafferImage.Merge )
nodeMenu.append( "/Image/Merge/Mix", GafferImage.Mix )
nodeMenu.append( "/Image/Transform/Resize", GafferImage.Resize )
nodeMenu.append( "/Image/Transform/Transform", GafferImage.ImageTransform, searchText = "ImageTransform" )
nodeMenu.append( "/Image/Transform/Crop", GafferImage.Crop, postCreator = GafferImageUI.CropUI.postCreate )
nodeMenu.append( "/Image/Transform/Offset", GafferImage.Offset )
nodeMenu.append( "/Image/Transform/Mirror", GafferImage.Mirror )
nodeMenu.append( "/Image/Warp/VectorWarp", GafferImage.VectorWarp )
nodeMenu.append( "/Image/Channels/Shuffle", GafferImageUI.ShuffleUI.nodeMenuCreateCommand, searchText = "Shuffle" )
nodeMenu.append( "/Image/Channels/Copy", GafferImage.CopyChannels, searchText = "CopyChannels" )
nodeMenu.append( "/Image/Channels/Delete", GafferImage.DeleteChannels, searchText = "DeleteChannels" )
nodeMenu.append( "/Image/Channels/Collect", GafferImage.CollectImages, searchText = "CollectImages" )
nodeMenu.append( "/Image/Utility/Metadata", GafferImage.ImageMetadata, searchText = "ImageMetadata" )
nodeMenu.append( "/Image/Utility/Delete Metadata", GafferImage.DeleteImageMetadata, searchText = "DeleteImageMetadata" )
nodeMenu.append( "/Image/Utility/Copy Metadata", GafferImage.CopyImageMetadata, searchText = "CopyImageMetadata" )
nodeMenu.append( "/Image/Utility/Stats", GafferImage.ImageStats, searchText = "ImageStats", postCreator = GafferImageUI.ImageStatsUI.postCreate  )
nodeMenu.append( "/Image/Utility/Sampler", GafferImage.ImageSampler, searchText = "ImageSampler" )
nodeMenu.append( "/Image/Utility/Catalogue", GafferImage.Catalogue )
nodeMenu.append( "/Image/Utility/Catalogue Select", GafferImage.CatalogueSelect )
nodeMenu.append( "/Image/Utility/FormatQuery", GafferImage.FormatQuery )
nodeMenu.append( "/Image/Deep/FlatToDeep", GafferImage.FlatToDeep, searchText = "FlatToDeep" )
nodeMenu.append( "/Image/Deep/Merge", GafferImage.DeepMerge, searchText = "DeepMerge" )
nodeMenu.append( "/Image/Deep/Tidy", GafferImage.DeepTidy, searchText = "DeepTidy" )
nodeMenu.append( "/Image/Deep/DeepToFlat", GafferImage.DeepToFlat )
nodeMenu.append( "/Image/Deep/Sample Counts", GafferImage.DeepSampleCounts, searchText = "DeepSampleCounts" )
nodeMenu.append( "/Image/Deep/Deep Sampler", GafferImage.DeepSampler, searchText = "DeepSampler" )
nodeMenu.append( "/Image/Deep/Deep Holdout", GafferImage.DeepHoldout, searchText = "DeepHoldout" )
nodeMenu.append( "/Image/Deep/Deep Recolor", GafferImage.DeepRecolor, searchText = "DeepRecolor" )
nodeMenu.append( "/Image/MultiView/Create Views", GafferImage.CreateViews, searchText = "CreateViews", postCreator = GafferImageUI.CreateViewsUI.postCreate )

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
		# Likewise, 3Delight comes with a library of shaders that we
		# show in the 3Delight menu and don't want to show here.
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
		# This match expression filters these categories of shader out
		# as follows :
		#
		# - (?!__) asserts that the shader does not begin with double underscore.
		# - (^|.*/) matches any number (including zero) of directory
		#   names preceding the shader name.
		# - (?<!maya/osl/) is a negative lookbehind, asserting that the
		#   directory is not maya/osl, the directory containing 3delight's
		#   shaders.
		# - (?<!3DelightForKatana/osl/) is the same, but for another location
		#   where 3delight seems to put copies of the same shaders.
		# - (?!as_|oslCode) is a negative lookahead, asserting that the shader
		#   name does not start with "as_", the prefix for all
		#   Appleseed shaders, or "oslCode", the prefix for all OSLCode
		#   shaders.
		# - [^/]*$ matches the rest of the shader name, ensuring it
		#   doesn't include any directory separators.
		matchExpression = re.compile( "(?!__)(^|.*/)(?<!maya/osl/)(?<!3DelightForKatana/osl/)(?!as_|oslCode)[^/]*$"),
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

# VDB nodes

import GafferVDB
import GafferVDBUI

nodeMenu.append( "/VDB/Level Set To Mesh", GafferVDB.LevelSetToMesh, searchText = "LevelSetToMesh" )
nodeMenu.append( "/VDB/Mesh To Level Set", GafferVDB.MeshToLevelSet, searchText = "MeshToLevelSet" )
nodeMenu.append( "/VDB/Level Set Offset", GafferVDB.LevelSetOffset, searchText = "LevelSetOffset" )
nodeMenu.append( "/VDB/Points Grid To Points", GafferVDB.PointsGridToPoints, searchText = "PointsGridToPoints" )
nodeMenu.append( "/VDB/Sphere Level Set", GafferVDB.SphereLevelSet, searchText="SphereLevelSet")

# USD nodes

import GafferUSD
import GafferUSDUI

nodeMenu.append( "/USD/Attributes", GafferUSD.USDAttributes, searchText = "USDAttributes" )
nodeMenu.append( "/USD/Layer Writer", GafferUSD.USDLayerWriter, searchText = "USDLayerWriter" )

# Dispatch nodes

import GafferDispatch
import GafferDispatchUI

nodeMenu.append( "/Dispatch/System Command", GafferDispatch.SystemCommand, searchText = "SystemCommand" )
nodeMenu.append( "/Dispatch/Python Command", GafferDispatch.PythonCommand, searchText = "PythonCommand" )
nodeMenu.append( "/Dispatch/Task List", GafferDispatch.TaskList, searchText = "TaskList" )
nodeMenu.append( "/Dispatch/Wedge", GafferDispatch.Wedge )
nodeMenu.append( "/Dispatch/Frame Mask", GafferDispatch.FrameMask, searchText = "FrameMask" )

# Utility nodes

nodeMenu.append( "/Utility/Expression", Gaffer.Expression )
nodeMenu.append( "/Utility/Node", Gaffer.Node )
nodeMenu.append( "/Utility/Random", Gaffer.Random )
nodeMenu.append( "/Utility/RandomChoice", Gaffer.RandomChoice )
nodeMenu.append( "/Utility/Box", GafferUI.BoxUI.nodeMenuCreateCommand )
nodeMenu.append( "/Utility/BoxIn", Gaffer.BoxIn )
nodeMenu.append( "/Utility/BoxOut", Gaffer.BoxOut )
nodeMenu.append( "/Utility/Edit Scope", Gaffer.EditScope, searchText = "EditScope" )
nodeMenu.append( "/Utility/Reference", GafferUI.ReferenceUI.nodeMenuCreateCommand )
nodeMenu.definition().append( "/Utility/Backdrop", { "command" : GafferUI.BackdropUI.nodeMenuCreateCommand } )
nodeMenu.append( "/Utility/Dot", Gaffer.Dot )
nodeMenu.append( "/Utility/Switch", Gaffer.Switch )
nodeMenu.append( "/Utility/Name Switch", Gaffer.NameSwitch, searchText = "NameSwitch" )
nodeMenu.append( "/Utility/Context Variables", Gaffer.ContextVariables, searchText = "ContextVariables" )
nodeMenu.append( "/Utility/Delete Context Variables", Gaffer.DeleteContextVariables, searchText = "DeleteContextVariables" )
nodeMenu.append( "/Utility/Time Warp", Gaffer.TimeWarp, searchText = "TimeWarp" )
nodeMenu.append( "/Utility/Spreadsheet", Gaffer.Spreadsheet )
nodeMenu.append( "/Utility/Context Query", Gaffer.ContextQuery, searchText = "ContextQuery" )

## Miscellaneous UI
###########################################################################

GafferUI.DotUI.connect( application.root() )

with IECore.IgnoredExceptions( ImportError ) :

	import GafferTractorUI

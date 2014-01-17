##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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
import traceback

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
GafferUI.ExecuteUI.appendMenuDefinitions( scriptWindowMenu, prefix="/Execute" )

# Add help menu
def launchGoogleGroup( menu ):
		url = r'https://groups.google.com/forum/#!forum/gaffer-dev'
		GafferUI.ShowURL.showURL( url )

#TODO - scour an examples directory for .gfr files
#TODO - ..then build a menu with items to launch each example
def helpExamples( menu ):
	result = IECore.MenuDefinition()
	return result

for menuItem, fileName in [
		( "/Help/User Guide", "$GAFFER_ROOT/doc/GafferUserGuide.pdf" ),
		( "/Help/Node Reference", "$GAFFER_ROOT/doc/GafferNodeReference.pdf" ),
		( "/Help/Licenses", "$GAFFER_ROOT/doc/GafferLicenses.pdf" ),
	] :
	
	fileName = os.path.expandvars( fileName )
	scriptWindowMenu.append(
		menuItem,
		{
			"command" : IECore.curry( GafferUI.showURL, fileName ),
			"active" : os.path.exists( fileName ),
		}
	)

scriptWindowMenu.append( "/Help/DocsDivider", 		{ "divider" : True } )
scriptWindowMenu.append( "/Help/Developer Discussion", { "command" : launchGoogleGroup } )
scriptWindowMenu.append( "/Help/DevDivider", 		{ "divider" : True } )
scriptWindowMenu.append( "/Help/Examples",			{ "subMenu" : helpExamples } )


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
	
		nodeMenu.append( "/Arnold/Options", GafferArnold.ArnoldOptions, searchText = "ArnoldOptions" )
		nodeMenu.append( "/Arnold/Attributes", GafferArnold.ArnoldAttributes, searchText = "ArnoldAttributes" )
		nodeMenu.append(
			"/Arnold/Render", GafferArnold.ArnoldRender,
			plugValues = {
				"fileName" : "${project:rootDirectory}/asses/${script:name}/${script:name}.####.ass",
			},
			searchText = "ArnoldRender"
		)

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
		nodeMenu.append( "/RenderMan/InteractiveRender", GafferRenderMan.InteractiveRenderManRender, searchText = "InteractiveRender" )
		
		scriptWindowMenu.append(
			"/Help/3Delight/User Guide",
			{
				"command" : IECore.curry( GafferUI.showURL, os.path.expandvars( "$DELIGHT/doc/3Delight-UserManual.pdf" ) ),
			}
		)

	except Exception, m :

		stacktrace = traceback.format_exc()
		IECore.msg( IECore.Msg.Level.Error, "startup/gui/menus.py", "Error loading RenderMan module - \"%s\".\n %s" % ( m, stacktrace ) )

# Scene nodes

nodeMenu.append( "/Scene/Source/Reader", GafferScene.SceneReader, searchText = "SceneReader" )
nodeMenu.append( "/Scene/Source/Alembic", GafferScene.AlembicSource, searchText = "AlembicSource" )
nodeMenu.append( "/Scene/Source/Object To Scene", GafferScene.ObjectToScene, searchText = "ObjectToScene" )
nodeMenu.append( "/Scene/Source/Camera", GafferScene.Camera )
nodeMenu.append( "/Scene/Source/Primitive/Cube", GafferScene.Cube )
nodeMenu.append( "/Scene/Source/Primitive/Plane", GafferScene.Plane )
nodeMenu.append( "/Scene/Source/Primitive/Sphere", GafferScene.Sphere )
nodeMenu.append( "/Scene/Source/Primitive/Text", GafferScene.Text )
nodeMenu.append( "/Scene/Object/Generators/Seeds", GafferScene.Seeds )
nodeMenu.append( "/Scene/Object/Generators/Instancer", GafferScene.Instancer )
nodeMenu.append( "/Scene/Object/Modifiers/Attribute Cache", GafferScene.AttributeCache, searchText = "AttributeCache" )
nodeMenu.append( "/Scene/Object/Modifiers/Delete Primitive Variables", GafferScene.DeletePrimitiveVariables, searchText = "DeletePrimitiveVariables" )
nodeMenu.append( "/Scene/Object/Modifiers/Mesh Type", GafferScene.MeshType, searchText = "MeshType"  )
nodeMenu.append( "/Scene/Object/Modifiers/Map Projection", GafferScene.MapProjection, searchText = "MapProjection"  )
nodeMenu.append( "/Scene/Object/Modifiers/Map Offset", GafferScene.MapOffset, searchText = "MapOffset"  )
nodeMenu.append( "/Scene/Attributes/Shader Assignment", GafferScene.ShaderAssignment, searchText = "ShaderAssignment" )
nodeMenu.append( "/Scene/Attributes/Shader Switch", GafferScene.ShaderSwitch, searchText = "ShaderSwitch" )
nodeMenu.append( "/Scene/Attributes/Standard Attributes", GafferScene.StandardAttributes, searchText = "StandardAttributes" )
nodeMenu.append( "/Scene/Attributes/Custom Attributes", GafferScene.CustomAttributes, searchText = "CustomAttributes" )
nodeMenu.append( "/Scene/Attributes/Delete Attributes", GafferScene.DeleteAttributes, searchText = "DeleteAttributes" )
nodeMenu.append( "/Scene/Filters/Path Filter", GafferScene.PathFilter, searchText = "PathFilter" )
nodeMenu.append( "/Scene/Filters/Union Filter", GafferScene.UnionFilter, searchText = "UnionFilter" )
nodeMenu.append( "/Scene/Hierarchy/Group", GafferScene.Group )
nodeMenu.append( "/Scene/Hierarchy/Parent", GafferScene.Parent )
nodeMenu.append( "/Scene/Hierarchy/SubTree", GafferScene.SubTree ) #\todo - rename to 'Subtree' (node needs to change too)
nodeMenu.append( "/Scene/Hierarchy/Prune", GafferScene.Prune )
nodeMenu.append( "/Scene/Hierarchy/Isolate", GafferScene.Isolate )
nodeMenu.append( "/Scene/Hierarchy/Switch", GafferScene.SceneSwitch, searchText = "SceneSwitch" )
nodeMenu.append( "/Scene/Transform/Transform", GafferScene.Transform )
nodeMenu.append( "/Scene/Transform/Point Constraint", GafferScene.PointConstraint, searchText = "PointConstraint" )
nodeMenu.append( "/Scene/Transform/Aim Constraint", GafferScene.AimConstraint, searchText = "AimConstraint" )
nodeMenu.append( "/Scene/Transform/Parent Constraint", GafferScene.ParentConstraint, searchText = "ParentConstraint" )
nodeMenu.append( "/Scene/Context/Time Warp", GafferScene.SceneTimeWarp, searchText = "SceneTimeWarp" )
nodeMenu.append( "/Scene/Context/Variables", GafferScene.SceneContextVariables, searchText = "SceneContextVariables" )
nodeMenu.append( "/Scene/Globals/Displays", GafferScene.Displays )
nodeMenu.append( "/Scene/Globals/Standard Options", GafferScene.StandardOptions, searchText = "StandardOptions" )
nodeMenu.append( "/Scene/Globals/Custom Options", GafferScene.CustomOptions, searchText = "CustomOptions" )
nodeMenu.append( "/Scene/OpenGL/Attributes", GafferScene.OpenGLAttributes, searchText = "OpenGLAttributes" )
nodeMenu.definition().append( "/Scene/OpenGL/Shader", { "subMenu" : GafferSceneUI.OpenGLShaderUI.shaderSubMenu } )
nodeMenu.append( "/Scene/OpenGL/Render", GafferScene.OpenGLRender, searchText = "OpenGLRender" )

# Image nodes

import GafferImage
import GafferImageUI

nodeMenu.append( "/Image/Source/Display", GafferImage.Display )
nodeMenu.append( "/Image/Source/Reader", GafferImage.ImageReader, searchText = "ImageReader" )
nodeMenu.append( "/Image/Source/Writer", GafferImage.ImageWriter, searchText = "ImageWriter" )
nodeMenu.append( "/Image/Color/Clamp", GafferImage.Clamp )
nodeMenu.append( "/Image/Color/Constant", GafferImage.Constant )
nodeMenu.append( "/Image/Color/Grade", GafferImage.Grade )
nodeMenu.append( "/Image/Color/OpenColorIO", GafferImage.OpenColorIO, searchText = "OpenColorIO" )
nodeMenu.append( "/Image/Merge/Merge", GafferImage.Merge )
nodeMenu.append( "/Image/Merge/Switch", GafferImage.ImageSwitch, searchText = "ImageSwitch" )
nodeMenu.append( "/Image/Transform/Reformat", GafferImage.Reformat )
nodeMenu.append( "/Image/Transform/Transform", GafferImage.ImageTransform, searchText = "ImageTransform" )
nodeMenu.append( "/Image/Channels/RemoveChannels", GafferImage.RemoveChannels )
nodeMenu.append( "/Image/Context/Time Warp", GafferImage.ImageTimeWarp, searchText = "ImageTimeWarp" )
nodeMenu.append( "/Image/Context/Variables", GafferImage.ImageContextVariables, searchText = "ImageContextVariables"  )
nodeMenu.append( "/Image/Utility/Stats", GafferImage.ImageStats, searchText = "ImageStats" )
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
		__shaderNodeCreator
	)

	nodeMenu.append( "/OSL/Image", GafferOSL.OSLImage, searchText = "OSLImage" )
	nodeMenu.append( "/OSL/Object", GafferOSL.OSLObject, searchText = "OSLObject" )

	scriptWindowMenu.append(
		"/Help/Open Shading Language/Language Reference",
		{
			"command" : IECore.curry( GafferUI.showURL, os.path.expandvars( "$GAFFER_ROOT/doc/osl/osl-languagespec.pdf" ) ),
		}
	)

# Cortex nodes
	
nodeMenu.append( "/Cortex/File/Reader", Gaffer.ObjectReader, searchText = "ObjectReader" )
nodeMenu.append( "/Cortex/File/Writer", Gaffer.ObjectWriter, searchText = "ObjectWriter" )

# \todo have a method for dynamically choosing between Gaffer.OpHolder and Gaffer.ExecutableOpHolder
nodeMenu.appendParameterisedHolders( "/Cortex/Ops", Gaffer.OpHolder, "IECORE_OP_PATHS" )
nodeMenu.appendParameterisedHolders( "/Cortex/Procedurals", Gaffer.ProceduralHolder, "IECORE_PROCEDURAL_PATHS" )

# Utility nodes

nodeMenu.append( "/Utility/Expression", Gaffer.Expression )
nodeMenu.append( "/Utility/Node", Gaffer.Node )
nodeMenu.append( "/Utility/Random", Gaffer.Random )
nodeMenu.append( "/Utility/Box", GafferUI.BoxUI.nodeMenuCreateCommand )
nodeMenu.append( "/Utility/Reference", GafferUI.ReferenceUI.nodeMenuCreateCommand )
nodeMenu.definition().append( "/Utility/Backdrop", { "command" : GafferUI.BackdropUI.nodeMenuCreateCommand } )

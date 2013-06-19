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

## Node creation menu
###########################################################################

nodeMenu = GafferUI.NodeMenu.acquire( application )

# Arnold nodes

try :

	import GafferArnold
	import GafferArnoldUI
	
	GafferArnoldUI.ShaderMenu.appendShaders( nodeMenu.definition() )
	
	nodeMenu.append( "/Arnold/Options", GafferArnold.ArnoldOptions, searchText = "ArnoldOptions" )
	nodeMenu.append( "/Arnold/Attributes", GafferArnold.ArnoldAttributes, searchText = "ArnoldAttributes" )
	nodeMenu.append( "/Arnold/Render", GafferArnold.ArnoldRender, searchText = "ArnoldRender" )

except Exception, m :

	stacktrace = traceback.format_exc()
	IECore.msg( IECore.Msg.Level.Error, "startup/gui/menus.py", "Error loading Arnold module - \"%s\".\n %s" % ( m, stacktrace ) )

# RenderMan nodes

try :

	import GafferRenderMan
	import GafferRenderManUI

	GafferRenderManUI.ShaderMenu.appendShaders( nodeMenu.definition() )
	
	nodeMenu.append( "/RenderMan/Attributes", GafferRenderMan.RenderManAttributes, searchText = "RenderManAttributes" )
	nodeMenu.append( "/RenderMan/Options", GafferRenderMan.RenderManOptions, searchText = "RenderManOptions" )
	nodeMenu.append( "/RenderMan/Render", GafferRenderMan.RenderManRender, searchText = "RenderManRender" )
	nodeMenu.append( "/RenderMan/InteractiveRender", GafferRenderMan.InteractiveRenderManRender, searchText = "InteractiveRender" )

except Exception, m :

	stacktrace = traceback.format_exc()
	IECore.msg( IECore.Msg.Level.Error, "startup/gui/menus.py", "Error loading RenderMan module - \"%s\".\n %s" % ( m, stacktrace ) )

# Scene nodes

nodeMenu.append( "/Scene/Source/SceneReader", GafferScene.SceneReader )
nodeMenu.append( "/Scene/Source/Alembic", GafferScene.AlembicSource )
nodeMenu.append( "/Scene/Source/ObjectToScene", GafferScene.ObjectToScene )
nodeMenu.append( "/Scene/Source/Camera", GafferScene.Camera )
nodeMenu.append( "/Scene/Source/Primitive/Cube", GafferScene.Cube )
nodeMenu.append( "/Scene/Source/Primitive/Plane", GafferScene.Plane )
nodeMenu.append( "/Scene/Source/Primitive/Sphere", GafferScene.Sphere )
nodeMenu.append( "/Scene/Source/Primitive/Text", GafferScene.Text )
nodeMenu.append( "/Scene/Object/Generators/Seeds", GafferScene.Seeds )
nodeMenu.append( "/Scene/Object/Generators/Instancer", GafferScene.Instancer )
nodeMenu.append( "/Scene/Object/Modifiers/AttributeCache", GafferScene.AttributeCache )
nodeMenu.append( "/Scene/Object/Modifiers/Delete Primitive Variables", GafferScene.DeletePrimitiveVariables, searchText = "DeletePrimitiveVariables" )
nodeMenu.append( "/Scene/Object/Modifiers/Mesh Type", GafferScene.MeshType, searchText = "MeshType"  )
nodeMenu.append( "/Scene/Object/Modifiers/Map Projection", GafferScene.MapProjection, searchText = "MapProjection"  )
nodeMenu.append( "/Scene/Attributes/Shader Assignment", GafferScene.ShaderAssignment, searchText = "ShaderAssignment" )
nodeMenu.append( "/Scene/Attributes/Standard Attributes", GafferScene.StandardAttributes, searchText = "StandardAttributes" )
nodeMenu.append( "/Scene/Attributes/Attributes", GafferScene.Attributes )
nodeMenu.append( "/Scene/Filters/PathFilter", GafferScene.PathFilter )
nodeMenu.append( "/Scene/Scene/Group", GafferScene.Group )
nodeMenu.append( "/Scene/Scene/SubTree", GafferScene.SubTree )
nodeMenu.append( "/Scene/Scene/Prune", GafferScene.Prune )
nodeMenu.append( "/Scene/Transform/Transform", GafferScene.Transform )
nodeMenu.append( "/Scene/Transform/Aim Constraint", GafferScene.AimConstraint, searchText = "AimConstraint" )
nodeMenu.append( "/Scene/Context/TimeWarp", GafferScene.SceneTimeWarp )
nodeMenu.append( "/Scene/Context/Variables", GafferScene.SceneContextVariables )
nodeMenu.append( "/Scene/Globals/Displays", GafferScene.Displays )
nodeMenu.append( "/Scene/Globals/Standard Options", GafferScene.StandardOptions, searchText = "StandardOptions" )
nodeMenu.append( "/Scene/Globals/Options", GafferScene.Options )
nodeMenu.append( "/Scene/OpenGL/Attributes", GafferScene.OpenGLAttributes, searchText = "OpenGLAttributes" )
nodeMenu.definition().append( "/Scene/OpenGL/Shader", { "subMenu" : GafferSceneUI.OpenGLShaderUI.shaderSubMenu } )
nodeMenu.append( "/Scene/OpenGL/Render", GafferScene.OpenGLRender, searchText = "OpenGLRender" )

# Image nodes

import GafferImage
import GafferImageUI

nodeMenu.append( "/Image/Source/Display", GafferImage.Display )
nodeMenu.append( "/Image/Source/Reader", GafferImage.ImageReader, searchText = "ImageReader" )
nodeMenu.append( "/Image/Source/Writer", GafferImage.ImageWriter, searchText = "ImageWriter" )
nodeMenu.append( "/Image/Color/Constant", GafferImage.Constant )
nodeMenu.append( "/Image/Color/Grade", GafferImage.Grade )
nodeMenu.append( "/Image/Color/OpenColorIO", GafferImage.OpenColorIO )
nodeMenu.append( "/Image/Filter/Merge", GafferImage.Merge )
nodeMenu.append( "/Image/Filter/Reformat", GafferImage.Reformat )
nodeMenu.append( "/Image/Filter/ImageTransform", GafferImage.ImageTransform )
nodeMenu.append( "/Image/Utility/Select", GafferImage.Select )
nodeMenu.append( "/Image/Utility/Stats", GafferImage.ImageStats, searchText = "ImageStats" )

# Cortex nodes
	
nodeMenu.append( "/Cortex/File/Read", Gaffer.ReadNode )
nodeMenu.append( "/Cortex/File/Write", Gaffer.WriteNode )

# \todo have a method for dynamically choosing between Gaffer.OpHolder and Gaffer.ExecutableOpHolder
nodeMenu.appendParameterisedHolders( "/Cortex/Ops", Gaffer.OpHolder, "IECORE_OP_PATHS" )
nodeMenu.appendParameterisedHolders( "/Cortex/Procedurals", Gaffer.ProceduralHolder, "IECORE_PROCEDURAL_PATHS" )

# Utility nodes

nodeMenu.append( "/Utility/Expression", Gaffer.Expression )
nodeMenu.append( "/Utility/Node", Gaffer.Node )
nodeMenu.append( "/Utility/Random", Gaffer.Random )
nodeMenu.append( "/Utility/Box", GafferUI.BoxUI.nodeMenuCreateCommand )
nodeMenu.append( "/Utility/Reference", GafferUI.ReferenceUI.nodeMenuCreateCommand )

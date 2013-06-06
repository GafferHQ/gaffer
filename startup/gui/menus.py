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

## \todo We can't simply import every module during startup - perhaps we should have
# a plugin autoload mechanism accessible in the preferences? It's important that we
# don't make that too complicated though, and that plugins remain as standard python
# modules and nothing more.
import GafferUI
import GafferSceneUI
try :
	import GafferArnoldUI
except Exception, m :
	stacktrace = traceback.format_exc()
	IECore.msg( IECore.Msg.Level.Error, "startup/gui/menus.py", "Error loading GafferArnoldUI - \"%s\".\n %s" % ( m, stacktrace ) )

import GafferRenderManUI
	
# ScriptWindow menu

scriptWindowMenu = GafferUI.ScriptWindow.menuDefinition()

GafferUI.ApplicationMenu.appendDefinitions( scriptWindowMenu, prefix="/Gaffer" )
GafferUI.FileMenu.appendDefinitions( scriptWindowMenu, prefix="/File" )
GafferUI.EditMenu.appendDefinitions( scriptWindowMenu, prefix="/Edit" )
GafferUI.LayoutMenu.appendDefinitions( scriptWindowMenu, name="/Layout" )
GafferUI.ExecuteUI.appendMenuDefinitions( scriptWindowMenu, prefix="/Execute" )

# Node menu

GafferUI.NodeMenu.append( "/Scene/Source/SceneReader", GafferScene.SceneReader )
GafferUI.NodeMenu.append( "/Scene/Source/ModelCache", GafferScene.ModelCacheSource )
GafferUI.NodeMenu.append( "/Scene/Source/Alembic", GafferScene.AlembicSource )
GafferUI.NodeMenu.append( "/Scene/Source/ObjectToScene", GafferScene.ObjectToScene )
GafferUI.NodeMenu.append( "/Scene/Source/Camera", GafferScene.Camera )
GafferUI.NodeMenu.append( "/Scene/Source/Primitive/Cube", GafferScene.Cube )
GafferUI.NodeMenu.append( "/Scene/Source/Primitive/Plane", GafferScene.Plane )
GafferUI.NodeMenu.append( "/Scene/Source/Primitive/Sphere", GafferScene.Sphere )
GafferUI.NodeMenu.append( "/Scene/Source/Primitive/Text", GafferScene.Text )
GafferUI.NodeMenu.append( "/Scene/Object/Generators/Seeds", GafferScene.Seeds )
GafferUI.NodeMenu.append( "/Scene/Object/Generators/Instancer", GafferScene.Instancer )
GafferUI.NodeMenu.append( "/Scene/Object/Modifiers/AttributeCache", GafferScene.AttributeCache )
GafferUI.NodeMenu.append( "/Scene/Object/Modifiers/Delete Primitive Variables", GafferScene.DeletePrimitiveVariables, searchText = "DeletePrimitiveVariables" )
GafferUI.NodeMenu.append( "/Scene/Object/Modifiers/Mesh Type", GafferScene.MeshType, searchText = "MeshType"  )
GafferUI.NodeMenu.append( "/Scene/Attributes/Shader Assignment", GafferScene.ShaderAssignment, searchText = "ShaderAssignment" )
GafferUI.NodeMenu.append( "/Scene/Attributes/Standard Attributes", GafferScene.StandardAttributes, searchText = "StandardAttributes" )
GafferUI.NodeMenu.append( "/Scene/Attributes/Attributes", GafferScene.Attributes )
GafferUI.NodeMenu.append( "/Scene/Filters/PathFilter", GafferScene.PathFilter )
GafferUI.NodeMenu.append( "/Scene/Scene/Group", GafferScene.Group )
GafferUI.NodeMenu.append( "/Scene/Scene/SubTree", GafferScene.SubTree )
GafferUI.NodeMenu.append( "/Scene/Scene/Prune", GafferScene.Prune )
GafferUI.NodeMenu.append( "/Scene/Transform/Transform", GafferScene.Transform )
GafferUI.NodeMenu.append( "/Scene/Transform/Aim Constraint", GafferScene.AimConstraint, searchText = "AimConstraint" )
GafferUI.NodeMenu.append( "/Scene/Context/TimeWarp", GafferScene.SceneTimeWarp )
GafferUI.NodeMenu.append( "/Scene/Context/Variables", GafferScene.SceneContextVariables )
GafferUI.NodeMenu.append( "/Scene/Globals/Displays", GafferScene.Displays )
GafferUI.NodeMenu.append( "/Scene/Globals/Standard Options", GafferScene.StandardOptions, searchText = "StandardOptions" )
GafferUI.NodeMenu.append( "/Scene/Globals/Options", GafferScene.Options )
GafferUI.NodeMenu.append( "/Scene/OpenGL/Attributes", GafferScene.OpenGLAttributes, searchText = "OpenGLAttributes" )
GafferUI.NodeMenu.definition().append( "/Scene/OpenGL/Shader", { "subMenu" : GafferSceneUI.OpenGLShaderUI.shaderSubMenu } )
GafferUI.NodeMenu.append( "/Scene/OpenGL/Render", GafferScene.OpenGLRender, searchText = "OpenGLRender" )

try :	
	import GafferImage
	import GafferImageUI

	GafferUI.NodeMenu.append( "/Image/Source/Display", GafferImage.Display )
	GafferUI.NodeMenu.append( "/Image/Source/Reader", GafferImage.ImageReader, searchText = "ImageReader" )
	GafferUI.NodeMenu.append( "/Image/Source/Writer", GafferImage.ImageWriter, searchText = "ImageWriter" )
	GafferUI.NodeMenu.append( "/Image/Color/Constant", GafferImage.Constant )
	GafferUI.NodeMenu.append( "/Image/Color/Grade", GafferImage.Grade )
	GafferUI.NodeMenu.append( "/Image/Color/OpenColorIO", GafferImage.OpenColorIO )
	GafferUI.NodeMenu.append( "/Image/Filter/Merge", GafferImage.Merge )
	GafferUI.NodeMenu.append( "/Image/Filter/Reformat", GafferImage.Reformat )
	GafferUI.NodeMenu.append( "/Image/Filter/ImageTransform", GafferImage.ImageTransform )
	GafferUI.NodeMenu.append( "/Image/Utility/Select", GafferImage.Select )
	GafferUI.NodeMenu.append( "/Image/Utility/Stats", GafferImage.ImageStats, searchText = "ImageStats" )
except ImportError :
	pass
	
GafferUI.NodeMenu.append( "/Cortex/File/Read", Gaffer.ReadNode )
GafferUI.NodeMenu.append( "/Cortex/File/Write", Gaffer.WriteNode )

# \todo have a method for dynamically choosing between Gaffer.OpHolder and Gaffer.ExecutableOpHolder
GafferUI.NodeMenu.appendParameterisedHolders( "/Cortex/Ops", Gaffer.OpHolder, "IECORE_OP_PATHS" )
GafferUI.NodeMenu.appendParameterisedHolders( "/Cortex/Procedurals", Gaffer.ProceduralHolder, "IECORE_PROCEDURAL_PATHS" )

GafferUI.NodeMenu.append( "/Utility/Expression", Gaffer.Expression )
GafferUI.NodeMenu.append( "/Utility/Node", Gaffer.Node )
GafferUI.NodeMenu.append( "/Utility/Random", Gaffer.Random )
GafferUI.NodeMenu.append( "/Utility/Box", GafferUI.BoxUI.nodeMenuCreateCommand )
GafferUI.NodeMenu.append( "/Utility/Reference", GafferUI.ReferenceUI.nodeMenuCreateCommand )

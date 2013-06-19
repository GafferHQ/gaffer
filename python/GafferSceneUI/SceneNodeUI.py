##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import fnmatch

import IECore

import Gaffer
import GafferUI

import GafferScene
import GafferSceneUI

# SceneNode

GafferUI.Metadata.registerNodeDescription(

GafferScene.SceneNode,

"""The base type for all nodes which are capable of generating a hierarchical scene.""",

"out",
"""The output scene.""",

"enabled",
"""The on/off state of the node. When it is off, the node outputs an empty scene.""",

)

def __noduleCreator( plug ) :

	if isinstance( plug, GafferScene.ScenePlug ) :
		return GafferUI.StandardNodule( plug )
		
	return None

GafferUI.Nodule.registerNodule( GafferScene.SceneNode.staticTypeId(), fnmatch.translate( "*" ), __noduleCreator )
GafferUI.PlugValueWidget.registerCreator( GafferScene.SceneNode.staticTypeId(), "in", None )
GafferUI.PlugValueWidget.registerCreator( GafferScene.SceneNode.staticTypeId(), "out", None )
GafferUI.PlugValueWidget.registerCreator( GafferScene.SceneNode.staticTypeId(), "enabled", None )

# Instancer

GafferUI.PlugValueWidget.registerCreator( GafferScene.Instancer.staticTypeId(), "instance", None )

# ObjectToScene

GafferUI.Nodule.registerNodule( GafferScene.ObjectToScene.staticTypeId(), "object", GafferUI.StandardNodule )

# FileSource

GafferUI.PlugValueWidget.registerCreator(
	GafferScene.FileSource.staticTypeId(),
	"refreshCount",
	GafferUI.IncrementingPlugValueWidget,
	label = "Refresh",
	undoable = False
)

## \todo Once it's possible to register Widgets to go on the right of a PlugWidget, place the refresh button there.

# SceneReader

GafferUI.PlugValueWidget.registerCreator(
	GafferScene.SceneReader.staticTypeId(),
	"fileName",
	lambda plug : GafferUI.PathPlugValueWidget( plug,
		path = Gaffer.FileSystemPath( "/", filter = Gaffer.FileSystemPath.createStandardFilter( extensions = IECore.SceneInterface.supportedExtensions() ) )
	)
)

# AlembicSource

GafferUI.PlugValueWidget.registerCreator(
	GafferScene.AlembicSource.staticTypeId(),
	"fileName",
	lambda plug : GafferUI.PathPlugValueWidget( plug,
		path = Gaffer.FileSystemPath( "/", filter = Gaffer.FileSystemPath.createStandardFilter( extensions = [ "abc" ] ) )
	)
)

# AttributeCache

GafferUI.PlugValueWidget.registerCreator(
	GafferScene.AttributeCache.staticTypeId(),
	"fileName",
	lambda plug : GafferUI.PathPlugValueWidget(
		plug,
		path = Gaffer.SequencePath( "/", filter = Gaffer.FileSystemPath.createStandardFilter( extensions = [ "fio" ] ) ),
	)
)

# BranchCreator

GafferUI.PlugValueWidget.registerCreator(
	GafferScene.BranchCreator.staticTypeId(),
	"parent",
	lambda plug : GafferUI.PathPlugValueWidget(
		plug,
		path = GafferScene.ScenePath( plug.node()["in"], plug.node().scriptNode().context(), "/" ),
	),
)

# ShaderAssignment

GafferUI.Nodule.registerNodule( GafferScene.ShaderAssignment.staticTypeId(), "shader", GafferUI.StandardNodule )

# Group

GafferUI.PlugValueWidget.registerCreator( GafferScene.Group.staticTypeId(), "in[0-9]*", None )
GafferUI.PlugValueWidget.registerCreator( GafferScene.Group.staticTypeId(), "transform", GafferUI.TransformPlugValueWidget, collapsed=None )

# Filter

GafferUI.PlugValueWidget.registerCreator( GafferScene.Filter.staticTypeId(), "match", None )

# Camera

GafferUI.PlugValueWidget.registerCreator(
	GafferScene.Camera.staticTypeId(),
	"projection",
	GafferUI.EnumPlugValueWidget,
	labelsAndValues = (
		( "Perspective", "perspective" ),
		( "Orthographic", "orthographic" ),
	),
)

# Constraint

GafferUI.PlugValueWidget.registerCreator(
	GafferScene.Constraint.staticTypeId(),
	"target",
	lambda plug : GafferUI.PathPlugValueWidget(
		plug,
		path = GafferScene.ScenePath( plug.node()["in"], plug.node().scriptNode().context(), "/" ),
	),
)

GafferUI.PlugValueWidget.registerCreator(
	GafferScene.Constraint.staticTypeId(),
	"targetMode",
	GafferUI.EnumPlugValueWidget,
	labelsAndValues = (
		( "Origin", GafferScene.Constraint.TargetMode.Origin ),
		( "BoundMin", GafferScene.Constraint.TargetMode.BoundMin ),
		( "BoundMax", GafferScene.Constraint.TargetMode.BoundMax ),
		( "BoundCenter", GafferScene.Constraint.TargetMode.BoundCenter ),	
	)
)

# MeshType

GafferUI.PlugValueWidget.registerCreator(
	GafferScene.MeshType.staticTypeId(),
	"meshType",
	GafferUI.EnumPlugValueWidget,
	labelsAndValues = (
		( "Unchanged", "" ),
		( "Poly", "linear" ),
		( "Subdiv", "catmullClark" ),
	),
)

# Plane

GafferUI.Metadata.registerNodeDescription(

GafferScene.Plane,

"""A node which produces scenes containing a plane.""",

"dimensions",
"Controls size of the plane in X and Y.",

"divisions",
"Controls tesselation of the plane.",

)

# Cube

GafferUI.Metadata.registerNodeDescription(

GafferScene.Cube,

"""A node which produces scenes containing a cube.""",

"dimensions",
"Controls size of the cube.",

)

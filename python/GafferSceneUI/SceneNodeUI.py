##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

import Gaffer
import GafferUI

import GafferScene
import GafferSceneUI

# SceneNode

def __noduleCreator( plug ) :

	if isinstance( plug, GafferScene.ScenePlug ) :
		return GafferUI.StandardNodule( plug )
		
	return None

GafferUI.Nodule.registerNodule( GafferScene.SceneNode.staticTypeId(), fnmatch.translate( "*" ), __noduleCreator )
GafferUI.PlugValueWidget.registerCreator( GafferScene.SceneNode.staticTypeId(), "in", None )
GafferUI.PlugValueWidget.registerCreator( GafferScene.SceneNode.staticTypeId(), "out", None )

# Instancer

GafferUI.PlugValueWidget.registerCreator( GafferScene.Instancer.staticTypeId(), "instance", None )

# ObjectToScene

GafferUI.Nodule.registerNodule( GafferScene.ObjectToScene.staticTypeId(), "object", GafferUI.StandardNodule )

# ModelCacheSource

GafferUI.PlugValueWidget.registerCreator(
	GafferScene.ModelCacheSource.staticTypeId(),
	"fileName",
	lambda plug : GafferUI.PathPlugValueWidget( plug,
		path = Gaffer.FileSystemPath( "/", filter = Gaffer.FileSystemPath.createStandardFilter( extensions = [ "mdc" ] ) )
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

# SceneElementProcessor

GafferUI.PlugValueWidget.registerCreator(
	GafferScene.SceneElementProcessor.staticTypeId(),
	"filter",
	GafferSceneUI.FilterPlugValueWidget,
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

# Assignment

GafferUI.Nodule.registerNodule( GafferScene.Assignment.staticTypeId(), "shader", GafferUI.StandardNodule )

# Group

GafferUI.PlugValueWidget.registerCreator( GafferScene.Group.staticTypeId(), "in[0-9]*", None )

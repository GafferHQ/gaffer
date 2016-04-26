##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferUI
import GafferScene

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.SceneReader,

	"description",
	"""
	The primary means of loading external assets (models, animation and cameras etc)
	from caches into Gaffer. Gaffer's native file format is the .scc (SceneCache) format
	provided by Cortex, but other formats may be supported by registering a new implementation
	of Cortex's abstract SceneInterface.

	> Note :
	>
	> Currently the SceneReader does not support Alembic caches - for those, the AlembicSource
	> node should be used instead.
	""",

	plugs = {

		"fileName" : [

			"description",
			"""
			The name of the file to be loaded. The file can be
			in any of the formats supported by Cortex's SceneInterfaces.
			""",

			"plugValueWidget:type", "GafferUI.FileSystemPathPlugValueWidget",
			"pathPlugValueWidget:leaf", True,
			"pathPlugValueWidget:valid", True,
			"pathPlugValueWidget:bookmarks", "sceneCache",
			"fileSystemPathPlugValueWidget:extensions", lambda plug : IECore.StringVectorData( IECore.SceneInterface.supportedExtensions() ),
			"fileSystemPathPlugValueWidget:extensionsLabel", "Show only cache files",

		],

		"refreshCount" : [

			"description",
			"""
			May be incremented to force a reload if the file has
			changed on disk - otherwise old contents may still
			be loaded via Gaffer's cache.
			""",

		],

		"tags" : [

			"description",
			"""
			Limits the parts of the scene loaded to only those
			with a specific set of tags.
			""",

		],

	}

)

##########################################################################
# Widgets
##########################################################################

GafferUI.PlugValueWidget.registerCreator(
	GafferScene.SceneReader,
	"refreshCount",
	GafferUI.IncrementingPlugValueWidget,
	label = "Refresh",
	undoable = False
)

## \todo Once it's possible to register Widgets to go on the right of a PlugWidget, place the refresh button there.

##########################################################################
# Right click menu for tags
##########################################################################

def __toggleTag( plug, tag, checked ) :

	tags = plug.getValue().split()
	if checked :
		tags.append( tag )
	else :
		tags.remove( tag )

	with Gaffer.UndoContext( plug.ancestor( Gaffer.ScriptNode ) ) :
		plug.setValue( " ".join( tags ) )

def __tagsPopupMenu( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug()
	node = plug.node()
	if not isinstance( node, GafferScene.SceneReader ) :
		return

	if plug != node["tags"] :
		return

	fileName = plugValueWidget.getContext().substitute( node["fileName"].getValue() )
	try :
		scene = IECore.SharedSceneInterfaces.get( fileName )
	except :
		return

	sceneTags = scene.readTags( scene.TagFilter.EveryTag )
	if not sceneTags :
		return
	sceneTags = sorted( [ str( tag ) for tag in sceneTags ] )

	with plugValueWidget.getContext() :
		currentTags = plug.getValue().split()

	menuDefinition.prepend( "/TagsDivider", { "divider" : True } )

	for tag in reversed( sceneTags ) :
		menuDefinition.prepend(
			"/Tags/%s" % tag,
			{
				"command" : IECore.curry( __toggleTag, plug, tag ),
				"checkBox" : tag in currentTags,
				"active" : plug.settable() and not plugValueWidget.getReadOnly(),
			}
		)

__tagsPopupMenuConnection = GafferUI.PlugValueWidget.popupMenuSignal().connect( __tagsPopupMenu )

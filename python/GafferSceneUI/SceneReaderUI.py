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

Gaffer.Metadata.registerNodeDescription(

GafferScene.SceneReader,

"""Reads scenes in any of the formats supported by Cortex's SceneInterface.""",

"tags",
"Limits the parts of the scene loaded to only those with a specific set of tags.",

"sets",
"Specifies a list of tags to be loaded and converted into gaffer sets.",

)

##########################################################################
# Widgets
##########################################################################

GafferUI.PlugValueWidget.registerCreator(
	GafferScene.SceneReader,
	"fileName",
	lambda plug : GafferUI.PathPlugValueWidget( plug,
		path = Gaffer.FileSystemPath( "/", filter = Gaffer.FileSystemPath.createStandardFilter( extensions = IECore.SceneInterface.supportedExtensions() ) ),
		pathChooserDialogueKeywords = {
			"bookmarks" : GafferUI.Bookmarks.acquire( plug, category = "sceneCache" ),
			"leaf" : True,
		},
	)
)

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

	if plug != node["tags"] and plug != node["sets"] :
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

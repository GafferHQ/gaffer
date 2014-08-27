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

GafferScene.SetFilter,

"""A filter which uses sets to define which locations are matched.""",

"set",
"The name of a set that defines the locations to be matched.",

)

##########################################################################
# Nodules
##########################################################################

GafferUI.Nodule.registerNodule( GafferScene.SetFilter, "set", lambda plug : None )

##########################################################################
# Right click menu for sets
##########################################################################

def __applySet( plug, setName ) :

	with Gaffer.UndoContext( plug.ancestor( Gaffer.ScriptNode ) ) :
		plug.setValue( setName )

def __setsPopupMenu( menuDefinition, plugValueWidget ) :

	## \todo If plugs on other nodes would like this menu too, then
	# we could use a piece of metadata to determine whether or not to
	# perform the menu creation.
	plug = plugValueWidget.getPlug()
	node = plug.node()
	if not isinstance( node, GafferScene.SetFilter ) :
		return

	if plug != node["set"] :
		return

	setNames = set()
	with plugValueWidget.getContext() :
		for output in node["match"].outputs() :
			if not isinstance( output.node(), GafferScene.SceneProcessor ) :
				continue
			globals = output.node()["in"]["globals"].getValue()
			if "gaffer:sets" not in globals :
				continue
			setNames.update( globals["gaffer:sets"].keys() )

	if not setNames :
		return

	menuDefinition.prepend( "/SetsDivider", { "divider" : True } )

	for setName in reversed( sorted( list( setNames ) ) ) :
		menuDefinition.prepend(
			"/Sets/%s" % setName,
			{
				"command" : IECore.curry( __applySet, plug, setName ),
				"active" : plug.settable() and not plugValueWidget.getReadOnly(),
			}
		)

__setsPopupMenuConnection = GafferUI.PlugValueWidget.popupMenuSignal().connect( __setsPopupMenu )

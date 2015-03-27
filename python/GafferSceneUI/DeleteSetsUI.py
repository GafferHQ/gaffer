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

import functools

import Gaffer
import GafferUI
import GafferScene

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNodeDescription(

GafferScene.DeleteSets,

"""A node which removes object sets.""",

"names",
"The names of the sets to be removed.",

"invertNames",
"When on, matching names are kept, and non-matching names are removed.",

)

##########################################################################
# Right click menu for sets
# This is driven by metadata so it can be used for plugs on other
# nodes too.
##########################################################################

def __addSet( plug, setName ) :

	with Gaffer.UndoContext( plug.ancestor( Gaffer.ScriptNode ) ) :
		if setName not in plug.getValue().split( " " ):
			oldValue = plug.getValue()
			plug.setValue( plug.getValue() + (" " if oldValue else "") + setName )

def __deleteSetsPopupMenu( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug()
	if plug is None :
		return

	node = plug.node()
	if not isinstance( node, GafferScene.DeleteSets ) :
		return

	if plug.getName() != "names":
		return

	globals = node["in"]["globals"].getValue()
	if "gaffer:sets" not in globals :
		return

	setNames = globals["gaffer:sets"].keys()

	if not setNames :
		return

	menuDefinition.prepend( "/SetsDivider", { "divider" : True } )

	for setName in reversed( sorted( setNames ) ) :
		menuDefinition.prepend(
			"/Add Set/%s" % setName,
			{
				"command" : functools.partial( __addSet, plug, setName ),
				"active" : plug.settable() and not plugValueWidget.getReadOnly(),
			}
		)

__deleteSetsPopupMenuConnection = GafferUI.PlugValueWidget.popupMenuSignal().connect( __deleteSetsPopupMenu )

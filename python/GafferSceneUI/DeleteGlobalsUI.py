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

Gaffer.Metadata.registerNode(

	GafferScene.DeleteGlobals,

	"description",
	"""
	A node which removes named items from the globals.
	To delete outputs or options specifically, prefer
	the DeleteOutputs and DeleteOptions nodes respectively,
	as they provide improved interfaces for their specific
	tasks.
	""",

	plugs = {

		"names" : [

			"description",
			"""
			The names of globals to be removed. Names should be
			separated by spaces and can use Gaffer's standard wildcards.
			""",

		],

		"invertNames" : [

			"description",
			"""
			When on, matching names are kept, and non-matching names are removed.
			""",

		],

	}

)

##########################################################################
# Right click menu for names
##########################################################################

def __toggleName( plug, name, active ) :

	names = plug.getValue().split()
	if active :
		names.append( name )
	else :
		names.remove( name )

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		plug.setValue( " ".join( names ) )

def __namesPopupMenu( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug()
	node = plug.node()
	if not isinstance( node, GafferScene.DeleteGlobals ) :
		return

	if plug != node["names"] :
		return

	with plugValueWidget.context() :
		globals = node["in"]["globals"].getValue()
		currentNames = set( node["names"].getValue().split() )

	prefix = node._namePrefix()
	names = [ n for n in globals.keys() if n.startswith( prefix ) ]
	if not names :
		return

	menuDefinition.prepend( "/NamesDivider", { "divider" : True } )

	menuPrefix = "/" + node.typeName().rsplit( ":" )[-1].replace( "Delete", "" ) + "/"
	for name in reversed( sorted( list( names ) ) ) :
		nameWithoutPrefix = name[len(prefix):]
		menuDefinition.prepend(
			menuPrefix + nameWithoutPrefix,
			{
				"command" : functools.partial( __toggleName, plug, nameWithoutPrefix ),
				"active" : plug.settable() and not Gaffer.MetadataAlgo.readOnly( plug ),
				"checkBox" : nameWithoutPrefix in currentNames,
			}
		)

GafferUI.PlugValueWidget.popupMenuSignal().connect( __namesPopupMenu )

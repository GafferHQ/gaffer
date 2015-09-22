##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferUI

## Appends menu items for the creation of user plugs on the specified parent.
def appendPlugCreationMenuDefinitions( plugParent, menuDefinition, prefix = "" ) :

	menuDefinition.append( prefix + "/Bool", { "command" : functools.partial( __addPlug, plugParent, Gaffer.BoolPlug ) } )
	menuDefinition.append( prefix + "/Float", { "command" : functools.partial( __addPlug, plugParent, Gaffer.FloatPlug ) } )
	menuDefinition.append( prefix + "/Int", { "command" : functools.partial( __addPlug, plugParent, Gaffer.IntPlug ) } )
	menuDefinition.append( prefix + "/NumericDivider", { "divider" : True } )

	menuDefinition.append( prefix + "/String", { "command" : functools.partial( __addPlug, plugParent, Gaffer.StringPlug ) } )
	menuDefinition.append( prefix + "/StringDivider", { "divider" : True } )

	menuDefinition.append( prefix + "/V2i", { "command" : functools.partial( __addPlug, plugParent, Gaffer.V2iPlug ) } )
	menuDefinition.append( prefix + "/V3i", { "command" : functools.partial( __addPlug, plugParent, Gaffer.V3iPlug ) } )
	menuDefinition.append( prefix + "/V2f", { "command" : functools.partial( __addPlug, plugParent, Gaffer.V2fPlug ) } )
	menuDefinition.append( prefix + "/V3f", { "command" : functools.partial( __addPlug, plugParent, Gaffer.V3fPlug  ) } )
	menuDefinition.append( prefix + "/VectorDivider", { "divider" : True } )

	menuDefinition.append( prefix + "/Color3f", { "command" : functools.partial( __addPlug, plugParent, Gaffer.Color3fPlug ) } )
	menuDefinition.append( prefix + "/Color4f", { "command" : functools.partial( __addPlug, plugParent, Gaffer.Color4fPlug ) } )

## Returns a widget that allows the user to add plugs to a particular parent.
# Intended for use within a PlugLayout.
def plugCreationWidget( plugParent ) :

	with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal ) as row :

		GafferUI.Spacer( IECore.V2i( GafferUI.PlugWidget.labelWidth(), 1 ) )
		button = GafferUI.MenuButton( image="plus.png", hasFrame=False, menu=GafferUI.Menu( functools.partial( __plugCreationMenuDefinition, plugParent ) ) )
		button.setToolTip( "Click to add plugs" )
		GafferUI.Spacer( IECore.V2i( 1 ), IECore.V2i( 999999, 1 ), parenting = { "expand" : True } )

	return row

def __addPlug( plugParent, plugType ) :

	with Gaffer.UndoContext( plugParent.ancestor( Gaffer.ScriptNode ) ) :
		plug = plugType( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		Gaffer.Metadata.registerPlugValue( plug, "nodule:type", "" )
		plugParent.addChild( plug )

def __plugCreationMenuDefinition( plugParent ) :

	result = IECore.MenuDefinition()
	appendPlugCreationMenuDefinitions( plugParent, result )
	return result

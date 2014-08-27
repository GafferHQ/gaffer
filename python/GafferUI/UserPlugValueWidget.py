##########################################################################
#
#  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

from __future__ import with_statement

import IECore

import Gaffer
import GafferUI

class UserPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, editable=True, **kw ) :

		self.__column = GafferUI.ListContainer( spacing = 6 )

		GafferUI.PlugValueWidget.__init__( self, self.__column, plug, **kw )

		with self.__column :
			self.__layout = GafferUI.PlugLayout( plug )
			if editable :
				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal ) :
					GafferUI.Spacer( IECore.V2i( GafferUI.PlugWidget.labelWidth(), 1 ) )
					addButton = GafferUI.MenuButton( image="plus.png", hasFrame=False, menu=GafferUI.Menu( self.__addMenuDefinition() ) )
					addButton.setToolTip( "Click to add plugs" )
					GafferUI.Spacer( IECore.V2i( 1 ), IECore.V2i( 999999, 1 ), parenting = { "expand" : True } )

	def hasLabel( self ) :

		return True

	def setReadOnly( self, readOnly ) :

		if readOnly == self.getReadOnly() :
			return

		GafferUI.PlugValueWidget.setReadOnly( self, readOnly )

		self.__layout.setReadOnly( readOnly )

	def childPlugValueWidget( self, childPlug, lazy=True ) :

		return self.__layout.plugValueWidget( childPlug, lazy )

	def _updateFromPlug( self ) :

		pass

	def __addMenuDefinition( self ) :

		result = IECore.MenuDefinition()

		result.append( "/Add/Bool", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addPlug ), Gaffer.BoolPlug ) } )
		result.append( "/Add/Float", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addPlug ), Gaffer.FloatPlug ) } )
		result.append( "/Add/Int", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addPlug ), Gaffer.IntPlug ) } )
		result.append( "/Add/NumericDivider", { "divider" : True } )

		result.append( "/Add/String", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addPlug ), Gaffer.StringPlug ) } )
		result.append( "/Add/StringDivider", { "divider" : True } )

		result.append( "/Add/V2i", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addPlug ), Gaffer.V2iPlug ) } )
		result.append( "/Add/V3i", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addPlug ), Gaffer.V3iPlug ) } )
		result.append( "/Add/V2f", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addPlug ), Gaffer.V2fPlug ) } )
		result.append( "/Add/V3f", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addPlug ), Gaffer.V3fPlug  ) } )
		result.append( "/Add/VectorDivider", { "divider" : True } )

		result.append( "/Add/Color3f", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addPlug ), Gaffer.Color3fPlug ) } )
		result.append( "/Add/Color4f", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addPlug ), Gaffer.Color4fPlug ) } )

		return result

	def __addPlug( self, plugType ) :

		d = GafferUI.TextInputDialogue( initialText = "unnamed", title = "Enter name", confirmLabel = "Create" )
		name = d.waitForText( parentWindow = self.ancestor( GafferUI.Window ) )
		d.setVisible( False )

		if not name :
			return

		with Gaffer.UndoContext( self.getPlug().node().scriptNode() ) :
			plug = plugType( name, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
			self.getPlug().addChild( plug )

GafferUI.PlugValueWidget.registerCreator( Gaffer.Node, "user", UserPlugValueWidget )

##########################################################################
# Plug menu
##########################################################################

def __deletePlug( plug ) :

	with Gaffer.UndoContext( plug.ancestor( Gaffer.ScriptNode ) ) :
		plug.parent().removeChild( plug )

def __plugPopupMenu( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug()
	node = plug.node()
	if plug.parent().isSame( node["user"] ) :
		menuDefinition.append( "/DeleteDivider", { "divider" : True } )
		menuDefinition.append( "/Delete", { "command" : IECore.curry( __deletePlug, plug ), "active" : not plugValueWidget.getReadOnly() } )

__plugPopupMenuConnection = GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu )

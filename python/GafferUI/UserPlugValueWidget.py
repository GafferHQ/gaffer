##########################################################################
#
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

from __future__ import with_statement

import IECore

import Gaffer
import GafferUI

class UserPlugValueWidget( GafferUI.CompoundPlugValueWidget ) :

	def __init__( self, plug, collapsed=None, label=None, editable=True, **kw ) :

		GafferUI.CompoundPlugValueWidget.__init__( self, plug, collapsed, label, **kw )

		self.__editable = editable
		self.__footerWidget = None

	def _footerWidget( self ) :

		if not self.__editable :
			return None

		if self.__footerWidget is not None :
			return self.__footerWidget

		self.__footerWidget = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )
		self.__footerWidget.append( GafferUI.Spacer( IECore.V2i( GafferUI.PlugWidget.labelWidth(), 1 ) ) )
		self.__footerWidget.append(
			GafferUI.MenuButton( image="plus.png", hasFrame=False, menu=GafferUI.Menu( self.__addMenuDefinition() ) )
		)
		self.__footerWidget.append( GafferUI.Spacer( IECore.V2i( 1 ), IECore.V2i( 999999, 1 ) ), expand = True )

		return self.__footerWidget

	def __addMenuDefinition( self ) :

		result = IECore.MenuDefinition()

		result.append( "/Add/Float", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addPlug ), Gaffer.FloatPlug ) } )
		result.append( "/Add/Int", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addPlug ), Gaffer.IntPlug ) } )
		result.append( "/Add/String", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addPlug ), Gaffer.StringPlug ) } )

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

GafferUI.PlugValueWidget.registerCreator( Gaffer.Node.staticTypeId(), "user", UserPlugValueWidget )

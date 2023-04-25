##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

## Supported metadata :
#
# buttonPlugValueWidget:clicked
class ButtonPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__button = GafferUI.Button()

		GafferUI.PlugValueWidget.__init__( self, self.__button, plug, **kw )

		self.__button.clickedSignal().connect( Gaffer.WeakMethod( self.__clicked ), scoped = False )

		self.setPlug( plug )

	def hasLabel( self ) :

		return True

	def setPlug( self, plug ) :

		GafferUI.PlugValueWidget.setPlug( self, plug )

		self.__nameChangedConnection = None
		if plug is not None :
			self.__nameChangedConnection = plug.nameChangedSignal().connect( Gaffer.WeakMethod( self.__nameChanged ), scoped = True )

	def _updateFromEditable( self ) :

		self.__button.setEnabled( self._editable() )

	def _updateFromMetadata( self ) :

		self.__updateLabel()

	def __nameChanged( self, plug, oldName ) :

		self.__updateLabel()

	def __updateLabel( self ) :

		label = ""
		if self.getPlug() :
			label = self.getPlug().getName()
			label = Gaffer.Metadata.value( self.getPlug(), "label" ) or label

		self.__button.setText( label )

	def __clicked( self, widget ) :

		code = Gaffer.Metadata.value( self.getPlug(), "buttonPlugValueWidget:clicked" )
		if not code :
			return False

		executionDict = {
			"IECore" : IECore,
			"Gaffer" : Gaffer,
			"plug" : self.getPlug(),
			"button" : self,
		}

		with GafferUI.ErrorDialogue.ErrorHandler( title = "Button Error", parentWindow = self.ancestor( GafferUI.Window ) ) :
			with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
				with self.getContext() :
					exec( code, executionDict, executionDict )

	def __plugMetadataChanged( self, plug, key, reason ) :

		if key=="label" and plug == self.getPlug() :
			self.__updateLabel()

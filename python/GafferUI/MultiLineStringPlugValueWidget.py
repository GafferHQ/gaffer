##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferUI

class MultiLineStringPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, continuousUpdate=False, **kw ) :

		self.__textWidget = GafferUI.MultiLineTextWidget()

		GafferUI.PlugValueWidget.__init__( self, self.__textWidget, plug, **kw )

		self._addPopupMenu( self.__textWidget )

		self.__keyPressConnection = self.__textWidget.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ) )
		self.__activatedConnection = self.__textWidget.activatedSignal().connect( Gaffer.WeakMethod( self.__setPlugValue ) )
		self.__editingFinishedConnection = self.__textWidget.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__setPlugValue ) )
		if continuousUpdate :
			self.__textChangedConnection = self.__textWidget.textChangedSignal().connect( Gaffer.WeakMethod( self.__setPlugValue ) )

		self._updateFromPlug()

	def textWidget( self ) :

		return self.__textWidget

	def _updateFromPlug( self ) :

		if self.getPlug() is not None :
			with self.getContext() :
				self.__textWidget.setText( self.getPlug().getValue() )

		self.__textWidget.setEditable( self._editable() )

	def __keyPress( self, widget, event ) :

		assert( widget is self.__textWidget )

		if not self.__textWidget.getEditable() :
			return False

		# escape abandons everything
		if event.key=="Escape" :
			self._updateFromPlug()
			return True

		return False

	def __setPlugValue( self, *unused ) :

		if not self._editable() :
			return

		text = self.__textWidget.getText()
		with Gaffer.UndoContext( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().setValue( text )

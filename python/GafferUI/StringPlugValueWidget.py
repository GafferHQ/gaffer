##########################################################################
#
#  Copyright (c) 2011-2013, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferUI

from GafferUI.PlugValueWidget import sole

## Supported Metadata :
#
# - "stringPlugValueWidget:continuousUpdate"
# - "stringPlugValueWidget:placeholderText" : The text displayed when the string value is left empty
class StringPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		self.__continuousUpdate = False

		self.__textWidget = GafferUI.TextWidget()

		GafferUI.PlugValueWidget.__init__( self, self.__textWidget, plugs, **kw )

		self._addPopupMenu( self.__textWidget )

		self.__textWidget.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False )
		self.__textWidget.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__editingFinished ), scoped = False )
		self.__textChangedConnection = self.__textWidget.textChangedSignal().connect( Gaffer.WeakMethod( self.__textChanged ), scoped = False )

		self._updateFromPlugs()

	def textWidget( self ) :

		return self.__textWidget

	def setHighlighted( self, highlighted ) :

		GafferUI.PlugValueWidget.setHighlighted( self, highlighted )
		self.textWidget().setHighlighted( highlighted )

	def _updateFromPlugs( self ) :

		value = None
		errored = False
		with self.getContext() :
			try :
				value = sole( p.getValue() for p in self.getPlugs() )
			except :
				errored = True

		text = value or ""
		if text != self.__textWidget.getText() :
			# Setting the text moves the cursor to the end,
			# even if the new text is the same. We must avoid
			# calling setText() in this situation, otherwise the
			# cursor is always moving to the end whenever a key is
			# pressed in continuousUpdate mode.
			with Gaffer.BlockedConnection( self.__textChangedConnection ) :
				self.__textWidget.setText( text )

		self.__textWidget.setErrored( errored )

		self.__continuousUpdate = all( Gaffer.Metadata.value( p, "stringPlugValueWidget:continuousUpdate" ) for p in self.getPlugs() )

		placeHolder = ""
		if value is None and len( self.getPlugs() ) :
			placeHolder = "---"
			# Mixed values require interaction before we commit the widget
			# value to the plugs. This prevents mixed values being overriden
			# by the empty string in the widget when it loses focus.
			self.__editRequiresInteraction = True
		else :
			placeHolder = self.__placeholderText()
			self.__editRequiresInteraction = False
		self.textWidget()._qtWidget().setPlaceholderText( placeHolder )

		self.__textWidget.setEditable( self._editable() )

	def __editInteractionOccured( self ) :

		if self.__editRequiresInteraction == False :
			return

		self.__editRequiresInteraction = False
		self.textWidget()._qtWidget().setPlaceholderText( self.__placeholderText() )

	def __placeholderText( self ) :

		return sole( Gaffer.Metadata.value( p, "stringPlugValueWidget:placeholderText" ) for p in self.getPlugs() ) or ""

	def __keyPress( self, widget, event ) :

		assert( widget is self.__textWidget )

		if not self.__textWidget.getEditable() :
			return False

		# escape abandons everything
		if event.key == "Escape" :
			self._updateFromPlugs()
			return True
		elif event.key == "Backspace" :
			# Allow a 'delete' press with the initial keyboard focus and a
			# mixed value placeholder to give the appearance of removing the
			# mixed value, allowing all plugs to be set to an empty string.
			self.__editInteractionOccured()

		return False

	def __textChanged( self, textWidget ) :

		assert( textWidget is self.__textWidget )

		self.__editInteractionOccured()

		if self.__continuousUpdate == True :
			self.__setPlugValues()

	def __editingFinished( self, textWidget ) :

		assert( textWidget is self.__textWidget )

		# If we required user editing (ie: mixed value placeholder) and haven't
		# had any, do nothing, so we don't stomp over the existing plug values.
		if self.__editRequiresInteraction :
			return

		self.__setPlugValues()

	def __setPlugValues( self ) :

		if self._editable() :
			text = self.__textWidget.getText()
			with Gaffer.UndoScope( next( iter( self.getPlugs() ) ).ancestor( Gaffer.ScriptNode ) ) :
				for plug in self.getPlugs() :
					plug.setValue( text )

			# now we've transferred the text changes to the global undo queue, we remove them
			# from the widget's private text editing undo queue. it will then ignore undo shortcuts,
			# allowing them to fall through to the global undo shortcut.
			self.__textWidget.clearUndo()

GafferUI.PlugValueWidget.registerType( Gaffer.StringPlug, StringPlugValueWidget )

##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

## Supported metadata :
#
#  "numericPlugValueWidget:fixedCharacterWidth"
class NumericPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		self.__numericWidget = GafferUI.NumericWidget( 0 )

		GafferUI.PlugValueWidget.__init__( self, self.__numericWidget, plugs, **kw )

		self._addPopupMenu( self.__numericWidget )

		# we use these to decide which actions to merge into a single undo
		self.__lastChangedReason = None
		self.__mergeGroupId = 0

		self.__numericWidget.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ) )
		self.__valueChangedConnection = self.__numericWidget.valueChangedSignal().connect( Gaffer.WeakMethod( self.__valueChanged ) )

	def numericWidget( self ) :

		return self.__numericWidget

	def setHighlighted( self, highlighted ) :

		GafferUI.PlugValueWidget.setHighlighted( self, highlighted )
		self.numericWidget().setHighlighted( highlighted )

	def getToolTip( self ) :

		result = GafferUI.PlugValueWidget.getToolTip( self )

		if self.getPlugs() :
			if result :
				result += "\n"
			result += "## Actions\n"
			result += " - Cursor up/down or <kbd>Ctrl</kbd> + scroll wheel to increment/decrement\n"
			result += " - Use `+`, `-`, `*`, `/` and `%` to perform simple maths\n"

		return result

	def _updateFromValues( self, values, exception ) :

		if len( values ) == 0 and exception is None and self.getPlugs() :
			# Placeholder update for a pending background compute. If we're animated,
			# we don't want to use a `---` placeholder because it messes up editing for
			# the user. Animation is quick enough to compute that there is no need
			# for a placeholder anyway, so we'll just wait for the final update.
			if all( Gaffer.Animation.isAnimated( p ) for p in self.getPlugs() ) :
				return

		# Update value and error state.

		value = sole( values )
		with Gaffer.Signals.BlockedConnection( self.__valueChangedConnection ) :

			# Always give the widget a value, even if we have multiple, because
			# the _type_ (int or float) is important, and affects interaction
			# with the widget.
			if value is not None :
				self.__numericWidget.setValue( value )
			elif self.getPlugs() :
				self.__numericWidget.setValue( next( iter( self.getPlugs() ) ).defaultValue() )

			# But if there are multiple values or an error, clear the actual
			# display so we don't show anything misleading.
			if exception is not None or value is None :
				self.__numericWidget.setText( "" )
				self.__numericWidget.setPlaceholderText( "---" )
			else :
				self.__numericWidget.setPlaceholderText( "" )

		self.__numericWidget.setErrored( exception is not None )

		# Update animation styling

		animated = any( Gaffer.Animation.isAnimated( p ) for p in self.getPlugs() )
		## \todo Perhaps this styling should be provided by the NumericWidget itself?
		widgetAnimated = GafferUI._Variant.fromVariant( self.__numericWidget._qtWidget().property( "gafferAnimated" ) ) or False
		if widgetAnimated != animated :
			self.__numericWidget._qtWidget().setProperty( "gafferAnimated", GafferUI._Variant.toVariant( bool( animated ) ) )
			self.__numericWidget._repolish()

	def _updateFromEditable( self ) :

		self.__numericWidget.setEditable( self._editable( canEditAnimation = True ) )

	def _updateFromMetadata( self ) :

		charWidth = None
		for plug in self.getPlugs() :
			plugCharWidth = Gaffer.Metadata.value( plug, "numericPlugValueWidget:fixedCharacterWidth" )
			if plugCharWidth is None and isinstance( plug, Gaffer.IntPlug ) :
				if plug.hasMinValue() and plug.hasMaxValue() :
					plugCharWidth = max( len( str( plug.minValue() ) ), len( str( plug.maxValue() ) ) )
			if plugCharWidth is not None :
				charWidth = max( charWidth, plugCharWidth ) if charWidth is not None else plugCharWidth

		self.__numericWidget.setFixedCharacterWidth( charWidth )

	def __keyPress( self, widget, event ) :

		assert( widget is self.__numericWidget )

		if not self.__numericWidget.getEditable() :
			return False

		# escape abandons everything
		if event.key=="Escape" :
			self._requestUpdateFromValues()
			return True

		return False

	def __valueChanged( self, widget, reason ) :

		if reason == GafferUI.NumericWidget.ValueChangedReason.InvalidEdit :
			self._requestUpdateFromValues()
			return

		if self._editable( canEditAnimation = True ) :

			if not widget.changesShouldBeMerged( self.__lastChangedReason, reason ) :
				self.__mergeGroupId += 1
			self.__lastChangedReason = reason

			self.__setPlugValues( mergeGroup = "NumericPlugValueWidget%d%d" % ( id( self, ), self.__mergeGroupId ) )

		return False

	def __setPlugValues( self, mergeGroup="" ) :

		with Gaffer.UndoScope( self.scriptNode(), mergeGroup=mergeGroup ) :

			with self._blockedUpdateFromValues() :

				for plug in self.getPlugs() :

					if Gaffer.Animation.isAnimated( plug ) :
						curve = Gaffer.Animation.acquire( plug )
						if self.__numericWidget.getText() != self.__numericWidget.valueToString( curve.evaluate( self.context().getTime() ) ) :
							curve.insertKey( self.context().getTime(), self.__numericWidget.getValue() )
					else :
						try :
							plug.setValue( self.__numericWidget.getValue() )
						except :
							pass

		# Now any changes that were made in the numeric widget have been transferred
		# into the global undo queue, we remove the text editing changes from the
		# widget's private text editing undo queue. It will then ignore undo shortcuts,
		# allowing them to fall through to the global undo shortcut.
		self.__numericWidget.clearUndo()

		# We always need to update the UI from the plugs after trying to set them,
		# because the plugs might clamp the value to something else. Furthermore
		# they might not even emit `plugDirtiedSignal() if they happens to clamp to the same
		# value as before. We block calls to `_updateFromValues()` while setting
		# the value to avoid having to do the work twice if `plugDirtiedSignal()` _is_ emitted.
		self._requestUpdateFromValues()

GafferUI.PlugValueWidget.registerType( Gaffer.FloatPlug, NumericPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.IntPlug, NumericPlugValueWidget )

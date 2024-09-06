##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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
import imath
import os

import IECore
import Gaffer
import GafferUI

##########################################################################
# MetadataValueWidgets. These display metadata values, allowing the user
# to edit them.
##########################################################################

class MetadataWidget( GafferUI.Widget ) :

	def __init__( self, topLevelWidget, key, target = None, defaultValue = None, **kw ) :

		GafferUI.Widget.__init__( self, topLevelWidget, **kw )

		self.__key = key
		self.__target = None
		self.__defaultValue = defaultValue

		self.setTarget( target )

	def setTarget( self, target ) :

		assert( isinstance( target, ( Gaffer.Node, Gaffer.Plug, type( None ) ) ) )

		self.__target = target
		self.setEnabled( self.__target is not None )

		if isinstance( self.__target, Gaffer.Node ) :
			self.__metadataChangedConnection = Gaffer.Metadata.nodeValueChangedSignal( self.__target ).connect(
				Gaffer.WeakMethod( self.__metadataChanged ),
				scoped = True
			)
		elif isinstance( self.__target, Gaffer.Plug ) :
			self.__metadataChangedConnection = Gaffer.Metadata.plugValueChangedSignal( self.__target.node() ).connect(
				Gaffer.WeakMethod( self.__metadataChanged ),
				scoped = True
			)
		else :
			self.__metadataChangedConnection = None

		self.__update()

	def getTarget( self ) :

		return self.__target

	def setKey( self, key ) :

		if key == self.__key :
			return

		self.__key = key
		self.__update()

	def getKey( self, key ) :

		return self.__key

	def defaultValue( self ) :

		return self.__defaultValue

	## Must be implemented in derived classes to update
	# the widget from the value.
	def _updateFromValue( self, value ) :

		raise NotImplementedError

	## Must be called by derived classes to update
	# the Metadata value when the widget value changes.
	def _updateFromWidget( self, value, mergeGroup = "" ) :

		if self.__target is None :
			return

		with Gaffer.UndoScope( self.__target.ancestor( Gaffer.ScriptNode ), mergeGroup = mergeGroup ) :
			Gaffer.Metadata.registerValue( self.__target, self.__key, value )

	## May be called by derived classes to deregister the
	# metadata value.
	def _deregisterValue( self ) :

		if self.__target is None :
			return

		with Gaffer.UndoScope( self.__target.ancestor( Gaffer.ScriptNode ) ) :
			Gaffer.Metadata.deregisterValue( self.__target, self.__key )

	def __update( self ) :

		if self.__target is None :
			self._updateFromValue( self.defaultValue() )
			return

		v = Gaffer.Metadata.value( self.__target, self.__key )
		if v is None :
			k = self.__fallbackKey( self.__key )
			if k is not None :
				v = Gaffer.Metadata.value( self.__target, k )

		self._updateFromValue( v if v is not None else self.defaultValue() )

	def __metadataChanged( self, target, key, reason ) :

		if key == self.__key and target == self.__target :
			self.__update()

	@staticmethod
	def __fallbackKey( k ) :

		for oldPrefix, newPrefix in [
			( "pathPlugValueWidget:", "path:" ),
			( "fileSystemPathPlugValueWidget:", "fileSystemPath:" ),
		] :
			if k.startswith( newPrefix ) :
				return k.replace( newPrefix, oldPrefix )

		return None

class BoolMetadataWidget( MetadataWidget ) :

	def __init__( self, key, target = None, defaultValue = False, **kw ) :

		self.__boolWidget = GafferUI.BoolWidget()
		MetadataWidget.__init__( self, self.__boolWidget, key, target, defaultValue = defaultValue, **kw )

		self.__boolWidget.stateChangedSignal().connect(
			Gaffer.WeakMethod( self.__stateChanged )
		)

	def _updateFromValue( self, value ) :

		self.__boolWidget.setState( value )

	def __stateChanged( self, *unused ) :

		self._updateFromWidget( self.__boolWidget.getState() )

class StringMetadataWidget( MetadataWidget ) :

	def __init__( self, key, target = None, defaultValue = "", acceptEmptyString = True, **kw ) :

		self.__textWidget = GafferUI.TextWidget()
		MetadataWidget.__init__( self, self.__textWidget, key, target, defaultValue = defaultValue, **kw )

		self.__acceptEmptyString = acceptEmptyString

		self.__textWidget.editingFinishedSignal().connect(
			Gaffer.WeakMethod( self.__editingFinished )
		)

	def textWidget( self ) :

		return self.__textWidget

	def _updateFromValue( self, value ) :

		self.__textWidget.setText( str( value ) )

	def __editingFinished( self, *unused ) :

		text = self.__textWidget.getText()
		if text or self.__acceptEmptyString :
			self._updateFromWidget( text )
		else :
			self._deregisterValue()

class MultiLineStringMetadataWidget( MetadataWidget ) :

	def __init__( self, key, target = None, defaultValue = "", role = GafferUI.MultiLineTextWidget.Role.Text, **kw ) :

		self.__textWidget = GafferUI.MultiLineTextWidget( role = role )
		MetadataWidget.__init__( self, self.__textWidget, key, target, defaultValue = defaultValue, **kw )

		self.__textWidget.editingFinishedSignal().connect(
			Gaffer.WeakMethod( self.__editingFinished )
		)

	def textWidget( self ) :

		return self.__textWidget

	def _updateFromValue( self, value ) :

		self.__textWidget.setText( str( value ) )

	def __editingFinished( self, *unused ) :

		self._updateFromWidget( self.__textWidget.getText() )

class ColorSwatchMetadataWidget( MetadataWidget ) :

	def __init__( self, key, target = None, defaultValue = imath.Color4f( 0, 0, 0, 0 ), **kw ) :

		self.__swatch = GafferUI.ColorSwatch( displayTransform = GafferUI.Widget.identityDisplayTransform )

		MetadataWidget.__init__( self, self.__swatch, key, target, defaultValue = defaultValue, **kw )

		self.__swatch._qtWidget().setFixedHeight( 18 )
		self.__swatch._qtWidget().setMaximumWidth( 40 )

		self.__swatch.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__buttonRelease ) )

	def _updateFromValue( self, value ) :

		self.__swatch.setColor( value )

	def __buttonRelease( self, swatch, event ) :

		if event.button != event.Buttons.Left :
			return False

		dialogue = GafferUI.ColorChooserDialogue( color = self.__swatch.getColor(), displayTransform = GafferUI.Widget.identityDisplayTransform )
		color = dialogue.waitForColor( parentWindow = self.ancestor( GafferUI.Window ) )

		if color is not None :
			self._updateFromWidget( color )

class MenuMetadataWidget( MetadataWidget ) :

	def __init__( self, key, labelsAndValues, target = None, defaultValue = None, **kw ) :

		self.__menuButton = GafferUI.MenuButton(
			menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) )
		)

		self.__labelsAndValues = labelsAndValues
		self.__currentValue = None

		MetadataWidget.__init__( self, self.__menuButton, key, target, defaultValue = defaultValue, **kw )

	def _updateFromValue( self, value ) :

		self.__currentValue = value

		buttonText = str( value )
		for label, value in self.__labelsAndValues :
			if value == self.__currentValue :
				buttonText = label
				break

		self.__menuButton.setText( buttonText )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()
		for label, value in self.__labelsAndValues :
			result.append(
				"/" + label,
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), value = value ),
					"checkBox" : value == self.__currentValue
				}
			)

		return result

	def __setValue( self, unused, value ) :

		self._updateFromWidget( value )


class FileSystemPathMetadataWidget( MetadataWidget ) :

	def __init__( self, key, target = None, acceptEmptyString = True, defaultValue = "", **kw ) :

		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )

		self.__path = Gaffer.FileSystemPath()
		self.__pathWidget = GafferUI.PathWidget( self.__path )

		MetadataWidget.__init__( self, self.__row, key, target, defaultValue = defaultValue, **kw )

		self.__row.append( self.__pathWidget )

		button = GafferUI.Button( image = "pathChooser.png", hasFrame=False )
		button.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ) )
		self.__row.append( button )

		self.__acceptEmptyString = acceptEmptyString

		self.__pathWidget.editingFinishedSignal().connect(
			Gaffer.WeakMethod( self.__editingFinished )
		)

	def _updateFromValue( self, value ) :

		self.__path.setFromString( str( value ) )

	def __editingFinished( self, *unused ) :

		text = str( self.__path )
		if text or self.__acceptEmptyString :
			self._updateFromWidget( text )
		else :
			self._deregisterValue()

	def __buttonClicked( self, widget ) :

		path = str( self.__path )
		path = path if os.path.exists( path ) else os.path.expanduser( "~" )

		dialogue = GafferUI.PathChooserDialogue( Gaffer.FileSystemPath( path ) )
		chosenPath = dialogue.waitForPath( parentWindow = self.ancestor( GafferUI.Window ) )

		if chosenPath is not None :
			self.__path.setFromString( str( chosenPath ) )
			self.__editingFinished()

class NumericMetadataWidget( MetadataWidget ) :

	def __init__( self, key, target = None, defaultValue = 0, **kw ) :

		self.__numericWidget = GafferUI.NumericWidget( value = defaultValue )

		self.__defaultValue = defaultValue
		# we use these to decide which actions to merge into a single undo
		self.__lastChangedReason = None
		self.__mergeGroupId = 0

		MetadataWidget.__init__( self, self.__numericWidget, key, target, defaultValue = defaultValue, **kw )

		self.__numericWidget.valueChangedSignal().connect(
			Gaffer.WeakMethod( self.__valueChanged )
		)

	def numericWidget( self ) :

		return self.__numericWidget

	def _updateFromValue( self, value ) :

		self.__numericWidget.setValue( type( self.__defaultValue )( value ) )

	def __valueChanged( self, widget, reason ) :

		if reason == GafferUI.NumericWidget.ValueChangedReason.InvalidEdit :
			self._updateFromValue( self.defaultValue() )
			return

		if not widget.changesShouldBeMerged( self.__lastChangedReason, reason ) :
			self.__mergeGroupId += 1
		self.__lastChangedReason = reason

		self._updateFromWidget(
			self.__numericWidget.getValue(),
			mergeGroup = "NumericMetadataWidget{}{}".format( id( self, ), self.__mergeGroupId )
		)

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

import weakref

import Gaffer
import GafferUI

from GafferUI.PlugValueWidget import sole

from Qt import QtCore

class ColorPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		self.__column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4 )

		GafferUI.PlugValueWidget.__init__( self, self.__column, plugs, **kw )

		with self.__column :

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

				self.__compoundNumericWidget = GafferUI.CompoundNumericPlugValueWidget( plugs )

				self.__swatch = GafferUI.ColorSwatchPlugValueWidget( plugs, parenting = { "expand" : True } )
				self.__swatch.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__swatchButtonRelease ), scoped = False )

				self.__chooserButton = GafferUI.Button( image = "colorPlugValueWidgetSlidersOff.png", hasFrame = False )
				self.__chooserButton.clickedSignal().connect( Gaffer.WeakMethod( self.__chooserButtonClicked ), scoped = False )

			self.__colorChooser = GafferUI.ColorChooserPlugValueWidget( plugs )

		self.setColorChooserVisible(
			sole( Gaffer.Metadata.value( plug, "colorPlugValueWidget:colorChooserVisible" ) for plug in self.getPlugs() )
		)

		self.__blinkBehaviour = None

	def setColorChooserVisible( self, visible ) :

		self.__colorChooser.setVisible( visible )
		self.__swatch.setVisible( not visible )
		self.__chooserButton.setImage(
			"colorPlugValueWidgetSliders{}.png".format( "On" if visible else "Off" )
		)

	def getColorChooserVisible( self ) :

		return self.__colorChooser.getVisible()

	def setPlugs( self, plugs ) :

		GafferUI.PlugValueWidget.setPlugs( self, plugs )

		self.__compoundNumericWidget.setPlugs( plugs )
		self.__colorChooser.setPlugs( plugs )
		self.__swatch.setPlugs( plugs )

	def setHighlighted( self, highlighted ) :

		GafferUI.PlugValueWidget.setHighlighted( self, highlighted )
		self.__compoundNumericWidget.setHighlighted( highlighted )

	def setReadOnly( self, readOnly ) :

		if readOnly == self.getReadOnly() :
			return

		GafferUI.PlugValueWidget.setReadOnly( self, readOnly )
		self.__compoundNumericWidget.setReadOnly( readOnly )
		self.__swatch.setReadOnly( readOnly )

	def childPlugValueWidget( self, childPlug ) :

		return self.__compoundNumericWidget.childPlugValueWidget( childPlug )

	def __swatchButtonRelease( self, widget, event ) :

		if not self._editable() :

			# The swatch will have been unable to display a colour chooser, so we
			# draw the user's attention to the components which are preventing that.
			if self.__blinkBehaviour is not None :
				self.__blinkBehaviour.stop()

			widgets = [
				self.__compoundNumericWidget.childPlugValueWidget( p )
				for p in Gaffer.Plug.Range( next( iter( self.getPlugs() ) ) )
			]
			widgets = [ w for w in widgets if not w._editable() ]
			self.__blinkBehaviour = _BlinkBehaviour( widgets )
			self.__blinkBehaviour.start()

			return False

	def __chooserButtonClicked( self, widget ) :

		visible = not self.getColorChooserVisible()
		self.setColorChooserVisible( visible )

		# Remember the user's choice so we can match it next time
		# we construct a widget for one of these plugs.
		for plug in self.getPlugs() :
			Gaffer.Metadata.registerValue( plug, "colorPlugValueWidget:colorChooserVisible", visible, persistent = False )

GafferUI.PlugValueWidget.registerType( Gaffer.Color3fPlug, ColorPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.Color4fPlug, ColorPlugValueWidget )

## \todo Consider if this is something that might be useful elsewhere, if
# there are other such things, and what a Behaviour base class for them
# might look like.
class _BlinkBehaviour( object ) :

	def __init__( self, targetWidgets, blinks = 2 ) :

		self.__targetWidgets = [ weakref.ref( w ) for w in targetWidgets ]
		self.__initialStates = [ w.getHighlighted() for w in targetWidgets ]

		self.__blinks = blinks
		self.__toggleCount = 0
		self.__timer = QtCore.QTimer()
		self.__timer.timeout.connect( self.__blink )

	def start( self ) :

		self.__toggleCount = 0
		self.__blink()
		self.__timer.start( 250 )

	def stop( self ) :

		self.__timer.stop()
		for widget, initialState in zip( self.__targetWidgets, self.__initialStates ) :
			widget = widget()
			if widget :
				widget.setHighlighted( initialState )

	def __blink( self ) :

		self.__toggleCount += 1

		for widget, initialState in zip( self.__targetWidgets, self.__initialStates ) :
			widget = widget()
			if widget :
				widget.setHighlighted( bool( ( int( initialState ) + self.__toggleCount ) % 2 ) )

		if self.__toggleCount >= self.__blinks * 2 :
			self.__timer.stop()

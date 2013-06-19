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

import weakref

import IECore

import Gaffer
import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )

class ColorPlugValueWidget( GafferUI.CompoundNumericPlugValueWidget ) :

	def __init__( self, plug, **kw ) :
			
		GafferUI.CompoundNumericPlugValueWidget.__init__( self, plug, **kw )

		self.__swatch = GafferUI.ColorSwatch()
		## \todo How do set maximum height with a public API?
		self.__swatch._qtWidget().setMaximumHeight( 20 )
		
		self._row().append( self.__swatch, expand=True )
						
		self.__buttonPressConnection = self.__swatch.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )
		
		self.__colorChooserDialogue = None
		self.__blinkBehaviour = None
		
		self._updateFromPlug()
		
	def _updateFromPlug( self ) :
	
		GafferUI.CompoundNumericPlugValueWidget._updateFromPlug( self )
	
		plug = self.getPlug()
		if plug is not None :
			with self.getContext() :
				self.__swatch.setColor( plug.getValue() )
		
	def __buttonPress( self, widget, event ) :
		
		if not self._editable() :
		
			if self.__blinkBehaviour is not None :
				self.__blinkBehaviour.stop()
			widgets = [ w for w in self._row()[:len( self.getPlug() )] if not w._editable() ]
			self.__blinkBehaviour = _BlinkBehaviour( widgets )
			self.__blinkBehaviour.start()
			
			return False
				
		# we only store a weak reference to the dialogue, because we want to allow it
		# to manage its own lifetime. this allows it to exist after we've died, which
		# can be useful for the user - they can bring up a node editor to get access to
		# the color chooser, and then close the node editor but keep the floating color
		# chooser. the only reason we keep a reference to the dialogue at all is so that
		# we can avoid opening two at the same time.
		if self.__colorChooserDialogue is None or self.__colorChooserDialogue() is None :
			self.__colorChooserDialogue = weakref.ref(
				_ColorPlugValueDialogue(
					self.getPlug(),
					self.ancestor( GafferUI.Window )
				)
			)

		self.__colorChooserDialogue().setVisible( True )
				
		return True
					
GafferUI.PlugValueWidget.registerType( Gaffer.Color3fPlug.staticTypeId(), ColorPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.Color4fPlug.staticTypeId(), ColorPlugValueWidget )

## \todo Perhaps we could make this a part of the public API and give it an acquire()
# method which the ColorPlugValueWidget uses?
## \todo Support undo properly, with concatenation of repeated operations.
class _ColorPlugValueDialogue( GafferUI.ColorChooserDialogue ) :

	def __init__( self, plug, parentWindow ) :
	
		GafferUI.ColorChooserDialogue.__init__( 
			self,
			title = plug.relativeName( plug.ancestor( Gaffer.ScriptNode.staticTypeId() ) ),
			color = plug.getValue()
		)

		self.__plug = plug

		node = plug.node()
		self.__nodeParentChangedConnection = node.parentChangedSignal().connect( Gaffer.WeakMethod( self.__destroy ) )
		self.__plugSetConnection = plug.node().plugSetSignal().connect( Gaffer.WeakMethod( self.__plugSet ) )
		
		self.__closedConnection = self.closedSignal().connect( Gaffer.WeakMethod( self.__destroy ) )
		self.__colorChangedConnection = self.colorChooser().colorChangedSignal().connect( Gaffer.WeakMethod( self.__colorChanged ) )
		self.__confirmClickedConnection = self.confirmButton.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ) )
		self.__cancelClickedConnection = self.cancelButton.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ) )

		parentWindow.addChildWindow( self )

	def __plugSet( self, plug ) :
		
		if plug.isSame( self.__plug ) :
			self.colorChooser().setColor( self.__plug.getValue() )

	def __colorChanged( self, colorChooser ) :
	
		self.__plug.setValue( self.colorChooser().getColor() )
	
	def __buttonClicked( self, button ) :
		
		if button is self.cancelButton :
			self.__plug.setValue( self.colorChooser().getInitialColor() )
		
		# ideally we'd just remove ourselves from our parent immediately, but that would
		# trigger this bug :
		#
		# 	https://bugreports.qt-project.org/browse/QTBUG-26761
		#
		# so instead we destroy ourselves on the next idle event.
		
		GafferUI.EventLoop.addIdleCallback( self.__destroy )
	
	def __destroy( self, *unused ) :
	
		self.parent().removeChild( self )
		return False # to remove idle callback

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
		
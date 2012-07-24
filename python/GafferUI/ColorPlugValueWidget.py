##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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

class ColorPlugValueWidget( GafferUI.CompoundNumericPlugValueWidget ) :

	def __init__( self, plug, **kw ) :
			
		GafferUI.CompoundNumericPlugValueWidget.__init__( self, plug, **kw )

		self.__swatch = GafferUI.ColorSwatch()
		self._row().append( self.__swatch, expand=True )
						
		self.__buttonPressConnection = self.__swatch.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )
		
		self.__colorChooserDialogue = None
		
		self._updateFromPlug()
		
	def _updateFromPlug( self ) :
	
		GafferUI.CompoundNumericPlugValueWidget._updateFromPlug( self )
	
		plug = self.getPlug()
		if plug is not None :
			with self.getContext() :
				self.__swatch.setColor( plug.getValue() )
		
	def __buttonPress( self, widget, event ) :
				
		if not self.__colorChooserDialogue :	
			self.__colorChooserDialogue = GafferUI.ColorChooserDialogue()
		
		self.ancestor( GafferUI.Window ).addChildWindow( self.__colorChooserDialogue )
		self.__colorChooserDialogue.setTitle( self.getPlug().relativeName( self.getPlug().ancestor( Gaffer.ScriptNode.staticTypeId() ) ) )
		self.__colorChooserDialogue.colorChooser().setColor( self.getPlug().getValue() )
		self.__colorChooserDialogue.colorChooser().setInitialColor( self.getPlug().getValue() )
		
		self.__colorChangedConnection = self.__colorChooserDialogue.colorChooser().colorChangedSignal().connect( Gaffer.WeakMethod( self.__colorChanged ) )
		self.__confirmClickedConnection = self.__colorChooserDialogue.confirmButton.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ) )
		self.__cancelClickedConnection = self.__colorChooserDialogue.cancelButton.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ) )
		self.__dialogueClosedConnection = self.__colorChooserDialogue.closedSignal().connect( Gaffer.WeakMethod( self.__dialogueClosed ) )
		
		self.__colorChooserDialogue.setVisible( True )
				
		return True
		
	def __colorChanged( self, colorDialogue ) :
	
		color = colorDialogue.getColor()
		self.getPlug().setValue( color )
		
	def __buttonClicked( self, button ) :
	
		if button is self.__colorChooserDialogue.cancelButton :
			self.getPlug().setValue( self.__colorChooserDialogue.colorChooser().getInitialColor() )
		
		self.__colorChooserDialogue.parent().removeChild( self.__colorChooserDialogue )	
		self.__colorChooserDialogue = None
		
	def __dialogueClosed( self, dialogue ) :
	
		self.__colorChooserDialogue = None
				
GafferUI.PlugValueWidget.registerType( Gaffer.Color3fPlug.staticTypeId(), ColorPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.Color4fPlug.staticTypeId(), ColorPlugValueWidget )

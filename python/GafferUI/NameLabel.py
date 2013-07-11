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

import IECore

import Gaffer
import GafferUI

## The NameLabel class displays a label which is kept in sync with the name of
# a particular GraphComponent. The label acts as a drag source for dragging the
# GraphComponent to another widget.
class NameLabel( GafferUI.Label ) :

	def __init__( self, graphComponent, horizontalAlignment=GafferUI.Label.HorizontalAlignment.Left, verticalAlignment=GafferUI.Label.VerticalAlignment.Center,**kw ) :
	
		GafferUI.Label.__init__( self, "", horizontalAlignment, verticalAlignment, **kw )

		self.setGraphComponent( graphComponent )
		
		self.__buttonPressConnection = self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )
		self.__dragBeginConnection = self.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ) )
		self.__dragEndConnection = self.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ) )

	## Calling setText() disables the name tracking behaviour.
	def setText( self, text ) :
	
		GafferUI.Label.setText( self, text )
		
		self.__nameChangedConnection = None

	def setGraphComponent( self, graphComponent ) :
	
		self.__graphComponent = graphComponent
		if self.__graphComponent is not None :
			self.__nameChangedConnection = self.__graphComponent.nameChangedSignal().connect( Gaffer.WeakMethod( self.__setText ) )
		else :
			self.__nameChangedConnection = None
			
		self.__setText()
		
	def getGraphComponent( self ) :
	
		return self.__graphComponent
	
	def __setText( self, *unwantedArgs ) :
	
		if self.getGraphComponent() is not None :
			GafferUI.Label.setText( self, IECore.CamelCase.toSpaced( self.__graphComponent.getName() ) )

	def __buttonPress( self, widget, event ) :
			
		return self.getGraphComponent() is not None and event.buttons & ( event.Buttons.Left | event.Buttons.Middle )
		
	def __dragBegin( self, widget, event ) :
	
		if event.buttons & ( event.Buttons.Left | event.Buttons.Middle ) :
			GafferUI.Pointer.setFromFile( "nodes.png" )
			return self.getGraphComponent()
		
		return None

	def __dragEnd( self, widget, event ) :
	
		GafferUI.Pointer.set( None )
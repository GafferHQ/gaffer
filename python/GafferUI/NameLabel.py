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

	def __init__( self, graphComponent, horizontalAlignment=GafferUI.Label.HorizontalAlignment.Left, verticalAlignment=GafferUI.Label.VerticalAlignment.Center, numComponents=1, formatter=None, **kw ) :
	
		GafferUI.Label.__init__( self, "", horizontalAlignment, verticalAlignment, **kw )

		self.__formatter = formatter if formatter is not None else self.__defaultFormatter
		self.__numComponents = numComponents
		
		self.__connections = []
		self.__graphComponent = False # force setGraphComponent() to update no matter what
		self.setGraphComponent( graphComponent )
		
		self.__buttonPressConnection = self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )
		self.__dragBeginConnection = self.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ) )
		self.__dragEndConnection = self.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ) )

	## Calling setText() disables the name tracking behaviour.
	def setText( self, text ) :
	
		GafferUI.Label.setText( self, text )
		
		self.__connections = []

	def setGraphComponent( self, graphComponent ) :
		
		if graphComponent is not None and self.__graphComponent is not False :
			if graphComponent.isSame( self.__graphComponent ) :
				return
		elif self.__graphComponent is None :
			return
		
		self.__graphComponent = graphComponent
		self.__setupConnections()	
		self.__setText()
		
	def getGraphComponent( self ) :
	
		return self.__graphComponent
	
	## Specifies how many levels of the hierarchy to be displayed in
	# the name. A value of 1 shows only the name of getGraphComponent().
	# A value of 2 also shows the parent name, and so on. Use setFormatter()
	# if you wish to customise how these names are displayed.
	def setNumComponents( self, numComponents ) :
	
		assert( numComponents > 0 )
	
		if numComponents == self.__numComponents :
			return
			
		self.__numComponents = numComponents
		self.__setupConnections()
		self.__setText()
		
	def getNumComponents( self ) :
	
		return self.__numComponents
	
	## Specifies a function which is passed a list of GraphComponents
	# and returns a string containing their names. This function will
	# be used to generate the label text.
	def setFormatter( self, formatter ) :
	
		self.__formatter = formatter
		self.__setText()
		
	def getFormatter( self ) :
	
		return self.__formatter
	
	def __setupConnections( self, reuseUntil=None ) :
			
		if self.__graphComponent is None :
			self.__connections = []
			return
		
		# when a parent has changed somewhere in the hierarchy,
		# we only need to make new connections for the components
		# for the new parent and its ancestors - the connections for
		# components below the parent can be reused. this might seem
		# like a rather pointless optimisation, but it's actually 
		# critical - we are called from within __parentChanged( someComponent )
		# and if were to reconnect __parentChanged to someComponent
		# here, __parentChanged would be called again immediately,
		# resulting in an infinite loop. our updatedConnections will
		# be a mix of reused connections and newly created ones.
						
		updatedConnections = []
		
		n = 0
		g = self.__graphComponent
		reuse = reuseUntil is not None
		while g is not None and n < self.__numComponents :
			if reuse :
				updatedConnections.extend( self.__connections[n*2:n*2+2] )
			else :
				updatedConnections.append( g.nameChangedSignal().connect( Gaffer.WeakMethod( self.__setText ) ) )
				if n < self.__numComponents - 1 :
					updatedConnections.append( g.parentChangedSignal().connect( Gaffer.WeakMethod( self.__parentChanged ) ) )

			if g.isSame( reuseUntil ) :
				reuse = False
				
			g = g.parent()
			n += 1
		
		self.__connections = updatedConnections
		
	def __parentChanged( self, child, oldParent ) :
		
		self.__setText()
		self.__setupConnections( reuseUntil = child )
	
	def __setText( self, *unwantedArgs ) :
		
		graphComponents = []
		
		n = 0
		g = self.__graphComponent
		while g is not None and n < self.__numComponents :
			graphComponents.append( g )
			g = g.parent()
			n += 1
				
		graphComponents.reverse()
		GafferUI.Label.setText( self, self.__formatter( graphComponents ) )

	def __buttonPress( self, widget, event ) :
			
		return self.getGraphComponent() is not None and event.buttons & ( event.Buttons.Left | event.Buttons.Middle )
		
	def __dragBegin( self, widget, event ) :
	
		if event.buttons & ( event.Buttons.Left | event.Buttons.Middle ) :
			GafferUI.Pointer.setFromFile( "nodes.png" )
			return self.getGraphComponent()
		
		return None

	def __dragEnd( self, widget, event ) :
	
		GafferUI.Pointer.set( None )

	@staticmethod
	def __defaultFormatter( graphComponents ) :
	
		return ".".join( IECore.CamelCase.toSpaced( g.getName() ) for g in graphComponents )

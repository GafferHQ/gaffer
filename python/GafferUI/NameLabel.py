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

import functools

import IECore

import Gaffer
import GafferUI

## The NameLabel class displays a label which is kept in sync with the name of
# one or more GraphComponents. The label acts as a drag source for dragging the
# GraphComponents to another widget.
class NameLabel( GafferUI.Label ) :

	### \todo Rename numComponents -> numAncestors at the next API break
	def __init__( self, graphComponent, horizontalAlignment=GafferUI.Label.HorizontalAlignment.Left, verticalAlignment=GafferUI.Label.VerticalAlignment.Center, numComponents=1, formatter=None, **kw ) :

		if isinstance( graphComponent, Gaffer.GraphComponent ) :
			graphComponents = { graphComponent }
		else :
			graphComponents = graphComponent or set()

		GafferUI.Label.__init__( self, "", horizontalAlignment, verticalAlignment, **kw )

		self.__formatter = formatter if formatter is not None else self.defaultFormatter
		self.__numComponents = numComponents

		self.__connections = {}
		self.__graphComponents = None # force setGraphComponent() to update no matter what
		self.setGraphComponents( graphComponents )

		self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )
		self.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ) )
		self.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ) )

	## Calling setText() disables the name tracking behaviour.
	## \deprecated. Use a custom formatter to override the text.
	def setText( self, text ) :

		GafferUI.Label.setText( self, text )

		self.__connections = {}

	def setGraphComponent( self, graphComponent ) :

		self.setGraphComponents( { graphComponent } if graphComponent is not None else set() )

	def getGraphComponent( self ) :

		count = len( self.__graphComponents )

		if count > 1 :
			raise RuntimeError( "getGraphComponent called with multiple GraphComponents" )
		elif count == 1 :
			return next( iter( self.__graphComponents ) )

		return None

	def setGraphComponents( self, graphComponents ) :

		if not isinstance( graphComponents, set ) :
			graphComponents = set( graphComponents )

		if graphComponents == self.__graphComponents :
			return

		self.__graphComponents = graphComponents.copy()
		self.__setupConnections()
		self.__setText()

	def getGraphComponents( self ):

		return self.__graphComponents.copy()

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

	@staticmethod
	def defaultFormatter( graphComponents ) :

		return ".".join( IECore.CamelCase.toSpaced( g.getName() ) for g in graphComponents )

	def __setupConnections( self ) :

		if not self.__graphComponents :
			self.__connections = {}
			return

		for component in self.__graphComponents :
			self.__updateConnections( component )

		for component in list( self.__connections.keys() ) :
			if component not in self.__graphComponents :
				del self.__connections[ component ]

	def __updateConnections( self, component, reuseUntil=None ) :

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
		g = component
		reuse = reuseUntil is not None
		while g is not None and n < self.__numComponents :
			if reuse :
				updatedConnections.extend( self.__connections[ component ][ n*2 : n*2+2 ] )
			else :
				updatedConnections.append(
					g.nameChangedSignal().connect(
						Gaffer.WeakMethod( self.__setText ),
						scoped = True
					)
				)
				if n < self.__numComponents - 1 :
					updatedConnections.append(
						g.parentChangedSignal().connect(
							functools.partial( Gaffer.WeakMethod( self.__parentChanged ), component ),
							scoped = True
						)
					)

			if g.isSame( reuseUntil ) :
				reuse = False

			g = g.parent()
			n += 1

		self.__connections[ component ] = updatedConnections

	def __parentChanged( self, presentedComponent, child, oldParent ) :

		self.__setText()
		self.__updateConnections( presentedComponent, reuseUntil = child )

	def __setText( self, *unwantedArgs ) :

		names = set()

		for graphComponent in self.__graphComponents :

			hierarchyComponents = []

			n = 0
			g = graphComponent
			while g is not None and n < self.__numComponents :
				hierarchyComponents.append( g )
				g = g.parent()
				n += 1

			hierarchyComponents.reverse()

			names.add( self.__formatter( hierarchyComponents ) )

		if len( names ) == 1 :
			label = next( iter( names ) )
		elif names :
			label = "---"
		else:
			label = ""

		GafferUI.Label.setText( self, label )

	def __buttonPress( self, widget, event ) :

		return bool( self.getGraphComponents() ) and event.buttons & ( event.Buttons.Left | event.Buttons.Middle )

	def __dragBegin( self, widget, event ) :

		if event.buttons & ( event.Buttons.Left | event.Buttons.Middle ) :
			GafferUI.Pointer.setCurrent( "nodes" )
			if len( self.__graphComponents ) == 1 :
				return next( iter( self.__graphComponents ) )
			else :
				return Gaffer.StandardSet( self.__graphComponents )

		return None

	def __dragEnd( self, widget, event ) :

		GafferUI.Pointer.setCurrent( None )

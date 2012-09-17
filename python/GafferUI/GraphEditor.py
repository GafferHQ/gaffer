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

from __future__ import with_statement

import IECore

import Gaffer
import GafferUI

class GraphEditor( GafferUI.EditorWidget ) :

	def __init__( self, scriptNode, **kw ) :
				
		self.__gadgetWidget = GafferUI.GadgetWidget(
			bufferOptions = set( [
				GafferUI.GLWidget.BufferOptions.Double,
			] ),
		)
		
		GafferUI.EditorWidget.__init__( self, self.__gadgetWidget, scriptNode, **kw )
		
		self.__gadgetWidget.viewportGadget().setChild( GafferUI.GraphGadget( self.scriptNode() ) )
		self.__frame()		

		self.__buttonPressConnection = self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )
		self.__keyPressConnection = self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ) )
					
	## Returns the internal GadgetWidget holding the GraphGadget.	
	def graphGadgetWidget( self ) :
	
		return self.__gadgetWidget

	## Returns the internal Gadget used to draw the graph. This may be
	# modified directly to set up appropriate filters etc. This is just
	# a convenience method returning graphGadgetWidget().viewportGadget().getChild().
	def graphGadget( self ) :
	
		return self.graphGadgetWidget().viewportGadget().getChild()
	
	__nodeContextMenuSignal = Gaffer.Signal2()
	## Returns a signal which is emitted to create a context menu for a
	# node in the graph. Slots may connect to this signal to edit the
	# menu definition on the fly - the signature for the signal is
	# ( node, menuDefinition ) and the menu definition should just be
	# edited in place. Typically you would add slots to this signal
	# as part of a startup script.
	@classmethod
	def nodeContextMenuSignal( cls ) :
	
		return cls.__nodeContextMenuSignal
		
	def __repr__( self ) :

		return "GafferUI.GraphEditor( scriptNode )"	

	def __buttonPress( self, widget, event ) :
				
		if event.buttons & GafferUI.ButtonEvent.Buttons.Right :
						
			# right click - display either the node creation popup menu
			# or a menu specific to the node under the mouse if possible.
			
			menuDefinition = GafferUI.NodeMenu.definition()
			
			gadgets = self.__gadgetWidget.viewportGadget().gadgetsAt( IECore.V2f( event.line.p1.x, event.line.p1.y ) )
			if len( gadgets ) :
				nodeGadget = gadgets[0]
				if not isinstance( nodeGadget, GafferUI.NodeGadget ) :
					nodeGadget = nodeGadget.ancestor( GafferUI.NodeGadget.staticTypeId() )		
				if nodeGadget :
					nodeMenuDefinition = IECore.MenuDefinition()
					self.nodeContextMenuSignal()( nodeGadget.node(), nodeMenuDefinition )
					if len( nodeMenuDefinition.items() ) :
						menuDefinition = nodeMenuDefinition
			
			self.__m = GafferUI.Menu( menuDefinition )
			self.__m.popup( self )
						
			return True
	
		return False
	
	def __keyPress( self, widget, event ) :
	
		if event.key == "F" :
			self.__frame()
			return True
		
		return False
		
	def __frame( self ) :
	
		graphGadget = self.graphGadget()
		
		# get the bounds of the selected nodes
		scriptNode = self.scriptNode()
		selection = scriptNode.selection()
		bound = IECore.Box3f()
		for node in selection :
			nodeGadget = graphGadget.nodeGadget( node )
			if nodeGadget :
				bound.extendBy( nodeGadget.transformedBound( graphGadget ) )
		
		# if there were no nodes selected then use the bound of the whole
		# graph.		
		if bound.isEmpty() :
			bound = graphGadget.bound()
			
		# if there's still nothing then an arbitrary area in the centre of the world
		if bound.isEmpty() :
			bound = IECore.Box3f( IECore.V3f( -10, -10, 0 ), IECore.V3f( 10, 10, 0 ) )
			
		# pad it a little bit so
		# it sits nicer in the frame
		bound.min -= IECore.V3f( 5, 5, 0 )
		bound.max += IECore.V3f( 5, 5, 0 )
				
		# now adjust the bounds so that we don't zoom in further than we want to
		boundSize = bound.size()
		widgetSize = IECore.V3f( self._qtWidget().width(), self._qtWidget().height(), 0 )
		pixelsPerUnit = widgetSize / boundSize
		adjustedPixelsPerUnit = min( pixelsPerUnit.x, pixelsPerUnit.y, 10 )
		newBoundSize = widgetSize / adjustedPixelsPerUnit
		boundCenter = bound.center()
		bound.min = boundCenter - newBoundSize / 2.0
		bound.max = boundCenter + newBoundSize / 2.0
			
		self.__gadgetWidget.viewportGadget().frame( bound )
		
GafferUI.EditorWidget.registerType( "GraphEditor", GraphEditor )

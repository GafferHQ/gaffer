##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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
from GafferUI import EditorWidget, GraphGadget, GadgetWidget, GLWidget

QtGui = GafferUI._qtImport( "QtGui" )

class GraphEditor( GafferUI.EditorWidget ) :

	def __init__( self, scriptNode=None ) :
		
		self.__gadgetWidget = GadgetWidget(
			bufferOptions = set( [
				GLWidget.BufferOptions.Double,
			] ),
			cameraMode = GadgetWidget.CameraMode.Mode2D,
		)
		
		EditorWidget.__init__( self, self.__gadgetWidget, scriptNode )
		
		self.__gadgetWidget.setBackgroundColor( IECore.Color3f( 0.5 ) )
		self.__gadgetWidget._framingBound = Gaffer.WeakMethod( self.__framingBound )
		
		self.__buttonPressConnection = self.buttonPressSignal().connect( self.__buttonPress )
	
		self.setScriptNode( scriptNode )
	
	def setScriptNode( self, scriptNode ) :
	
		if not hasattr( self, "_GraphEditor__gadgetWidget" ) :
			# we're still constructing
			return
	
		EditorWidget.setScriptNode( self, scriptNode )
		
		gadget = None
		if scriptNode :
			gadget = GraphGadget( scriptNode )
			
		self.__gadgetWidget.setGadget( gadget )
			
	def __repr__( self ) :

		return "GafferUI.GraphEditor()"	

	def __buttonPress( self, widget, event ) :
				
		if event.buttons & GafferUI.ButtonEvent.Buttons.Right :
						
			# right click
			
			self.__m = GafferUI.Menu( GafferUI.NodeMenu.definition() )
			self.__m.popup( self )
						
			return True
	
		return False
		
	def __framingBound( self ) :
	
		graphGadget = self.__gadgetWidget.getGadget()
		if not graphGadget :
			return IECore.Box3f()
		
		# get the bounds of the selected nodes
		scriptNode = self.getScriptNode()
		selection = scriptNode.selection()
		result = IECore.Box3f()
		for node in selection.members() :
			nodeGadget = graphGadget.nodeGadget( node )
			if nodeGadget :
				result.extendBy( nodeGadget.transformedBound( graphGadget ) )
		
		# if there were no nodes selected then use the bound of the whole
		# graph.		
		if result.isEmpty() :
			result = graphGadget.bound()
			
		# if there's still nothing then frame -10,10 so we're looking at where
		# new nodes will be appearing	
		if result.isEmpty() :
			result = IECore.Box3f( IECore.V3f( -10, -10, 0 ), IECore.V3f( 10, 10, 0 ) )
			
		# pad it a little bit so
		# it sits nicer in the frame
		result.min -= IECore.V3f( 5, 5, 0 )
		result.max += IECore.V3f( 5, 5, 0 )
				
		# now adjust the bounds so that we don't zoom in further than we want to
		boundSize = result.size()
		widgetSize = IECore.V3f( self._qtWidget().width(), self._qtWidget().height(), 0 )
		pixelsPerUnit = widgetSize / boundSize
		adjustedPixelsPerUnit = min( pixelsPerUnit.x, pixelsPerUnit.y, 10 )
		newBoundSize = widgetSize / adjustedPixelsPerUnit
		boundCenter = result.center()
		result.min = boundCenter - newBoundSize / 2.0
		result.max = boundCenter + newBoundSize / 2.0
			
		return result
		
EditorWidget.registerType( "GraphEditor", GraphEditor )

##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

# PlugValueWidget registrations
##########################################################################

class _RandomColorPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :
	
		self.__grid = GafferUI.GridContainer( spacing = 4 )
		
		GafferUI.PlugValueWidget.__init__( self, self.__grid, plug, **kw )
		
		with self.__grid :
			for x in range( 0, 10 ) :
				for y in range( 0, 3 ) :
					GafferUI.ColorSwatch( index = ( x, y ) )	
		
		self._updateFromPlug()
		
	def _updateFromPlug( self ) :
			
		node = self.getPlug().node()
		seed = node["seed"].getValue()
		
		gridSize = self.__grid.gridSize()
		for x in range( 0, gridSize.x ) :
			for y in range( 0, gridSize.y ) :
				self.__grid[x,y].setColor( node.randomColor( seed ) )
				seed += 1
				
GafferUI.PlugValueWidget.registerCreator( Gaffer.Random.staticTypeId(), "outColor", _RandomColorPlugValueWidget )
GafferUI.PlugValueWidget.registerCreator( Gaffer.Random.staticTypeId(), "outFloat", None )

# PlugValueWidget popup menu
##########################################################################

def __createRandom( plug ) :

	node = plug.node()
	parentNode = node.ancestor( Gaffer.Node.staticTypeId() )

	with Gaffer.UndoContext( node.scriptNode() ) :
	
		randomNode = Gaffer.Random()
		parentNode.addChild( randomNode )
		
		if isinstance( plug, Gaffer.FloatPlug ) :
			plug.setInput( randomNode["outFloat"] )
		elif isinstance( plug, Gaffer.Color3fPlug ) :
			plug.setInput( randomNode["outColor"] )
			
	GafferUI.NodeEditor.acquire( randomNode )

def __popupMenu( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug()
	if not isinstance( plug, ( Gaffer.FloatPlug, Gaffer.Color3fPlug ) ) :
		return
		
	node = plug.node()
	if node is None or node.parent() is None :
		return

	input = plug.getInput()
	if input is None and plugValueWidget._editable() :		
		menuDefinition.prepend( "/Randomise...", { "command" : IECore.curry( __createRandom, plug ) } )
		
__popupMenuConnection = GafferUI.PlugValueWidget.popupMenuSignal().connect( __popupMenu )

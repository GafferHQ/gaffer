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

from __future__ import with_statement

import IECore

import Gaffer
import GafferUI

import GafferScene
import GafferSceneUI

## \todo Decide how/where we show the display label.
class DisplaysPlugValueWidget( GafferUI.CompoundPlugValueWidget ) :

	def __init__( self, plug ) :
	
		GafferUI.CompoundPlugValueWidget.__init__( self, plug, collapsed = None )

		self.__footerWidget = None

	def _footerWidget( self ) :
	
		if self.__footerWidget is not None :
			return self.__footerWidget
		
		self.__footerWidget = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
		
		addButton = GafferUI.MenuButton(
			image="plus.png", hasFrame=False, menu = GafferUI.Menu( Gaffer.WeakMethod( self.__addMenuDefinition ) )
		)
		self.__footerWidget.append( addButton )
		self.__footerWidget.append( GafferUI.Spacer( IECore.V2i( 1 ), maximumSize = IECore.V2i( 100000, 1 ) ), expand = True )
				
		return self.__footerWidget
	
	def _childPlugWidget( self, childPlug ) :
		
		return _ChildPlugWidget( childPlug )
			
	def __addMenuDefinition( self ) :
	
		node = self.getPlug().node()
		currentLabels = set( [ display["label"].getValue() for display in node["displays"].children() ] )
		
		m = IECore.MenuDefinition()
		
		registeredDisplays = node.registeredDisplays()
		for label in registeredDisplays :
			menuPath = label
			if not menuPath.startswith( "/" ) :
				menuPath = "/" + menuPath
			m.append(
				menuPath,
				{
					"command" : IECore.curry( node.addDisplay, label ),
					"active" : label not in currentLabels
				}	
			)

		if len( registeredDisplays ) :
			m.append( "/BlankDivider", { "divider" : True } )
			
		m.append( "/Blank", { "command" : IECore.curry( node.addDisplay, "", IECore.Display( "", "", "" ) ) } )
	
		return m

class _ChildPlugWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, childPlug ) :
	
		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing=4 )
		GafferUI.PlugValueWidget.__init__( self, column, childPlug )
		
		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing=4 )
		column.append( row )

		collapseButton = GafferUI.Button( image = "collapsibleArrowRight.png", hasFrame=False )
		collapseButton.__clickedConnection = collapseButton.clickedSignal().connect( Gaffer.WeakMethod( self.__collapseButtonClicked ) )
		row.append( collapseButton )
		
		row.append( GafferUI.PlugValueWidget.create( childPlug["active"] ) )
		row.append( GafferUI.PlugValueWidget.create( childPlug["name"] ) )
		row.append( GafferUI.PlugValueWidget.create( childPlug["type"] ) )
		row.append( GafferUI.PlugValueWidget.create( childPlug["data"] ) )
		
		parameterList = GafferUI.CompoundDataPlugValueWidget( childPlug["parameters"], collapsed=None )
		parameterList.setVisible( False )
		column.append( parameterList )

	def __collapseButtonClicked( self, button ) :
	
		column = button.parent().parent()
		parameterList = column[1]
		visible = not parameterList.getVisible()
		parameterList.setVisible( visible )
		button.setImage( "collapsibleArrowDown.png" if visible else "collapsibleArrowRight.png" )

	def _updateFromPlug( self ) :
	
		pass
		
GafferUI.PlugValueWidget.registerCreator( GafferScene.Displays.staticTypeId(), "displays", DisplaysPlugValueWidget )

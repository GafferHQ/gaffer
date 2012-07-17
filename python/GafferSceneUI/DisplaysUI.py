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

class DisplaysPlugValueWidget( GafferUI.CompoundPlugValueWidget ) :

	def __init__( self, plug ) :
	
		GafferUI.CompoundPlugValueWidget.__init__( self, plug, collapsible = False )

		self.__footerWidget = None

	def _footerWidget( self ) :
	
		if self.__footerWidget is not None :
			return self.__footerWidget
		
		self.__footerWidget = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
		
		addButton = GafferUI.Button( image="plus.png", hasFrame=False )
		self.__addButtonClickedConnection = addButton.clickedSignal().connect( Gaffer.WeakMethod( self.__addClicked ) )
		self.__footerWidget.append( addButton )
		self.__footerWidget.append( GafferUI.Spacer( IECore.V2i( 1 ) ), expand = True )
				
		return self.__footerWidget
	
	def _childPlugWidget( self, childPlug ) :
		
		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing=4 )
		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing=4 )
		column.append( row )

		collapseButton = GafferUI.Button( image = "collapsibleArrowRight.png", hasFrame=False )
		collapseButton.__clickedConnection = collapseButton.clickedSignal().connect( Gaffer.WeakMethod( self.__collapseButtonClicked ) )
		row.append( collapseButton )
		
		row.append( GafferUI.PlugValueWidget.create( childPlug["active"] ) )
		row.append( GafferUI.PlugValueWidget.create( childPlug["name"] ) )
		row.append( GafferUI.PlugValueWidget.create( childPlug["type"] ) )
		row.append( GafferUI.PlugValueWidget.create( childPlug["data"] ) )
		
		parameterList = GafferSceneUI.ParameterListPlugValueWidget( childPlug["parameters"], collapsible=False )
		parameterList.setVisible( False )
		column.append( parameterList )
			
		return column
	
	def __collapseButtonClicked( self, button ) :
	
		column = button.parent().parent()
		parameterList = column[1]
		visible = not parameterList.getVisible()
		parameterList.setVisible( visible )
		button.setImage( "collapsibleArrowDown.png" if visible else "collapsibleArrowRight.png" )

	def __addClicked( self, button ) :
	
		self.getPlug().node().addDisplay( "", "", "" )
	
GafferUI.PlugValueWidget.registerCreator( GafferScene.Displays.staticTypeId(), "displays", DisplaysPlugValueWidget )

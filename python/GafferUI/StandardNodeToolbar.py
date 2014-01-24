##########################################################################
#  
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

class StandardNodeToolbar( GafferUI.NodeToolbar ) :

	def __init__( self, node, **kw ) :
	
		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
		
		GafferUI.NodeToolbar.__init__( self, node, self.__row, **kw )
		
		for plug in node.children( Gaffer.Plug.staticTypeId() ) :
			
			if plug.getName().startswith( "__" ) :
				continue
			
			widget = GafferUI.PlugValueWidget.create( plug )
			if widget is None :
				continue
							
			if ( isinstance( widget, GafferUI.PlugValueWidget )
			     and not widget.hasLabel()
			     and Gaffer.Metadata.plugValue( plug, "label" ) != ""
			) :
				widget = GafferUI.PlugWidget( widget )
				widget.labelPlugValueWidget().label()._qtWidget().setFixedWidth( 0 )
				
			self.__row.append( widget )
			if Gaffer.Metadata.plugValue( plug, "divider" ) :
				self.__row.append( GafferUI.Divider( GafferUI.Divider.Orientation.Vertical ) )
		
		self.__row.insert( 0, GafferUI.Spacer( IECore.V2i( 1, 1 ) ), expand = True )

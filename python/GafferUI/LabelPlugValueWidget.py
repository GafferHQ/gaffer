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

import GafferUI

## A simple PlugValueWidget which just displays the name of the plug,
# with the popup action menu for the plug.
class LabelPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, horizontalAlignment=GafferUI.Label.HorizontalAlignment.Left, verticalAlignment=GafferUI.Label.VerticalAlignment.Center, **kw ) :
		
		self.__label = GafferUI.NameLabel(
			plug,
			horizontalAlignment = horizontalAlignment,
			verticalAlignment = verticalAlignment,
		)
		
		GafferUI.PlugValueWidget.__init__( self, self.__label, plug, **kw )
	
		toolTip = "<h3>" + plug.relativeName( plug.node() ) + "</h3>"
		description = GafferUI.Metadata.plugDescription( plug )
		if description :
			toolTip += "\n\n" + description
			
		self.__label.setToolTip( toolTip )
				
		self._addPopupMenu( self.__label )

	def label( self ) :
	
		return self.__label

	def setPlug( self, plug ) :
	
		GafferUI.PlugValueWidget.setPlug( self, plug )
	
		self.__label.setGraphComponent( plug )

	def _updateFromPlug( self ) :
	
		self.__label.setEnabled( self._editable() )

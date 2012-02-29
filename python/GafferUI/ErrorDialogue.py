##########################################################################
#  
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

import sys
import traceback

import IECore

import Gaffer
import GafferUI

class ErrorDialogue( GafferUI.Dialogue ) :

	def __init__( self, title, message, details=None, **kw ) :

		GafferUI.Dialogue.__init__( self, title, sizeMode=GafferUI.Window.SizeMode.Manual, **kw )
		
		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 8 )
		messageWidget = GafferUI.Label( IECore.StringUtil.wrap( message, 60 ) )
		messageFrame = GafferUI.Frame( child = messageWidget, borderWidth=8 )
		
		column.append( messageFrame )
		
		if details is not None :
		
			detailsWidget = GafferUI.MultiLineTextWidget(
				text = details,
				editable = False,
			)
			
			detailsFrame = GafferUI.Frame( child = detailsWidget, borderWidth=8 )
			
			column.append(
				GafferUI.Collapsible( label = "Details", collapsed = True, child = detailsFrame )						
			)
					
		self._setWidget( column )
								
		self.__closeButton = self._addButton( "Close" )
	
	## Displays the last raised exception in a modal dialogue.	
	@staticmethod
	def displayException( title="Error", messagePrefix=None, withDetails=True, parentWindow=None ) :
	
		message = str( sys.exc_info()[1] )
		if messagePrefix :
			message = messagePrefix + message
			
		if withDetails :
			details = "".join( traceback.format_exc() )
		else :
			details = False
			
		dialogue = ErrorDialogue(
			title = title,
			message = message,
			details = details,
		)
					
		dialogue.waitForButton( parentWindow=parentWindow )

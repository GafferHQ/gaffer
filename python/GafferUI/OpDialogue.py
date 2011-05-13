##########################################################################
#  
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

import IECore

import Gaffer
import GafferUI

## A dialogue which allows a user to edit the parameters of an
# IECore.Op instance and then execute it.
class OpDialogue( GafferUI.Dialogue ) :

	def __init__( self, opInstance, title=None ) :

		if title is None :
			title = IECore.CamelCase.toSpaced( opInstance.typeName() )

		GafferUI.Dialogue.__init__( self, title )
		
		self.__node = Gaffer.ParameterisedHolderNode()
		self.__node.setParameterised( opInstance )

		self._setWidget( GafferUI.NodeUI.create( self.__node ) )
		
		self.__cancelButton = self._addButton( "Cancel" )
		self.__executeButton = self._addButton( "Execute" )
	
	## Causes the dialogue to enter a modal state, returning the result
	# of executing the Op, or None if the user cancelled the operation.
	def waitForResult( self ) :
	
		button = self.waitForButton()
		
		if button is self.__executeButton :
		
			## \todo Deal with exceptions by reporting them and
			# returning to the wait state.
		
			self.__node.setParameterisedValues()
			return self.__node.getParameterised()[0]()

		return None

##########################################################################
#  
#  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

import Gaffer
import GafferUI

class PathChooserDialogue( GafferUI.Dialogue ) :

	def __init__( self, path, title="Select path", cancelLabel="Cancel", confirmLabel="OK" ) :
	
		GafferUI.Dialogue.__init__( self, title )
		
		self.__path = path
		
		self.__pathChooserWidget = GafferUI.PathChooserWidget( path )
		self._setWidget( self.__pathChooserWidget )
		self.__pathChooserSelectedConnection = self.__pathChooserWidget.pathSelectedSignal().connect( Gaffer.WeakMethod( self.__pathChooserSelected ) )

		self.__cancelButton = self._addButton( cancelLabel )
		self.__cancelButtonConnection = self.__cancelButton.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ) )
		self.__confirmButton = self._addButton( confirmLabel )
		self.__confirmButtonConnection = self.__confirmButton.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ) )
		
		self.__pathSelectedSignal = Gaffer.ObjectSignal()
	
	## A signal called when a path has been selected. Slots for this signal
	# should accept a single argument which will be the PathChooserDialogue instance.	
	def pathSelectedSignal( self ) :
	
		return self.__pathSelectedSignal
	
	## Causes the dialogue to enter a modal state, returning the path once it has been
	# selected by the user. Returns None if the dialogue is cancelled.
	def waitForPath( self ) :
	
		self.__pathChooserWidget.pathWidget().grabFocus()
	
		button = self.waitForButton()
		
		if button is self.__confirmButton :
			return self.__path.copy()
			
		return None
		
	def __buttonClicked( self, button ) :
	
		if button is self.__confirmButton :
			self.pathSelectedSignal()( self )
	
	def __pathChooserSelected( self, pathChooser ) :
		
		assert( pathChooser is self.__pathChooserWidget )
		self.__confirmButton.clickedSignal()( self.__confirmButton )	
		
	

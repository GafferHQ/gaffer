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

class EnumPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, labelsAndValues, **kw ) :
	
		self.__selectionMenu = GafferUI.MultiSelectionMenu( allowMultipleSelection = False, allowEmptySelection = False )
		GafferUI.PlugValueWidget.__init__( self, self.__selectionMenu, plug, **kw )
	
		self.__labelsAndValues = labelsAndValues
		for label, value in self.__labelsAndValues :
			self.__selectionMenu.append( label )
	
		self.__selectionChangedConnection = self.__selectionMenu.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__selectionChanged ) )

		self._addPopupMenu( self.__selectionMenu )
		
		self._updateFromPlug()
	
	def selectionMenu( self ) :
	
		return self.__selectionMenu
	
	def _updateFromPlug( self ) :
	
		self.__selectionMenu.setEnabled( self._editable() )
		
		if self.getPlug() is not None :
			with self.getContext() :
				plugValue = self.getPlug().getValue()
				for labelAndValue in self.__labelsAndValues :
					if labelAndValue[1] == plugValue :
						with Gaffer.BlockedConnection( self.__selectionChangedConnection ) :
							self.__selectionMenu.setSelection( labelAndValue[0] )
	
	def __selectionChanged( self, selectionMenu ) :
	
		with Gaffer.UndoContext( self.getPlug().ancestor( Gaffer.ScriptNode.staticTypeId() ) ) :
			name = selectionMenu.getSelection()[0]
			self.getPlug().setValue( self.__labelsAndValues[ selectionMenu.index(name) ][1] )
		

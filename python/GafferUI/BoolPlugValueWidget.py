##########################################################################
#  
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2012-2013, John Haddon. All rights reserved.
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

import Gaffer
import GafferUI

QtGui = GafferUI._qtImport( "QtGui" )

class BoolPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :
	
		self.__checkBox = GafferUI.CheckBox()
		
		GafferUI.PlugValueWidget.__init__( self, self.__checkBox, plug, **kw )

		self._addPopupMenu( self.__checkBox )

		self.__stateChangedConnection = self.__checkBox.stateChangedSignal().connect( Gaffer.WeakMethod( self.__stateChanged ) )
						
		self._updateFromPlug()

	def setHighlighted( self, highlighted ) :
	
		GafferUI.PlugValueWidget.setHighlighted( self, highlighted )
		self.__checkBox.setHighlighted( highlighted )
		
	def _updateFromPlug( self ) :
		
		if self.getPlug() is not None :
			with self.getContext() :
				with Gaffer.BlockedConnection( self.__stateChangedConnection ) :
					self.__checkBox.setState( self.getPlug().getValue() )
		
		self.__checkBox.setEnabled( self._editable() )
		
	def __stateChanged( self, widget ) :
		
		self.__setPlugValue()
			
		return False
	
	def __setPlugValue( self ) :
			
		with Gaffer.UndoContext( self.getPlug().ancestor( Gaffer.ScriptNode.staticTypeId() ) ) :
						
			self.getPlug().setValue( self.__checkBox.getState() )
	
GafferUI.PlugValueWidget.registerType( Gaffer.BoolPlug.staticTypeId(), BoolPlugValueWidget )

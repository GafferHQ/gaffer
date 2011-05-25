##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

from __future__ import with_statement

import Gaffer
import GafferUI

QtGui = GafferUI._qtImport( "QtGui" )

## \todo Maths expressions to modify the existing value
## \todo Enter names of other plugs to create a connection
## \todo Color change for connected plugs and output plugs
## \todo Reject drag and drop of anything that's not a number
class NumericPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug ) :
	
		GafferUI.PlugValueWidget.__init__( self, QtGui.QWidget(), plug )

		self._qtWidget().setLayout( QtGui.QGridLayout() )
		self.__numericWidget = GafferUI.NumericWidget( plug.getValue() )		
		self._qtWidget().layout().setSpacing( 0 )
		self._qtWidget().layout().setContentsMargins( 0, 0, 0, 0 )
		self._qtWidget().layout().addWidget( self.__numericWidget._qtWidget(), 0, 0 )
 
		self.__keyPressConnection = self.__numericWidget.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ) )
		self.__editingFinishedConnection = self.__numericWidget.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__textChanged ) )
						
		self.updateFromPlug()
		
	def updateFromPlug( self ) :

		if not hasattr( self, "_NumericPlugValueWidget__numericWidget" ) :
			# we're still constructing
			return
		
		if self.getPlug() is not None :
			self.__numericWidget.setValue( self.getPlug().getValue() )
					
		self.__numericWidget.setEditable( self._editable() )
	
	def __keyPress( self, widget, event ) :
	
		assert( widget is self.__numericWidget )
	
		if not self.__numericWidget.getEditable() :
			return False
				
		# escape abandons everything
		if event.key=="Escape" :
			self.updateFromPlug()
			return True
			
		return False
		
	def __textChanged( self, widget ) :
		
		if self._editable() :
			self.__setPlugValue()
			
		return False
	
	def __setPlugValue( self ) :
			
		with Gaffer.UndoContext( self.getPlug().ancestor( Gaffer.ScriptNode.staticTypeId() ) ) :
						
			try :	
				self.getPlug().setValue( self.__numericWidget.getValue() )
			except :
				self.updateFromPlug()	
	
GafferUI.PlugValueWidget.registerType( Gaffer.FloatPlug.staticTypeId(), NumericPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.IntPlug.staticTypeId(), NumericPlugValueWidget )

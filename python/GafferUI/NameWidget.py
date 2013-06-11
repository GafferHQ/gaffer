##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

from __future__ import with_statement

import Gaffer
import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )
QtGui = GafferUI._qtImport( "QtGui" )

class NameWidget( GafferUI.TextWidget ) :

	def __init__( self, graphComponent, **kw ) :
	
		GafferUI.TextWidget.__init__( self, **kw )

		self._qtWidget().setValidator( QtGui.QRegExpValidator( QtCore.QRegExp( "[A-Za-z_]+[A-Za-z_0-9]*" ), self._qtWidget() ) )

		self.setGraphComponent( graphComponent )

		self.__editingFinishedConnection = self.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__setName ) )

	def setGraphComponent( self, graphComponent ) :
	
		self.__graphComponent = graphComponent	
		self.__nameChangedConnection = self.__graphComponent.nameChangedSignal().connect( Gaffer.WeakMethod( self.__setText ) )
		
		self.__setText()
		
	def getGraphComponent( self ) :
	
		return self.__graphComponent
	
	def __setName( self, *unwantedArgs ) :
		
		with Gaffer.UndoContext( self.__graphComponent.ancestor( Gaffer.ScriptNode().staticTypeId() ) ) :
			self.setText( self.__graphComponent.setName( self.getText() ) )

	def __setText( self, *unwantedArgs ) :
	
		self.setText( self.__graphComponent.getName() )

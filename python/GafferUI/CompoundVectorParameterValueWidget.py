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

class CompoundVectorParameterValueWidget( GafferUI.CompoundParameterValueWidget ) :

	def __init__( self, parameterHandler, collapsible=True ) :
		
		self.__vectorDataWidget = None
			
		GafferUI.CompoundParameterValueWidget.__init__( self, parameterHandler, collapsible )
				
		self.__plugSetConnection = parameterHandler.plug().node().plugSetSignal().connect( Gaffer.WeakMethod( self.__plugChanged ) )
			
	def _buildChildParameterUIs( self, column ) :
	
		header = [ IECore.CamelCase.toSpaced( x ) for x in self.parameterHandler().parameter().keys() ]
	
		self.__vectorDataWidget = GafferUI.VectorDataWidget( header = header )
		self.__dataChangedConnection = self.__vectorDataWidget.dataChangedSignal().connect( Gaffer.WeakMethod( self.__dataChanged ) )

		column.append( self.__vectorDataWidget )

		self.__updateFromPlug()
	
	def __updateFromPlug( self ) :
	
		if self.__vectorDataWidget is None :
			return
	
		data = []
		for plug in self.parameterHandler().plug().children() :
			data.append( plug.getValue() )
			
		self.__vectorDataWidget.setData( data )
		
	def __plugChanged( self, plug ) :
	
		if plug.parent().isSame( self.parameterHandler().plug() ) :
			self.__updateFromPlug()
			
	def __dataChanged( self, vectorDataWidget ) :
	
		data = vectorDataWidget.getData()
		with Gaffer.BlockedConnection( self.__plugSetConnection ) :
			for d, p in zip( data, self.parameterHandler().plug().children() ) :
				p.setValue( d )
				
GafferUI.ParameterValueWidget.registerType( IECore.CompoundVectorParameter.staticTypeId(), CompoundVectorParameterValueWidget )

##########################################################################
#  
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

import IECore

import Gaffer
import GafferUI

class CompoundVectorParameterValueWidget( GafferUI.CompoundParameterValueWidget ) :

	def __init__( self, parameterHandler, collapsible=None, **kw ) :
					
		GafferUI.CompoundParameterValueWidget.__init__( self, parameterHandler, collapsible, _plugValueWidgetClass=_PlugValueWidget, **kw )

class _PlugValueWidget( GafferUI.CompoundParameterValueWidget._PlugValueWidget ) :

	def __init__( self, parameterHandler, collapsed ) :

		GafferUI.CompoundParameterValueWidget._PlugValueWidget.__init__( self, parameterHandler, collapsed )

		self.__vectorDataWidget = None

	def _headerWidget( self ) :
	
		if self.__vectorDataWidget is not None :
			return self.__vectorDataWidget
			
		header = [ IECore.CamelCase.toSpaced( x ) for x in self._parameter().keys() ]
		columnToolTips = [ self._parameterToolTip( self._parameterHandler().childParameterHandler( x ) ) for x in self._parameter().values() ]
			
		self.__vectorDataWidget = GafferUI.VectorDataWidget( header = header, columnToolTips = columnToolTips )

		self.__dataChangedConnection = self.__vectorDataWidget.dataChangedSignal().connect( Gaffer.WeakMethod( self.__dataChanged ) )

		self._updateFromPlug()
		
		return self.__vectorDataWidget
				
	def _childPlugs( self ) :

		# because we represent everything in the header we don't
		# need any plug widgets made by the base class.
		return []	
							
	def _updateFromPlug( self ) :
				
		GafferUI.CompoundParameterValueWidget._PlugValueWidget._updateFromPlug( self )
		
		if self.__vectorDataWidget is None:
			return
		
		data = []
		for plug in self._parameterHandler().plug().children() :
			plugData = plug.getValue()
			if len( data ) and len( plugData ) != len( data[0] ) :
				# in __dataChanged we have to update the child plug values
				# one at a time. when adding or removing rows, this means that the
				# columns will have differing lengths until the last plug
				# has been set. in this case we shortcut ourselves, and wait
				# for the final plug to be set before updating the VectorDataWidget.
				return
			data.append( plugData )
		
		self.__vectorDataWidget.setData( data )
		self.__vectorDataWidget.setEditable( self._editable() )
					
	def __dataChanged( self, vectorDataWidget ) :
	
		data = vectorDataWidget.getData()
		
		with Gaffer.UndoContext( self.getPlug().ancestor( Gaffer.ScriptNode.staticTypeId() ) ) :
			for d, p in zip( data, self._parameterHandler().plug().children() ) :
				p.setValue( d )
				
GafferUI.ParameterValueWidget.registerType( IECore.CompoundVectorParameter.staticTypeId(), CompoundVectorParameterValueWidget )

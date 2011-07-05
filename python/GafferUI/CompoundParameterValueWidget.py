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

class CompoundParameterValueWidget( GafferUI.ParameterValueWidget ) :

	_columnSpacing = 4
	_labelWidth = 110

	def __init__( self, parameterHandler, collapsible=True ) :
	
		self.__column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = self._columnSpacing )
		
		if collapsible :
			collapsibleLabel = IECore.CamelCase.toSpaced( parameterHandler.plug().getName() )
			topLevelWidget = GafferUI.Collapsible( label = collapsibleLabel, collapsed = True )
			topLevelWidget.setChild( self.__column )
		else :
			topLevelWidget = self.__column
			
		GafferUI.ParameterValueWidget.__init__( self, topLevelWidget, parameterHandler )
		
		if collapsible :
			self.__collapsibleStateChangedConnection = topLevelWidget.stateChangedSignal().connect( Gaffer.WeakMethod( self.__buildChildUIs ) )
		else :
			self.__buildChildUIs()

	def __buildChildUIs( self, *unusedArgs ) :
	
		if len( self.__column ) :
			return
			
		for childPlug in self.plug().children() :
		
			childParameter = self.parameter()[childPlug.getName()]
			valueWidget = GafferUI.ParameterValueWidget.create( self.parameterHandler().childParameterHandler( childParameter ) )
			if not valueWidget :
				continue
				
			if isinstance( valueWidget, CompoundParameterValueWidget ) :
			
				self.__column.append( valueWidget )
				
			else :
			
				row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 8 )
				
				label = GafferUI.Label(
					IECore.CamelCase.toSpaced( childPlug.getName() ),
					horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right
				)
				label.setToolTip( IECore.StringUtil.wrap(
						childPlug.relativeName( childPlug.node() ) + "\n\n" +
						childParameter.description,
						60
					)
				)
				
				## \todo Decide how we allow this sort of tweak using the public
				# interface. Perhaps we should have a SizeableContainer or something?
				label._qtWidget().setMinimumWidth( self._labelWidth )
				label._qtWidget().setMaximumWidth( self._labelWidth )
		
				row.append( label )
				row.append( valueWidget )
				
				self.__column.append( row )

GafferUI.ParameterValueWidget.registerType( IECore.CompoundParameter.staticTypeId(), CompoundParameterValueWidget )

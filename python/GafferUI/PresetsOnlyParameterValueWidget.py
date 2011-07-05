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

from __future__ import with_statement

import IECore

import Gaffer
import GafferUI

class PresetsOnlyParameterValueWidget( GafferUI.ParameterValueWidget ) :

	def __init__( self, parameterHandler ) :
	
		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
		
		GafferUI.ParameterValueWidget.__init__( self, self.__row, parameterHandler )
		
		self.__row.append( GafferUI.Image( "collapsibleArrowDownHover.png" ) )
		self.__label = GafferUI.Label( "" )
		self.__row.append( self.__label )

		self.__buttonPressConnection = self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )
		
		self.__plugSetConnection = self.plug().node().plugSetSignal().connect( Gaffer.WeakMethod( self.__plugSet ) )
		
		self.__updateFromPlug()
	
	def __buttonPress( self, widget, event ) :
	
		menuDefinition = IECore.MenuDefinition()
		for name in self.parameter().presetNames() :
			menuDefinition.append( "/" + name, { "command" : IECore.curry( Gaffer.WeakMethod( self.__setValue ), name ) } )
			
		menu = GafferUI.Menu( menuDefinition )
		menu.popup()
	
	def __setValue( self, name ) :
	
		self.parameter().setValue( name )
		with Gaffer.UndoContext( self.plug().ancestor( Gaffer.ScriptNode.staticTypeId() ) ) :
			self.parameterHandler().setPlugValue()
	
	def __plugSet( self, plug ) :
	
		if plug.isSame( self.plug() ) :
			self.__updateFromPlug()
		
	def __updateFromPlug( self ) :
	
		self.parameterHandler().setParameterValue()
		
		text = self.parameter().getCurrentPresetName()
		
		self.__label.setText( self.parameter().getCurrentPresetName() )

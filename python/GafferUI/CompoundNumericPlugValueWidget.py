##########################################################################
#  
#  Copyright (c) 2011-2013, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

class CompoundNumericPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :
	
		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing=4 )
		
		GafferUI.PlugValueWidget.__init__( self, self.__row, plug, **kw )

		componentPlugs = plug.children()
		for p in componentPlugs :
			w = GafferUI.NumericPlugValueWidget( p )
			self.__row.append( w )
	
	def setHighlighted( self, highlighted ) :
	
		GafferUI.PlugValueWidget.setHighlighted( self, highlighted )
		
		for i in range( 0, len( self.getPlug() ) ) :
			self.__row[i].setHighlighted( highlighted )

	def setReadOnly( self, readOnly ) :
	
		if readOnly == self.getReadOnly() :
			return
		
		GafferUI.PlugValueWidget.setReadOnly( self, readOnly )
		
		for w in self.__row :
			if isinstance( w, GafferUI.PlugValueWidget ) :
				w.setReadOnly( readOnly )
				
	def _updateFromPlug( self ) :

		pass
	
	## Returns the ListContainer used as the main layout for this Widget.
	# Derived classes may use it to add to the layout.	
	def _row( self ) :
	
		return self.__row	
	
	# Reimplemented to perform casting between vector and color types.	
	def _dropValue( self, dragDropEvent ) :
	
		result = GafferUI.PlugValueWidget._dropValue( self, dragDropEvent )
		if result is not None :
			return result
	
		if isinstance( dragDropEvent.data, IECore.Data ) and hasattr( dragDropEvent.data, "value" ) :
			value = dragDropEvent.data.value
			if hasattr( value, "dimensions" ) and isinstance( value.dimensions(), int ) :
				with self.getContext() :
					result = self.getPlug().getValue()
				componentType = type( result[0] )
				for i in range( 0, min( result.dimensions(), value.dimensions() ) ) :
					result[i] = componentType( value[i] )
				return result
		
		return None
			
GafferUI.PlugValueWidget.registerType( Gaffer.V2fPlug.staticTypeId(), CompoundNumericPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.V3fPlug.staticTypeId(), CompoundNumericPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.V2iPlug.staticTypeId(), CompoundNumericPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.V3iPlug.staticTypeId(), CompoundNumericPlugValueWidget )


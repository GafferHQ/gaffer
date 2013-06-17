##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

## A simple PlugValueWidget which just displays the name of the plug,
# with the popup action menu for the plug.
class LabelPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, horizontalAlignment=GafferUI.Label.HorizontalAlignment.Left, verticalAlignment=GafferUI.Label.VerticalAlignment.Center, **kw ) :
		
		self.__label = GafferUI.NameLabel(
			plug,
			horizontalAlignment = horizontalAlignment,
			verticalAlignment = verticalAlignment,
		)
		
		GafferUI.PlugValueWidget.__init__( self, self.__label, plug, **kw )
			
		# connecting at group 0 so we're called before the slot
		# connected by the NameLabel class.
		self.__dragBeginConnection = self.__label.dragBeginSignal().connect( 0, Gaffer.WeakMethod( self.__dragBegin ) )
		
		self._addPopupMenu( self.__label )
		
		self.setPlug( plug )
		
	def label( self ) :
	
		return self.__label

	def setPlug( self, plug ) :
	
		GafferUI.PlugValueWidget.setPlug( self, plug )
	
		self.__label.setGraphComponent( plug )
		
		label = GafferUI.Metadata.plugValue( plug, "label" )
		if label is not None :
			self.__label.setText( label )

	def setHighlighted( self, highlighted ) :
	
		GafferUI.PlugValueWidget.setHighlighted( self, highlighted )
		
		self.__label.setHighlighted( highlighted )
		
	def getToolTip( self ) :
	
		result = GafferUI.PlugValueWidget.getToolTip( self )
		
		result += "<ul>"
		result += "<li>Left drag to connect</li>"
		if hasattr( self.getPlug(), "getValue" ) :
			result += "<li>Shift-left or middle drag to transfer value</li>"
		result += "<ul>"

		return result

	def _updateFromPlug( self ) :
	
		self.__label.setEnabled( not self.getPlug().getFlags( Gaffer.Plug.Flags.ReadOnly ) )

	def __dragBegin( self, widget, event ) :
		
		# initiate a drag containing the value of the plug,
		# but only if it's a shift-left drag or a middle drag.
		# otherwise we allow the NameLabel class to initiate a
		# drag containing the plug itself.
		
		if not hasattr( self.getPlug(), "getValue" ) :
			return None
		
		shiftLeft = event.Buttons.Left and ( event.modifiers & event.Modifiers.Shift )
		middle = event.buttons == event.Buttons.Middle
		if not ( shiftLeft or middle ) :
			return None
			
		with self.getContext() :
			return self.getPlug().getValue()
		
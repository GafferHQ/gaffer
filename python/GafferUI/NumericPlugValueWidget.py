##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

from __future__ import with_statement

import Gaffer
import GafferUI

## \todo Maths expressions to modify the existing value
## \todo Enter names of other plugs to create a connection
## \todo Color change for connected plugs and output plugs
## \todo Reject drag and drop of anything that's not a number
class NumericPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :
	
		self.__numericWidget = GafferUI.NumericWidget( 0 )
			
		GafferUI.PlugValueWidget.__init__( self, self.__numericWidget, plug, **kw )

		self._addPopupMenu( self.__numericWidget )

		# we use these to decide which actions to merge into a single undo
		self.__lastChangedReason = None
		self.__mergeGroupId = 0

		self.__keyPressConnection = self.__numericWidget.keyPressSignal().connect( Gaffer.WeakMethod( self._keyPress ) )
		self.__valueChangedConnection = self.__numericWidget.valueChangedSignal().connect( Gaffer.WeakMethod( self.__valueChanged ) )
						
		self._updateFromPlug()
		self.__updateWidth()
	
	def setPlug( self, plug ) :
	
		GafferUI.PlugValueWidget.setPlug( self, plug )
		
		self.__updateWidth()
		
	def numericWidget( self ) :
	
		return self.__numericWidget
	
	def setHighlighted( self, highlighted ) :
	
		GafferUI.PlugValueWidget.setHighlighted( self, highlighted )
		self.numericWidget().setHighlighted( highlighted )
	
	def getToolTip( self ) :
	
		result = GafferUI.PlugValueWidget.getToolTip( self )
		
		if self.getPlug() is not None :
			result += "<ul>"
			result += "<li>Cursor up/down to increment/decrement</li>"
			result += "<ul>"

		return result

	def _updateFromPlug( self ) :

		plug = self.getPlug()
		if plug is not None :
			
			with self.getContext() :
				with Gaffer.BlockedConnection( self.__valueChangedConnection ) :
					self.__numericWidget.setValue( plug.getValue() )
					
		self.__numericWidget.setEditable( self._editable() )
	
	def _keyPress( self, widget, event ) :
	
		assert( widget is self.__numericWidget )
	
		if not self.__numericWidget.getEditable() :
			return False
				
		# escape abandons everything
		if event.key=="Escape" :
			self._updateFromPlug()
			return True
			
		return False
		
	def __valueChanged( self, widget, reason ) :
							
		if self._editable() :
			
			if not widget.changesShouldBeMerged( self.__lastChangedReason, reason ) :
				self.__mergeGroupId += 1
			self.__lastChangedReason = reason
	
			self.__setPlugValue( mergeGroup = "NumericPlugValueWidget%d%d" % ( id( self, ), self.__mergeGroupId ) )
					
		return False
	
	def __setPlugValue( self, mergeGroup="" ) :
				
		with Gaffer.UndoContext( self.getPlug().ancestor( Gaffer.ScriptNode.staticTypeId() ), mergeGroup=mergeGroup ) :

			with Gaffer.BlockedConnection( self._plugConnections() ) :
				try :
					self.getPlug().setValue( self.__numericWidget.getValue() )
				except :
					pass
			
			# now any changes that were made in the numeric widget have been transferred
			# into the global undo queue, we remove the text editing changes from the
			# widget's private text editing undo queue. it will then ignore undo shortcuts,
			# allowing them to fall through to the global undo shortcut.
			self.__numericWidget.clearUndo()

			# we always need to update the ui from the plug after trying to set it,
			# because the plug might clamp the value to something else. furthermore
			# it might not even emit plugSetSignal if it happens to clamp to the same
			# value as it had before. we block calls to _updateFromPlug() while setting
			# the value to avoid having to do the work twice if plugSetSignal is emitted.
			self._updateFromPlug()
	
	def __updateWidth( self ) :
	
		charWidth = None
		if isinstance( self.getPlug(), Gaffer.IntPlug ) and self.getPlug().hasMaxValue() :
			charWidth = len( str( self.getPlug().maxValue() ) )
		self.__numericWidget.setFixedCharacterWidth( charWidth )
	
GafferUI.PlugValueWidget.registerType( Gaffer.FloatPlug.staticTypeId(), NumericPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.IntPlug.staticTypeId(), NumericPlugValueWidget )

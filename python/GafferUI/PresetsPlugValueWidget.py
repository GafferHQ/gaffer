##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

class PresetsPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__selectionMenu = GafferUI.MultiSelectionMenu( allowMultipleSelection = False, allowEmptySelection = False )
		GafferUI.PlugValueWidget.__init__( self, self.__selectionMenu, plug, **kw )

		for n in Gaffer.NodeAlgo.presets( plug ) :
			self.__selectionMenu.append( n )
		
		self.__selectionChangedConnection = self.__selectionMenu.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__selectionChanged ) )

		self._addPopupMenu( self.__selectionMenu )

		self._updateFromPlug()

	def _updateFromPlug( self ) :

		self.__selectionMenu.setEnabled( self._editable() )

		if self.getPlug() is not None :
			with self.getContext() :
				with Gaffer.BlockedConnection( self.__selectionChangedConnection ) :
					self.__selectionMenu.setSelection( Gaffer.NodeAlgo.currentPreset( self.getPlug() ) )

	def __selectionChanged( self, selectionMenu ) :

		with Gaffer.UndoContext( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			name = selectionMenu.getSelection()[0]
			Gaffer.NodeAlgo.applyPreset( self.getPlug(), name )

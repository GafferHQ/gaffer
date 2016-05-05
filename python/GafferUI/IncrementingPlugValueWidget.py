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

from __future__ import with_statement

import Gaffer
import GafferUI

class IncrementingPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, label, increment = 1, undoable = True, **kw ) :

		self.__button = GafferUI.Button( label )

		GafferUI.PlugValueWidget.__init__( self, self.__button, plug, **kw )

		self.__increment = increment
		self.__undoable = undoable

		self.__clickedConnection = self.__button.clickedSignal().connect( Gaffer.WeakMethod( self.__clicked ) )

	def _updateFromPlug( self ) :

		pass

	def hasLabel( self ) :

		return True

	def __clicked( self, widget ) :

		assert( widget is self.__button )

		undoState = Gaffer.UndoContext.State.Enabled if self.__undoable else Gaffer.UndoContext.State.Disabled

		with Gaffer.UndoContext( self.getPlug().ancestor( Gaffer.ScriptNode ), undoState ) :
			self.getPlug().setValue( self.getPlug().getValue() + self.__increment )

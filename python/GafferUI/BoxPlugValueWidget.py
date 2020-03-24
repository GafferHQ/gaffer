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

class BoxPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing=4 )

		GafferUI.PlugValueWidget.__init__( self, self.__column, plug, **kw )

		with self.__column :
			GafferUI.PlugValueWidget.create( plug["min"] )
			GafferUI.PlugValueWidget.create( plug["max"] )

	def setPlug( self, plug ) :

		assert( len( plug ) == len( self.getPlug() ) )

		GafferUI.PlugValueWidget.setPlug( self, plug )

		self.__column[0].setPlug( plug["min"] )
		self.__column[1].setPlug( plug["max"] )

	def setHighlighted( self, highlighted ) :

		GafferUI.PlugValueWidget.setHighlighted( self, highlighted )

		for c in self.__column :
			c.setHighlighted( highlighted )

	def setReadOnly( self, readOnly ) :

		if readOnly == self.getReadOnly() :
			return

		GafferUI.PlugValueWidget.setReadOnly( self, readOnly )

		for c in self.__column :
			c.setReadOnly( readOnly )

	def childPlugValueWidget( self, childPlug ) :

		for w in self.__column :
			if childPlug.isSame( w.getPlug() ) :
				return w

		return None

	def _updateFromPlug( self ) :

		pass

GafferUI.PlugValueWidget.registerType( Gaffer.Box2fPlug, BoxPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.Box3fPlug, BoxPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.Box2iPlug, BoxPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.Box3iPlug, BoxPlugValueWidget )

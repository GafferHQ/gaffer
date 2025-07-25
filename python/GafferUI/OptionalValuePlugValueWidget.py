##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

class OptionalValuePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )

		GafferUI.PlugValueWidget.__init__( self, self.__row, plugs, **kw )

		self.__row.append(
			GafferUI.BoolPlugValueWidget(
				{ plug["enabled"] for plug in self.getPlugs() },
				displayMode = GafferUI.BoolWidget.DisplayMode.Switch,
			),
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top
		)

		self.__row.append(
			GafferUI.PlugValueWidget.create( { plug["value"] for plug in self.getPlugs() } ),
			expand = True,
		)

	def setPlugs( self, plugs ) :

		GafferUI.PlugValueWidget.setPlugs( self, plugs )

		self.__row[0].setPlugs( { plug["enabled"] for plug in self.getPlugs() } )
		self.__row[1].setPlugs( { plug["value"] for plug in self.getPlugs() } )

	def childPlugValueWidget( self, childPlug ) :

		for w in self.__row :
			if childPlug in w.getPlugs() :
				return w

		return None

	@staticmethod
	def _valuesForUpdate( plugs, auxiliaryPlugs ) :

		return [ p["enabled"].getValue() for p in plugs ]

	def _updateFromValues( self, values, exception ) :

		self.__row[1].setEnabled( all( values ) )

GafferUI.PlugValueWidget.registerType( Gaffer.OptionalValuePlug, OptionalValuePlugValueWidget )

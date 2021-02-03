##########################################################################
#
#  Copyright (c) 2014 John Haddon. All rights reserved.
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

## A PlugValueWidget which uses a PlugLayout to present all the child
# plugs of the main plug.
#
# Metadata
# --------
#
# - "layoutPlugValueWidget:orientation" : "vertical" or "horizontal"
class LayoutPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		orientation = Gaffer.Metadata.value( plug, "layoutPlugValueWidget:orientation" )
		self.__orientation = {
			"vertical" : GafferUI.ListContainer.Orientation.Vertical,
			"horizontal" : GafferUI.ListContainer.Orientation.Horizontal,
			None : GafferUI.ListContainer.Orientation.Vertical,
		}[orientation]

		self.__layout = GafferUI.PlugLayout( plug, self.__orientation )
		GafferUI.PlugValueWidget.__init__( self, self.__layout, plug, **kw )

	def hasLabel( self ) :

		## \todo `hasLabel` is an abused concept, where loads of widgets
		# claim to have a label when they don't, just as a convenient way of
		# disabling the label that PlugLayout would add itself. Maybe we should
		# ditch it entirely and just use `"label", ""` metadata to disable
		# lables when we want to?

		return self.__orientation == GafferUI.ListContainer.Orientation.Vertical

	def setReadOnly( self, readOnly ) :

		GafferUI.PlugValueWidget.setReadOnly( self, readOnly )
		self.__layout.setReadOnly( readOnly )

	def childPlugValueWidget( self, childPlug ) :

		return self.__layout.plugValueWidget( childPlug )

	def _updateFromPlug( self ) :

		pass

GafferUI.PlugValueWidget.registerType( Gaffer.TransformPlug, LayoutPlugValueWidget )

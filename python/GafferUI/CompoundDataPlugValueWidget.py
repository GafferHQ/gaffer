##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

## Supported plug metadata :
#
# "compoundDataPlugValueWidget:editable"
#
## \deprecated Use LayoutPlugValueWidget and PlugCreationWidget
# directly instead.
class CompoundDataPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__column = GafferUI.ListContainer( spacing = 6 )

		GafferUI.PlugValueWidget.__init__( self, self.__column, plug, **kw )

		with self.__column :

			self.__layout = GafferUI.PlugLayout( plug )
			self.__plugCreationWidget = GafferUI.PlugCreationWidget( plug )

	def hasLabel( self ) :

		return True

	def setPlug( self, plug ) :

		GafferUI.PlugValueWidget.setPlug( self, plug )

		self.__layout = GafferUI.PlugLayout( plug )
		self.__plugCreationWidget = GafferUI.PlugCreationWidget( plug )
		self.__column[:] = [ self.__layout, self.__plugCreationWidget ]

	def childPlugValueWidget( self, childPlug ) :

		return self.__layout.plugValueWidget( childPlug )

	def _updateFromMetadata( self ) :

		editable = Gaffer.Metadata.value( self.getPlug(), "compoundDataPlugValueWidget:editable" )
		editable = editable if editable is not None else True
		self.__plugCreationWidget.setVisible( editable )

	def _updateFromEditable( self ) :

		# Not using `_editable()` as it considers the whole plug to be non-editable if
		# any child has an input connection, but that shouldn't prevent us adding a new
		# child.
		self.__plugCreationWidget.setEnabled(
			self.getPlug().getInput() is None and not Gaffer.MetadataAlgo.readOnly( self.getPlug() )
		)

GafferUI.PlugValueWidget.registerType( Gaffer.CompoundDataPlug, CompoundDataPlugValueWidget )

##########################################################################
# Plug metadata
##########################################################################

Gaffer.Metadata.registerValue( Gaffer.CompoundDataPlug, "*", "deletable", lambda plug : plug.getFlags( Gaffer.Plug.Flags.Dynamic ) )
Gaffer.Metadata.registerValue( Gaffer.CompoundDataPlug, "plugCreationWidget:useGeometricInterpretation", True )

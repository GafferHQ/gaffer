##########################################################################
#
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2012, John Haddon. All rights reserved.
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
# "vectorDataPlugValueWidget:dragPointer"
class VectorDataPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__dataWidget = GafferUI.VectorDataWidget()

		GafferUI.PlugValueWidget.__init__( self, self.__dataWidget, plug, **kw )

		self.__dataWidget.dataChangedSignal().connect( Gaffer.WeakMethod( self.__dataChanged ), scoped = False )

		self._updateFromPlug()

	def vectorDataWidget( self ) :

		return self.__dataWidget

	def setHighlighted( self, highlighted ) :

		GafferUI.PlugValueWidget.setHighlighted( self, highlighted )
		self.vectorDataWidget().setHighlighted( highlighted )

	def _updateFromPlug( self ) :

		plug = self.getPlug()
		if plug is not None :
			with self.getContext() :
				plugValue = plug.getValue()
				if plugValue is None :
					# the VectorDataWidget isn't so keen on not having data to work with,
					# so we'll make an empty data of the right type.
					plugValue = plug.ValueType()
				self.__dataWidget.setData( plugValue )

			dragPointer = Gaffer.Metadata.value( plug, "vectorDataPlugValueWidget:dragPointer" )
			if dragPointer is not None :
				self.__dataWidget.setDragPointer( dragPointer )

		self.__dataWidget.setEditable( self._editable() )

	def __dataChanged( self, widget ) :

		assert( widget is self.__dataWidget )

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			with Gaffer.Signals.BlockedConnection( self._plugConnections() ) :
				self.getPlug().setValue( self.__dataWidget.getData()[0] )

GafferUI.PlugValueWidget.registerType( Gaffer.BoolVectorDataPlug, VectorDataPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.IntVectorDataPlug, VectorDataPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.FloatVectorDataPlug, VectorDataPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.StringVectorDataPlug, VectorDataPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.V3fVectorDataPlug, VectorDataPlugValueWidget )

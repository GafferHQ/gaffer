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

import sys

import IECore

import Gaffer
import GafferUI

# Supported plug metadata :
#
# - "vectorDataPlugValueWidget:dragPointer"
# - "vectorDataPlugValueWidget:index" : Used to order child plugs
# - "vectorDataPlugValueWidget:header" : Provides custom headers for child plugs
# - "vectorDataPlugValueWidget:elementDefaultValue" : Default
#   value for elements in newly added rows.
class VectorDataPlugValueWidget( GafferUI.PlugValueWidget ) :

	# If `plug` has children, then they will be used to form
	# the columns of the VectorDataWidget. If `plug` has no
	# children, it will be shown as a single column.
	def __init__( self, plug, **kw ) :

		self.__dataWidget = _VectorDataWidget()

		GafferUI.PlugValueWidget.__init__( self, self.__dataWidget, plug, **kw )

		dataPlugs = self.__dataPlugs()
		if len( dataPlugs ) > 1 :
			self.__dataWidget.setHeader( [
				Gaffer.Metadata.value( p, "vectorDataPlugValueWidget:header" ) or IECore.CamelCase.toSpaced( p.getName() )
				for p in dataPlugs
			] )
			self.__dataWidget.setToolTips( [ Gaffer.Metadata.value( p, "description" ) or "" for p in dataPlugs ] )

		self.__dataWidget.dataChangedSignal().connect( Gaffer.WeakMethod( self.__dataChanged ) )

	def vectorDataWidget( self ) :

		return self.__dataWidget

	def setHighlighted( self, highlighted ) :

		GafferUI.PlugValueWidget.setHighlighted( self, highlighted )
		self.vectorDataWidget().setHighlighted( highlighted )

	@staticmethod
	def _valuesForUpdate( plugs, auxiliaryPlugs ) :

		assert( len( plugs ) == 1 )
		plug = next( iter( plugs ) )
		if len( plug ) :
			return { c : c.getValue() for c in plug }
		else :
			return { plug : plug.getValue() }

	def _updateFromValues( self, values, exception ) :

		if values :
			self.__dataWidget.setData( [ values[p] for p in self.__dataPlugs() ] )

		self.__dataWidget.setErrored( exception is not None )

	def _updateFromMetadata( self ) :

		dragPointer = None
		if self.getPlug() is not None :
			dragPointer = Gaffer.Metadata.value( self.getPlug(), "vectorDataPlugValueWidget:dragPointer" )
		self.__dataWidget.setDragPointer( dragPointer or "values" )

	def _updateFromEditable( self ) :

		self.__dataWidget.setEditable( self._editable() )

	def __dataPlugs( self ) :

		if not len( self.getPlug() ) :
			return [ self.getPlug() ]

		indicesAndPlugs = [ list( x ) for x in enumerate( self.getPlug() ) ]
		for indexAndPlug in indicesAndPlugs :
			index = Gaffer.Metadata.value( indexAndPlug[1], "vectorDataPlugValueWidget:index" )
			if index is not None :
				indexAndPlug[0] = index if index >= 0 else sys.maxsize + index

		indicesAndPlugs.sort( key = lambda x : x[0] )
		return [ x[1] for x in indicesAndPlugs ]

	def __dataChanged( self, widget ) :

		assert( widget is self.__dataWidget )

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			with self._blockedUpdateFromValues() :
				data = self.__dataWidget.getData()
				for plug, value in zip( self.__dataPlugs(), self.__dataWidget.getData() ) :
					plug.setValue( value )

class _VectorDataWidget( GafferUI.VectorDataWidget ) :

	def __init__( self, **kw ) :

		GafferUI.VectorDataWidget.__init__( self, **kw )

	def _createRows( self ) :

		plugValueWidget = self.ancestor( VectorDataPlugValueWidget )
		plugs = plugValueWidget._VectorDataPlugValueWidget__dataPlugs()
		rows = GafferUI.VectorDataWidget._createRows( self )

		for row, plug in zip( rows, plugs ) :
			value = Gaffer.Metadata.value( plug, "vectorDataPlugValueWidget:elementDefaultValue" )
			if value is not None :
				row[0] = value

		return rows

GafferUI.PlugValueWidget.registerType( Gaffer.BoolVectorDataPlug, VectorDataPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.IntVectorDataPlug, VectorDataPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.Int64VectorDataPlug, VectorDataPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.FloatVectorDataPlug, VectorDataPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.StringVectorDataPlug, VectorDataPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.V2iVectorDataPlug, VectorDataPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.V3iVectorDataPlug, VectorDataPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.V2fVectorDataPlug, VectorDataPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.V3fVectorDataPlug, VectorDataPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.Color3fVectorDataPlug, VectorDataPlugValueWidget )

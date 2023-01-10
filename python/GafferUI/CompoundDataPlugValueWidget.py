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

import functools
import imath

import IECore

import Gaffer
import GafferUI

## Supported plug metadata :
#
# "compoundDataPlugValueWidget:editable"
class CompoundDataPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__column = GafferUI.ListContainer( spacing = 6 )

		GafferUI.PlugValueWidget.__init__( self, self.__column, plug, **kw )

		with self.__column :

			self.__layout = GafferUI.PlugLayout( plug )

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal ) as self.__editRow :

				GafferUI.Spacer( imath.V2i( GafferUI.PlugWidget.labelWidth(), 1 ) )

				GafferUI.MenuButton(
					image = "plus.png",
					hasFrame = False,
					menu = GafferUI.Menu( Gaffer.WeakMethod( self.__addMenuDefinition ) )
				)

				GafferUI.Spacer( imath.V2i( 1 ), imath.V2i( 999999, 1 ), parenting = { "expand" : True } )

		self._updateFromPlug()

	def hasLabel( self ) :

		return True

	def setPlug( self, plug ) :

		GafferUI.PlugValueWidget.setPlug( self, plug )

		self.__layout = GafferUI.PlugLayout( plug )
		self.__column[0] = self.__layout

	def setReadOnly( self, readOnly ) :

		if readOnly == self.getReadOnly() :
			return

		GafferUI.PlugValueWidget.setReadOnly( self, readOnly )

		self.__layout.setReadOnly( readOnly )

	def childPlugValueWidget( self, childPlug ) :

		return self.__layout.plugValueWidget( childPlug )

	def _updateFromPlug( self ) :

		editable = True
		readOnly = False
		if self.getPlug() is not None :
			editable = Gaffer.Metadata.value( self.getPlug(), "compoundDataPlugValueWidget:editable" )
			editable = editable if editable is not None else True
			readOnly = Gaffer.MetadataAlgo.readOnly( self.getPlug() )

		self.__editRow.setVisible( editable )
		self.__editRow.setEnabled( not readOnly )

	def __addMenuDefinition( self ) :

		result = IECore.MenuDefinition()
		result.append( "/Add/Bool", { "command" : functools.partial( Gaffer.WeakMethod( self.__addItem ), "", IECore.BoolData( False ) ) } )
		result.append( "/Add/Float", { "command" : functools.partial( Gaffer.WeakMethod( self.__addItem ), "", IECore.FloatData( 0 ) ) } )
		result.append( "/Add/Int", { "command" : functools.partial( Gaffer.WeakMethod( self.__addItem ), "", IECore.IntData( 0 ) ) } )
		result.append( "/Add/NumericDivider", { "divider" : True } )

		result.append( "/Add/String", { "command" : functools.partial( Gaffer.WeakMethod( self.__addItem ), "", IECore.StringData( "" ) ) } )
		result.append( "/Add/StringDivider", { "divider" : True } )

		result.append( "/Add/V2i/Vector", { "command" : functools.partial( Gaffer.WeakMethod( self.__addItem ), "", IECore.V2iData( imath.V2i( 0 ), IECore.GeometricData.Interpretation.Vector ) ) } )
		result.append( "/Add/V2i/Normal", { "command" : functools.partial( Gaffer.WeakMethod( self.__addItem ), "", IECore.V2iData( imath.V2i( 0 ), IECore.GeometricData.Interpretation.Normal ) ) } )
		result.append( "/Add/V2i/Point", { "command" : functools.partial( Gaffer.WeakMethod( self.__addItem ), "", IECore.V2iData( imath.V2i( 0 ), IECore.GeometricData.Interpretation.Point ) ) } )

		result.append( "/Add/V3i/Vector", { "command" : functools.partial( Gaffer.WeakMethod( self.__addItem ), "", IECore.V3iData( imath.V3i( 0 ), IECore.GeometricData.Interpretation.Vector ) ) } )
		result.append( "/Add/V3i/Normal", { "command" : functools.partial( Gaffer.WeakMethod( self.__addItem ), "", IECore.V3iData( imath.V3i( 0 ), IECore.GeometricData.Interpretation.Normal ) ) } )
		result.append( "/Add/V3i/Point", { "command" : functools.partial( Gaffer.WeakMethod( self.__addItem ), "", IECore.V3iData( imath.V3i( 0 ), IECore.GeometricData.Interpretation.Point ) ) } )

		result.append( "/Add/V2f/Vector", { "command" : functools.partial( Gaffer.WeakMethod( self.__addItem ), "", IECore.V2fData( imath.V2f( 0 ), IECore.GeometricData.Interpretation.Vector ) ) } )
		result.append( "/Add/V2f/Normal", { "command" : functools.partial( Gaffer.WeakMethod( self.__addItem ), "", IECore.V2fData( imath.V2f( 0 ), IECore.GeometricData.Interpretation.Normal ) ) } )
		result.append( "/Add/V2f/Point", { "command" : functools.partial( Gaffer.WeakMethod( self.__addItem ), "", IECore.V2fData( imath.V2f( 0 ), IECore.GeometricData.Interpretation.Point ) ) } )

		result.append( "/Add/V3f/Vector", { "command" : functools.partial( Gaffer.WeakMethod( self.__addItem ), "", IECore.V3fData( imath.V3f( 0 ), IECore.GeometricData.Interpretation.Vector ) ) } )
		result.append( "/Add/V3f/Normal", { "command" : functools.partial( Gaffer.WeakMethod( self.__addItem ), "", IECore.V3fData( imath.V3f( 0 ), IECore.GeometricData.Interpretation.Normal ) ) } )
		result.append( "/Add/V3f/Point", { "command" : functools.partial( Gaffer.WeakMethod( self.__addItem ), "", IECore.V3fData( imath.V3f( 0 ), IECore.GeometricData.Interpretation.Point ) ) } )

		result.append( "/Add/VectorDivider", { "divider" : True } )

		result.append( "/Add/Color3f", { "command" : functools.partial( Gaffer.WeakMethod( self.__addItem ), "", IECore.Color3fData( imath.Color3f( 0 ) ) ) } )
		result.append( "/Add/Color4f", { "command" : functools.partial( Gaffer.WeakMethod( self.__addItem ), "", IECore.Color4fData( imath.Color4f( 0, 0, 0, 1 ) ) ) } )

		result.append( "/Add/BoxDivider", { "divider" : True } )

		result.append( "/Add/Box2i", { "command" : functools.partial( Gaffer.WeakMethod( self.__addItem ), "", IECore.Box2iData( imath.Box2i( imath.V2i( 0 ), imath.V2i( 1 ) ) ) ) } )
		result.append( "/Add/Box2f", { "command" : functools.partial( Gaffer.WeakMethod( self.__addItem ), "", IECore.Box2fData( imath.Box2f( imath.V2f( 0 ), imath.V2f( 1 ) ) ) ) } )
		result.append( "/Add/Box3i", { "command" : functools.partial( Gaffer.WeakMethod( self.__addItem ), "", IECore.Box3iData( imath.Box3i( imath.V3i( 0 ), imath.V3i( 1 ) ) ) ) } )
		result.append( "/Add/Box3f", { "command" : functools.partial( Gaffer.WeakMethod( self.__addItem ), "", IECore.Box3fData( imath.Box3f( imath.V3f( 0 ), imath.V3f( 1 ) ) ) ) } )

		result.append( "/Add/ArrayDivider", { "divider" : True } )

		for label, plugType in [
			( "Float", Gaffer.FloatVectorDataPlug ),
			( "Int", Gaffer.IntVectorDataPlug),
			( "NumericDivider", None ),
			( "String", Gaffer.StringVectorDataPlug ),
		] :
			if plugType is not None :
				result.append( "/Add/Array/" + label, {"command" : IECore.curry( Gaffer.WeakMethod( self.__addItem ), "", plugType.ValueType() ) } )
			else :
				result.append( "/Add/Array/" + label, { "divider" : True } )

		return result

	def __addItem( self, name, value ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().addChild( Gaffer.NameValuePlug( name, value, True, "member1", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

GafferUI.PlugValueWidget.registerType( Gaffer.CompoundDataPlug, CompoundDataPlugValueWidget )

##########################################################################
# Plug metadata
##########################################################################

Gaffer.Metadata.registerValue( Gaffer.CompoundDataPlug, "*", "deletable", lambda plug : plug.getFlags( Gaffer.Plug.Flags.Dynamic ) )

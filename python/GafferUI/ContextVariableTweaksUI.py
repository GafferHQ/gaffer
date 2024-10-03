##########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

import imath
import functools

import IECore

import Gaffer
import GafferUI

Gaffer.Metadata.registerNode(

	Gaffer.ContextVariableTweaks,

	"description",
	"""
	Makes modifications to context variables. Tweaks are applied to context variables coming
	from downstream nodes, resulting in different values given to upstream nodes.
	""",

	plugs = {

		"ignoreMissing" : [

			"description",
			"""
			Ignores tweaks targeting missing context variables. When off, missing context
			variables cause the node to error, unless the tweak mode is `CreateIfMissing`.
			""",
			"nodule:type", "",

		],

		"tweaks" : [

			"description",
			"""
			The tweaks to be made to the context variables. Arbitrary numbers of user defined
			tweaks may be added as children of this plug via the user interface, or
			using the ContextVariableTweaks API via python.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layout:customWidget::footer:widgetType", "GafferUI.ContextVariableTweaksUI._TweaksFooter",
			"layout:customWidget:footer:index", -1,

			"nodule:type", "",

		],

		"tweaks.*" : [

			"tweakPlugValueWidget:propertyType", "context variable",

		]

	}

)

##########################################################################
# _TweaksFooter
##########################################################################

class _TweaksFooter( GafferUI.PlugValueWidget ) :

	def __init__( self, plug ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )

		GafferUI.PlugValueWidget.__init__( self, row, plug )

		with row :

			GafferUI.Spacer( imath.V2i( GafferUI.PlugWidget.labelWidth(), 1 ) )

			self.__button = GafferUI.MenuButton(
				image = "plus.png",
				hasFrame = False,
				menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) )
			)

			GafferUI.Spacer( imath.V2i( 1 ), imath.V2i( 999999, 1 ), parenting = { "expand" : True } )

	def _updateFromEditable( self ) :

		# Not using `_editable()` as it considers the whole plug to be non-editable if
		# any child has an input connection, but that shouldn't prevent us adding a new
		# tweak.
		self.__button.setEnabled( self.getPlug().getInput() is None and not Gaffer.MetadataAlgo.readOnly( self.getPlug() ) )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()

		for item, subMenu in [
			( Gaffer.BoolPlug, "" ),
			( Gaffer.FloatPlug, "" ),
			( Gaffer.IntPlug, "" ),
			( "NumericDivider", "" ),
			( Gaffer.StringPlug, "" ),
			( "StringDivider", "" ),
			( Gaffer.V2iPlug, "" ),
			( Gaffer.V3iPlug, "" ),
			( Gaffer.V2fPlug, "" ),
			( Gaffer.V3fPlug, "" ),
			( "VectorDivider", "" ),
			( Gaffer.Color3fPlug, "" ),
			( Gaffer.Color4fPlug, "" ),
			( "BoxDivider", "" ),
			( IECore.Box2iData( imath.Box2i( imath.V2i( 0 ), imath.V2i( 1 ) ) ), "" ),
			( IECore.Box2fData( imath.Box2f( imath.V2f( 0 ), imath.V2f( 1 ) ) ), "" ),
			( IECore.Box3iData( imath.Box3i( imath.V3i( 0 ), imath.V3i( 1 ) ) ), "" ),
			( IECore.Box3fData( imath.Box3f( imath.V3f( 0 ), imath.V3f( 1 ) ) ), "" ),
			( "ArrayDivider", "" ),
			( IECore.FloatVectorData(), "Array" ),
			( IECore.IntVectorData(), "Array" ),
			( "StringVectorDivider", "Array" ),
			( IECore.StringVectorData(), "Array" ),
		] :
			prefix = "/" + subMenu if subMenu else ""

			if isinstance( item, str ) :
				result.append( prefix + "/" + item, { "divider" : True } )
			else :
				itemName = item.typeName() if isinstance( item, IECore.Data ) else item.__name__
				itemName = itemName.replace( "Plug", "" ).replace( "Data", "" ).replace( "Vector", "" )

				result.append(
					prefix + "/" + itemName,
					{
						"command" : functools.partial( Gaffer.WeakMethod( self.__addTweak ), "", item ),
					}
				)

		return result

	def __addTweak( self, name, plugTypeOrValue ) :

		if isinstance( plugTypeOrValue, IECore.Data ) :
			plug = Gaffer.TweakPlug( name, plugTypeOrValue )
		else :
			plug = Gaffer.TweakPlug( name, plugTypeOrValue() )

		plug.setName( "tweak0" )

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().addChild( plug )

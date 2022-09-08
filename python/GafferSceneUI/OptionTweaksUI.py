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
import six
import functools
import collections

import IECore

import Gaffer
import GafferUI
import GafferScene

Gaffer.Metadata.registerNode(

	GafferScene.OptionTweaks,

	"description",
	"""
	Makes modifications to options.
	""",

	plugs = {

		"ignoreMissing" : [

			"description",
			"""
			Ignores tweaks targeting missing options. When off, missing options
			cause the node to error.
			"""

		],

		"tweaks" : [

			"description",
			"""
			The tweaks to be made to the options. Arbitrary numbers of user defined
			tweaks may be added as children of this plug via the user interface, or
			using the OptionTweaks API via python.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layout:customWidget:footer:widgetType", "GafferSceneUI.OptionTweaksUI._TweaksFooter",
			"layout:customWidget:footer:index", -1,

			"nodule:type", "",

		],

		"tweaks.*" : [

			"tweakPlugValueWidget:allowCreate", True,

		],

	}
)

##########################################################################
# Internal utilities
##########################################################################

def _optionTweaksNode( plugValueWidget ) :

	# The plug may not belong to an OptionTweaks node
	# directly. Instead it may have been promoted
	# elsewhere and be driving a target plug on an
	# OptionTweaks node.

	def walkOutputs( plug ) :

		if isinstance( plug.node(), GafferScene.OptionTweaks ) :
			return plug.node()

		for output in plug.outputs() :
			node = walkOutputs( output )
			if node is not None :
				return node

	return walkOutputs( plugValueWidget.getPlug() )

##########################################################################
# _TweaksFooter
##########################################################################

class _TweaksFooter( GafferUI.PlugValueWidget ) :

	def __init__( self, plug ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )

		GafferUI.PlugValueWidget.__init__( self, row, plug )

		with row :

				GafferUI.Spacer( imath.V2i( GafferUI.PlugWidget.labelWidth(), 1 ) )

				GafferUI.MenuButton(
					image = "plus.png",
					hasFrame = False,
					menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) )
				)

				GafferUI.Spacer( imath.V2i( 1 ), imath.V2i( 999999, 1 ), parenting = { "expand" : True } )

	def _updateFromPlug( self ) :

		self.setEnabled( self._editable() )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()

		result.append(
			"/From Scene",
			{
				"subMenu" : Gaffer.WeakMethod( self.__addFromGlobalsMenuDefinition )
			}
		)

		result.append( "/FromPathsDivider", { "divider" : True } )

		# TODO - would be nice to share these default options with other users of TweakPlug
		for item in [
			Gaffer.BoolPlug,
			Gaffer.FloatPlug,
			Gaffer.IntPlug,
			"NumericDivider",
			Gaffer.StringPlug,
			"StringDivider",
			Gaffer.V2iPlug,
			Gaffer.V3iPlug,
			Gaffer.V2fPlug,
			Gaffer.V3fPlug,
			"VectorDivider",
			Gaffer.Color3fPlug,
			Gaffer.Color4fPlug
		] :

			if isinstance( item, six.string_types ) :
				result.append( "/" + item, { "divider" : True } )
			else :
				result.append(
					"/" + item.__name__.replace( "Plug", "" ),
					{
						"command" : functools.partial( Gaffer.WeakMethod( self.__addTweak ), "", "", item ),
					}
				)

		return result

	def __addFromGlobalsMenuDefinition( self ) :

		result = IECore.MenuDefinition()

		node = _optionTweaksNode( self )
		options = {}

		if node is not None :
			with self.getContext() :
				options = node["out"]["globals"].getValue()

		prefix = "option:"

		options = collections.OrderedDict( ( k, v ) for k, v in options.items() if k.startswith( prefix ) )

		for key, value in [ ( k, v ) for k, v in options.items() if k.replace( ':', '_' ) not in node["tweaks"] ] :
			nameWithoutPrefix = key[ len( prefix ): ]
			result.append(
				"/" + nameWithoutPrefix,
				{
					"command" : functools.partial(
						Gaffer.WeakMethod( self.__addTweak ),
						key.replace( ':', '_' ),
						nameWithoutPrefix,
						value
					)
				}
			)

		if not len( result.items() ) :
			result.append(
				"/No Options Found", { "active" : False }
			)
			return result

		return result

	def __addTweak( self, plugName, optionName, plugTypeOrValue ) :

		if isinstance( plugTypeOrValue, IECore.Data ) :
			plug = Gaffer.TweakPlug( optionName, plugTypeOrValue )
		else :
			plug = Gaffer.TweakPlug( optionName, plugTypeOrValue() )

		if plugName :
			plug.setName( plugName )

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().addChild( plug )
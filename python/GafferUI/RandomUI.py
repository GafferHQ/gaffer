##########################################################################
#
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

import functools

import imath

import Gaffer
import GafferUI

Gaffer.Metadata.registerNode(

	Gaffer.Random,

	"description",
	"""
	Generates repeatable random values from a seed. This can be
	very useful for the procedural generation of variation.
	Numeric or colour values may be generated.

	The random values are generated from a seed and a Context
	Variable - to get useful variation either the seed or the
	value of the Context Variable must be varied too.
	""",

	"nodeGadget:type", "GafferUI::AuxiliaryNodeGadget",
	"auxiliaryNodeGadget:label", "r",
	"nodeGadget:focusGadgetVisible", False,

	plugs = {

		"seed" : [

			"description",
			"""
			Seed for the random number generator. Different seeds
			produce different random numbers. When controlling two
			different properties using the same Context Variable,
			different seeds may be used to ensure that the generated
			values are different.
			""",

		],

		"seedVariable" : [

			"description",
			"""
			The most important plug for achieving interesting variation.
			Should be set to the name of a Context Variable which will
			be different for each evaluation of the node. Good examples
			are "scene:path" to generate a different value per scene
			location, or "frame" to generate a different value per frame.
			""",

			"preset:Time", "frame",
			"preset:Scene Location", "scene:path",

		],

		"floatRange" : [

			"description",
			"""
			The minimum and maximum values that will be generated for the
			outFloat plug.
			""",

		],

		"baseColor" : [

			"description",
			"""
			Used as the basis for the random colours generated for the
			outColor plug. All colours start with this value and then
			have a random HSV variation applied, using the ranges specified
			below.
			""",

		],

		"hue" : [

			"description",
			"""
			The +- range over which the hue of the base colour is varied.
			""",

		],

		"saturation" : [

			"description",
			"""
			The +- range over which the saturation of the base colour is varied.
			""",

		],

		"value" : [

			"description",
			"""
			The +- range over which the value of the base colour is varied.
			""",

		],

		"outFloat" : [

			"description",
			"""
			Random floating point output derived from seed, Context Variable
			and float range plugs.
			""",

			"layout:section", "Settings.Outputs",

		],

		"outColor" : [

			"description",
			"""
			Random colour output derived from seed, Context Variable, base
			colour, hue, saturation and value plugs.
			""",

			"layout:section", "Settings.Outputs",

			"plugValueWidget:type", "GafferUI.RandomUI._RandomColorPlugValueWidget",

		]

	}

)

# PlugValueWidget registrations
##########################################################################

class _RandomColorPlugValueWidget( GafferUI.PlugValueWidget ) :

	__gridSize = imath.V2i( 10, 3 )

	def __init__( self, plug, **kw ) :

		self.__grid = GafferUI.GridContainer( spacing = 4 )

		GafferUI.PlugValueWidget.__init__( self, self.__grid, plug, **kw )

		with self.__grid :
			for x in range( 0, self.__gridSize.x ) :
				for y in range( 0, self.__gridSize.y ) :
					GafferUI.ColorSwatch( parenting = { "index" : ( x, y ) } )

	@staticmethod
	def _valuesForUpdate( plugs, auxiliaryPlugs ) :

		node = next( iter( plugs ) ).source().node()
		seed = node["seed"].getValue()

		result = []
		for x in range( 0, _RandomColorPlugValueWidget.__gridSize.x ) :
			column = []
			for y in range( 0, _RandomColorPlugValueWidget.__gridSize.y ) :
				column.append( node.randomColor( seed ) )
				seed += 1
			result.append( column )

		return result

	def _updateFromValues( self, values, exception ) :

		for x in range( 0, self.__gridSize.x ) :
			for y in range( 0, self.__gridSize.y ) :
				if exception is not None :
					self.__grid[x,y].setColor( imath.Color3f( 1, 0.33, 0.33 ) )
				elif len( values ) :
					self.__grid[x,y].setColor( values[x][y] )
				else :
					# We are called with `values == []` prior to
					# the BackgroundTask for `_valuesForUpdate()`
					# being launched. No point displaying a "busy"
					# state as it is typically so quick as to just
					# be visual noise.
					pass

# PlugValueWidget popup menu
##########################################################################

def __createRandom( plug ) :

	node = plug.node()
	parentNode = node.ancestor( Gaffer.Node )

	with Gaffer.UndoScope( node.scriptNode() ) :

		randomNode = Gaffer.Random()
		parentNode.addChild( randomNode )

		if isinstance( plug, ( Gaffer.FloatPlug, Gaffer.IntPlug ) ) :
			plug.setInput( randomNode["outFloat"] )
		elif isinstance( plug, Gaffer.Color3fPlug ) :
			plug.setInput( randomNode["outColor"] )

	GafferUI.NodeEditor.acquire( randomNode )

def __popupMenu( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug()
	if not isinstance( plug, ( Gaffer.FloatPlug, Gaffer.IntPlug, Gaffer.Color3fPlug ) ) :
		return

	node = plug.node()
	if node is None or node.parent() is None :
		return

	input = plug.getInput()
	if input is None and plugValueWidget._editable() :
		menuDefinition.prepend( "/RandomiseDivider", { "divider" : True } )
		menuDefinition.prepend(
			"/Randomise...",
			{
				"command" : functools.partial( __createRandom, plug ),
				"active" : not Gaffer.MetadataAlgo.readOnly( plug ),
			}
		)

GafferUI.PlugValueWidget.popupMenuSignal().connect( __popupMenu )

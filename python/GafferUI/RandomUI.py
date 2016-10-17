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

import Gaffer
import GafferUI

Gaffer.Metadata.registerNode(

	Gaffer.Random,

	"description",
	"""
	Generates repeatable random values from a seed. This can be
	very useful for the procedural generation of variation.
	Numeric or colour values may be generated.

	The random values are generated from a seed and a context
	variable - to get useful variation either the seed or the
	value of the context variable must be varied too.
	""",

	plugs = {

		"seed" : [

			"description",
			"""
			Seed for the random number generator. Different seeds
			produce different random numbers. When controlling two
			different properties using the same context variable,
			different seeds may be used to ensure that the generated
			values are different.
			""",

		],

		"contextEntry" : [

			"description",
			"""
			The most important plug for achieving interesting variation.
			Should be set to the name of a context variable which will
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
			Random floating point output derived from seed, context variable
			and float range plugs.
			""",

			"plugValueWidget:type", "",

		],

		"outColor" : [

			"description",
			"""
			Random colour output derived from seed, context variable, base
			colour, hue, saturation and value plugs.
			""",

			"plugValueWidget:type", "GafferUI.RandomUI._RandomColorPlugValueWidget",

		]

	}

)

# PlugValueWidget registrations
##########################################################################

class _RandomColorPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__grid = GafferUI.GridContainer( spacing = 4 )

		GafferUI.PlugValueWidget.__init__( self, self.__grid, plug, **kw )

		with self.__grid :
			for x in range( 0, 10 ) :
				for y in range( 0, 3 ) :
					GafferUI.ColorSwatch( parenting = { "index" : ( x, y ) } )

		self._updateFromPlug()

	def _updateFromPlug( self ) :

		node = self.getPlug().source().node()
		seed = node["seed"].getValue()

		gridSize = self.__grid.gridSize()
		for x in range( 0, gridSize.x ) :
			for y in range( 0, gridSize.y ) :
				self.__grid[x,y].setColor( node.randomColor( seed ) )
				seed += 1

# PlugValueWidget popup menu
##########################################################################

def __createRandom( plug ) :

	node = plug.node()
	parentNode = node.ancestor( Gaffer.Node )

	with Gaffer.UndoContext( node.scriptNode() ) :

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
				"active" : not plugValueWidget.getReadOnly() and not Gaffer.readOnly( plug ),
			}
		)

__popupMenuConnection = GafferUI.PlugValueWidget.popupMenuSignal().connect( __popupMenu )

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

import functools
import imath

import IECore

import Gaffer
import GafferUI

Gaffer.Metadata.registerNode(

	Gaffer.RandomChoice,

	"description",
	"""
	Chooses random values from a list of choices, with optional weights
	to specify the relative probability of each choice.

	The randomness is generated from a seed and a context
	variable; to get useful variation either the seed or the
	value of the context variable must be varied too.
	""",

	"nodeGadget:type", "GafferUI::AuxiliaryNodeGadget",
	"auxiliaryNodeGadget:label", "r",
	"nodeGadget:focusGadgetVisible", False,

	"layout:activator:isSetup", lambda node : "out" in node,
	"layout:activator:isNotSetup", lambda node : "out" not in node,

	"layout:customWidget:setupButton:widgetType", "GafferUI.RandomChoiceUI._SetupButton",
	"layout:customWidget:setupButton:section", "Settings",
	"layout:customWidget:setupButton:index", -1,
	"layout:customWidget:setupButton:visibilityActivator", "isNotSetup",

	plugs = {

		"*" : [

			# Prevents creation of unwanted BoxIn nodes when
			# plugs are promoted.
			"nodule:type", "",

		],

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

		"seedVariable" : [

			"description",
			"""
			The most important plug for achieving interesting variation.
			Should be set to the name of a context variable which will
			be different for each evaluation of the node. Good examples
			are `scene:path` to generate a different value per scene
			location, or `frame` to generate a different value per frame.
			""",

			"preset:Time", "frame",
			"preset:Scene Location", "scene:path",

		],

		"choices" : [

			"description",
			"""
			The choices that will be randomly selected between based on the seed.
			""",

			"plugValueWidget:type", "GafferUI.VectorDataPlugValueWidget",

			"layout:visibilityActivator", "isSetup",

		],

		"choices.values" : [

			"description",
			"""
			The list of values for the choices. Use the `choices.weights` plug
			to assign a relative probability to each choice.
			""",

			"vectorDataPlugValueWidget:header", "Value",

		],

		"choices.weights" : [

			"description",
			"""
			The list of weights for the choices. Choices with a higher weight
			have a greater chance of being chosen.
			""",

			"vectorDataPlugValueWidget:header", "Weight",
			"vectorDataPlugValueWidget:index", -1,
			"vectorDataPlugValueWidget:elementDefaultValue", 1.0,

		],

		"out" : [

			"description",
			"""
			Outputs a random choice from the `choices` plug.
			""",

		]

	}

)

# _SetupButton
# ============

class _SetupButton( GafferUI.Widget ) :

	def __init__( self, node ) :

		self.__node = node
		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )

		GafferUI.Widget.__init__( self, self.__row )

		with self.__row :

				GafferUI.Spacer( imath.V2i( GafferUI.PlugWidget.labelWidth(), 1 ) )

				GafferUI.MenuButton(
					menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ), title = "Add Output" ),
					image = "plus.png", hasFrame = False
				)

				GafferUI.Spacer( imath.V2i( 1 ), imath.V2i( 999999, 1 ), parenting = { "expand" : True } )

	def __menuDefinition( self, menu ) :

		result = IECore.MenuDefinition()

		def setup( node, plugType ) :

			with Gaffer.UndoScope( node.scriptNode() ) :
				node.setup( plugType() )

		for plugType in (
			Gaffer.BoolPlug,
			Gaffer.FloatPlug,
			Gaffer.IntPlug,
			None,
			Gaffer.StringPlug,
			None,
			Gaffer.V2iPlug,
			Gaffer.V3fPlug,
			None,
			Gaffer.Color3fPlug
		) :
			if plugType is None :
				result.append( "/Divider{}".format( result.size() ), { "divider" : True } )
			else :
				result.append(
					plugType.__name__.replace( "Plug", "" ),
					{
						"command" : functools.partial( setup, self.__node, plugType ),
						"active" : not Gaffer.MetadataAlgo.readOnly( self.__node ),
					}
				)

		return result

# PlugValueWidget popup menu
# ==========================

def __createRandomChoice( plugs ) :

	parentNode = plugs[0].node().parent()

	with Gaffer.UndoScope( parentNode.scriptNode() ) :

		node = Gaffer.RandomChoice()
		node.setup( plugs[0] )
		parentNode.addChild( node )

		for plug in plugs :
			plug.setInput( node["out"] )

	GafferUI.NodeEditor.acquire( node )

def __popupMenu( menuDefinition, plugValueWidget ) :

	if not plugValueWidget._editable() :
		return

	for plug in plugValueWidget.getPlugs() :
		if not isinstance( plug, Gaffer.ValuePlug ) :
			return
		if plug.getInput() is not None or Gaffer.MetadataAlgo.readOnly( plug ) :
			return
		if not Gaffer.RandomChoice.canSetup( plug ) :
			return
		if plug.node() is None or plug.node().parent() is None :
			return

	# If we can, put ourselves in the same section as the item created by RandomUI.
	# Otherwise make out own section.

	item = { "command" : functools.partial( __createRandomChoice, list( plugValueWidget.getPlugs() ) ) }

	try :
		menuDefinition.insertAfter( "/Randomise (Choice)...", item, "/Randomise..." )
	except KeyError :
		menuDefinition.prepend( "/RandomiseDivider", { "divider" : True } )
		menuDefinition.prepend( "/Randomise...", item )

GafferUI.PlugValueWidget.popupMenuSignal().connect( __popupMenu, scoped = False )

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
import collections

import IECore
import IECoreScene

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

##########################################################################
# Internal utilities
##########################################################################

def __getLabel( plug, parentPlug = None ) :

	prefix = ""
	suffix = ""

	n = plug.node()
	qPlug = n.queryPlug( plug )

	prefix = qPlug["name"].getValue() if qPlug["name"].getValue() != "" else "none"

	if parentPlug is not None :
		oPlug = n.outPlugFromQuery( qPlug )

		currentPlug = plug
		while (
			currentPlug is not None and
			currentPlug != oPlug
		) :

			suffix = "." + currentPlug.getName() + suffix
			currentPlug = currentPlug.parent()

	result = prefix + suffix

	return result


##########################################################################
# Output widget
##########################################################################

class _OutputWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, childPlug, **kw ) :

		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )

		GafferUI.PlugValueWidget.__init__( self, self.__row, childPlug )

		nameWidget = GafferUI.LabelPlugValueWidget(
			self.getPlugs(),
			horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right
		)
		nameWidget.label()._qtWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() )
		self.__row.append(
			nameWidget,
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top
		)

		existsLabelWidget = GafferUI.LabelPlugValueWidget(
			{ plug["exists"] for plug in self.getPlugs() },
			horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right
		)
		existsLabelWidget.label()._qtWidget().setFixedWidth( 40 )
		self.__row.append(
			existsLabelWidget,
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top
		)

		self.__row.append(
			GafferUI.BoolPlugValueWidget( { plug["exists"] for plug in self.getPlugs() } ),
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top
		)

		valueLabelWidget = GafferUI.LabelPlugValueWidget(
			{ plug["value"] for plug in self.getPlugs() },
			horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right
		)
		valueLabelWidget.label()._qtWidget().setFixedWidth( 40 )
		self.__row.append(
			valueLabelWidget,
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top
		)

		self.__row.append(
			GafferUI.PlugValueWidget.create( { plug["value"] for plug in self.getPlugs() } )
		)

	def setPlugs( self, plugs ) :

		GafferUI.PlugValueWidget.setPlugs( self, plugs )

		self.__row[0].setPlugs( plugs )
		self.__row[1].setPlugs( { plug["exists"] for plug in plugs } )
		self.__row[2].setPlugs( { plug["exists"] for plug in plugs } )
		self.__row[3].setPlugs( { plug["value"] for plug in plugs } )
		self.__row[4].setPlugs( { plug["value"] for plug in plugs } )

	def hasLabel( self ) :

		return True

	def childPlugValueWidget( self, childPlug ) :

		for w in self.__row :
			if childPlug in w.getPlugs() :
				return w

		return None

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.OptionQuery,

	"description",
	"""
	Queries global scene options, creating an output for each option.
	""",

	plugs = {

		"scene" : [

			"description",
			"""
			The scene to query the options from.
			""",

		],

		"queries" : [

			"description",
			"""
			The options to be queried - arbitrary numbers of options may be added
			as children of this plug via the user interface, or via python. Each
			child is a `NameValuePlug` whose `name` plug is the option to query,
			and whose `value` plug is the default value to use if the option can
			not be retrieved.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",

			"layout:customWidget:footer:widgetType", "GafferSceneUI.OptionQueryUI._OptionQueryFooter",
			"layout:customWidget:footer:index", -1,

			"nodule:type", "",

		],

		"queries.*" : [

			"description",
			"""
			A pair of option name to query and default value.
			""",

		],

		"queries.*.name" : [

			"description",
			"""
			The name of the option to query.
			""",

		],

		"queries.*.value" : [

			"description",
			"""
			The value to output if the option does not exist.
			""",

		],

		"out" : [

			"description",
			"""
			The parent plug of the query outputs. The order of outputs corresponds
			to the order of children of `queries`.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",

			"layout:section", "Settings.Outputs",

			"nodule:type", "GafferUI::CompoundNodule",
			"noduleLayout:spacing", 0.4,
			"noduleLayout:customGadget:addButton:gadgetType", "",

		],

		"out.*" : [

			"description",
			"""
			The result of the query.
			""",

			"label", functools.partial( __getLabel, parentPlug = ""),

			"plugValueWidget:type", "GafferSceneUI.OptionQueryUI._OutputWidget",

			"nodule:type", "GafferUI::CompoundNodule",

		],

		"out.*.exists" : [

			"description",
			"""
			Outputs true if the option exists, otherwise false.
			""",

			"noduleLayout:label", functools.partial( __getLabel, parentPlug = "exists" ),

		],

		"out.*.value" : [

			"description",
			"""
			Outputs the value of the option, or the default value if the option
			does not exist.
			""",

		],

		"out.*.value..." : [

			"noduleLayout:label", functools.partial( __getLabel, parentPlug = "values" ),

		],

	}
)

##########################################################################
# _OutputQueryFooter
##########################################################################

class _OptionQueryFooter( GafferUI.PlugValueWidget ) :

	def __init__( self, plug ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )

		GafferUI.PlugValueWidget.__init__( self, row, plug )

		with row :

			GafferUI.Spacer( imath.V2i( GafferUI.PlugWidget.labelWidth(), 1 ) )

			self.__menuButton = GafferUI.MenuButton(
				image = "plus.png",
				hasFrame = False,
				menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) )
			)

			GafferUI.Spacer( imath.V2i( 1 ), imath.V2i( 999999, 1 ), parenting = { "expand": True } )

		plug.node().plugSetSignal().connect(
			Gaffer.WeakMethod( self.__updateQueryMetadata )
		)

	def _updateFromEditable( self ) :

		self.__menuButton.setEnabled( self._editable() )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()

		result.append(
			"/From Scene",
			{
				"subMenu" : Gaffer.WeakMethod( self.__addFromGlobalsMenuDefinition )
			}
		)

		result.append( "/FromPathsDivider", { "divider" : True } )

		for label, plugCreator in [
			( "Bool", Gaffer.BoolPlug ),
			( "Float", Gaffer.FloatPlug ),
			( "Int", Gaffer.IntPlug ),
			( "NumericDivider", None ),
			( "String", Gaffer.StringPlug ),
			( "StringDivider", None ),
			( "V2i", Gaffer.V2iPlug ),
			( "V3i", Gaffer.V3iPlug ),
			( "V2f", Gaffer.V2fPlug ),
			( "V3f", Gaffer.V3fPlug ),
			( "VectorDivider", None ),
			( "Color3f", Gaffer.Color3fPlug ),
			( "Color4f", Gaffer.Color4fPlug ),
			( "ObjectDivider", None ),
			( "Object", functools.partial( Gaffer.ObjectPlug, defaultValue = IECore.NullObject.defaultNullObject() ) ),
		] :
			if plugCreator is None :
				result.append( f"/{label}", { "divider": True } )
			else :
				result.append(
					f"/{label}",
					{
						"command" : functools.partial( Gaffer.WeakMethod( self.__addQuery ), "", plugCreator ),
					}
				)

		return result

	def __addFromGlobalsMenuDefinition( self ) :

		result = IECore.MenuDefinition()

		node = self.getPlug().node()
		assert( isinstance( node, GafferScene.OptionQuery ) )

		with self.context() :
			options = node["scene"]["globals"].getValue()
			existingQueries = { query["name"].getValue() for query in node["queries"] }

		prefix = "option:"

		for name, value in [ ( k[len( prefix ):], v ) for k, v in options.items() if k.startswith( prefix ) ] :
			result.append(
				"/{}".format( name ),
				{
					"command" : functools.partial(
						Gaffer.WeakMethod( self.__addQuery ), name, value
					),
					"active" : name not in existingQueries
				}
			)

		if not len( result.items() ) :
			result.append(
				"/No Options Found", { "active" : False }
			)
			return result

		return result

	def __addQuery( self, optionName, plugCreatorOrValue ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :

			node = self.getPlug().node()

			if isinstance( plugCreatorOrValue, IECore.Data ) :
				prototypePlug = Gaffer.PlugAlgo.createPlugFromData(
					"valuePrototype",
					Gaffer.Plug.Direction.In,
					Gaffer.Plug.Flags.Default,
					plugCreatorOrValue
				)
				node.addQuery( prototypePlug, optionName )
			else:
				node.addQuery( plugCreatorOrValue(), optionName )

	def __updateQueryMetadata( self, plug ) :

		node = plug.node()

		if node["queries"].isAncestorOf( plug ) :

			qPlug = plug.ancestor( Gaffer.NameValuePlug )

			if qPlug is not None and qPlug["name"] == plug :

				Gaffer.Metadata.plugValueChangedSignal( node )(
					node.outPlugFromQuery( qPlug ),
					"label",
					Gaffer.Metadata.ValueChangedReason.StaticRegistration
				)

##########################################################################
# Delete Plug
##########################################################################

def __plugPopupMenu( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug().ancestor( Gaffer.NameValuePlug )

	if plug is not None and isinstance( plug.node(), GafferScene.OptionQuery ) :

		if len( menuDefinition.items() ) :
			menuDefinition.append( "/DeleteDivider", { "divider" : True } )

		menuDefinition.append( "/Delete", { "command" : functools.partial( __deletePlug, plug ), "active" : not Gaffer.MetadataAlgo.readOnly( plug ) } )

def __deletePlug( plug ) :

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		plug.node().removeQuery( plug )

GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu )

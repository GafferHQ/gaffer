##########################################################################
#
#  Copyright (c) 2022, Image Engine Design Inc. All rights reserved.
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

##########################################################################
# Internal utilities
##########################################################################

def __getLabel( plug, parentPlug = None, sanitise = False ) :

	prefix = ""
	suffix = ""

	n = plug.node()
	qPlug = n.queryPlugFromOutPlug( plug )

	prefix = qPlug["name"].getValue() if qPlug["name"].getValue() != "" else "none"

	if parentPlug is not None :
		oPlug = n.outPlugFromQueryPlug( qPlug )

		currentPlug = plug
		while (
			currentPlug is not None and
			currentPlug != oPlug
		) :

			suffix = "." + currentPlug.getName() + suffix
			currentPlug = currentPlug.parent()

	result = prefix + suffix
	result = result.replace( ".", "_" ) if sanitise else result

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

	Gaffer.ContextQuery,

	"description",
	"""
	Queries variables from the current context, creating outputs for each variable.
	""",

	"nodeGadget:type", "GafferUI::AuxiliaryNodeGadget",
	"nodeGadget:shape", "oval",
	"uiEditor:nodeGadgetTypes", IECore.StringVectorData( [ "GafferUI::AuxiliaryNodeGadget", "GafferUI::StandardNodeGadget" ] ),
	"auxiliaryNodeGadget:label", "c",
	"nodeGadget:focusGadgetVisible", False,

	plugs = {

		"queries" : [

			"description",
			"""
			The context variables to be queried - arbitrary numbers of context
			variables may be added as children of this plug via the user interface,
			or via python. Each child is a `NameValuePlug` whose `name` plug is
			the context variable to query, and whose `value` plug is the default
			value to use if the variable does not exist in the context with an
			appropriate type.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",

			"layout:customWidget:footer:widgetType", "GafferUI.ContextQueryUI._ContextQueryFooter",
			"layout:customWidget:footer:index", -1,

			"nodule:type", "",

		],

		"queries.*" : [

			"description",
			"""
			A pair of variable name to query and default value.
			""",

		],

		"queries.*.name" : [

			"description",
			"""
			The name of the variable to query.
			""",

		],

		"queries.*.value" : [

			"description",
			"""
			The value to output if the variable does not exist.
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
			"noduleLayout:customGadget:addButton:gadgetType", ""

		],

		"out.*" : [

			"description",
			"""
			The result of the query.
			""",

			"label", functools.partial( __getLabel, parentPlug = ""),

			"plugValueWidget:type", "GafferUI.ContextQueryUI._OutputWidget",

			"nodule:type", "GafferUI::CompoundNodule",

		],

		"out.*.exists" : [

			"description",
			"""
			Outputs true if the variable exists in the context, and is a compatible type.
			""",

			"noduleLayout:label", functools.partial( __getLabel, parentPlug = "exists" ),

		],

		"out.*.value" : [

			"description",
			"""
			Outputs the value of the specified variable, or the default value
			if the variable does not exist ( or is incompatible ).
			""",

		],

		"out.*.value..." : [

			"noduleLayout:label", functools.partial( __getLabel, parentPlug = "values" ),

		],

	}
)

##########################################################################
# _ContextQueryFooter
##########################################################################

class _ContextQueryFooter( GafferUI.PlugValueWidget ) :

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

			GafferUI.Spacer( imath.V2i( 1 ), imath.V2i( 999999, 1 ), parenting = { "expand": True } )

		plug.node().plugSetSignal().connect(
			Gaffer.WeakMethod( self.__updateQueryMetadata ),
			scoped = False
		)

	def _updateFromPlug( self ) :

		self.setEnabled( self._editable() )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()

		for item in [
			Gaffer.BoolPlug(),
			Gaffer.FloatPlug(),
			Gaffer.IntPlug(),
			"NumericDivider",
			Gaffer.StringPlug(),
			"StringDivider",
			Gaffer.V2iPlug(),
			Gaffer.V3iPlug(),
			Gaffer.V2fPlug(),
			Gaffer.V3fPlug(),
			"VectorDivider",
			Gaffer.Color3fPlug(),
			Gaffer.Color4fPlug(),
			"ColorDivider",
			Gaffer.Box2iPlug(),
			Gaffer.Box2fPlug(),
			Gaffer.Box3iPlug(),
			Gaffer.Box3fPlug(),
			"BoxDivider",
			Gaffer.FloatVectorDataPlug( defaultValue = IECore.FloatVectorData() ),
			Gaffer.IntVectorDataPlug( defaultValue = IECore.IntVectorData() ),
			Gaffer.StringVectorDataPlug( defaultValue = IECore.StringVectorData() )
		] :
			if isinstance( item, str ) :
				result.append( "/" + item, { "divider": True } )
			else :
				name = type( item ).__name__.replace( "Plug", "" )
				if name == "StringVectorData":
					result.append( "/Array/NumericDivider", { "divider": True } )
				if "Vector" in name:
					name = "Array/" + name.split( "Vector" )[0]
				result.append(
					"/" + name,
					{
						"command" : functools.partial( Gaffer.WeakMethod( self.__addQuery ), "", item ),
					}
				)

		return result

	def __addQuery( self, name, templatePlug ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :

			node = self.getPlug().node()

			node.addQuery( templatePlug, name )

	def __updateQueryMetadata( self, plug ) :

		node = plug.node()

		if node["queries"].isAncestorOf( plug ) :

			qPlug = plug.ancestor( Gaffer.NameValuePlug )

			if qPlug is not None and qPlug["name"] == plug :

				Gaffer.Metadata.plugValueChangedSignal( node )(
					node.outPlugFromQueryPlug( qPlug ),
					"label",
					Gaffer.Metadata.ValueChangedReason.StaticRegistration
				)

##########################################################################
# Popup menus
##########################################################################

def __deletePlug( plug ) :

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		plug.node().removeQuery( plug )

def __createContextQuery( plug ) :

	node = plug.node()
	parentNode = node.ancestor( Gaffer.Node )

	with Gaffer.UndoScope( node.scriptNode() ) :

		contextQueryNode = Gaffer.ContextQuery()
		parentNode.addChild( contextQueryNode )

		contextQueryNode.addQuery( plug, "" )
		plug.setInput( contextQueryNode["out"][0]["value"] )

	GafferUI.NodeEditor.acquire( contextQueryNode )

def __plugPopupMenu( menuDefinition, plugValueWidget ) :

	queryPlug = plugValueWidget.getPlug().ancestor( Gaffer.NameValuePlug )

	# For Query plugs on a ContextQuery, we allow deleting them
	if queryPlug is not None and isinstance( queryPlug.node(), Gaffer.ContextQuery ) :

		if len( menuDefinition.items() ) :
			menuDefinition.append( "/DeleteDivider", { "divider" : True } )

		menuDefinition.append( "/Delete", { "command" : functools.partial( __deletePlug, queryPlug ), "active" : not Gaffer.MetadataAlgo.readOnly( queryPlug ) } )
		return

	# For ValuePlug in general, we offer the option to drive them with ContextQuery
	plug = plugValueWidget.getPlug()
	if not isinstance( plug, Gaffer.ValuePlug ) :
		return

	node = plug.node()
	if node is None or node.parent() is None :
		return

	input = plug.getInput()
	if input is not None or not plugValueWidget._editable() or Gaffer.MetadataAlgo.readOnly( plug ) :
		return

	menuDefinition.prepend( "/ContextQueryDivider", { "divider" : True } )
	menuDefinition.prepend(
		"/Create Context Query...",
		{
			"command" : functools.partial( __createContextQuery, plug )
		}
	)

GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu, scoped = False )

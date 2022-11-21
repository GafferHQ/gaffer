#########################################################################
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
import six

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

		self.__column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4 )

		GafferUI.PlugValueWidget.__init__( self, self.__column, childPlug )

		self.__column.append( GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) )
		self.__column.append( GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) )

		nameWidget = GafferUI.LabelPlugValueWidget(
			self.getPlugs(),
			horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right
		)
		nameWidget.label()._qtWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() )
		self.__column[0].append(
			nameWidget,
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top
		)

		existsLabelWidget = GafferUI.LabelPlugValueWidget(
			{ plug["exists"] for plug in self.getPlugs() },
			horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right
		)
		existsLabelWidget.label()._qtWidget().setFixedWidth( 35 )
		self.__column[0].append(
			existsLabelWidget,
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top
		)

		self.__column[0].append(
			GafferUI.BoolPlugValueWidget( { plug["exists"] for plug in self.getPlugs() } ),
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top
		)

		typeLabelWidget = GafferUI.LabelPlugValueWidget(
			{ plug['type'] for plug in self.getPlugs() },
			horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right
		)
		typeLabelWidget.label()._qtWidget().setFixedWidth( 30 )
		self.__column[0].append(
			typeLabelWidget,
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top
		)

		self.__column[0].append(
			GafferUI.StringPlugValueWidget( { plug["type"] for plug in self.getPlugs() } ),
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top
		)

		interpLabelWidget = GafferUI.LabelPlugValueWidget(
			{ plug["interpolation"] for plug in self.getPlugs() },
			horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right
		)
		interpLabelWidget.label()._qtWidget().setFixedWidth( 80 )
		self.__column[0].append(
			interpLabelWidget,
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top
		)
		interpPresetWidget = GafferUI.PresetsPlugValueWidget(
			{ plug["interpolation"] for plug in self.getPlugs() } )
		interpPresetWidget.menuButton()._qtWidget().setFixedWidth( 80 )
		self.__column[0].append( interpPresetWidget )

		valueLabelWidget = GafferUI.LabelPlugValueWidget(
			{ plug["value"] for plug in self.getPlugs() },
			horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right
		)
		valueLabelWidget.label()._qtWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() )
		self.__column[1].append(
			valueLabelWidget,
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top
		)
		self.__column[1].append(
			GafferUI.PlugValueWidget.create( { plug["value"] for plug in self.getPlugs() } )
		)

	def setPlugs( self, plugs ) :

		GafferUI.PlugValueWidget.setPlugs( self, plugs )

		self.__column[0][0].setPlugs( plugs )
		self.__column[0][1].setPlugs( { plug["exists"] for plug in plugs } )
		self.__column[0][2].setPlugs( { plug["exists"] for plug in plugs } )
		self.__column[0][3].setPlugs( { plug["type"] for plug in plugs } )
		self.__column[0][4].setPlugs( { plug["type"] for plug in plugs } )
		self.__column[0][5].setPlugs( { plug["interpolation"] for plug in plugs } )
		self.__column[0][6].setPlugs( { plug["interpolation"] for plug in plugs } )
		self.__column[1][0].setPlugs( { plug["value"] for plug in plugs } )
		self.__column[1][1].setPlugs( { plug["value"] for plug in plugs } )

	def hasLabel( self ) :

		return True

	def childPlugValueWidget( self, childPlug ) :

		for row in self.__column :
			for w in row :
				if childPlug in w.getPlugs() :
					return w

		return None

	def setReadOnly( self, readOnly ) :

		if readOnly == self.getReadOnly() :
			return

		GafferUI.PlugValueWidget.setReadOnly( self, readOnly )

		for row in self.__column :
			for w in row :
				w.setReadOnly( readOnly )

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.PrimitiveVariableQuery,

	"description",
	"""
	Queries primitive variables at a scene location, creating an output for
	each primitive variable.
	""",

	plugs = {

		"scene" : [

			"description",
			"""
			The scene to query the primitive variable from.
			""",

		],

		"location" : [

			"description",
			"""
			The location within the scene to query the primitive variable at.
			> Note : If the location does not exist then the query will not be
			> performed and all outputs will be set to their default values.
			""",

			"plugValueWidget:type", "GafferSceneUI.ScenePathPlugValueWidget",
			"scenePathPlugValueWidget:scene", "scene",
			"nodule:type", ""

		],

		"queries" : [

			"description",
			"""
			The primitive variables to be queried - arbitrary numbers of primitive
			variables may be added as children of this plug via the user interface,
			or via python. Each child is a `NameValuePlug` whose `name` plug is the
			name of the primitive variable to query, and whose `value` plug is the
			default value to use if the primitive variable can not be retrieved.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",

			"layout:customWidget:footer:widgetType", "GafferSceneUI.PrimitiveVariableQueryUI._PrimitiveVariableQueryFooter",
			"layout:customWidget:footer:index", -1,

			"nodule:type", "",

		],

		"queries.*" : [

			"description",
			"""
			A pair of primitive variable name to query and default value.
			""",

		],

		"queries.*.name" : [

			"description",
			"""
			The name of the primitive variable to query.
			""",

		],

		"queries.*.value" : [

			"description",
			"""
			The value to output if the primitive variable does not exist.
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

			"plugValueWidget:type", "GafferSceneUI.PrimitiveVariableQueryUI._OutputWidget",

			"nodule:type", "GafferUI::CompoundNodule",

		],

		"out.*.exists" : [

			"description",
			"""
			Outputs true if the primitive variable exists, otherwise false.
			""",

			"noduleLayout:label", functools.partial( __getLabel, parentPlug = "exists" ),

		],

		"out.*.value" : [

			"description",
			"""
			Outputs the value of the primitive variable, or the default value if
			the primitive variable does not exist.
			""",

		],

		"out.*.value..." : [

			"noduleLayout:label", functools.partial( __getLabel, parentPlug = "values" ),

		],

		"out.*.type" : [

			"description",
			"""
			Outputs the type of the primitive variable data, or empty string if
			the primitive variable does not exist.
			""",

			"noduleLayout:label", functools.partial( __getLabel, parentPlug = "type" ),

		],

		"out.*.interpolation" : [

			"description",
			"""
			Outputs the interpolation of the primitive variable, or `Invalid` if
			the primitive variable does not exist.
			""",

			"preset:Invalid", IECoreScene.PrimitiveVariable.Interpolation.Invalid,
			"preset:Constant", IECoreScene.PrimitiveVariable.Interpolation.Constant,
			"preset:Uniform", IECoreScene.PrimitiveVariable.Interpolation.Uniform,
			"preset:Vertex", IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			"preset:Varying", IECoreScene.PrimitiveVariable.Interpolation.Varying,
			"preset:FaceVarying", IECoreScene.PrimitiveVariable.Interpolation.FaceVarying,

			"noduleLayout:label", functools.partial( __getLabel, parentPlug = "interpolation" ),

		],

	}
)

##########################################################################
# _PrimitiveVariableQueryFooter
##########################################################################

class _PrimitiveVariableQueryFooter( GafferUI.PlugValueWidget ) :

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

		result.append( "/FromPathsDivider", { "divider" : True } )

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
			"ColorDivider",
			Gaffer.BoolVectorDataPlug( defaultValue = IECore.BoolVectorData() ),
			Gaffer.FloatVectorDataPlug( defaultValue = IECore.FloatVectorData() ),
			Gaffer.IntVectorDataPlug( defaultValue = IECore.IntVectorData() ),
			"Array/NumericDivider",
			Gaffer.StringVectorDataPlug( defaultValue = IECore.StringVectorData() ),
			"Array/StringDivider",
			Gaffer.V2iVectorDataPlug( defaultValue = IECore.V2iVectorData() ),
			Gaffer.V3iVectorDataPlug( defaultValue = IECore.V3iVectorData() ),
			Gaffer.V2fVectorDataPlug( defaultValue = IECore.V2fVectorData() ),
			Gaffer.V3fVectorDataPlug( defaultValue = IECore.V3fVectorData() ),
			"Array/VectorDivider",
			Gaffer.Color3fVectorDataPlug( defaultValue = IECore.Color3fVectorData() ),
		] :
			if isinstance( item, six.string_types ) :
				result.append( "/" + item, { "divider": True } )
			else :
				name = type( item ).__name__.replace( "Plug", "" )
				if "Vector" in name:
					name = "Array/" + name.split( "Vector" )[0]
				result.append(
					"/" + name,
					{
						"command" : functools.partial( Gaffer.WeakMethod( self.__addQuery ), "", "", item ),
					}
				)

		return result

	def __addQuery( self, plugName, variableName, plugOrValue ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :

			node = self.getPlug().node()

			if isinstance( plugOrValue, IECore.Data ) :
				dummyPlug = Gaffer.PlugAlgo.createPlugFromData(
					plugName,
					Gaffer.Plug.Direction.In,
					Gaffer.Plug.Flags.Default,
					plugOrValue
				)
				node.addQuery( dummyPlug, variableName )
			else:
				node.addQuery( plugOrValue, variableName )

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

	readOnlyUI = plugValueWidget.getReadOnly()
	plug = plugValueWidget.getPlug().ancestor( Gaffer.NameValuePlug )

	if plug is not None and isinstance( plug.node(), GafferScene.PrimitiveVariableQuery ) :

		if len( menuDefinition.items() ) :
			menuDefinition.append( "/DeleteDivider", { "divider" : True } )

		menuDefinition.append( "/Delete", { "command" : functools.partial( __deletePlug, plug ), "active" : not readOnlyUI and not Gaffer.MetadataAlgo.readOnly( plug ) } )

def __deletePlug( plug ) :

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		plug.node().removeQuery( plug )

GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu, scoped = False )

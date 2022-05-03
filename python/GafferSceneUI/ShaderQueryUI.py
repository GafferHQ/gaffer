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
import six

import IECore

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

##########################################################################
# Internal utilities
##########################################################################

def __getLabel( plug, parentPlug = None, sanitise = False ) :

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

	def setReadOnly( self, readOnly ) :

		if readOnly == self.getReadOnly() :
			return

		GafferUI.PlugValueWidget.setReadOnly( self, readOnly )

		for w in self.__row :
			w.setReadOnly( readOnly )


##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.ShaderQuery,

	"description",
	"""
	Queries shader parameters from a scene location, creating outputs
	for each parameter.
	""",

	plugs = {

		"scene" : [

			"description",
			"""
			The scene to query the shader for.
			""",

		],

		"location" : [

			"description",
			"""
			The location within the scene to query the shader at.
			> Note : If the location does not exist then the query will not be
			> performed and all outputs will be set to their default values.
			""",

			"plugValueWidget:type", "GafferSceneUI.ScenePathPlugValueWidget",
			"scenePathPlugValueWidget:scene", "scene",
			"nodule:type", "",

		],

		"shader" : [

			"description",
			"""
			The name of the shader to query.
			> Note : If the shader does not exist then the query will not be
			> performed and all outputs will be set to their default values.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"presetsPlugValueWidget:allowCustom", True,

			"preset:None", "",
			"nodule:type", "",

		],

		"inherit" : [

			"description",
			"""
			Queries inherited shader assignments if the location has no local
			assignment of its own.
			""",

			"nodule:type", "",

		],

		"queries" : [

			"description",
			"""
			The shader parameters to be queried - arbitrary numbers of shader
			parameters may be added as children of this plug via the user interface,
			or via python. Each child is a `NameValuePlug` whose `name` plug is
			the shader parameter to query, and whose `value` plug is the default
			value to use if the shader parameter can not be retrieved.

			The full network of the shader given by `shader` is available
			to be queried. Parameters on shaders in the network other than the
			output shader can be specified as `shaderName.parameterName`.

			> Note : If either the shader or parameter does not exist then the
			> query will not be performed and all outputs will be set to their
			> default values.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",

			"layout:customWidget:footer:widgetType", "GafferSceneUI.ShaderQueryUI._ShaderQueryFooter",
			"layout:customWidget:footer:index", -1,

			"nodule:type", "",

		],

		"queries.*" : [

			"description",
			"""
			The default value to output if the parameter does not exist.
			""",

			"spreadsheet:columnName", functools.partial( __getLabel, parentPlug = "queries", sanitise = True ),

		],

		"queries.*.name" : [

			"description",
			"""
			The name of the parameter to query.
			""",

		],

		"queries.*.value" : [

			"description",
			"""
			The value to output if the parameter does not exist.
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
			"noduleLayout:section", "right",
			"noduleLayout:spacing", 0.4,

		],

		"out.*" : [

			"description",
			"""
			The result of the query.
			""",

			"label", functools.partial( __getLabel, parentPlug = ""),

			"plugValueWidget:type", "GafferSceneUI.ShaderQueryUI._OutputWidget",

			"nodule:type", "GafferUI::CompoundNodule",
			"noduleLayout:section", "right",

		],

		"out.*.exists" : [

			"description",
			"""
			Outputs true if the shader, location and parameter exist, otherwise
			false.
			""",

			"noduleLayout:label", functools.partial( __getLabel, parentPlug = "exists" ),

			"noduleLayout:section", "right",

		],

		"out.*.value" : [

			"description",
			"""
			Outputs the value of the specified parameter, or the default value
			if the parameter does not exist.
			""",

			"noduleLayout:section", "right",
			"noduleLayout:spacing", 0.2,

		],

		"out.*.value..." : [

			"noduleLayout:label", functools.partial( __getLabel, parentPlug = "values" ),

			"noduleLayout:section", "right",

		],

	}
)


##########################################################################
# _ShaderQueryFooter
##########################################################################

class _ShaderQueryFooter( GafferUI.PlugValueWidget ) :

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
			Gaffer.Color4fPlug,
		] :
			if isinstance( item, six.string_types ) :
				result.append( "/" + item, { "divider": True } )
			else :
				result.append(
					"/" + item.__name__.replace( "Plug", "" ),
					{
						"command" : functools.partial( Gaffer.WeakMethod( self.__addQuery ), "", item ),
					}
				)

		return result

	def __addQuery( self, name, plugTypeOrValue ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :

			node = self.getPlug().node()

			if isinstance( plugTypeOrValue, IECore.Data ) :
				dummyPlug = Gaffer.PlugAlgo.createPlugFromData(
					"dummyPlug",
					Gaffer.Plug.Direction.In,
					Gaffer.Plug.Flags.Default,
					plugTypeOrValue
				)
				node.addQuery( dummyPlug, name)
			else:
				node.addQuery( plugTypeOrValue(), name)

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

	if plug is not None :

		if len( menuDefinition.items() ) :
			menuDefinition.append( "/DeleteDivider", { "divider" : True } )

		menuDefinition.append( "/Delete", { "command" : functools.partial( __deletePlug, plug ), "active" : not readOnlyUI and not Gaffer.MetadataAlgo.readOnly( plug ) } )

def __deletePlug( plug ) :

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		plug.node().removeQuery( plug )

GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu, scoped = False )

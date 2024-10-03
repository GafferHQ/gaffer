##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

from ._TableView import _TableView

from Qt import QtCore

Gaffer.Metadata.registerNode(

	Gaffer.Collect,

	"description",
	"""
	Collects arbitrary input values across a range of contexts, outputting
	arrays containing the values collected across that range.
	""",

	"layout:section:Settings.Inputs:collapsed", False,

	plugs = {

		"contextVariable" : [

			"description",
			"""
			The context variable used to vary the values of the inputs being
			collected. This should be used in the node network upstream of the
			inputs.
			""",

			"noduleLayout:visible", False,

		],

		"indexContextVariable" : [

			"description",
			"""
			The context variable used to specify the index being collected. This
			may be used in the node network upstream of the inputs.
			""",

			"noduleLayout:visible", False,

		],

		"contextValues" : [

			"description",
			"""
			The values of the context variable. Collection will be performed once
			for each context value.
			""",

			"nodule:type", "",

		],

		"enabled" : [

			"description",
			"""
			Enables or disables collection. This may be varied based on the
			context variable, so that collection may be disabled in some
			contexts but not others. Only values for enabled contexts are
			included in the output arrays.
			""",

			"layout:section", "Settings",
			"nodule:type", "GafferUI::StandardNodule",

		],

		"in" : [

			"description",
			"""
			Container of inputs to be collected from. Inputs may be added by
			calling `collectNode.addInput( plug )` or using the UI. Each input
			provides a corresponding output parented under the `out` plug.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",

			"layout:section", "Settings.Inputs",

			"layout:customWidget:footer:widgetType", "GafferUI.CollectUI._InputFooter",
			"layout:customWidget:footer:index", -1,

			"nodule:type", "GafferUI::CompoundNodule",
			"noduleLayout:spacing", 0.2,
			"noduleLayout:customGadget:addButton:gadgetType", "GafferUI.CollectUI._InputAdder",

		],

		"in.*" : [

			"description",
			lambda plug : f"""An input value to be collected once in each context, with an array of the results
			being provided by `out.{plug.getName()}`.""",

			"renameable", True,

		],

		"enabledValues" : [

			"description",
			"""
			Outputs an array of the context values for which collection was enabled by the `enabled` plug.
			""",

			# We show the value for this plug in the `_OutputPlugValueWidget`.
			"plugValueWidget:type", "",
			"noduleLayout:index", 0,

		],

		"out" : [

			"description",
			"""
			Container of array outputs corresponding to the inputs provided by the `in` plug.
			""",

			"plugValueWidget:type", "GafferUI.CollectUI._OutputPlugValueWidget",
			"layout:section", "Results",

			"nodule:type", "GafferUI::CompoundNodule",
			"noduleLayout:spacing", 0.2,
			"noduleLayout:index", 1,

		],

		"out.*" : [

			"description",
			lambda plug : f"""An array of all the results collected from `in.{plug.getName()}`.""",

		],

	}
)

##########################################################################
# _InputFooter
##########################################################################

class _InputFooter( GafferUI.PlugValueWidget ) :

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

		self.__menuButton.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ) )
		self.__menuButton.dragLeaveSignal().connect( Gaffer.WeakMethod( self.__dragLeave ) )
		self.__menuButton.dropSignal().connect( Gaffer.WeakMethod( self.__drop ) )

	def _updateFromEditable( self ) :

		self.__menuButton.setEnabled(
			self.getPlug().getInput() is None and not Gaffer.MetadataAlgo.readOnly( self.getPlug() )
		)

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
			"ColorDivider",
			Gaffer.M33fPlug,
			Gaffer.M44fPlug,
		] :
			if isinstance( item, str ) :
				result.append( "/" + item, { "divider": True } )
			else :
				result.append(
					"/" + item.__name__.replace( "Plug", "" ),
					{
						"command" : functools.partial( Gaffer.WeakMethod( self.__addInput ), item ),
					}
				)

		return result

	def __dragEnter( self, widget, event ) :

		if not isinstance( event.data, Gaffer.ValuePlug ) :
			return False

		if not self.getPlug().node().canAddInput( event.data ) :
			return False

		self.__menuButton.setHighlighted( True )
		return True

	def __dragLeave( self, widget, event ) :

		self.__menuButton.setHighlighted( False )
		return True

	def __drop( self, widget, event ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().node().addInput( event.data )

		self.__menuButton.setHighlighted( False )
		return True

	def __addInput( self, plugType ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :

			node = self.getPlug().node()
			node.addInput( plugType() )

##########################################################################
# _InputAdder
##########################################################################

class _InputAdder( GafferUI.PlugAdder ) :

	def __init__( self, plug ) :

		GafferUI.PlugAdder.__init__( self )

		self.__node = plug.node()

	def canCreateConnection( self, endpoint ) :

		if not GafferUI.PlugAdder.canCreateConnection( self, endpoint ) :
			return False

		return endpoint.direction() == Gaffer.Plug.Direction.Out and self.__node.canAddInput( endpoint )

	def createConnection( self, endpoint ) :

		with Gaffer.UndoScope( self.__node.scriptNode() ) :
			input = self.__node.addInput( endpoint )
			input.setInput( endpoint )

GafferUI.NoduleLayout.registerCustomGadget( "GafferUI.CollectUI._InputAdder", _InputAdder )

##########################################################################
# _OutputPlugValueWidget
##########################################################################

class _OutputPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		self.__vectorDataWidget = GafferUI.VectorDataWidget(
			editable = False,
			horizontalScrollMode = GafferUI.ScrollMode.Automatic
		)

		self.__busyWidget = GafferUI.BusyWidget( size = 18 )
		# Sneak into the corner of the table view.
		self.__busyWidget._qtWidget().setParent( self.__vectorDataWidget._qtWidget() )

		GafferUI.PlugValueWidget.__init__( self, self.__vectorDataWidget, plugs, **kw )

	def hasLabel( self ) :

		return True

	def _auxiliaryPlugs( self, plug ) :

		node = plug.node()
		if isinstance( node, Gaffer.Collect ) :
			return [ node["enabledValues"] ]

	@staticmethod
	def _valuesForUpdate( plugs, auxiliaryPlugs ) :

		return [
			{
				"enabledValues" : enabledValuesPlug.getValue(),
				"outputs" : [ _OutputPlugValueWidget.__conformToVectorData( c.getValue() ) for c in plug.children() ],
			}
			for plug, ( enabledValuesPlug, ) in zip( plugs, auxiliaryPlugs )
		]

	def _updateFromValues( self, values, exception ) :

		if values :
			self.__vectorDataWidget.setHeader(
				[ "Context" ] + [ IECore.CamelCase.toSpaced( c.getName() ) for c in self.getPlug().children() ]
			)
			self.__vectorDataWidget.setData( [ values[0]["enabledValues"] ] + values[0]["outputs"] )

		self.__busyWidget.setVisible( exception is None and not values )
		self.__vectorDataWidget.setErrored( exception is not None )

	@staticmethod
	def __conformToVectorData( o ) :

		if not isinstance( o, IECore.ObjectVector ) :
			return o

		# It's unreasonable to expect VectorDataWidget to support ObjectVector
		# because in the general case it could contain arbitrary objects and
		# need a UI for editing. But in this case we know the widget is
		# read-only, and that simple string formatting of the result is sufficient.

		return IECore.StringVectorData( [ str( x ) for x in o ] )

##########################################################################
# Delete menu items. We can't use the usual `deletable` metadata because
# we need to call `removeInput()` to synchronise deletion of the input
# and output plugs.
##########################################################################

def __plugPopupMenu( menuDefinition, plug ) :

	node = plug.node()
	if not isinstance( node, Gaffer.Collect ) or plug.parent() not in { node["in"], node["out"] } :
		return

	if len( menuDefinition.items() ) :
		menuDefinition.append( "/DeleteDivider", { "divider" : True } )

	menuDefinition.append( "/Delete", { "command" : functools.partial( __deletePlug, plug ), "active" : not Gaffer.MetadataAlgo.readOnly( plug ) } )

def __deletePlug( plug ) :

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		input = plug if plug.direction() == Gaffer.Plug.Direction.In else plug.node().inputPlugForOutput( plug )
		plug.node().removeInput( input )

GafferUI.PlugValueWidget.popupMenuSignal().connect(
	lambda menuDefinition, plugValueWidget : __plugPopupMenu( menuDefinition, plugValueWidget.getPlug() )
)

GafferUI.GraphEditor.plugContextMenuSignal().connect(
	lambda graphEditor, plug, menuDefinition : __plugPopupMenu( menuDefinition, plug )
)

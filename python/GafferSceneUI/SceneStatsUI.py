##########################################################################
#
#  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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
import GafferScene

from GafferUI.PlugValueWidget import sole

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.SceneStats,

	"description",
	"""
	Computes aggregate statistics across all scene locations matched by a filter.
	Statistics are generated for an arbitrary number of user-defined input queries,
	so can be used to inspect any property of the scene. For each query,
	the sum, min, max and average values are computed and provided on output plugs.
	Each query can be enabled/disabled on a per-location basis.

	> Tip : Nodes such as PrimitiveQuery, AttributeQuery and PrimitiveVariableQuery
	> provide ideal query inputs. The query location should be `${scene:path}` so
	> that the query is repeated for each filtered location.
	""",

	plugs = {

		"scene" : {

			"description" :
			"""
			The scene to gather statistics from.
			""",

			"noduleLayout:section" : "top",

		},

		"filter" : {

			"description" :
			"""
			The filter controlling which locations are included in the statistics.
			The input queries are evaluated for each matched location.
			""",

			"layout:section" : "Filter",
			# Having the filter on the top is unconventional, but the layout
			# works better with query inputs on the left and outputs on the
			# right.
			"noduleLayout:section" : "top",
			"layout:index" : -3, # Just before the enabled plug,
			"nodule:type" : "GafferUI::StandardNodule",
			"plugValueWidget:type" : "GafferSceneUI.FilterPlugValueWidget",

		},

		"queries" : {

			"description" :
			"""
			The input values to be queried. Arbitrary numbers of queries may
			be added using the `addQuery()` API method or the `+` button in the
			UI.
			""",

			"plugValueWidget:type" : "GafferUI.LayoutPlugValueWidget",

			"layout:customWidget:footer:widgetType" : "GafferUI.PlugCreationWidget",
			"layout:customWidget:footer:index" : -1,

			"plugCreationWidget:action" : "addQuery",
			"plugCreationWidget:includedTypes" : (
				"Gaffer::BoolPlug Gaffer::IntPlug Gaffer::FloatPlug "
				"Gaffer::V2iPlug Gaffer::V3iPlug Gaffer::V2fPlug Gaffer::V3fPlug "
				"Gaffer::Color3fPlug Gaffer::Color4fPlug"
			),

			"nodule:type" : "GafferUI::CompoundNodule",
			"noduleLayout:section" : "left",
			"noduleLayout:spacing" : 0.4,
			"noduleLayout:customGadget:addButton:gadgetType" : "GafferUI.PlugCreationGadget",

		},

		"queries.*" : {

			"renameable" : True,
			"plugValueWidget:type" : "GafferSceneUI.SceneStatsUI._QueryWidget",
			"nodule:type" : "GafferUI::CompoundNodule",

		},

		"queries.*.enabled" : {

			"description" :
			"""
			Enables or disables the query. Evaluated on a per-location basis,
			so statistics collection can be turned off at specific locations.
			This can be necessary to produce accurate averages and min/max stats.
			For example, to compute the average vertex count for all meshes, the
			query should be disabled for locations that don't hold a mesh.

			> Tip : A common way of checking primitive type is to use
			> a PatternMatch node with the `type` output of a PrimitiveQuery.
			""",

			"noduleLayout:visible" : False,

		},

		"queries.*.value" : {

			"description" :
			"""
			The value for which statistics will be computed. Should
			be connected to an input which varies per scene location.
			For example, a PrimitiveQuery or AttributeQuery with
			`location` set to `${scene:path}`.
			""",

			"noduleLayout:label" : lambda plug : plug.parent().getName(),

		},

		"out" : {

			"description" :
			"""
			Outputs the statistics for the `queries` plugs. Each query has a
			corresponding output with the same name.
			""",

			"plugValueWidget:type" : "",

			"layout:section" : "Settings.Outputs",

			"nodule:type" : "GafferUI::CompoundNodule",
			"noduleLayout:section" : "right",
			"noduleLayout:spacing" : 0.4,
			"noduleLayout:customGadget:addButton:gadgetType" : "GafferUI.PlugVisibilityGadget",

		},

		"out.*" : {

			"nodule:type" : "GafferUI::CompoundNodule",
			"noduleLayout:spacing" : 0.2,
			"noduleLayout:section" : "right",

		},

		"out.*.*" : {

			"noduleLayout:label" : lambda plug : plug.relativeName( plug.parent().parent() ),
			"noduleLayout:visible" : False,
			"plugVisibilityGadget:showable" : True,

		},

		"out.*.sum" : {

			"description" :
			"""
			The sum of the input over all queried locations.
			""",

		},

		"out.*.min" : {

			"description" :
			"""
			The minimum value of the input at all queried locations.
			""",

		},

		"out.*.max" : {

			"description" :
			"""
			The maximum value of the input at all queried locations.
			""",

		},

		"out.*.count" : {

			"description" :
			"""
			The number of times the input was queried. This is the number
			of times the filter matched and the query's `enabled` plug was
			turned on.
			""",

		},

		"out.*.average" : {

			"description" :
			"""
			The average value of the input across all queried locations.
			""",

		},

	}

)

##########################################################################
# Query widget
##########################################################################

class _QueryWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, queryPlugs, **kw ) :

		self.__column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4 )

		if isinstance( queryPlugs, Gaffer.Plug ) :
			queryPlugs = { queryPlugs }

		GafferUI.PlugValueWidget.__init__( self, self.__column, queryPlugs )

		self.__plugWidgets = {}
		with self.__column :

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

				self.__collapseButton = GafferUI.Button( image = "collapsibleArrowRight.png", hasFrame = False )
				self.__collapseButton.clickedSignal().connect( Gaffer.WeakMethod( self.__collapseButtonClicked ) )

				self.__plugWidgets["in"] = GafferUI.PlugWidget( GafferUI.PlugValueWidget.create( queryPlugs, typeMetadata = None ) )
				self.__plugWidgets["in"].labelPlugValueWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() - 12 ) # Adjust for `collapseButton`

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4 ) as self.__outputsColumn :

				outPlugs = [ plug.node()["out"][plug.getName()] for plug in self.getPlugs() ]
				for childName in outPlugs[0].keys() :
					widget = GafferUI.PlugWidget( GafferUI.PlugValueWidget.create( { plug[childName] for plug in outPlugs } ) )
					widget.labelPlugValueWidget().setFixedWidth(
						GafferUI.PlugWidget.labelWidth()
					)
					self.__plugWidgets[childName] = widget

			self.__setOutputsVisible( sole( Gaffer.Metadata.value( p, "ui:queryWidget:outputsVisible" ) for p in queryPlugs ) )

	def setPlugs( self, plugs ) :

		GafferUI.PlugValueWidget.setPlugs( self, plugs )

		self.__plugWidgets["in"].setPlugs( plugs )
		outPlugs = [ plug.node()["out"][plug.getName()] for plug in self.getPlugs() ]
		for childName in outPlugs[0].keys()  :
			self.__plugWidgets[childName].setPlugs(
				{ plug[childName] for plug in outPlugs }
			)

	def hasLabel( self ) :

		return True

	def childPlugValueWidget( self, childPlug ) :

		return self.__plugWidgets["in"].plugValueWidget().childPlugValueWidget( childPlug )

	def __collapseButtonClicked( self, button ) :

		self.__setOutputsVisible( not self.__getOutputsVisible() )

	def __getOutputsVisible( self ) :

		return self.__outputsColumn.getVisible()

	def __setOutputsVisible( self, visible ) :

		self.__outputsColumn.setVisible( visible )
		self.__collapseButton.setImage( "collapsibleArrowDown.png" if visible else "collapsibleArrowRight.png" )

		for plug in self.getPlugs() :
			Gaffer.Metadata.registerValue( plug, "ui:queryWidget:outputsVisible", visible, persistent = False )

##########################################################################
# Popup menu
##########################################################################

def __plugPopupMenu( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug()
	if plug is None or not isinstance( plug.node(), GafferScene.SceneStats ) :
		return

	queriesPlug = plug.node()["queries"]
	if plug.parent() != queriesPlug :
		return

	if len( menuDefinition.items() ) :
		menuDefinition.append( "/DeleteDivider", { "divider" : True } )

	menuDefinition.append(
		"/Delete",
		{
			"command" : functools.partial( __deleteQuery, plug ),
			"active" : not Gaffer.MetadataAlgo.readOnly( queriesPlug ),
		}
	)

def __deleteQuery( queryPlug ) :

	with Gaffer.UndoScope( queryPlug.ancestor( Gaffer.ScriptNode ) ) :
		queryPlug.node().removeQuery( queryPlug )

GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu )

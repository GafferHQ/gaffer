##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

import IECore

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

## Base class to simplify the creation of Editors which operate on ScenePlugs.
class SceneEditor( GafferUI.NodeSetEditor ) :

	## Provides an `in` ScenePlug which defines the scene to be
	#  displayed and/or edited.
	class Settings( GafferUI.Editor.Settings ) :

		# Pass `withHierarchyFilter = True` to set up a standard filter directed
		# to a `__filteredIn` input plug.
		def __init__( self, withHierarchyFilter = False ) :

			GafferUI.Editor.Settings.__init__( self )

			self["in"] = GafferScene.ScenePlug()

			if withHierarchyFilter :

				self["__filteredIn"] = GafferScene.ScenePlug()
				self["__hierarchyFilter"] = _HierarchyFilter()
				self["__hierarchyFilter"]["in"].setInput( self["in"] )
				self["__filteredIn"].setInput( self["__hierarchyFilter"]["out"] )
				Gaffer.PlugAlgo.promote( self["__hierarchyFilter"]["filter"] )
				Gaffer.PlugAlgo.promote( self["__hierarchyFilter"]["setFilter"] )

	IECore.registerRunTimeTyped( Settings, typeName = "GafferSceneUI::SceneEditor::Settings" )

	def __init__( self, topLevelWidget, scriptNode, **kw ) :

		GafferUI.NodeSetEditor.__init__( self, topLevelWidget, scriptNode, nodeSet = scriptNode.focusSet(), **kw )

		self.__parentingConnections = {}

		self.__globalEditTargetLinked = False
		self.parentChangedSignal().connect( Gaffer.WeakMethod( self.__parentChanged ) )

	def editScope( self ) :

		if not "editScope" in self.settings() :
			return None

		return Gaffer.PlugAlgo.findSource(
			self.settings()["editScope"],
			lambda plug : plug.node() if isinstance( plug.node(), Gaffer.EditScope ) else None
		)

	def _updateFromSet( self ) :

		# Find a ScenePlug and connect it to `settings()["in"]`.

		updatedParentingConnections = {}

		with Gaffer.DirtyPropagationScope() :

			node = self.getNodeSet()[-1] if self.getNodeSet() else None
			outputScenePlug = None
			if node is not None :
				outputScenePlug = next(
					( p for p in GafferScene.ScenePlug.RecursiveOutputRange( node ) if not p.getName().startswith( "__" ) ),
					None
				)

			self.settings()["in"].setInput( outputScenePlug )

			if outputScenePlug is not None :

				plugConnection = self.__parentingConnections.get( outputScenePlug )
				if plugConnection is None :
					plugConnection = outputScenePlug.parentChangedSignal().connect(
						Gaffer.WeakMethod( self.__scenePlugParentChanged ), scoped = True
					)
				updatedParentingConnections[outputScenePlug] = plugConnection

				nodeConnections = self.__parentingConnections.get( node )
				if nodeConnections is None :
					nodeConnections = [
						node.childAddedSignal().connect( Gaffer.WeakMethod( self.__childAddedOrRemoved ), scoped = True ),
						node.childRemovedSignal().connect( Gaffer.WeakMethod( self.__childAddedOrRemoved ), scoped = True ),
					]
				updatedParentingConnections[node] = nodeConnections

		# Note : We reuse existing connections where we can to avoid getting
		# into infinite loops. We are called from the very signals we are
		# connecting to, so if we made _new_ connections then we would be called
		# _again_ for the same invocation of the signal.
		self.__parentingConnections = updatedParentingConnections

		# Called last, because it will call `_titleFormat()`, which depends on
		# the inputs we just created.
		GafferUI.NodeSetEditor._updateFromSet( self )

	def _titleFormat( self ) :

		return GafferUI.NodeSetEditor._titleFormat(
			self,
			_maxNodes = 1 if self.settings()["in"].getInput() is not None else 0,
			_reverseNodes = True,
			_ellipsis = False
		)

	def __parentChanged( self, widget ) :

		if self.__globalEditTargetLinked or not "editScope" in self.settings() :
			return

		compoundEditor = self.ancestor( GafferUI.CompoundEditor )
		if compoundEditor :
			self.settings()["editScope"].setInput( compoundEditor.settings()["editScope"] )
			self.__globalEditTargetLinked = True

	def __scenePlugParentChanged( self, plug, newParent ) :

		self._updateFromSet()

	def __childAddedOrRemoved( self, node, child ) :

		if isinstance( child, GafferScene.ScenePlug ) :
			self._updateFromSet()

# Settings metadata
# =================

Gaffer.Metadata.registerNode(

	SceneEditor.Settings,

	plugs = {

		"filter" : {

			"description" :
			"""
			Filters the input scene to isolate locations with matching names.
			The filter may contain any of Gaffer's standard wildcards, and may
			either be used to match individual location names or entire paths.

			Examples
			--------

			- `building` : Matches any location in the scene which has the
			  text `building` anywhere in its name.
			- `/cityA/.../building*` : Matches only locations within `cityA`
			  whose name starts with `building`.
			""",

			"plugValueWidget:type" : "GafferUI.TogglePlugValueWidget",
			"togglePlugValueWidget:image:on" : "searchOn.png",
			"togglePlugValueWidget:image:off" : "search.png",
			# We need a non-default value to toggle to, so that the first
			# toggling can highlight the icon. `*` seems like a reasonable value
			# since it has no effect on the filtering, and hints that wildcards
			# are available.
			"togglePlugValueWidget:defaultToggleValue" : "*",
			"stringPlugValueWidget:placeholderText" : "Filter...",
			"layout:section" : "Filter"

		},

		"setFilter" : {

			"description" :
			"""
			Filters the input scene to isolate locations belonging to specific
			sets.
			""",

			"label" : "",
			"plugValueWidget:type" : "GafferSceneUI.SceneEditor._SetFilterPlugValueWidget",
			"layout:section" : "Filter"

		},

	}

)

# _HierarchyFilter
# ================

# Provides a standard filter for the input scene hierarchy,
# allowing the user to search for specific locations or filter
# using sets.
class _HierarchyFilter( GafferScene.SceneProcessor ) :

	def __init__( self, name = "_HierarchyFilter" ) :

		GafferScene.SceneProcessor.__init__( self, name )

		self["filter"] = Gaffer.StringPlug()
		self["setFilter"] = Gaffer.StringPlug()

		# We transform the `filter` match pattern into a set, rather
		# than using it with a PathFilter directly. Otherwise `...`
		# causes us to speculatively include all descendants
		# even if there is no concrete match.

		self["__pathFilter"] = GafferScene.PathFilter()
		self["__filterSet"] = GafferScene.Set()
		self["__filterSet"]["in"].setInput( self["in"] )
		self["__filterSet"]["filter"].setInput( self["__pathFilter"]["out"] )
		self["__filterSet"]["name"].setValue( "__HierarchyFilter__FilterSet__" )

		self["__pathFilterExpression"] = Gaffer.Expression()
		self["__pathFilterExpression"].setExpression(
			'import GafferSceneUI;'
			'parent["__pathFilter"]["paths"] = GafferSceneUI.SceneEditor._HierarchyFilter._pathFilterExpression('
			'	parent["filter"]'
			')'
		)

		# We combine the `filter` and `setFilter` into a single SetFilter
		# expression for everything we want to view.

		self["__setFilter"] = GafferScene.SetFilter()

		self["__setFilterExpression"] = Gaffer.Expression()
		self["__setFilterExpression"].setExpression(
			'import GafferSceneUI;'
			'parent["__setFilter"]["setExpression"] = GafferSceneUI.SceneEditor._HierarchyFilter._setFilterExpression('
			'	parent["filter"], parent["setFilter"]'
			')'
		)

		# An Isolate node is used to do the actual filtering.

		self["__isolate"] = GafferScene.Isolate()
		self["__isolate"]["in"].setInput( self["__filterSet"]["out"] )
		self["__isolate"]["filter"].setInput( self["__setFilter"]["out"] )
		# Disable the node unless we have filtering to perform.
		self["__isolate"]["enabled"].setInput( self["__setFilter"]["setExpression"] )

		self["out"].setInput( self["__isolate"]["out"] )

	__identityFilterValues = { "", "*", "/..." }

	@classmethod
	def _pathFilterExpression( cls, filterValue ) :

		result = IECore.StringVectorData()
		if filterValue in cls.__identityFilterValues :
			return result

		if "/" in filterValue :
			result.append( filterValue )
		elif IECore.StringAlgo.hasWildcards( filterValue ) :
			result.append( f"/.../{filterValue}" )
		else :
			result.append( f"/.../*{filterValue}*" )

		return result

	@classmethod
	def _setFilterExpression( cls, filterValue, setFilterValue ) :

		filterSet = "__HierarchyFilter__FilterSet__" if filterValue not in cls.__identityFilterValues else None

		if filterSet and setFilterValue :
			return f"({filterSet} in ({setFilterValue})) | (({setFilterValue}) in {filterSet})"
		else :
			return filterSet or setFilterValue

IECore.registerRunTimeTyped( _HierarchyFilter, typeName = "GafferSceneUI::SceneEditor::_HierarchyFilter" )

SceneEditor._HierarchyFilter = _HierarchyFilter

# _SetFilterPlugValueWidget
# =========================

class _SetFilterPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__button = GafferUI.MenuButton(
			image = "setFilterOff.png",
			menu = GafferUI.Menu(
				Gaffer.WeakMethod( self.__setsMenuDefinition ),
				title = "Set Filter"
			),
			hasFrame = False,
		)

		GafferUI.PlugValueWidget.__init__( self, self.__button, plug )

		self.__lastNonDefaultValue = None
		self.__availableSetNames = []

	def _auxiliaryPlugs( self, plug ) :

		return [ plug.node()["in"] ]

	@staticmethod
	def _valuesForUpdate( plugs, auxiliaryPlugs ) :

		assert( len( plugs ) == 1 )

		setNames = []
		scenePlug = next( iter( auxiliaryPlugs ) )[0]
		with IECore.IgnoredExceptions( Gaffer.ProcessException ) :
			setNames = [ str( s ) for s in scenePlug.setNames() ]

		return [ {
			"value" : next( iter( plugs ) ).getValue(),
			"setNames" : setNames,
		} ]

	def _updateFromValues( self, values, exception ) :

		if not values :
			# Background update started
			return

		assert( len( values ) == 1 and exception is None )

		value = values[0]["value"]
		if value != self.getPlug().defaultValue() :
			self.__lastNonDefaultValue = value

		self.__button.setImage( "setFilter{}.png".format( "On" if value else "Off" ) )
		self.__availableSetNames = values[0]["setNames"]

	def __setsMenuDefinition( self ) :

		m = IECore.MenuDefinition()

		availableSets = set( self.__availableSetNames )

		builtInSets = { "__lights", "__lightFilters", "__cameras", "__coordinateSystems" }
		selectedSets = set( self.getPlug().getValue().split() )

		m.append(
			"/Enabled", {
				"checkBox" : not self.getPlug().isSetToDefault(),
				"command" : functools.partial(
					Gaffer.WeakMethod( self.__setPlugValue ),
					self.__lastNonDefaultValue if self.getPlug().isSetToDefault() else ""
				),
				"active" : self.__lastNonDefaultValue is not None,
			}
		)

		m.append( "/EnabledDivider", { "divider" : True } )

		def item( setName ) :

			updatedSets = set( selectedSets )
			if setName in updatedSets :
				updatedSets.remove( setName )
			else :
				updatedSets.add( setName )

			return {
				"checkBox" : s in selectedSets,
				"command" : functools.partial( Gaffer.WeakMethod( self.__setPlugValue ), " ".join( sorted( updatedSets ) ) )
			}

		for s in sorted( builtInSets ) :
			m.append(
				"/{}".format( IECore.CamelCase.toSpaced( s[2:] ) ),
				item( s )
			)

		haveDivider = False
		pathFn = GafferSceneUI.SetUI.getMenuPathFunction()
		for s in sorted( availableSets | selectedSets ) :
			if s in builtInSets :
				continue
			if not haveDivider :
				m.append( "/BuiltInDivider", { "divider" : True } )
				haveDivider = True
			m.append( "/" + pathFn( s ), item( s ) )

		return m

	def __setPlugValue( self, value, *unused ) :

		self.getPlug().setValue( value )

SceneEditor._SetFilterPlugValueWidget = _SetFilterPlugValueWidget

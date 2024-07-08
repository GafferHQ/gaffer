##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2014, John Haddon. All rights reserved.
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

import re
import sys
import functools
import collections

import IECore

import Gaffer
import GafferUI

from Qt import QtWidgets

## A class for laying out widgets to represent all the plugs held on a particular parent.
#
# Per-plug metadata support :
#
#	- "<layoutName>:index" controls ordering of plugs within the layout
#	- "<layoutName>:section" places the plug in a named section of the layout
#	- "<layoutName>:divider" specifies whether or not a plug should be followed by a divider
#	- "<layoutName>:activator" the name of an activator to control editability,
#	  or a boolean value to control it directly
#	- "<layoutName>:visibilityActivator" the name of an activator to control visibility,
#	  or a boolean value to control it directly
#	- "<layoutName>:accessory" groups as an accessory to the previous widget
#	- "<layoutName>:width" gives a specific width to the plug's widget
#
# Per-parent metadata support :
#
#   - <layoutName>:section:sectionName:summary" dynamic metadata entry returning a
#     string to be used as a summary for the section.
#   - <layoutName>:section:sectionName:collapsed" boolean indicating whether or
#     not a section should be collapsed initially.
#   - "<layoutName>:activator:activatorName" a dynamic boolean metadata entry to control
#     the activation of plugs within the layout
#   - "<layoutName>:activators" a dynamic metadata entry returning a CompoundData of booleans
#     for several named activators.
#
# ## Custom widgets
#
# Custom widgets unassociated with any specific plugs may also be added to plug layouts.
# This can be useful when customising user interfaces for a particular facility - for instance
# to display asset management information for each node.
#
# A custom widget is specified using parent metadata entries starting with
# "<layoutName>:customWidget:Name:" prefixes, where "Name" is a unique identifier for the
# custom widget :
#
#   - "<layoutName>:customWidget:Name:widgetType" specifies a string containing the fully qualified
#     name of a python callable which will be used to create the widget. This callable will be passed
#     the same parent GraphComponent (node or plug) that the PlugLayout is being created for.
#   - "<layoutName>:customWidget:Name:*" as for the standard per-plug "<layoutName>:*" metadata, so custom
#     widgets may be assigned to a section, reordered, given activators etc.
#
class PlugLayout( GafferUI.Widget ) :

	def __init__( self, parent, orientation = GafferUI.ListContainer.Orientation.Vertical, layoutName = "layout", rootSection = "", embedded = False, **kw ) :

		assert( isinstance( parent, ( Gaffer.Node, Gaffer.Plug ) ) )

		# embedded indicates that the PlugLayout is embedded in another layout
		# which affects how the widget is built
		self.__embedded = embedded

		self.__layout = _TabLayout( orientation, embedded = embedded ) if isinstance( parent, Gaffer.Node ) and not rootSection else _CollapsibleLayout( orientation )

		GafferUI.Widget.__init__( self, self.__layout, **kw )

		self.__parent = parent
		self.__layoutName = layoutName
		# not to be confused with __rootSection, which holds an actual _Section object
		self.__rootSectionName = rootSection

		# we need to connect to the childAdded/childRemoved signals on
		# the parent so we can update the ui when plugs are added and removed.
		parent.childAddedSignal().connect( Gaffer.WeakMethod( self.__childAddedOrRemoved ), scoped = False )
		parent.childRemovedSignal().connect( Gaffer.WeakMethod( self.__childAddedOrRemoved ), scoped = False )

		# since our layout is driven by metadata, we must respond dynamically
		# to changes in that metadata.
		Gaffer.Metadata.plugValueChangedSignal( self.__node() ).connect( Gaffer.WeakMethod( self.__plugMetadataChanged ), scoped = False )
		if isinstance( self.__parent, Gaffer.Node ) :
			Gaffer.Metadata.nodeValueChangedSignal( self.__parent ).connect(
				Gaffer.WeakMethod( self.__nodeMetadataChanged ), scoped = False
			)

		# and since our activations are driven by plug values, we must respond
		# when the plugs are dirtied.
		self.__node().plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__plugDirtied ), scoped = False )

		# frequently events that trigger a ui update come in batches, so we
		# perform the update lazily using a LazyMethod. the dirty variables
		# keep track of the work we'll need to do in the update.
		self.__layoutDirty = True
		self.__activationsDirty = True
		self.__summariesDirty = True

		# mapping from layout item to widget, where the key is either a plug or
		# the name of a custom widget (as returned by layoutOrder()).
		self.__widgets = {}
		self.__rootSection = _Section( self.__parent )

		# Set up an appropriate context in which to view the plugs.
		self.__context = GafferUI.PlugValueWidget._PlugValueWidget__defaultContext( self.__parent )
		self.__contextChangedConnection = self.__context.changedSignal().connect(
			Gaffer.WeakMethod( self.__contextChanged ), scoped = True
		)

		# Build the layout
		self.__update()

	def context( self ) :

		return self.__context

	## Returns a PlugValueWidget representing the specified child plug.
	def plugValueWidget( self, childPlug ) :

		self.__updateLazily.flush( self )

		w = self.__widgets.get( childPlug, None )
		if w is None :
			return w
		elif isinstance( w, GafferUI.PlugValueWidget ) :
			return w
		else :
			return w.plugValueWidget()

	## Returns the custom widget registered with the specified name.
	def customWidget( self, name ) :

		self.__updateLazily.flush( self )

		return self.__widgets.get( name )

	## Returns the list of section names that will be used when laying
	# out the plugs of the specified parent. The sections are returned
	# in the order in which they will be created.
	@classmethod
	def layoutSections( cls, parent, includeCustomWidgets = False, layoutName = "layout" ) :

		d = collections.OrderedDict()
		for item in cls.layoutOrder( parent, includeCustomWidgets, layoutName = layoutName ) :
			sectionPath = cls.__staticSectionPath( item, parent, layoutName )
			sectionName = ".".join( sectionPath )
			d[sectionName] = 1

		return list( d.keys() )

	## Returns the child plugs of the parent in the order in which they
	# will be laid out, based on "<layoutName>:index" Metadata entries. If
	# includeCustomWidgets is True, then the positions of custom widgets
	# are represented by the appearance of the names of the widgets as
	# strings within the list. If a section name is specified, then the
	# result will be filtered to include only items in that section.
	@classmethod
	def layoutOrder( cls, parent, includeCustomWidgets = False, section = None, layoutName = "layout", rootSection = "" ) :

		items = parent.children( Gaffer.Plug )
		items = [ plug for plug in items if not plug.getName().startswith( "__" ) ]

		if includeCustomWidgets :
			for name in Gaffer.Metadata.registeredValues( parent ) :
				m = re.match( layoutName + ":customWidget:(.+):widgetType", name )
				if m and cls.__metadataValue( parent, name ) :
					items.append( m.group( 1 ) )

		itemsAndIndices = [ list( x ) for x in enumerate( items ) ]
		for itemAndIndex in itemsAndIndices :
			index = cls.__staticItemMetadataValue( itemAndIndex[1], "index", parent, layoutName )
			if index is not None :
				index = index if index >= 0 else sys.maxsize + index
				itemAndIndex[0] = index

		itemsAndIndices.sort( key = lambda x : x[0] )

		if section is not None :
			sectionPath = section.split( "." ) if section else []
			itemsAndIndices = [ x for x in itemsAndIndices if cls.__staticSectionPath( x[1], parent, layoutName ) == sectionPath ]

		if rootSection :
			rootSectionPath = rootSection.split( "." if rootSection else [] )
			itemsAndIndices = [ x for x in itemsAndIndices if cls.__staticSectionPath( x[1], parent, layoutName )[:len(rootSectionPath)] == rootSectionPath ]

		return [ x[1] for x in itemsAndIndices ]

	@GafferUI.LazyMethod()
	def __updateLazily( self ) :

		self.__update()

	def __update( self ) :

		if self.__layoutDirty :
			self.__updateLayout()
			self.__layoutDirty = False

		if self.__activationsDirty :
			self.__updateActivations()
			self.__activationsDirty = False

		if self.__summariesDirty :
			self.__updateSummariesWalk( self.__rootSection )
			self.__summariesDirty = False

		# delegate to our layout class to create a concrete
		# layout from the section definitions.

		self.__layout.update( self.__rootSection )

	def __updateLayout( self ) :

		# get the items to lay out - these are a combination
		# of plugs and strings representing custom widgets.
		items = self.layoutOrder( self.__parent, includeCustomWidgets = True, layoutName = self.__layoutName, rootSection = self.__rootSectionName )

		# ditch widgets we don't need any more

		itemsSet = set( items )
		self.__widgets = { k : v for k, v in self.__widgets.items() if k in itemsSet }

		# ditch widgets whose metadata type has changed - we must recreate these.
		self.__widgets = {
			k : v for k, v in self.__widgets.items()
			if isinstance( k, str ) or v is not None and Gaffer.Metadata.value( k, "plugValueWidget:type" ) == v.__plugValueWidgetType
		}


		# make (or reuse existing) widgets for each item, and sort them into
		# sections.
		rootSectionDepth = self.__rootSectionName.count( "." ) + 1 if self.__rootSectionName else 0
		self.__rootSection.clear()
		for item in items :

			if item not in self.__widgets :
				if isinstance( item, Gaffer.Plug ) :
					widget = self.__createPlugWidget( item )
				else :
					widget = self.__createCustomWidget( item )
				self.__widgets[item] = widget
			else :
				widget = self.__widgets[item]

			if widget is None :
				continue

			section = self.__rootSection
			for sectionName in self.__sectionPath( item )[rootSectionDepth:] :
				section = section.subsection( sectionName )

			if len( section.widgets ) and self.__itemMetadataValue( item, "accessory" ) :
				if isinstance( section.widgets[-1], _AccessoryRow ) :
					section.widgets[-1].append( widget )
				else :
					row = _AccessoryRow()
					row.append( section.widgets[-1] )
					row.append( widget )
					section.widgets[-1] = row
			else :
				section.widgets.append( widget )

			if self.__itemMetadataValue( item, "divider" ) :
				section.widgets.append( GafferUI.Divider(
					GafferUI.Divider.Orientation.Horizontal if self.__layout.orientation() == GafferUI.ListContainer.Orientation.Vertical else GafferUI.Divider.Orientation.Vertical
				) )

	def __updateActivations( self ) :

		with self.context() :
			# Must scope the context when getting activators, because they are typically
			# computed from the plug values, and may therefore trigger a compute.
			activators = self.__metadataValue( self.__parent, self.__layoutName + ":activators" ) or {}

		activators = { k : v.value for k, v in activators.items() } # convert CompoundData of BoolData to dict of booleans

		def active( activatorMetadata ) :

			if activatorMetadata is None or activatorMetadata == "" :
				return True
			elif isinstance( activatorMetadata, bool ) :
				return activatorMetadata
			else :
				assert( isinstance( activatorMetadata, str ) )
				activatorName = activatorMetadata
				result = activators.get( activatorName )
				if result is None :
					with self.context() :
						metadataName = self.__layoutName + ":activator:" + activatorName
						result = self.__metadataValue( self.__parent, metadataName )
						if isinstance( result, str ) :
							localsAndGlobals = { "parent" : self.__parent }
							result = eval( result, localsAndGlobals, localsAndGlobals )
						if result is None and metadataName not in Gaffer.Metadata.registeredValues( self.__parent ) :
							IECore.msg(
								IECore.Msg.Level.Warning, "PlugLayout",
								"Activator metadata `{}` not registered".format( metadataName )
							)
					result = result if result is not None else False
					activators[activatorName] = result

				return result

		for item, widget in self.__widgets.items() :
			if widget is not None :
				widget.setEnabled( active( self.__itemMetadataValue( item, "activator" ) ) )
				widget.setVisible( active( self.__itemMetadataValue( item, "visibilityActivator" ) ) )

	def __updateSummariesWalk( self, section ) :

		with self.context() :
			# Must scope the context because summaries are typically
			# generated from plug values, and may therefore trigger
			# a compute.
			try :
				section.summary = self.__metadataValue( self.__parent, self.__layoutName + ":section:" + section.fullName + ":summary" ) or ""
			except Gaffer.ProcessException :
				section.summary = "<img src={}>".format( Gaffer.rootPath() / "graphics" / "errorSmall.png" )

		section.valuesChanged = False

		for subsection in section.subsections.values() :
			self.__updateSummariesWalk( subsection )
			# If one of our subsections has changed, we don't need to
			# check any of our own plugs, we just propagate the flag.
			if subsection.valuesChanged :
				section.valuesChanged = True

		if not section.valuesChanged :
			# Check our own widgets, this is a little icky, the alternative
			# would be to iterate our items, reverse engineer the section
			# then update that, but this allows us to early-out much sooner.
			for widget in section.widgets :
				if self.__widgetPlugValuesChanged( widget ) :
					section.valuesChanged = True
					break

	@staticmethod
	def __widgetPlugValuesChanged( widget ) :

		plugs = []
		if isinstance( widget, GafferUI.PlugWidget ) :
			widget = widget.plugValueWidget()
		if hasattr( widget, 'getPlugs' ) :
			plugs = widget.getPlugs()

		return any( GafferUI.LabelPlugValueWidget._hasUserValue( p ) for p in plugs )

	def __import( self, path ) :

		path = path.split( "." )
		result = __import__( path[0] )
		for n in path[1:] :
			result = getattr( result, n )

		return result

	def __createPlugWidget( self, plug ) :

		result = GafferUI.PlugValueWidget.create( plug )
		if result is None :
			return result

		width = self.__itemMetadataValue( plug, "width" )
		if width is not None :
			result._qtWidget().setFixedWidth( width )

		minimumWidth = self.__itemMetadataValue( plug, "minimumWidth" )
		if minimumWidth is not None :
			result._qtWidget().setMinimumWidth( minimumWidth )

		if result._qtWidget().layout() is not None and ( width is not None or minimumWidth is not None ) :
			result._qtWidget().layout().setSizeConstraint( QtWidgets.QLayout.SetDefaultConstraint )

		if isinstance( result, GafferUI.PlugValueWidget ) and not result.hasLabel() and self.__itemMetadataValue( plug, "label" ) != "" :
			result = GafferUI.PlugWidget( result )
			if self.__layout.orientation() == GafferUI.ListContainer.Orientation.Horizontal :
				# undo the annoying fixed size the PlugWidget has applied
				# to the label.
				## \todo Shift all the label size fixing out of PlugWidget and just fix the
				# widget here if we're in a vertical orientation.
				QWIDGETSIZE_MAX = 16777215 # qt #define not exposed by PyQt or PySide
				result.labelPlugValueWidget().label()._qtWidget().setFixedWidth( QWIDGETSIZE_MAX )

		# Store the metadata value that controlled the type created, so we can compare to it
		# in the future to determine if we can reuse the widget.
		result.__plugValueWidgetType = Gaffer.Metadata.value( plug, "plugValueWidget:type" )

		return result

	def __createCustomWidget( self, name ) :

		widgetType = self.__itemMetadataValue( name, "widgetType" )
		widgetClass = self.__import( widgetType )

		result = widgetClass( self.__parent )

		return result

	def __node( self ) :

		return self.__parent if isinstance( self.__parent, Gaffer.Node ) else self.__parent.node()

	@classmethod
	def __metadataValue( cls, plugOrNode, name ) :

		return Gaffer.Metadata.value( plugOrNode, name )

	@classmethod
	def __staticItemMetadataValue( cls, item, name, parent, layoutName ) :

		if isinstance( item, Gaffer.Plug ) :
			v = Gaffer.Metadata.value( item, layoutName + ":" + name )
			if v is None and name in ( "divider", "label" ) :
				# Backwards compatibility with old unprefixed metadata names.
				v = Gaffer.Metadata.value( item, name )
			return v
		else :
			return cls.__metadataValue( parent, layoutName + ":customWidget:" + item + ":" + name )

	def __itemMetadataValue( self, item, name ) :

		return self.__staticItemMetadataValue( item, name, parent = self.__parent, layoutName = self.__layoutName )

	@classmethod
	def __staticSectionPath( cls, item, parent, layoutName ) :

		m = None
		if isinstance( parent, Gaffer.Node ) :
			# Backwards compatibility with old metadata entry
			## \todo Remove
			m = cls.__staticItemMetadataValue( item, "nodeUI:section", parent, layoutName )
			if m == "header" :
				m = ""

		if m is None :
			m = cls.__staticItemMetadataValue( item, "section", parent, layoutName )

		return m.split( "." ) if m else []

	def __sectionPath( self, item ) :

		return self.__staticSectionPath( item, parent = self.__parent, layoutName = self.__layoutName )

	def __childAddedOrRemoved( self, *unusedArgs ) :

		# typically many children are added and removed at once, so
		# we do a lazy update so we can batch up several changes into one.
		# upheaval is over.
		self.__layoutDirty = True
		self.__updateLazily()

	def __plugMetadataChanged( self, plug, key, reason ) :

		if plug.parent() == self.__parent :
			if key in (
				"divider",
				self.__layoutName + ":divider",
				self.__layoutName + ":index",
				self.__layoutName + ":section",
				self.__layoutName + ":accessory",
				"plugValueWidget:type"
			) :
				# We often see sequences of several metadata changes, so
				# we schedule a lazy update to batch them into one UI update.
				self.__layoutDirty = True
				self.__updateLazily()
		elif plug == self.__parent :
			self.__parentMetadataChanged( key )

	def __nodeMetadataChanged( self, node, key, reason ) :

		assert( node == self.__parent )
		self.__parentMetadataChanged( key )

	def __parentMetadataChanged( self, key ) :

		if re.match( self.__layoutName + ":section:.*:summary", key ) :
			self.__summariesDirty = True
			self.__updateLazily()
		elif re.match( self.__layoutName + ":customWidget:.*", key ) :
			self.__layoutDirty = True
			self.__updateLazily()

	def __plugDirtied( self, plug ) :

		if plug.direction() != plug.Direction.In :
			return

		self.__activationsDirty = True
		self.__summariesDirty = True
		self.__updateLazily()

	def __contextChanged( self, context, name ) :

		self.__activationsDirty = True
		self.__summariesDirty = True
		self.__updateLazily()


class _AccessoryRow( GafferUI.ListContainer ) :

	def __init__( self, **kw ) :

		GafferUI.ListContainer.__init__( self, GafferUI.ListContainer.Orientation.Horizontal, spacing = 4, **kw )

# The _Section class provides a simple abstract representation of a hierarchical
# layout. Each section contains a list of widgets to be displayed in that section,
# and an OrderedDict of named subsections.
class _Section( object ) :

	def __init__( self, _parent, _fullName = "" ) :

		self.__parent = _parent
		self.fullName = _fullName

		self.clear()

	def subsection( self, name ) :

		result = self.subsections.get( name )
		if result is not None :
			return result

		result = _Section(
			self.__parent,
			self.fullName + "." + name if self.fullName else name
		)

		self.subsections[name] = result
		return result

	def clear( self ) :

		self.widgets = []
		self.subsections = collections.OrderedDict()
		self.summary = ""
		self.valuesChanged = False

	def saveState( self, name, value ) :

		Gaffer.Metadata.registerValue( self.__parent, self.__stateName( name ), value, persistent = False )

	def restoreState( self, name ) :

		return Gaffer.Metadata.value( self.__parent, self.__stateName( name ) )

	def __stateName( self, name ) :

		return "layout:section:" + self.fullName + ":" + name

# The PlugLayout class deals with all the details of plugs, metadata and
# signals to define an abstract layout in terms of _Sections. It then
# delegates to the _Layout classes to create an actual layout in terms
# of Widgets. This allows us to present different layouts based on whether
# or the parent is a node (tabbed layout) or a plug (collapsible layout).
class _Layout( GafferUI.Widget ) :

	def __init__( self, topLevelWidget, orientation, **kw ) :

		GafferUI.Widget.__init__( self, topLevelWidget, **kw )

		self.__orientation = orientation

	def orientation( self ) :

		return self.__orientation

	# Returns `True` if the layout contains any visible widgets,
	# `False` otherwise.
	def update( self, section ) :

		raise NotImplementedError

class _TabLayout( _Layout ) :

	def __init__( self, orientation, embedded = False, **kw ) :

		self.__embedded = embedded

		self.__mainColumn = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )

		_Layout.__init__( self, self.__mainColumn, orientation, **kw )

		with self.__mainColumn :
			self.__widgetsColumn = GafferUI.ListContainer( self.orientation(), spacing = 4, borderWidth = 4 )
			self.__tabbedContainer = GafferUI.TabbedContainer()
			# if the TabLayout is embedded, we want to restrict the maximum width/height depending on the orientation
			if self.__embedded :
				if self.orientation() == GafferUI.ListContainer.Orientation.Vertical :
					self.__tabbedContainer._qtWidget().setSizePolicy( QtWidgets.QSizePolicy( QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum ) )
				else :
					self.__tabbedContainer._qtWidget().setSizePolicy( QtWidgets.QSizePolicy( QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Expanding ) )

		self.__currentTabChangedConnection = self.__tabbedContainer.currentChangedSignal().connect(
			Gaffer.WeakMethod( self.__currentTabChanged ),
			scoped = False
		)

	def update( self, section ) :

		self.__section = section
		self.__widgetsColumn[:] = section.widgets

		existingTabs = collections.OrderedDict()
		for tab in self.__tabbedContainer[:] :
			existingTabs[self.__tabbedContainer.getLabel( tab )] = tab

		updatedTabs = collections.OrderedDict()
		updatedTabVisibilities = []
		for name, subsection in section.subsections.items() :
			tab = existingTabs.get( name )
			if tab is None :
				# Use scroll bars only when the TabLayout is not embedded
				if self.__embedded :
					tab = GafferUI.Frame( borderWidth = 0, borderStyle = GafferUI.Frame.BorderStyle.None_ )
				else :
					tab = GafferUI.ScrolledContainer( borderWidth = 8 )
					if self.orientation() == GafferUI.ListContainer.Orientation.Vertical :
						tab.setHorizontalMode( GafferUI.ScrollMode.Never )
					else :
						tab.setVerticalMode( GafferUI.ScrollMode.Never )

				tab.setChild( _CollapsibleLayout( self.orientation() ) )
			updatedTabVisibilities.append( tab.getChild().update( subsection ) )
			updatedTabs[name] = tab

		if existingTabs.keys() != updatedTabs.keys() :
			with Gaffer.Signals.BlockedConnection( self.__currentTabChangedConnection ) :
				del self.__tabbedContainer[:]
				for name, tab in updatedTabs.items() :
					self.__tabbedContainer.append( tab, label = name )

		for index, subsection in enumerate( section.subsections.values() ) :
			self.__tabbedContainer.setTabVisible( self.__tabbedContainer[index], updatedTabVisibilities[index] )
			## \todo Consider how/if we should add a public tooltip API to TabbedContainer.
			self.__tabbedContainer._qtWidget().setTabToolTip( index, subsection.summary )

		if not len( existingTabs ) :
			currentTabIndex = self.__section.restoreState( "currentTab" ) or 0
			if currentTabIndex < len( self.__tabbedContainer ) :
				self.__tabbedContainer.setCurrent( self.__tabbedContainer[currentTabIndex] )

		haveVisibleWidgets = any( w.getVisible() for w in self.__widgetsColumn )
		haveVisibleTabs = any( self.__tabbedContainer.getTabVisible( t ) for t in self.__tabbedContainer )

		self.__widgetsColumn.setVisible( haveVisibleWidgets )
		self.__tabbedContainer.setVisible( haveVisibleTabs )

		return haveVisibleWidgets or haveVisibleTabs

	def __currentTabChanged( self, tabbedContainer, currentTab ) :

		self.__section.saveState( "currentTab", tabbedContainer.index( currentTab ) )

class _CollapsibleLayout( _Layout ) :

	def __init__( self, orientation, **kw ) :

		self.__column = GafferUI.ListContainer( orientation, spacing = 4 )

		_Layout.__init__( self, self.__column, orientation, **kw )

		self.__collapsibles = {} # Indexed by section name

	def update( self, section ) :

		widgets = list( section.widgets )

		for name, subsection in section.subsections.items() :

			collapsible = self.__collapsibles.get( name )
			if collapsible is None :

				collapsible = GafferUI.Collapsible( name, _CollapsibleLayout( self.orientation() ), collapsed = True )
				# Hack to add margins at the top and bottom but not at the sides.
				## \todo This is exposed in the public API via the borderWidth
				# parameter to the Collapsible. That parameter sucks because a) it
				# makes a margin rather than a border, and b) it doesn't allow per-edge
				# control. Either make that make sense, or remove it and find a way
				# of deferring all this to the style.
				collapsible._qtWidget().layout().setContentsMargins( 0, 2, 0, 2 )

				collapsible.setCornerWidget( GafferUI.Label(), True )
				## \todo This is fighting the default sizing applied in the Label constructor. Really we need a standard
				# way of controlling size behaviours for all widgets in the public API.
				collapsible.getCornerWidget()._qtWidget().setSizePolicy( QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed )

				if subsection.restoreState( "collapsed" ) is False :
					collapsible.setCollapsed( False )

				collapsible.stateChangedSignal().connect(
					functools.partial( Gaffer.WeakMethod( self.__collapsibleStateChanged ), subsection = subsection ),
					scoped = False
				)

				self.__collapsibles[name] = collapsible

			collapsible.setVisible(
				collapsible.getChild().update( subsection )
			)

			collapsible.getCornerWidget().setText(
				"<small>" + "&nbsp;( " + subsection.summary + " )</small>" if subsection.summary else ""
			)

			currentValueChanged = collapsible._qtWidget().property( "gafferValueChanged" )
			if subsection.valuesChanged != currentValueChanged :
				collapsible._qtWidget().setProperty( "gafferValueChanged", GafferUI._Variant.toVariant( subsection.valuesChanged ) )
				collapsible._repolish()

			widgets.append( collapsible )

		self.__column[:] = widgets

		return any( w.getVisible() for w in self.__column )

	def __collapsibleStateChanged( self, collapsible, subsection ) :

		subsection.saveState( "collapsed", collapsible.getCollapsed() )

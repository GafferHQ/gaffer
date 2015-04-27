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

import collections

import Gaffer
import GafferUI

## A class for laying out widgets to represent all the plugs held on a particular parent.
#
# Supported metadata :
#
#	- "layout:index" controls ordering of plugs within the layout
#	- "layout:section" places the plug in a named section of the layout
#	- "divider" specifies whether or not a plug should be followed by a divider
#	- "layout:widgetType" the class name for the widget type of a particular plug
#
class PlugLayout( GafferUI.Widget ) :

	def __init__( self, parent, orientation = GafferUI.ListContainer.Orientation.Vertical, **kw ) :

		assert( isinstance( parent, ( Gaffer.Node, Gaffer.Plug ) ) )

		self.__layout = _TabLayout( orientation ) if isinstance( parent, Gaffer.Node ) else _CollapsibleLayout( orientation )

		GafferUI.Widget.__init__( self, self.__layout, **kw )

		self.__parent = parent
		self.__readOnly = False

		# we need to connect to the childAdded/childRemoved signals on
		# the parent so we can update the ui when plugs are added and removed.
		self.__childAddedConnection = parent.childAddedSignal().connect( Gaffer.WeakMethod( self.__childAddedOrRemoved ) )
 		self.__childRemovedConnection = parent.childRemovedSignal().connect( Gaffer.WeakMethod( self.__childAddedOrRemoved ) )

		# building plug uis can be very expensive, and often we're initially hidden in a non-current tab
		# or a collapsed section. so we defer our building until we become visible to avoid unnecessary overhead.
		self.__visibilityChangedConnection = self.visibilityChangedSignal().connect( Gaffer.WeakMethod( self.__visibilityChanged ) )

		# since our layout is driven by metadata, we must respond dynamically
		# to changes in that metadata.
		self.__metadataChangedConnection = Gaffer.Metadata.plugValueChangedSignal().connect( Gaffer.WeakMethod( self.__plugMetadataChanged ) )

		# frequently events that trigger a ui update come in batches, so we
		# only perform the update on idle events to avoid unnecessary
		# repeated updates. this variable tracks whether or not such an update is
		# scheduled.
		self.__updatePending = False

		self.__plugsToWidgets = {} # mapping from child plug to widget

	def getReadOnly( self ) :

		return self.__readOnly

	def setReadOnly( self, readOnly ) :

 		if readOnly == self.getReadOnly() :
 			return

 		self.__readOnly = readOnly
 		for widget in self.__plugsToWidgets.values() :
			self.__applyReadOnly( widget )

	## Returns a PlugValueWidget representing the specified child plug.
	# Because the layout is built lazily on demand, this might return None due
	# to the user not having opened up the ui - in this case lazy=False may
	# be passed to force the creation of the ui.
	def plugValueWidget( self, childPlug, lazy=True ) :

		if not lazy and len( self.__plugsToWidgets ) == 0 :
			self.__update()

		w = self.__plugsToWidgets.get( childPlug, None )
		if w is None :
			return w
		elif isinstance( w, GafferUI.PlugValueWidget ) :
			return w
		else :
			return w.plugValueWidget()

	## Takes a list of plugs and returns a new list, sorted into
	# the order in which they'll be laid out, based on "layout:index"
	# Metadata entries.
	@staticmethod
	def layoutOrder( plugs ) :

		plugsAndIndices = [ list( x ) for x in enumerate( plugs ) ]
		for plugAndIndex in plugsAndIndices :
			index = Gaffer.Metadata.plugValue( plugAndIndex[1], "layout:index" )
			if index is not None :
				plugAndIndex[0] = index

		plugsAndIndices.sort( key = lambda x : x[0] )

		return [ x[1] for x in plugsAndIndices ]

	def __update( self ) :

		# get the plugs we want to represent
		plugs = self.__parent.children( Gaffer.Plug )
		plugs = [ plug for plug in plugs if not plug.getName().startswith( "__" ) ]

		# reorder them based on metadata
		plugs = self.layoutOrder( plugs )

		# ditch widgets we don't need any more
		plugsSet = set( plugs )
		self.__plugsToWidgets = dict(
			( plug, widget ) for plug, widget in self.__plugsToWidgets.items() if plug in plugsSet
		)

		# make (or reuse existing) widgets for each plug, and sort them into
		# sections.
		rootSection = _Section()
		for plug in plugs :

			if plug not in self.__plugsToWidgets :
				widget = self.__createPlugWidget( plug )
				self.__plugsToWidgets[plug] = widget
			else :
				widget = self.__plugsToWidgets[plug]

			if widget is None :
				continue

			section = rootSection
			for sectionName in self.__sectionPath( plug ) :
				section = section.subsections.setdefault( sectionName, _Section() )

			section.widgets.append( widget )

			if Gaffer.Metadata.plugValue( plug, "divider" ) :
				section.widgets.append( GafferUI.Divider(
					GafferUI.Divider.Orientation.Horizontal if self.__layout.orientation() == GafferUI.ListContainer.Orientation.Vertical else GafferUI.Divider.Orientation.Vertical
				) )

		# delegate to our layout class to create a concrete
		# layout from the section definitions.
		self.__layout.update( rootSection )

 	def __createPlugWidget( self, plug ) :

		widgetType = Gaffer.Metadata.plugValue( plug, "layout:widgetType" )
		if widgetType is not None :

			if widgetType == "None" :
				return None
			else :
				widgetType = widgetType.split( "." )
				widgetClass = __import__( widgetType[0] )
				for n in widgetType[1:] :
					widgetClass = getattr( widgetClass, n )
				result = widgetClass( plug )

		else :

			result = GafferUI.PlugValueWidget.create( plug )
			if result is None :
				return result

 		if not result.hasLabel() and Gaffer.Metadata.plugValue( plug, "label" ) != "" :
 			result = GafferUI.PlugWidget( result )
			if self.__layout.orientation() == GafferUI.ListContainer.Orientation.Horizontal :
				# undo the annoying fixed size the PlugWidget has applied
				# to the label.
				## \todo Shift all the label size fixing out of PlugWidget and just fix the
				# widget here if we're in a vertical orientation.
				QWIDGETSIZE_MAX = 16777215 # qt #define not exposed by PyQt or PySide
				result.labelPlugValueWidget().label()._qtWidget().setFixedWidth( QWIDGETSIZE_MAX )

		self.__applyReadOnly( result )

 		return result

	def __sectionPath( self, plug ) :

		m = None
		if isinstance( self.__parent, Gaffer.Node ) :
			# Backwards compatibility with old metadata entry
			## \todo Remove
			m = Gaffer.Metadata.plugValue( plug, "nodeUI:section" )
			if m == "header" :
				m = ""

		if m is None :
			m = Gaffer.Metadata.plugValue( plug, "layout:section" )

		return m.split( "." ) if m else []

	def __visibilityChanged( self, widget ) :

		assert( widget is self )
		if self.visible() :
			self.__update()
			del self.__visibilityChangedConnection # only need to build once

	def __childAddedOrRemoved( self, *unusedArgs ) :

		if not self.visible() :
			return

		# typically many children are added and removed at once. we don't
		# want to be rebuilding the ui for each individual event, so we
		# add an idle callback to do the rebuild once the
		# upheaval is over.
		self.__scheduleUpdate()

	def __scheduleUpdate( self ) :

		if self.__updatePending :
			return

		GafferUI.EventLoop.addIdleCallback( Gaffer.WeakMethod( self.__idleUpdate, fallbackResult=False ) )
		self.__updatePending = True

	def __idleUpdate( self ) :

		self.__update()
		self.__updatePending = False

		return False # removes the callback

	def __applyReadOnly( self, widget ) :

		if widget is None :
			return

		if isinstance( widget, GafferUI.PlugValueWidget ) :
			widget.setReadOnly( self.getReadOnly() )
		elif isinstance(  widget, GafferUI.PlugWidget ) :
			widget.labelPlugValueWidget().setReadOnly( self.getReadOnly() )
			widget.plugValueWidget().setReadOnly( self.getReadOnly() )
		else :
			widget.plugValueWidget().setReadOnly( self.getReadOnly() )

	def __plugMetadataChanged( self, nodeTypeId, plugPath, key ) :

		if not self.visible() :
			return

		node = self.__parent if isinstance( self.__parent, Gaffer.Node ) else self.__parent.node()
		if not node.isInstanceOf( node.typeId() ) :
			return

		if key in ( "divider", "layout:index", "layout:section" ) :
			# we often see sequences of several metadata changes - so
			# we schedule an update on idle to batch them into one ui update.
			self.__scheduleUpdate()

# The _Section class provides a simple abstract representation of a hierarchical
# layout. Each section contains a list of widgets, and an OrderedDict of named
# subsections.
class _Section( object ) :

	def __init__( self ) :

		self.widgets = []
		self.subsections = collections.OrderedDict()

# The PlugLayout class deals with all the details of plugs, metadata and
# signals to define an abstract layout in terms of _Sections. It then
# delegates to the _Layout classes to create an actual layout.
class _Layout( GafferUI.Widget ) :

	def __init__( self, topLevelWidget, orientation, **kw ) :

		GafferUI.Widget.__init__( self, topLevelWidget, **kw )

		self.__orientation = orientation

	def orientation( self ) :

		return self.__orientation

	def update( self, section ) :

		raise NotImplementedError

class _TabLayout( _Layout ) :

	def __init__( self, orientation, **kw ) :

		self.__mainColumn = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )

		_Layout.__init__( self, self.__mainColumn, orientation, **kw )

		with self.__mainColumn :
			self.__widgetsColumn = GafferUI.ListContainer( self.orientation(), spacing = 4, borderWidth = 4 )
			self.__tabbedContainer = GafferUI.TabbedContainer()

	def update( self, section ) :

		self.__widgetsColumn[:] = section.widgets

		existingTabs = collections.OrderedDict()
		for tab in self.__tabbedContainer[:] :
			existingTabs[self.__tabbedContainer.getLabel( tab )] = tab

		updatedTabs = collections.OrderedDict()
		for name, subsection in section.subsections.items() :
			tab = existingTabs.get( name )
			if tab is None :
				tab = GafferUI.ScrolledContainer( borderWidth = 8 )
				if self.orientation() == GafferUI.ListContainer.Orientation.Vertical :
					tab.setHorizontalMode( GafferUI.ScrolledContainer.ScrollMode.Never )
				else :
					tab.setVerticalMode( GafferUI.ScrolledContainer.ScrollMode.Never )
				tab.setChild( _CollapsibleLayout( self.orientation() ) )
			tab.getChild().update( subsection )
			updatedTabs[name] = tab

		if existingTabs.keys() != updatedTabs.keys() :
			del self.__tabbedContainer[:]
			for name, tab in updatedTabs.items() :
				self.__tabbedContainer.append( tab, label = name )

		self.__widgetsColumn.setVisible( len( section.widgets ) )
		self.__tabbedContainer.setVisible( len( self.__tabbedContainer ) )

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
				collapsible = GafferUI.Collapsible( name, _CollapsibleLayout( self.orientation() ), borderWidth = 2, collapsed = True )
				self.__collapsibles[name] = collapsible
			collapsible.getChild().update( subsection )
			widgets.append( collapsible )

		self.__column[:] = widgets

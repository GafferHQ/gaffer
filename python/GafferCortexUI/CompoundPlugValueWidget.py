##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferUI

from Qt import QtWidgets

# This was the predecessor to the far superior GafferUI.PlugLayout
# class that we now use. It survives here as a relic because it is
# still relied upon by CompoundParameterValueWidget and
# ClassVectorParameterValueWidget. Do not use it for anything else!
class CompoundPlugValueWidget( GafferUI.PlugValueWidget ) :

	## Possible values for collapsed are :
	#
	#	True  : use Collapsible container which starts off collapsed
	#	False : use Collapsible container which starts off opened
	#	None  : don't use Collapsible container
	#
	# Note that the True/False values for collapsible just set the initial state -
	# after this the current state is stored for the session on a per-node basis
	# for user convenience.
	#
	# If summary is specified it will be called each time a child plug changes value,
	# and the result used to provide a summary in the collapsible header.
	def __init__( self, plug, collapsed=True, label=None, summary=None, **kw ) :

		self.__column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4 )
		self.__label = label if label else IECore.CamelCase.toSpaced( plug.getName() )

		self.__collapsible = None
		if collapsed is not None :
			self.__collapsible = GafferUI.Collapsible(
				self.__label,
				collapsed = self.__getStoredCollapseState( plug, collapsed ),
			)
			self.__collapsible.setChild( self.__column )
			self.__collapsible.setCornerWidget( GafferUI.Label(), True )
			## \todo This is fighting the default sizing applied in the Label constructor. Really we need a standard
			# way of controlling size behaviours for all widgets in the public API.
			self.__collapsible.getCornerWidget()._qtWidget().setSizePolicy( QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed )
			self.__collapseStateChangedConnection = self.__collapsible.stateChangedSignal().connect( Gaffer.WeakMethod( self.__collapseStateChanged ), scoped = True )

		GafferUI.PlugValueWidget.__init__(
			self,
			self.__collapsible if self.__collapsible is not None else self.__column,
			plug,
			**kw
		)

		self.__plugAddedConnection = plug.childAddedSignal().connect( Gaffer.WeakMethod( self.__childAddedOrRemoved ), scoped = True )
		self.__plugRemovedConnection = plug.childRemovedSignal().connect( Gaffer.WeakMethod( self.__childAddedOrRemoved ), scoped = True )
		self.__childrenChangedPending = False

		# arrange to build the rest of the ui in a deferred fashion. this means that we will be
		# fully constructed when we call _childPlugWidget etc, rather than expecting derived
		# class' implementations to work even before their constructor has completed.
		# it also means we don't pay the cost of building huge uis upfront, and rather do it incrementally
		# as the user opens up sections. for non-collapsed uis, we build when a parent is received, which
		# allows the top level window to get the sizing right, and for collapsed uis we build when the
		# the ui first becomes visible due to being opened.
		if collapsed == True :
			self.__visibilityChangedConnection = self.__column.visibilityChangedSignal().connect( Gaffer.WeakMethod( self.__visibilityChanged ), scoped = True )
		else :
			self.__parentChangedConnection = self.parentChangedSignal().connect( Gaffer.WeakMethod( self.__parentChanged ), scoped = True )

		self.__visibilityChangedConnection = self.__column.visibilityChangedSignal().connect( Gaffer.WeakMethod( self.__visibilityChanged ), scoped = True )

		self.__childPlugUIs = {} # mapping from child plug to PlugWidget

		self.__summary = summary

		CompoundPlugValueWidget._updateFromPlug( self )

	## Returns a PlugValueWidget representing the specified child plug.
	def childPlugValueWidget( self, childPlug ) :

		self.__updateChildPlugUIs()

		w = self.__childPlugUIs.get( childPlug, None )
		if w is None :
			return w
		elif isinstance( w, GafferUI.PlugValueWidget ) :
			return w
		else :
			return w.plugValueWidget()

	def hasLabel( self ) :

		return True

	def _updateFromPlug( self ) :

		if self.__summary is not None and self.__collapsible is not None :
			with self.getContext() :
				s = self.__summary( self.getPlug() )
				if s :
					s = "<small>" + "&nbsp;( " + s + " ) </small>"
				self.__collapsible.getCornerWidget().setText( s )

	## May be overridden by derived classes to return a widget to be placed
	# at the top of the layout.
	def _headerWidget( self ) :

		return None

	## May be overridden by derived classes to customise the creation of widgets
	# to represent the child plugs.	The returned widget must either derive from
	# PlugValueWidget or must have a plugValueWidget() method which returns
	# a PlugValueWidget.
	def _childPlugWidget( self, childPlug ) :

		result = GafferUI.PlugValueWidget.create( childPlug )
		if isinstance( result, GafferUI.PlugValueWidget ) and not result.hasLabel() :
			result = GafferUI.PlugWidget( result )

		return result

	## May be overridden by derived classes to return a widget to be placed
	# at the bottom of the layout.
	def _footerWidget( self ) :

		return None

	## Returns the Collapsible widget used to contain the child widgets,
	# or None if this ui is not collapsible.
	def _collapsible( self ) :

		return self.__collapsible

	## May be overridden by derived classes to specify which child plugs
	# are represented and in what order.
	def _childPlugs( self ) :

		return self.getPlug().children()

	## \todo Mapping plugName->widget makes us vulnerable to name changes.
	# See similar comments in StandardNodeUI and StandardNodeToolbar.
	def __updateChildPlugUIs( self ) :

		# ditch child uis we don't need any more
		childPlugs = self._childPlugs()
		for childPlug in list( self.__childPlugUIs.keys() ) :
			if childPlug not in childPlugs :
				del self.__childPlugUIs[childPlug]

		# make (or reuse existing) uis for each child plug
		orderedChildUIs = []
		for childPlug in childPlugs :
			if childPlug.getName().startswith( "__" ) :
				continue
			if childPlug not in self.__childPlugUIs :
				widget = self._childPlugWidget( childPlug )
				assert( isinstance( widget, ( GafferUI.PlugValueWidget, type( None ) ) ) or hasattr( widget, "plugValueWidget" ) )
				self.__childPlugUIs[childPlug] = widget
			else :
				widget = self.__childPlugUIs[childPlug]
			if widget is not None :
				orderedChildUIs.append( widget )
				if Gaffer.Metadata.value( childPlug, "divider" ) :
					orderedChildUIs.append( GafferUI.Divider() )

		# add header and footer
		headerWidget = self._headerWidget()
		if headerWidget is not None :
			orderedChildUIs.insert( 0, headerWidget )
		footerWidget = self._footerWidget()
		if footerWidget is not None :
			orderedChildUIs.append( footerWidget )

		# and update the column to display them
		self.__column[:] = orderedChildUIs

	def __visibilityChanged( self, column ) :

		assert( column is self.__column )

		if self.__column.visible() :
			self.__updateChildPlugUIs()
			self.__visibilityChangedConnection = None # only need to build once

	def __parentChanged( self, widget ) :

		assert( widget is self )

		if not len( self.__column ) :
			self.__updateChildPlugUIs()
			self.__parentChangedConnection = None # only need to build once

	def __childAddedOrRemoved( self, *unusedArgs ) :

		# typically many children are added and removed at once. we don't
		# want to be rebuilding the ui for each individual event, so we
		# add an idle callback to do the rebuild once the
		# upheaval is over.

		if not self.__childrenChangedPending :
			GafferUI.EventLoop.addIdleCallback( self.__childrenChanged )
			self.__childrenChangedPending = True

	def __childrenChanged( self ) :

		if not self.__column.visible() :
			return

		self.__updateChildPlugUIs()
		self.__childrenChangedPending = False

		return False # removes the callback

	def __collapseStateChanged( self, widget ) :

		assert( widget is self.__collapsible )
		self.__setStoredCollapseState( self.getPlug(), widget.getCollapsed() )

	def __setStoredCollapseState( self, plug, collapsed ) :

		node = plug.node()
		if "__uiCollapsed" in node :
			storagePlug = node["__uiCollapsed"]
		else :
			storagePlug = Gaffer.ObjectPlug(
				defaultValue = IECore.CompoundData(),
				flags = Gaffer.Plug.Flags.Default & ~Gaffer.Plug.Flags.Serialisable,
			)
			node["__uiCollapsed"] = storagePlug

		storage = storagePlug.getValue()
		# we use the label in the key so that SectionedPlugValueWidgets and the like
		# store a state per section.
		key = plug.relativeName( node ) + "|" + self.__label
		storage[key] = IECore.BoolData( collapsed )
		storagePlug.setValue( storage )

	def __getStoredCollapseState( self, plug, default ) :

		node = plug.node()
		if "__uiCollapsed" not in node :
			return default

		storagePlug = node["__uiCollapsed"]
		storage = storagePlug.getValue()
		key = plug.relativeName( node ) + "|" + self.__label
		value = storage.get( key )
		if value is None :
			return default

		return value.value

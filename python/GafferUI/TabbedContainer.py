##########################################################################
#
#  Copyright (c) 2011-2013, John Haddon. All rights reserved.
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

import functools

import IECore

import Gaffer
import GafferUI

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

class TabbedContainer( GafferUI.ContainerWidget ) :

	__DragState = IECore.Enum.create( "None_", "Waiting", "Active" )
	__palette = None

	def __init__( self, cornerWidget=None, **kw ) :

		GafferUI.ContainerWidget.__init__( self, _TabWidget(), **kw )

		# Tab bar
		# -------

		self.__tabBar = GafferUI.Widget( QtWidgets.QTabBar() )
		self.__tabBar._qtWidget().setDrawBase( False )
		self.__tabBar._qtWidget().tabMoved.connect( Gaffer.WeakMethod( self.__moveWidget ) )
		self.__tabBar.dragEnterSignal().connect( Gaffer.WeakMethod( self.__tabBarDragEnter ), scoped = False )
		self.__tabBar.dragMoveSignal().connect( Gaffer.WeakMethod( self.__tabBarDragMove ), scoped = False )
		self.__tabBar.dragLeaveSignal().connect( Gaffer.WeakMethod( self.__tabBarDragLeave ), scoped = False )
		self.__tabBarDragState = self.__DragState.None_

		# See comments in Button.py
		if TabbedContainer.__palette is None :
			TabbedContainer.__palette = QtGui.QPalette( QtWidgets.QApplication.instance().palette( self.__tabBar._qtWidget() ) )
			TabbedContainer.__palette.setColor( QtGui.QPalette.Disabled, QtGui.QPalette.Light, QtGui.QColor( 0, 0, 0, 0 ) )

		self.__tabBar._qtWidget().setPalette( TabbedContainer.__palette )

		self._qtWidget().setTabBar( self.__tabBar._qtWidget() )
		self._qtWidget().setElideMode( QtCore.Qt.ElideNone )

		# Corner widget and scrolling
		# ---------------------------
		#
		# QTabBar does provide scroll buttons for use when there is not enough
		# horizontal space to show all tabs. But these are really awkward to use
		# : you may not know which way to scroll, it may take several clicks to
		# find the thing you want, and it's hard to track the jumpy movement of
		# the tabs. Instead we provide a dropdown menu which provides an
		# overview of all tabs and allows you to jump to the right one with a
		# single click. This is stored in `self.__cornerContainer[0]`, alongside
		# an optional user-provided corner widget which is stored in
		# `self.__cornerContainer[1]`.

		self.__cornerContainer = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )
		with self.__cornerContainer :
			GafferUI.MenuButton(
				image = "tabScrollMenu.png", hasFrame = False,
				menu = GafferUI.Menu( Gaffer.WeakMethod( self.__scrollMenuDefinition ) )
			)
		self._qtWidget().setCornerWidget( self.__cornerContainer._qtWidget() )
		self.setCornerWidget( cornerWidget )

		# When there's not enough horizontal space, we need QTabWidget to scroll
		# to show the current tab. But `QTabBarPrivate::makeVisible()` refuses
		# to do this unless the scroll buttons are visible. So we have to
		# pretend to be using them and then use the stylesheet to set their size to
		# 0. One benefit of this hack is that we can track the show/hide events
		# for the buttons so that we only show our menu button when scrolling
		# is necessary. This is a bit more reliable than trying to do it ourselves
		# using resize events and size queries.

		self._qtWidget().setUsesScrollButtons( True )
		assert( len( self._qtWidget().tabBar().children() ) == 2 ) # We expect a left and a right button
		_VisibilityLink(
			self._qtWidget().tabBar().children()[0],
			self.__cornerContainer[0]._qtWidget()
		)

		# Child storage and signals
		# -------------------------

		self.__widgets = []
		self.__currentChangedSignal = GafferUI.WidgetEventSignal()
		self._qtWidget().currentChanged.connect( Gaffer.WeakMethod( self.__currentChanged ) )

	def append( self, child, label="" ) :

		oldParent = child.parent()
		if oldParent is not None :
			oldParent.removeChild( child )

		self.__widgets.append( child )
		self._qtWidget().addTab( child._qtWidget(), label )

		# note that we are deliberately not calling child._applyVisibility(),
		# because the tabbed container operates by managing the visibility
		# of the children itself - interfering with that would cause all manner
		# of graphical glitches.

	def remove( self,  child ) :

		self.removeChild( child )

	def insert( self, index, child, label="" ) :

		l = len( self.__widgets )
		if index > l :
			index = l

		oldParent = child.parent()
		if oldParent is not None :
			oldParent.removeChild( child )

		self.__widgets.insert( index, child )
		self._qtWidget().insertTab( index, child._qtWidget(), label )

	def setLabel( self, child, labelText ) :

		self._qtWidget().setTabText( self.__widgets.index( child ), labelText )

	def getLabel( self, child ) :

		return str( self._qtWidget().tabText( self.__widgets.index( child ) ) )

	def setCurrent( self, child ) :

		self._qtWidget().setCurrentIndex( self.__widgets.index( child ) )

	def getCurrent( self ) :

		if not self.__widgets :
			return None

		return self.__widgets[ self._qtWidget().currentIndex() ]

	def __moveWidget( self, fromIndex, toIndex ) :

		w = self.__widgets[ fromIndex ]
		del self.__widgets[ fromIndex ]
		self.__widgets.insert( toIndex, w )

	def __getitem__( self, index ) :

		return self.__widgets[index]

	def __delitem__( self, index ) :

		if isinstance( index, slice ) :
			indices = range( *(index.indices( len( self ) ) ) )
			for i in indices :
				self._qtWidget().removeTab( self._qtWidget().indexOf( self[i]._qtWidget() ) )
				self[i]._qtWidget().setParent( None )
				self[i]._applyVisibility()
			del self.__widgets[index]
		else :
			self.removeChild( self.__widgets[index] )

	def __len__( self ) :

		return len( self.__widgets )

	def index( self, child ) :

		return self.__widgets.index( child )

	def addChild( self, child, label="" ) :

		self.append( child, label )

	def removeChild( self, child ) :

		if child is self.getCornerWidget() :
			self.setCornerWidget( None )
		else :
			assert( child in self.__widgets )
			# We must remove the child from __widgets before the tab, otherwise
			# currentChangedSignal will be emit with the old widget.
			removalIndex = self.__widgets.index( child )
			self.__widgets.remove( child )
			self._qtWidget().removeTab( removalIndex )

			child._qtWidget().setParent( None )
			child._applyVisibility()

	def setCornerWidget( self, cornerWidget ) :

		if len( self.__cornerContainer ) > 1 :
			del self.__cornerContainer[1]

		if cornerWidget is not None :
			oldParent = cornerWidget.parent()
			if oldParent is not None :
				oldParent.removeChild( cornerWidget )
			assert( len( self.__cornerContainer ) == 1 )
			self.__cornerContainer.append( cornerWidget )

	def getCornerWidget( self ) :

		return self.__cornerContainer[1] if len( self.__cornerContainer ) > 1 else None

	## If the tabs are hidden, then the corner widget will
	# also be hidden.
	def setTabsVisible( self, visible ) :

		self._qtWidget().tabBar().setVisible( visible )
		self.__cornerContainer.setVisible( visible )

	def getTabsVisible( self ) :

		return not self._qtWidget().tabBar().isHidden()

	def currentChangedSignal( self ) :

		return self.__currentChangedSignal

	def _revealDescendant( self, descendant ) :

		child = None
		while descendant is not None :
			parent = descendant.parent()
			if parent is self :
				child = descendant
				break
			descendant = parent

		if child is not None :
			self.setCurrent( child )

	def __currentChanged( self, index ) :

		current = self[index] if len(self) else None
		self.__currentChangedSignal( self, current )

	def __tabBarDragEnter( self, widget, event ) :

		if isinstance( event.data, IECore.NullObject ) :
			return False

		# we delay the tab switch a little to make sure that the user isn't just passing through
		self.__tabBarDragState = self.__DragState.Waiting
		QtCore.QTimer.singleShot( QtWidgets.QApplication.doubleClickInterval(), self.__tabBarDragActivate )
		return True

	def __tabBarDragMove( self, widget, event ) :

		if self.__tabBarDragState == self.__DragState.Active :
			self.__switchToTabUnderCursor()

	def __tabBarDragLeave( self, widget, event ) :

		self.__tabBarDragState = self.__DragState.None_
		return True

	def __tabBarDragActivate( self ) :

		if self.__tabBarDragState == self.__DragState.Waiting :
			self.__tabBarDragState = self.__DragState.Active
			self.__switchToTabUnderCursor()

	def __switchToTabUnderCursor( self ) :

		p = self.__tabBar._qtWidget().mapFromGlobal( QtGui.QCursor.pos() )
		tab = self.__tabBar._qtWidget().tabAt( p )
		if tab >= 0 :
			self._qtWidget().setCurrentIndex( tab )

	def __scrollMenuDefinition( self ) :

		result = IECore.MenuDefinition()

		current = self.getCurrent()
		for child in self :
			result.append(
				self.getLabel( child ),
				{
					"checkBox" : child is current,
					"command" : functools.partial(
						Gaffer.WeakMethod( self.__scrollTo ),
						child
					)
				}
			)

		return result

	def __scrollTo( self, child, *unused ) :

		self.setCurrent( child )

# Private implementation - a QTabWidget with custom size behaviour.
class _TabWidget( QtWidgets.QTabWidget ) :

	def __init__( self, parent = None ) :

		QtWidgets.QTabWidget.__init__( self, parent )

	# Reimplemented so that the tabs aren't taken into
	# account when they're not visible.
	def sizeHint( self ) :

		result = QtWidgets.QTabWidget.sizeHint( self )
		if self.tabBar().isHidden() :
			if self.tabPosition() in ( self.North, self.South ) :
				result.setHeight( result.height() - self.tabBar().sizeHint().height() )
			else :
				result.setWidth( result.width() - self.tabBar().sizeHint().width() )

		return result

	# Reimplemented so that the tabs aren't taken into
	# account when they're not visible.
	def minimumSizeHint( self ) :

		result = QtWidgets.QTabWidget.minimumSizeHint( self )
		if self.tabBar().isHidden() :
			if self.tabPosition() in ( self.North, self.South ) :
				result.setHeight( result.height() - self.tabBar().minimumSizeHint().height() )
			else :
				result.setWidth( result.width() - self.tabBar().minimumSizeHint().width() )

		return result

# Used to synchronise the visibility of our "scroll menu" with the visibility
# of Qt's scroll buttons.
class _VisibilityLink( QtCore.QObject ) :

	def __init__( self, sourceWidget, destinationWidget ) :

		# Parent to destination widget
		QtCore.QObject.__init__( self, destinationWidget )

		sourceWidget.installEventFilter( self )

	def eventFilter( self, qObject, qEvent ) :

		qEventType = qEvent.type()
		if qEventType == qEvent.Show or qEventType == qEvent.Hide :
			self.parent().setVisible( qObject.isVisible() )

		return False

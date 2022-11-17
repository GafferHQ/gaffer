##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

import weakref
import inspect
import warnings
import imath

import IECore

import Gaffer
import GafferUI
from ._StyleSheet import _styleSheet

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

class _WidgetMetaclass( Gaffer.Signals.Trackable.__class__ ) :

	def __call__( cls, *args, **kw ) :

		instance = type.__call__( cls, *args, **kw )
		instance._postConstructor()

		return instance

## The Widget class provides a base class for all widgets in GafferUI.
#
# When building UIs, you will typically derive from an existing Widget subclass such as Window,
# Dialogue or Editor and then populate it with other Widgets. You define behaviours by connecting
# methods of your class to event signals on your base class and child Widgets. It is
# important to avoid circular references when doing this - naively connecting a signal of your
# base class to a method on your class creates a reference cycle - although this will eventually
# be broken by the garbage collector, it may extend the lifetime of the UI beyond the appropriate
# point. To avoid this problem a simple rule of thumb is to always connect signals to Gaffer.WeakMethod
# instances referring to your methods.
#
# GafferUI.Widget subclasses are implemented using Qt widgets (using PySide or PyQt), but the public API
# exposed by the GafferUI classes never includes Qt functions or classes directly - this
# allows the implementation to be changed in the future. Furthermore it allows the use
# of the GafferUI module without learning all the Qt API. To enforce this separation,
# GafferUI classes must not derive from Qt classes.
#
# # Layout definition using `with`
#
# The default parent for new widgets can be defined using the python `with` statement.
# This makes it possible to structure the code to closely resemble the structure of the
# layout itself, greatly aiding readability.
#
# ```
# with GafferUI.Window( "Example" ) as window :
#
# 	with GafferUI.TabbedContainer() :
#
# 		with GafferUI.ListContainer( parenting = { "label" : "Buttons" } ) :
#
# 			GafferUI.Button( "Button 1" )
# 			GafferUI.Button( "Button 2" )
#
# 		GafferUI.MultiLineTextWidget( "Enter text here...", parenting = { "label" : "Text" } )
#
# window.setVisible( True )
# GafferUI.EventLoop.mainEventLoop().start()
# ```
#
# Behind the scenes, newly constructed widgets are automatically added to the
# parent widget using a call to `parent.addChild( widget, **parenting )`. This allows
# optional arguments to `addChild()` to be specified during layout creation - above
# we use this to define the names for the tabs corresponding to each child of the
# TabbedContainer.
#
# \todo Consider how this relates to the Gadget class. Currently I'm aiming to have the two classes
# have identical signatures in as many places as possible, with the possibility of perhaps having
# a common base class in the future. Right now the signatures are the same for the event signals and
# for the tool tips.
class Widget( Gaffer.Signals.Trackable, metaclass = _WidgetMetaclass ) :

	## All GafferUI.Widget instances must hold a corresponding QtWidgets.QWidget instance
	# which provides the top level implementation for the widget, and to which other
	# widgets may be parented. This QWidget is created during __init__, and cannot be
	# replaced later. Derived classes may pass either a QtWidgets.QWidget directly, or if
	# they prefer may pass a GafferUI.Widget, in which case a top level QWidget will be
	# created automatically, with the GafferUI.Widget being parented to it. The top level
	# QWidget can be accessed at any time using the _qtWidget() method. Note that this is
	# protected to encourage non-reliance on knowledge of the Qt backend.
	#
	# If a current parent has been defined using the `with` syntax described above,
	# the parenting argument may be passed as a dictionay of optional keywords for the
	# automatic `parent.addChild()` call.
	def __init__( self, topLevelWidget, toolTip="", parenting = None ) :

		Gaffer.Signals.Trackable.__init__( self )

		assert( isinstance( topLevelWidget, ( QtWidgets.QWidget, Widget ) ) )

		if isinstance( topLevelWidget, QtWidgets.QWidget ) :
			assert( Widget.__qtWidgetOwners.get( topLevelWidget ) is None )
			self.__qtWidget = topLevelWidget

			## Qt treats subclasses of QWidget differently from direct instances of QWidget itself
			# where in direct instances of QWidget the behavior of the attribute "WA_StyledBackground"
			# is set in place, however there is a bug in PySide that treats direct instances of QWidget
			# in the same way as their subclassed ones, because of that we need to set the
			# attribute WA_StyledBackground to all direct instances of QWidget to get the expected
			# behavior from Qt when using PySide.
			# more details:
			# http://stackoverflow.com/questions/32313469/stylesheet-in-pyside-not-working
			if type( topLevelWidget ) == QtWidgets.QWidget :
				self.__qtWidget.setAttribute( QtCore.Qt.WA_StyledBackground, True )
		else :
			self.__gafferWidget = topLevelWidget
			self.__qtWidget = QtWidgets.QWidget()
			self.__qtWidget.setLayout( QtWidgets.QGridLayout() )
			## We need to set the size constraint to prevent widgets expanding in an unwanted
			# way. However we may want other types to expand in the future. I think what we
			# really need to do is somehow make __qtWidget without a layout, and just have
			# it's size etc. dictated directly by self.__gafferWidget._qtWidget() somehow.
			self.__qtWidget.layout().setSizeConstraint( QtWidgets.QLayout.SetMinAndMaxSize )
			self.__qtWidget.layout().setContentsMargins( 0, 0, 0, 0 )
			self.__qtWidget.layout().addWidget( self.__gafferWidget._qtWidget(), 0, 0 )

		Widget.__qtWidgetOwners[self.__qtWidget] = weakref.ref( self )

		# disable different focus appearance on os x
		## \todo If we have a style class for Widget at some point, then perhaps
		# this should go in there.
		self.__qtWidget.setAttribute( QtCore.Qt.WA_MacShowFocusRect, False )

		self._keyPressSignal = None
		self._keyReleaseSignal = None
		self._buttonPressSignal = None
		self._buttonReleaseSignal = None
		self._buttonDoubleClickSignal = None
		self._mouseMoveSignal = None
		self._enterSignal = None
		self._leaveSignal = None
		self._dragBeginSignal = None
		self._dragEnterSignal = None
		self._dragMoveSignal = None
		self._dragLeaveSignal = None
		self._dropSignal = None
		self._dragEndSignal = None
		self._wheelSignal = None
		self._visibilityChangedSignal = None
		self._contextMenuSignal = None
		self._parentChangedSignal = None

		self.__visible = not isinstance( self, GafferUI.Window )

		# perform automatic parenting if necessary. we don't want to do this
		# for menus, because they don't have the same parenting semantics. if other
		# types end up with similar requirements then we should probably just have
		# a mechanism for them to say they don't want to participate rather than
		# hardcoding stuff here.
		if len( self.__parentStack ) and not isinstance( self, GafferUI.Menu ) :
			if self.__initNesting() == self.__parentStack[-1][1] + 1 :
				if self.__parentStack[-1][0] is not None :
					parenting = parenting or {}
					self.__parentStack[-1][0].addChild( self, **parenting )

		self.__eventFilterInstalled = False
		# if a class has overridden getToolTip, then the tooltips
		# may be dynamic based on context, and we need to display
		# them using the event filter.
		c = self.__class__
		while c and c is not Widget :
			if "getToolTip" in c.__dict__ :
				self.__ensureEventFilter()
				break
			c = c.__bases__[0]

		if isinstance( self, GafferUI.Window ) :
			# We need keypress events at the window level
			# in `_EventFilter.__dragKeyPress()`.
			self.__ensureEventFilter()

		self.setToolTip( toolTip )

		self.__applyQWidgetStyleClasses()

	## Sets whether or not this Widget is visible. Widgets are
	# visible by default, except for Windows which need to be made
	# visible explicitly after creation.
	def setVisible( self, visible ) :

		visible = bool( visible )

		if visible == self.__visible :
			return

		self.__visible = visible
		if (
			not self.__visible or
			isinstance( self, GafferUI.Window ) or
			self.__qtWidget.parent() is not None
		) :
			self.__qtWidget.setVisible( self.__visible )
		else :
			# we're visible, but we're not a window and
			# we have no parent. if we were to apply
			# the visibility now then qt would turn us into
			# a visible top level window. we don't want that
			# so we'll wait to get a parent again and apply
			# the visibility in _applyVisibility().
			pass

	## Returns False if this Widget has been explicitly hidden
	# using setVisible( False ), and True otherwise. Note that if
	# a parent Widget has been hidden, then this function may still
	# return True even though the child is actually hidden. Use the
	# visible() method to determine visibility taking into account
	# parent Widgets.
	def getVisible( self ) :

		# I'm very reluctant to have an explicit visibility field on Widget like this,
		# as you'd think that would be duplicating the real information Qt holds inside
		# QWidget. But Qt shows and hides things behind your back when parenting widgets,
		# so there's no real way of knowing whether the Qt visibility is a result of
		# your explicit actions or of Qt's implicit actions. Qt does have a flag
		# WA_WState_ExplicitShowHide which appears to record whether or not the current
		# visibility was requested explicitly, but in the case that that is false,
		# I can't see a way of determining what the explicit visibility should be
		# without tracking it separately. The only time our idea of visibility should
		# differ from Qt's is if we're a parentless widget, so at least most of the time
		# the assertion covers our asses a bit.
		if self.__qtWidget.parent() or isinstance( self, GafferUI.Window ) :
			assert( self.__visible == ( not self.__qtWidget.isHidden() ) )

		return self.__visible

	## Returns True if this Widget and all its parents up to the specified
	# ancestor are visible.
	def visible( self, relativeTo=None ) :

		if relativeTo is not None :
			relativeTo = relativeTo.__qtWidget

		return self.__qtWidget.isVisibleTo( relativeTo )

	## Even when Widget.visible() is True, the Widget may not /actually/
	# be visible to the user - for instance it may not be in the current
	# tab in its group, or it may have been scrolled to one side. This
	# method takes care of everything necessary to make sure this is not
	# the case, and the Widget is directly visible to the user.
	def reveal( self ) :

		widget = self
		while widget is not None :
			widget.setVisible( True )
			if widget is not self :
				widget._revealDescendant( self )
			widget = widget.ancestor( GafferUI.ContainerWidget )

	## Sets whether or not this Widget is enabled - when
	# not enabled Widgets are typically greyed out and signals
	# will not be emitted for them. Disabling a Widget disables
	# all children too.
	def setEnabled( self, enabled ) :

		self.__qtWidget.setEnabled( enabled )

	## Returns False if this Widget has been explicitly disabled using
	# setEnabled( False ), and True otherwise. Note that if a parent
	# Widget has been disabled, then this function may still return
	# True even though the child is effectively disabled. Use the
	# enabled() method to determine enabled state taking into account
	# parent Widgets.
	def getEnabled( self ) :

		return not self.__qtWidget.testAttribute( QtCore.Qt.WA_ForceDisabled )

	## Returns True if neither this Widget nor all its parents up to the specified
	# ancestor have been disabled with setEnabled( False ).
	def enabled( self, relativeTo=None ) :

		if relativeTo is not None :
			relativeTo = relativeTo.__qtWidget

		return self.__qtWidget.isEnabledTo( relativeTo )

	## Sets whether or not this Widget should be rendered in a highlighted
	# state. This status is not inherited by child widgets. Note that highlighted
	# drawing has not yet been implemented for all Widget types. Derived classes
	# may reimplement this method as necessary, but must call the base class
	# implementation from their reimplementation.
	## \todo Implement highlighting for more subclasses.
	def setHighlighted( self, highlighted ) :

		if highlighted == self.getHighlighted() :
			return

		self._qtWidget().setProperty( "gafferHighlighted", GafferUI._Variant.toVariant( highlighted ) )
		self._repolish()

	def getHighlighted( self ) :

		if "gafferHighlighted" not in self._qtWidget().dynamicPropertyNames() :
			return False

		return GafferUI._Variant.fromVariant( self._qtWidget().property( "gafferHighlighted" ) )

	## Returns the GafferUI.Widget which is the parent for this
	# Widget, or None if it has no parent.
	def parent( self ) :

		q = self._qtWidget()

		while q is not None :

			parentWidget = q.parentWidget()
			if parentWidget is not None :
				q = parentWidget
			else :
				# we have to account for the strange parenting
				# relationships that go on inside graphicsviews.
				graphicsProxyWidget = q.graphicsProxyWidget()
				if graphicsProxyWidget :
					q = graphicsProxyWidget.scene().parent()
				else :
					q = None

			if q in Widget.__qtWidgetOwners :
				return Widget.__qtWidgetOwners[q]()

		return None

	## Returns the first Widget in the hierarchy above this one
	# to match the desired type.
	def ancestor( self, type ) :

		w = self
		while w is not None :
			w = w.parent()
			if isinstance( w, type ) :
				return w

		return None

	## Returns true if this Widget is an ancestor (or direct parent) of other.
	def isAncestorOf( self, other ) :

		while other :
			parent = other.parent()
			if parent is self :
				return True
			other = parent

		return False

	## \deprecated Use bound().size() instead.
	def size( self ) :

		return imath.V2i( self.__qtWidget.width(), self.__qtWidget.height() )

	## Returns the bounding box of the Widget as a Box2i. If relativeTo
	# is None then the bound is provided in screen coordinates, if a
	# Widget is passed then it is provided relative to that Widget.
	def bound( self, relativeTo=None ) :

		# traverse up the hierarchy, accumulating the transform
		# till we reach the top. in an ideal world we'd just call
		# self.__qtWidget.mapToGlobal() but that doesn't take into
		# account the fact that a widget may be embedded in a QGraphicsScene.
		q = self.__qtWidget
		pos = QtCore.QPoint( 0, 0 )
		while q is not None :
			graphicsProxyWidget = q.graphicsProxyWidget()
			if graphicsProxyWidget is not None :
				pos = graphicsProxyWidget.mapToScene( pos.x(), pos.y() )
				pos = QtCore.QPoint( pos.x(), pos.y() )
				q = graphicsProxyWidget.scene().parent()
			elif q.isWindow() :
				pos = q.mapToGlobal( pos )
				q = None
			else :
				parentWidget = q.parentWidget()
				if parentWidget is not None :
					pos = q.mapToParent( pos )
				q = parentWidget

		pos = imath.V2i( pos.x(), pos.y() )
		if relativeTo is not None :
			pos -= relativeTo.bound().min()

		return imath.Box2i( pos, pos + imath.V2i( self.__qtWidget.width(), self.__qtWidget.height() ) )

	def keyPressSignal( self ) :

		self.__ensureEventFilter()
		if self._keyPressSignal is None :
			self._keyPressSignal = GafferUI.WidgetEventSignal()
		return self._keyPressSignal

	def keyReleaseSignal( self ) :

		self.__ensureEventFilter()
		if self._keyReleaseSignal is None :
			self._keyReleaseSignal = GafferUI.WidgetEventSignal()
		return self._keyReleaseSignal

	## \todo Should these be renamed to mousePressSignal and mouseReleaseSignal?
	def buttonPressSignal( self ) :

		self.__ensureEventFilter()
		if self._buttonPressSignal is None :
			self._buttonPressSignal = GafferUI.WidgetEventSignal()
		return self._buttonPressSignal

	def buttonReleaseSignal( self ) :

		self.__ensureEventFilter()
		if self._buttonReleaseSignal is None :
			self._buttonReleaseSignal = GafferUI.WidgetEventSignal()
		return self._buttonReleaseSignal

	def buttonDoubleClickSignal( self ) :

		self.__ensureEventFilter()
		if self._buttonDoubleClickSignal is None :
			self._buttonDoubleClickSignal = GafferUI.WidgetEventSignal()
		return self._buttonDoubleClickSignal

	def mouseMoveSignal( self ) :

		if self._mouseMoveSignal is None :
			self._mouseMoveSignal = GafferUI.WidgetEventSignal()
			self.__ensureEventFilter()
			self.__ensureMouseTracking()
		return self._mouseMoveSignal

	def enterSignal( self ) :

		self.__ensureEventFilter()
		if self._enterSignal is None :
			self._enterSignal = GafferUI.WidgetSignal()
		return self._enterSignal

	def leaveSignal( self ) :

		self.__ensureEventFilter()
		if self._leaveSignal is None :
			self._leaveSignal = GafferUI.WidgetSignal()
		return self._leaveSignal

	## This signal is emitted if a previous buttonPressSignal() returned true, and the
	# user has subsequently moved the mouse with the button down. To initiate a drag
	# a Widget must return an IECore::RunTimeTyped object representing the data being
	# dragged - note that this return type differs from many signals where either True
	# or False is returned, and that a False return value will actually initiate a
	# drag with IECore.BoolData( False ) which is almost certainly not what is intended.
	# Return None to signify that no drag should be initiated.
	#
	# When a drag is in motion, dragEnterSignals are emitted as the cursor
	# enters Widgets, and if True is returned, that Widget becomes the current target for the
	# drag. The target widget receives dragMoveSignals and a dropSignal when
	# the drag ends. Finally, the originating Widget receives a dragEndSignal
	# to signify the result of the drop.
	def dragBeginSignal( self ) :

		if self._dragBeginSignal is None :
			self._dragBeginSignal = GafferUI.WidgetDragBeginSignal()
			self.__ensureEventFilter()
			self.__ensureMouseTracking()
		return self._dragBeginSignal

	## This signal is emitted when a drag enters a Widget. You must return True
	# from a connected slot in order for dragMoveSignal() and dropSignal()
	# to be emitted subsequently.
	def dragEnterSignal( self ) :

		if self._dragEnterSignal is None :
			self._dragEnterSignal = GafferUI.WidgetEventSignal()
			self.__ensureEventFilter()
			self.__ensureMouseTracking()
		return self._dragEnterSignal

	## This signal is emitted when a drag is moving within a Widget which
	# previously returned true from a dragEnterSignal() emission.
	def dragMoveSignal( self ) :

		if self._dragMoveSignal is None :
			self._dragMoveSignal = GafferUI.WidgetEventSignal()
			self.__ensureEventFilter()
			self.__ensureMouseTracking()
		return self._dragMoveSignal

	## This signal is emitted on the previous target when a new Widget
	# accepts the drag in dragEnterSignal().
	def dragLeaveSignal( self ) :

		if self._dragLeaveSignal is None :
			self._dragLeaveSignal = GafferUI.WidgetEventSignal()
			self.__ensureEventFilter()
			self.__ensureMouseTracking()
		return self._dragLeaveSignal

	## This signal is emitted when a drop is made within a Widget which
	# previously returned true from a dragEnterSignal().
	def dropSignal( self ) :

		if self._dropSignal is None :
			self._dropSignal = GafferUI.WidgetEventSignal()
		return self._dropSignal

	## After the dropSignal() has been emitted on the destination of the drag, the
	# dragEndSignal() is emitted on the Gadget which provided the source of the
	# drag.
	def dragEndSignal( self ) :

		if self._dragEndSignal is None :
			self._dragEndSignal = GafferUI.WidgetEventSignal()
		return self._dragEndSignal

	def wheelSignal( self ) :

		self.__ensureEventFilter()
		if self._wheelSignal is None :
			self._wheelSignal = GafferUI.WidgetEventSignal()
		return self._wheelSignal

	## Note that this is not emitted every time setVisible() is called -
	# instead it is emitted when the Widget either becomes or ceases to
	# be visible on screen.
	def visibilityChangedSignal( self ) :

		self.__ensureEventFilter()
		if self._visibilityChangedSignal is None :
			self._visibilityChangedSignal = GafferUI.WidgetSignal()
		return self._visibilityChangedSignal

	def contextMenuSignal( self ) :

		self.__ensureEventFilter()
		if self._contextMenuSignal is None :
			self._contextMenuSignal = GafferUI.WidgetSignal()
		return self._contextMenuSignal

	def parentChangedSignal( self ) :

		self.__ensureEventFilter()
		if self._parentChangedSignal is None :
			self._parentChangedSignal = GafferUI.WidgetSignal()
		return self._parentChangedSignal

	## A signal emitted whenever the keyboard focus moves from one Widget
	# to another. The signature for slots is ( oldWidget, newWidget ).
	## \todo Add methods for setting and querying the focus. TextWidget
	# and MultiLineTextWidget provide their own methods for this but these
	# don't apply generally so they should be replaced. Currently I'm favouring
	# simple setFocus( widget ) and getFocus() class methods on the Widget class -
	# since there can be only one focussed widget at a time it doesn't really make
	# sense for it to be a property of each widget.
	@classmethod
	def focusChangedSignal( cls ) :

		cls.__ensureFocusChangedConnection()
		return cls.__focusChangedSignal

	## Returns the tooltip to be displayed. This may be overriden
	# by derived classes to provide sensible default behaviour, but
	# allow custom behaviour when setToolTip( nonEmptyString ) has
	# been called.
	def getToolTip( self ) :

		return str( self._qtWidget().toolTip() )

	## Sets the tooltip to be displayed for this Widget. This
	# will override any default behaviour until setToolTip( "" )
	# is called.
	def setToolTip( self, toolTip ) :

		assert( isinstance( toolTip, str ) )

		self._qtWidget().setToolTip( toolTip )

		if toolTip :
			# Qt does have a default event handler for tooltips,
			# but we install our own so we can support markdown
			# formatting automatically.
			self.__ensureEventFilter()

	## Returns the current position of the mouse. If relativeTo
	# is not specified, then the position will be in screen coordinates,
	# otherwise it will be in the local coordinate system of the
	# specified widget.
	@staticmethod
	def mousePosition( relativeTo=None ) :

		p = QtGui.QCursor.pos()
		p = imath.V2i( p.x(), p.y() )
		if relativeTo is not None :
			p = p - relativeTo.bound().min()

		return p

	@staticmethod
	def currentModifiers() :

		return Widget._modifiers( QtWidgets.QApplication.queryKeyboardModifiers() )

	## Returns the widget at the specified screen position.
	# If widgetType is specified, then it is used to find
	# an ancestor of the widget at the position.
	@staticmethod
	def widgetAt( position, widgetType = None ) :

		if widgetType is None :
			widgetType = GafferUI.Widget

		qWidget = QtWidgets.QApplication.instance().widgetAt( position[0], position[1] )
		widget = GafferUI.Widget._owner( qWidget )

		if widget is not None and isinstance( widget._qtWidget(), QtWidgets.QGraphicsView ) :
			# if the widget is a QGraphicsView, then we have to dive into it ourselves
			# to find any widgets embedded within it - qt won't do that for us.
			graphicsView = widget._qtWidget()
			localPosition = graphicsView.mapFromGlobal( QtCore.QPoint( position[0], position[1] ) )
			graphicsItem = graphicsView.itemAt( localPosition )
			if isinstance( graphicsItem, QtWidgets.QGraphicsProxyWidget ) :
				localPosition = graphicsView.mapToScene( localPosition )
				localPosition = graphicsItem.mapFromScene( localPosition )
				qWidget = graphicsItem.widget().childAt( localPosition.x(), localPosition.y() )
				widget = GafferUI.Widget._owner( qWidget )

		if widget is not None and not isinstance( widget, widgetType ) :
			widget = widget.ancestor( widgetType )

		return widget

	## Called after the Widget's `__init__` method has completed. Useful
	# for performing operations from a base class after the subclass is
	# fully constructed. Overrides should call the base class `_postConstructor()`
	# before doing their own work.
	def _postConstructor( self ) :

		pass

	## Returns the top level QWidget instance used to implement
	# the GafferUI.Widget functionality.
	def _qtWidget( self ) :

		return self.__qtWidget

	## Returns the GafferUI.Widget that owns the specified QtWidgets.QWidget
	@classmethod
	def _owner( cls, qtWidget ) :

		while qtWidget is not None :

			if qtWidget in cls.__qtWidgetOwners :
				return cls.__qtWidgetOwners[qtWidget]()

			qtWidget = qtWidget.parentWidget()

		return None

	__qtWidgetOwners = weakref.WeakKeyDictionary()

	## Applies the current visibility to self._qtWidget(). It is
	# essential that this is called whenever the Qt parent of the
	# widget is changed, to work around undesirable Qt behaviours
	# (documented in the function body). In theory we could do this
	# automatically in response to parent changed events, but that
	# would mean an event filter on /every/ widget which would be
	# slow.
	## \todo Perhaps if we can implement a faster event filter we
	# can do this automatically. If doing this, take note of
	# comments in TabbedContainer.append().
	def _applyVisibility( self ) :

		if self.__qtWidget.parent() is None :
			# When a QWidget becomes parentless, Qt will turn
			# it into a toplevel window. We really don't want
			# that, so we'll hide it until it gets a parent
			# again.
			self.__qtWidget.setVisible( False )
		else :
			# If the parent has changed, qt may have hidden
			# the widget, so if necessary we reapply the visibility
			# we actually want.
			if self.__visible != ( not self.__qtWidget.isHidden() ) :
				self.__qtWidget.setVisible( self.__visible )

	## Used by the ContainerWidget classes to implement the automatic parenting
	# using the with statement.
	@classmethod
	def _pushParent( cls, container ) :

		assert( isinstance( container, ( GafferUI.ContainerWidget, type( None ) ) ) )

		cls.__parentStack.append( ( container, cls.__initNesting() ) )

	@classmethod
	def _popParent( cls ) :

		return cls.__parentStack.pop()[0]

	# Returns how many Widgets are currently in construction
	# on the call stack. We use this to avoid automatically
	# parenting Widgets that are being created inside a constructor.
	@staticmethod
	def __initNesting() :

		widgetsInInit = set()
		frame = inspect.currentframe()
		while frame :
			if frame.f_code.co_name=="__init__" :
				frameSelf = frame.f_locals[frame.f_code.co_varnames[0]]
				if isinstance( frameSelf, Widget ) :
					widgetsInInit.add( frameSelf )
			frame = frame.f_back

		return len( widgetsInInit )

	__parentStack = []

	## Converts a Qt key code into a string
	@classmethod
	def _key( cls, qtKey ) :

		if not cls.__keyMapping :
			for k in dir( QtCore.Qt ) :
				if k.startswith( "Key_" ) :
					keyValue = int( getattr( QtCore.Qt, k ) )
					keyString = k[4:]
					cls.__keyMapping[keyValue] = keyString

		return cls.__keyMapping[int(qtKey)]

	__keyMapping = {}

	## Converts a Qt buttons enum value into Gaffer ButtonEvent enum
	@staticmethod
	def _buttons( qtButtons ) :

		result = GafferUI.ButtonEvent.Buttons.None_
		if qtButtons & QtCore.Qt.LeftButton :
			result |= GafferUI.ButtonEvent.Buttons.Left
		if qtButtons & QtCore.Qt.MidButton :
			result |= GafferUI.ButtonEvent.Buttons.Middle
		if qtButtons & QtCore.Qt.RightButton :
			result |= GafferUI.ButtonEvent.Buttons.Right

		return GafferUI.ButtonEvent.Buttons( result )

	## Converts Qt modifiers to Gaffer modifiers
	@staticmethod
	def _modifiers( qtModifiers ) :

		modifiers = GafferUI.ModifiableEvent.Modifiers.None_
		if qtModifiers & QtCore.Qt.ShiftModifier :
			modifiers = modifiers | GafferUI.ModifiableEvent.Modifiers.Shift
		if qtModifiers & QtCore.Qt.ControlModifier :
			modifiers = modifiers | GafferUI.ModifiableEvent.Modifiers.Control
		if qtModifiers & QtCore.Qt.AltModifier :
			modifiers = modifiers | GafferUI.ModifiableEvent.Modifiers.Alt

		return GafferUI.ModifiableEvent.Modifiers( modifiers )

	## Converts an IECore.Color[34]f to a QtColor. Note that this
	# does not take into account GafferUI.DisplayTransform.
	@staticmethod
	def _qtColor( color ) :

		color = color * 255
		return QtGui.QColor(
			min( 255, max( 0, color.r ) ),
			min( 255, max( 0, color.g ) ),
			min( 255, max( 0, color.b ) ),
		)

	# We try not to install the event filter until absolutely
	# necessary, as there's an overhead in having it in place.
	# This function installs the filter, and is called when
	# we know that the filter will be needed (typically when a
	# client accesses one of the signals triggered by the filter).
	def __ensureEventFilter( self ) :

		if not self.__eventFilterInstalled :
			self._qtWidget().installEventFilter( _eventFilter )
			if isinstance( self._qtWidget(), QtWidgets.QAbstractScrollArea ) :
				self._qtWidget().viewport().installEventFilter( _eventFilter )
			self.__eventFilterInstalled = True

	def __ensureMouseTracking( self ) :

		if isinstance( self._qtWidget(), QtWidgets.QAbstractScrollArea ) :
			self._qtWidget().viewport().setMouseTracking( True )
		else :
			self._qtWidget().setMouseTracking( True )


	__focusChangedSignal = Gaffer.Signals.Signal2()
	__focusChangedConnected = False
	@classmethod
	def __ensureFocusChangedConnection( cls ) :

		if not cls.__focusChangedConnected :
			QtWidgets.QApplication.instance().focusChanged.connect( cls.__focusChanged )
			cls.__focusChangedConnected = True

	@classmethod
	def __focusChanged( cls, oldWidget, newWidget ) :

		cls.__focusChangedSignal( cls._owner( oldWidget ), cls._owner( newWidget ) )

		if cls.__focusChangedSignal.empty() :
			# if nothing's connected to the signal currently, then disconnect, because
			# we don't want the overhead of dealing with focus changes when no-one is
			# interested.
			QtWidgets.QApplication.instance().focusChanged.disconnect( cls.__focusChanged )
			cls.__focusChangedConnected = False

	def _repolish( self, qtWidget=None ) :

		if qtWidget is None :
			qtWidget = self._qtWidget()

		style = qtWidget.style()
		style.unpolish( qtWidget )
		for child in qtWidget.children() :
			if isinstance( child, QtWidgets.QWidget ) :
				self._repolish( child )
		style.polish( qtWidget )

	def _setStyleSheet( self ):

		self.__qtWidget.setStyleSheet( _styleSheet )

	@classmethod
	def __styleClassName( cls ) :

		nameParts = []

		if cls.__module__ != "__main__" :
			nameParts.extend( cls.__module__.split( '.' ) )

		# Avoid things like GafferUI.Button.Button -> GafferUI.Button
		if not nameParts or cls.__name__ != nameParts[ -1 ] :
			nameParts.append( cls.__name__ )

		return ".".join( nameParts )

	def __applyQWidgetStyleClasses( self ) :

		# Expose our class as a custom property to allow stylesheets to target
		# widgets by GafferUI class names (Qt's class is bound to the class
		# selector, and class property).
		# We include the module name to ensure we don't have collisions with
		# custom widgets.

		self._qtWidget().setProperty( "gafferClass", self.__styleClassName() )

		allClasses = []

		for cls in inspect.getmro( self.__class__ ) :
			if hasattr( cls, '_Widget__styleClassName' ) :
				allClasses.append( cls.__styleClassName() )

		self._qtWidget().setProperty( "gafferClasses", allClasses )

class _EventFilter( QtCore.QObject ) :

	def __init__( self ) :

		QtCore.QObject.__init__( self )

		# variables used in the implementation of drag and drop.
		self.__lastButtonPressWidget = None
		self.__lastButtonPressEvent = None
		self.__dragDropEvent = None

		# the vast majority ( ~99% at time of testing ) of events entering
		# eventFilter() are totally irrelevant to us. it's therefore very
		# important for interactivity to exit the filter as fast as possible
		# in these cases. first testing for membership of this set seems the
		# best way. if further optimisation becomes necessary, then perhaps the
		# best solution is an event filter implemented in c++, which does the early
		# out based on the mask and then calls through to python only if this fails.
		self.__eventMask = set( (
			QtCore.QEvent.ToolTip,
			QtCore.QEvent.KeyPress,
			QtCore.QEvent.KeyRelease,
			QtCore.QEvent.MouseButtonPress,
			QtCore.QEvent.MouseButtonRelease,
			QtCore.QEvent.MouseButtonDblClick,
			QtCore.QEvent.MouseMove,
			QtCore.QEvent.Enter,
			QtCore.QEvent.Leave,
			QtCore.QEvent.Wheel,
			QtCore.QEvent.Show,
			QtCore.QEvent.Hide,
			QtCore.QEvent.ContextMenu,
			QtCore.QEvent.ParentChange,
		) )

	def eventFilter( self, qObject, qEvent ) :

		qEventType = qEvent.type() # for speed it's best not to keep calling this below
		# early out as quickly as possible for the majority of cases where we have literally
		# no interest in the event.
		if qEventType not in self.__eventMask :
			return False

		# we display tooltips and emit visibility events even on disabled widgets
		if qEventType==qEvent.ToolTip :

			return self.__toolTip( qObject, qEvent )

		elif qEventType==qEvent.Show or qEventType==qEvent.Hide :

			return self.__showHide( qObject, qEvent )

		# but for anything else we ignore disabled widgets
		if not qObject.isEnabled() :
			return False

		if qEventType==qEvent.KeyPress :

			return self.__keyPress( qObject, qEvent )

		elif qEventType==qEvent.KeyRelease :

			return self.__keyRelease( qObject, qEvent )

		elif qEventType==qEvent.MouseButtonPress :

			return self.__mouseButtonPress( qObject, qEvent )

		elif qEventType==qEvent.MouseButtonRelease :

			return self.__mouseButtonRelease( qObject, qEvent )

		elif qEventType==qEvent.MouseButtonDblClick :

			return self.__mouseButtonDblClick( qObject, qEvent )

		elif qEventType==qEvent.MouseMove :

			return self.__mouseMove( qObject, qEvent )

		elif qEventType==qEvent.Enter :

			return self.__enter( qObject, qEvent )

		elif qEventType==qEvent.Leave :

			return self.__leave( qObject, qEvent )

		elif qEventType==qEvent.Wheel :

			return self.__wheel( qObject, qEvent )

		elif qEventType==qEvent.ContextMenu :

			return self.__contextMenu( qObject, qEvent )

		elif qEventType==qEvent.ParentChange :

			return self.__parentChange( qObject, qEvent )

		return False

	def __toolTip( self, qObject, qEvent ) :

		widget = Widget._owner( qObject )
		toolTip = widget.getToolTip()
		if toolTip :
			toolTip = GafferUI.DocumentationAlgo.markdownToHTML( toolTip )
			QtWidgets.QToolTip.showText( qEvent.globalPos(), toolTip, qObject )
			return True
		else :
			return False

	def __showHide( self, qObject, qEvent ) :

		widget = Widget._owner( qObject )
		if widget is not None and widget._visibilityChangedSignal is not None :
			widget._visibilityChangedSignal( widget )
		return False

	def __keyPress( self, qObject, qEvent ) :

		if self.__dragKeyPress( qObject, qEvent ) :
			return True

		widget = Widget._owner( qObject )
		if widget._keyPressSignal is not None :

			event = GafferUI.KeyEvent(
				Widget._key( qEvent.key() ),
				Widget._modifiers( qEvent.modifiers() ),
			)

			return widget._keyPressSignal( widget, event )

		return False

	def __keyRelease( self, qObject, qEvent ) :

		# When a key is held, the following events are observed:
		#   MacOS: p p p p r
		#   Linux: p r p r p r p r
		# We conform linux to match Mac as it feels more intuitive.
		if qEvent.isAutoRepeat() :
			return True

		if self.__updateDragModifiers( qObject, qEvent ) :
			return True

		widget = Widget._owner( qObject )
		if widget._keyReleaseSignal is not None :

			event = GafferUI.KeyEvent(
				Widget._key( qEvent.key() ),
				Widget._modifiers( qEvent.modifiers() ),
			)

			return widget._keyReleaseSignal( widget, event )

		return False

	def __virtualButtons( self, qtButtons ):
		result = Widget._buttons( qtButtons )
		if self.__dragDropEvent is not None and self.__dragDropEvent.__startedByKeyPress :
			result |= GafferUI.ButtonEvent.Buttons.Left
		return GafferUI.ButtonEvent.Buttons( result )

	def __mouseButtonPress( self, qObject, qEvent ) :

		if (
			self.__dragDropEvent is not None and self.__dragDropEvent.__startedByKeyPress
			and ( Widget._buttons( qEvent.button() ) & GafferUI.ButtonEvent.Buttons.Left )
		) :
			# We are doing a virtual drag based on a keypress, but once the actual mouse button gets pressed,
			# we replace it with an actual drag.
			self.__dragDropEvent.__startedByKeyPress = False
			return True

		widget = Widget._owner( qObject )
		if widget._buttonPressSignal is not None :
			event = GafferUI.ButtonEvent(
				Widget._buttons( qEvent.button() ),
				self.__virtualButtons( qEvent.buttons() ),
				self.__widgetSpaceLine( qEvent, widget ),
				0.0,
				Widget._modifiers( qEvent.modifiers() ),
			)

			if event.buttons  :
				result = widget._buttonPressSignal( widget, event )
				if result :
					self.__lastButtonPressWidget = weakref.ref( widget )
					self.__lastButtonPressEvent = event
				return result

		return False

	def __mouseButtonRelease( self, qObject, qEvent ) :

		buttons = self.__virtualButtons( qEvent.buttons() )
		if self.__dragDropEvent is not None and ( buttons & self.__dragDropEvent.buttons ) == 0 :
			return self.__endDrag( qObject, qEvent )
		else :

			self.__lastButtonPressWidget = None
			self.__lastButtonPressEvent = None

			widget = Widget._owner( qObject )
			if widget._buttonReleaseSignal is not None :

				event = GafferUI.ButtonEvent(
					Widget._buttons( qEvent.button() ),
					buttons,
					self.__widgetSpaceLine( qEvent, widget ),
					0.0,
					Widget._modifiers( qEvent.modifiers() ),
				)

				return widget._buttonReleaseSignal( widget, event )

		return False

	def __mouseButtonDblClick( self, qObject, qEvent ) :

		self.__lastButtonPressWidget = None

		widget = Widget._owner( qObject )
		if widget._buttonDoubleClickSignal is not None :

			event = GafferUI.ButtonEvent(
				Widget._buttons( qEvent.button() ),
				Widget._buttons( qEvent.buttons() ),
				self.__widgetSpaceLine( qEvent, widget ),
				0.0,
				Widget._modifiers( qEvent.modifiers() ),
			)

			return widget._buttonDoubleClickSignal( widget, event )

		return False

	def __mouseMove( self, qObject, qEvent ) :

		if self.__doDrag( qObject, qEvent ) :
			return True

		widget = Widget._owner( qObject )
		if widget._mouseMoveSignal is not None :

			event = GafferUI.ButtonEvent(
				Widget._buttons( qEvent.button() ),
				self.__virtualButtons( qEvent.buttons() ),
				self.__widgetSpaceLine( qEvent, widget ),
				0.0,
				Widget._modifiers( qEvent.modifiers() ),
			)

			return widget._mouseMoveSignal( widget, event )

		return False

	def __enter( self, qObject, qEvent ) :

		widget = Widget._owner( qObject )
		if widget is not None and widget._enterSignal is not None :
			return widget._enterSignal( widget )

		return False

	def __leave( self, qObject, qEvent ) :

		widget = Widget._owner( qObject )
		if widget is not None and widget._leaveSignal is not None :
			return widget._leaveSignal( widget )

		return False

	def __wheel( self, qObject, qEvent ) :

		widget = Widget._owner( qObject )
		if widget._wheelSignal is not None :

			event = GafferUI.ButtonEvent(
				GafferUI.ButtonEvent.Buttons.None_,
				self.__virtualButtons( qEvent.buttons() ),
				self.__widgetSpaceLine( qEvent, widget ),
				qEvent.delta() / 8.0,
				Widget._modifiers( qEvent.modifiers() ),
			)

			return widget._wheelSignal( widget, event )

		return False

	def __contextMenu( self, qObject, qEvent ) :

		if qEvent.modifiers() :
			return False

		widget = Widget._owner( qObject )
		if widget._contextMenuSignal is not None :
			return widget._contextMenuSignal( widget )

		return False

	def __parentChange( self, qObject, qEvent ) :

		## \todo It might be nice to investigate having the
		# the signature for this signal match that of
		# GraphComponent::parentChangedSignal(), which takes
		# an additional argument for the previous parent. We
		# may be able to get the value for that from a
		# ParentAboutToChange event.
		widget = Widget._owner( qObject )
		if widget._parentChangedSignal is not None :
			widget._parentChangedSignal( widget )
			return True

		return False

	# Although Qt has a drag and drop system, we ignore it and implement our
	# own. This isn't ideal. The primary reasons for implementing our own are :
	#
	# * We need drag and drop to work identically between Widgets and Gadgets.
	# * We want drag move events to be receivable even when the cursor
	#   is outside a Widget/Gadget - this is essential for intuitive
	#   drag-to-zoom and manipulators, but is not supported by Qt.
	# * Qt on Mac has this really annoying slideBack animation for failed
	#   drags that can't be disabled, and only wants to work for the left
	#   mouse button.
	#
	def __doDrag( self, qObject, qEvent ) :

		if not self.__dragDropEvent :
			return self.__startDrag( qObject, qEvent )
		else :
			return self.__updateDrag( qObject, qEvent )

		return False

	def __startDrag( self, qObject, qEvent, forKeyPress = False ) :

		if self.__lastButtonPressWidget is None :
			return False

		if qEvent.buttons() == QtCore.Qt.NoButton :
			# sometimes Qt can fail to give us a mouse button release event
			# for the widget that received the mouse button press - in particular
			# this appears to happen when a context menu is raised in the press
			# event. this can mean we end up here, with a __lastButtonPressWidget
			# we don't want, attempting to start a drag when no buttons are down.
			# so we fix that.
			self.__lastButtonPressWidget = None
			return False

		sourceWidget = self.__lastButtonPressWidget()
		if sourceWidget is None :
			# the widget died
			return False

		threshold = 3 if not forKeyPress else 0
		if ( self.__lastButtonPressEvent.line.p0 - self.__widgetSpaceLine( qEvent, sourceWidget ).p0 ).length() < threshold :
			return False

		if sourceWidget._dragBeginSignal is None :
			return False

		dragDropEvent = GafferUI.DragDropEvent(
			Widget._buttons( qEvent.button() ),
			Widget._buttons( qEvent.buttons() ),
			self.__lastButtonPressEvent.line,
			Widget._modifiers( qEvent.modifiers() ),
		)
		dragDropEvent.sourceWidget = sourceWidget
		dragDropEvent.destinationWidget = None
		dragDropEvent.__startedByKeyPress = forKeyPress

		dragData = sourceWidget._dragBeginSignal( sourceWidget, dragDropEvent )
		if dragData is not None :

			dragDropEvent.data = dragData

			self.__lastButtonPressWidget = None
			self.__lastButtonPressEvent = None
			self.__dragDropEvent = dragDropEvent

			self.__updateDrag( qObject, qEvent )

			return True

	def __doDragEnterAndLeave( self, qObject, qEvent ) :

		candidateWidget = Widget.widgetAt( imath.V2i( qEvent.globalPos().x(), qEvent.globalPos().y() ) )

		newDestinationWidget = None
		while candidateWidget is not None :
			if candidateWidget is self.__dragDropEvent.destinationWidget :
				return
			if candidateWidget._dragEnterSignal is not None :
				self.__dragDropEvent.line = self.__widgetSpaceLine( qEvent, candidateWidget )
				if candidateWidget._dragEnterSignal( candidateWidget, self.__dragDropEvent ) :
					newDestinationWidget = candidateWidget
					break
			candidateWidget = candidateWidget.parent()

		if newDestinationWidget is None :
			if self.__dragDropEvent.destinationWidget is self.__dragDropEvent.sourceWidget :
				# we allow the source widget to keep a hold of the drag even when outside
				# its borders, so that we can do intuitive drag-to-zoom and sliders that
				# go outside their displayed range.
				newDestinationWidget = self.__dragDropEvent.destinationWidget

		if newDestinationWidget is not self.__dragDropEvent.destinationWidget :
			previousDestinationWidget = self.__dragDropEvent.destinationWidget
			self.__dragDropEvent.destinationWidget = newDestinationWidget
			if previousDestinationWidget is not None and previousDestinationWidget._dragLeaveSignal is not None :
				self.__dragDropEvent.line = self.__widgetSpaceLine( qEvent, previousDestinationWidget )
				previousDestinationWidget._dragLeaveSignal( previousDestinationWidget, self.__dragDropEvent )

	def __updateDrag( self, qObject, qEvent ) :

		self.__dragDropEvent.modifiers = Widget._modifiers( qEvent.modifiers() )

		# emit enter and leave events as necessary, updating
		# the destination widget as we do.
		self.__doDragEnterAndLeave( qObject, qEvent )

		# emit move events on current destination
		dst = self.__dragDropEvent.destinationWidget
		if dst is None :
			return True

		if dst._dragMoveSignal :
			self.__dragDropEvent.line = self.__widgetSpaceLine( qEvent, dst )
			dst._dragMoveSignal( dst, self.__dragDropEvent )

		return True

	def __updateDragModifiers( self, qObject, qEvent ) :

		if self.__dragDropEvent is None :
			return False

		modifiers = Widget._modifiers( qEvent.modifiers() )
		if modifiers == self.__dragDropEvent.modifiers :
			return False

		dst = self.__dragDropEvent.destinationWidget
		if dst is None :
			return False

		self.__dragDropEvent.modifiers = modifiers
		if dst._dragMoveSignal :
			dst._dragMoveSignal( dst, self.__dragDropEvent )

		return True

	def __endDrag( self, qObject, qEvent ) :

		# Reset self.__dragDropEvent to None before emitting
		# dropSignal or dragEndSignal, because slots connected
		# to those signals could do anything at all - including
		# popping up modal dialogues which then want to start new
		# drags.

		dragDropEvent = self.__dragDropEvent
		self.__dragDropEvent = None

		# Emit dropSignal() on the destination.

		dst = dragDropEvent.destinationWidget
		if dst is not None and dst._dropSignal :

			dragDropEvent.line = self.__widgetSpaceLine( qEvent, dst )
			dragDropEvent.dropResult = dst._dropSignal( dst, dragDropEvent )

		# Emit dragEndSignal() on source.

		src = dragDropEvent.sourceWidget
		if src._dragEndSignal :

			dragDropEvent.line = self.__widgetSpaceLine( qEvent, src )

			src._dragEndSignal(
				src,
				dragDropEvent
			)

		return True

	def __dragKeyPress( self, qObject, qKeyEvent ) :

		if self.__updateDragModifiers( qObject, qKeyEvent ) :
			return True

		if qKeyEvent.key() != QtCore.Qt.Key_G or qKeyEvent.modifiers() :
			return False

		if self.__dragDropEvent is None :

			# Start drag by simulating a mouse press

			if not isinstance( GafferUI.Widget._owner( qObject ), GafferUI.Window ) :
				# Only start a drag if no widget lower in the hierarchy wanted
				# the keypress.
				return False

			globalPos = QtGui.QCursor.pos()
			qWidget = QtWidgets.QApplication.instance().widgetAt( globalPos )
			if qWidget is None :
				return

			qEvent = QtGui.QMouseEvent(
				QtCore.QEvent.MouseButtonPress,
				qWidget.mapFromGlobal( globalPos ),
				globalPos,
				QtCore.Qt.LeftButton,
				QtCore.Qt.LeftButton,
				qKeyEvent.modifiers()
			)

			if self.__mouseButtonPress( qWidget, qEvent ) :
				self.__startDrag( qWidget, qEvent, forKeyPress = True )
				return True

		else :

			# End drag

			globalPos = QtGui.QCursor.pos()
			qWidget = self.__dragDropEvent.sourceWidget._qtWidget()

			qEvent = QtGui.QMouseEvent(
				QtCore.QEvent.MouseButtonRelease,
				qWidget.mapFromGlobal( globalPos ),
				globalPos,
				QtCore.Qt.LeftButton,
				QtCore.Qt.NoButton,
				qKeyEvent.modifiers()
			)

			self.__endDrag( self.__dragDropEvent.sourceWidget._qtWidget(), qEvent )
			return True

	# Maps the position of the supplied Qt mouse event into the coordinate
	# space of the target Gaffer widget. This is required as certain widget
	# configurations (eg: QTableView with a visible header) result in qEvent
	# coordinate origins differing from the Gaffer Widget's origin.
	def __widgetSpaceLine( self, qEvent, targetWidget ) :

		cursorPos = imath.V2i( qEvent.globalPos().x(), qEvent.globalPos().y() )
		cursorPos -= targetWidget.bound().min()

		return IECore.LineSegment3f(
			imath.V3f( cursorPos.x, cursorPos.y, 1 ),
			imath.V3f( cursorPos.x, cursorPos.y, 0 )
		)

# this single instance is used by all widgets
_eventFilter = _EventFilter()

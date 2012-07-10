##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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
import string
import os
import math
import inspect

import IECore

import Gaffer
import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )
QtGui = GafferUI._qtImport( "QtGui" )

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
# \todo Consider how this relates to the Gadget class. Currently I'm aiming to have the two classes
# have identical signatures in as many places as possible, with the possibility of perhaps having
# a common base class in the future. Right now the signatures are the same for the event signals and
# for the tool tips.
class Widget( object ) :

	## All GafferUI.Widget instances must hold a corresponding QtGui.QWidget instance
	# which provides the top level implementation for the widget, and to which other
	# widgets may be parented. This QWidget is created during __init__, and cannot be
	# replaced later. Derived classes may pass either a QtGui.QWidget directly, or if
	# they prefer may pass a GafferUI.Widget, in which case a top level QWidget will be
	# created automatically, with the GafferUI.Widget being parented to it. The top level
	# QWidget can be accessed at any time using the _qtWidget() method. Note that this is
	# protected to encourage non-reliance on knowledge of the Qt backend.
	#
	# All subclass __init__ methods /must/ accept keyword arguments as **kw, and pass them
	# to their base class constructor. These arguments are used to specify arguments to
	# Container.addChild() when using the automatic parenting mechanism. Keyword arguments
	# must not be used for any other purpose.
	def __init__( self, topLevelWidget, toolTip="", **kw ) :
	
		assert( isinstance( topLevelWidget, ( QtGui.QWidget, Widget ) ) )
		
		if isinstance( topLevelWidget, QtGui.QWidget ) :
			assert( Widget.__qtWidgetOwners.get( topLevelWidget ) is None )
			self.__qtWidget = topLevelWidget
		else :
			self.__gafferWidget = topLevelWidget
			self.__qtWidget = QtGui.QWidget()
			self.__qtWidget.setLayout( QtGui.QGridLayout() )
			## We need to set the size constraint to prevent widgets expanding in an unwanted
			# way. However we may want other types to expand in the future. I think what we
			# really need to do is somehow make __qtWidget without a layout, and just have
			# it's size etc. dictated directly by self.__gafferWidget._qtWidget() somehow.
			self.__qtWidget.layout().setSizeConstraint( QtGui.QLayout.SetMinAndMaxSize )
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
 		self._wheelSignal = None
 		self._visibilityChangedSignal = None
 		self._contextMenuSignal = None
 		
 		self.__visible = not isinstance( self, GafferUI.Window )
 		
		self.setToolTip( toolTip )
		
		# perform automatic parenting if necessary. we don't want to do this
		# for menus, because they don't have the same parenting semantics. if other
		# types end up with similar requirements then we should probably just have
		# a mechanism for them to say they don't want to participate rather than
		# hardcoding stuff here.
		if len( self.__parentStack ) and not isinstance( self, GafferUI.Menu ) :
			if self.__initNesting() == self.__parentStack[-1][1] + 1 :
				self.__parentStack[-1][0].addChild( self, **kw )
				
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
		
	## Sets whether or not this Widget is visible. Widgets are
	# visible by default, except for Windows which need to be made
	# visible explicitly after creation.		
	def setVisible( self, visible ) :
	
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
			# the visibility in _assignQtParent().
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

	## Returns the GafferUI.Widget which is the parent for this
	# Widget, or None if it has no parent.
	def parent( self ) :
	
		q = self._qtWidget()
				
		while q is not None :
					
			q = q.parentWidget()
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
		
	def size( self ) :
	
		return IECore.V2i( self.__qtWidget.width(), self.__qtWidget.height() )

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
	
		self.__ensureEventFilter()
		if self._mouseMoveSignal is None :
			self._mouseMoveSignal = GafferUI.WidgetEventSignal()
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
	
		assert( isinstance( toolTip, basestring ) )
		
		self._qtWidget().setToolTip( toolTip )
		
	## Returns the top level QWidget instance used to implement
	# the GafferUI.Widget functionality.
	def _qtWidget( self ) :
	
		return self.__qtWidget
			
	## Returns the GafferUI.Widget that owns the specified QtGui.QWidget
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
	# can do this automatically.
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
	
		assert( isinstance( container, GafferUI.ContainerWidget ) )
	
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
		frame = inspect.currentframe( 1 )
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
	
		result = GafferUI.ButtonEvent.Buttons.None
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
	
		modifiers = GafferUI.ModifiableEvent.Modifiers.None
		if qtModifiers & QtCore.Qt.ShiftModifier :
			modifiers = modifiers | GafferUI.ModifiableEvent.Modifiers.Shift
		if qtModifiers & QtCore.Qt.ControlModifier :
			modifiers = modifiers | GafferUI.ModifiableEvent.Modifiers.Control
		if qtModifiers & QtCore.Qt.AltModifier :
			modifiers = modifiers | GafferUI.ModifiableEvent.Modifiers.Alt		
			
		return GafferUI.ModifiableEvent.Modifiers( modifiers )
	
	## Converts an IECore.Color[34]f to a QtColor
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
			self.__eventFilterInstalled = True

	def _setStyleSheet( self ):

		self.__qtWidget.setStyleSheet( self.__styleSheet )

	## \todo Unify with GafferUI.Style for colours at least.
	__styleSheet = string.Template( 

		"""
		QWidget#gafferWindow {

			color: $foreground;
			font: 8pt "Sans";
			etch-disabled-text: 0;
			background-color: $backgroundMid;
			border: 1px solid #555555;
		}

		QWidget {
		
			background-color: transparent;
			
		}
		
		QLabel, QCheckBox, QPushButton, QComboBox, QMenu, QMenuBar, QTabBar, QLineEdit, QAbstractItemView, QPlainTextEdit, QDateTimeEdit {
		
			color: $foreground;
			font: 10px;
			etch-disabled-text: 0;
			alternate-background-color: $alternateColor;
			selection-background-color: $brightColor;
			outline: none;
			
		}

		QMenuBar {
		
			background-color: $backgroundDarkest;
			font-weight: bold;
			padding: 0px;
			margin: 0px;
			
		}

		QMenuBar::item {

			background-color: $backgroundDarkest;
			padding: 5px 8px 5px 8px;
			
		}

		QMenu {

			border: 1px solid $backgroundDark;
			padding-bottom: 5px;
			padding-top: 5px;

		}

		QMenu::item {

			background-color: transparent;
			border: 0px;
			padding: 2px 25px 2px 20px;
			
		}
		
		QMenu::item:disabled {

			color: $foregroundFaded;

		}

		QMenu::right-arrow {
			image: url($GAFFER_ROOT/graphics/subMenuArrow.png);
			padding: 0px 7px 0px 0px;
		}
		
		QMenu::separator {

			height: 1px;
			background: $backgroundDark;
			margin-left: 10px;
			margin-right: 10px;
			margin-top: 5px;
			margin-bottom: 5px;

		}
		
		QMenu::indicator {
			padding: 0px 0px 0px 3px;
		}
		
		
		QMenu::indicator:non-exclusive:checked {
			image: url($GAFFER_ROOT/graphics/menuChecked.png);
		}
		
		QMenu::indicator:exclusive:checked:selected {
			image: url($GAFFER_ROOT/graphics/arrowRight10.png);
		}
		
		QMenu, QTabBar::tab:selected, QPushButton, QHeaderView::section, QComboBox {

			background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 $backgroundLight, stop: 1 $backgroundMid);

		}
		
		QPlainTextEdit {
		
			border: 1px solid $backgroundDark;
		
		}

		QLineEdit, QPlainTextEdit[readOnly="false"] {

			border: 1px solid $backgroundDark;
			padding: 1px;
			margin: 0px;

		}

		QLineEdit[readOnly="false"], QPlainTextEdit[readOnly="false"] {

			background-color: $backgroundLighter;

		}

		QLineEdit:focus, QPlainTextEdit[readOnly="false"]:focus {

			border: 2px solid $brightColor;
			padding: 0px;

		}

		QDateTimeEdit {

			background-color: $backgroundLighter;
			padding: 1px;
			margin: 0px;
			border: 1px solid $backgroundDark;	
		}
		
		QDateTimeEdit::drop-down {
			width: 15px;
			image: url($GAFFER_ROOT/graphics/arrowDown10.png);
		}

		#qt_calendar_navigationbar {
		
			background-color : $brightColor;
		
		}
		
		#qt_calendar_monthbutton, #qt_calendar_yearbutton {
		
			color : $foreground;
			font-weight : bold;
			font-size : 16pt;
		
		}
		
		#qt_calendar_monthbutton::menu-indicator {
			image : none;
		}
		
		#qt_calendar_calendarview {
		
			color : $foreground;
			font-weight : normal;
			font-size : 14pt;
			selection-background-color: $brightColor;
			background-color : $backgroundLighter;
			gridline-color: $backgroundDark;

		}
		
		QPushButton, QComboBox {
		
			font-weight: bold;
		
		}

		QPushButton#gafferWithFrame, QComboBox {

			border: 1px solid $backgroundDark;
			border-radius: 3px;
			padding: 4px;

		}

		QPushButton#gafferWithFrame:hover, QComboBox:hover {

			border: 2px solid $brightColor;
			
		}
		
		QPushButton#gafferWithoutFrame {
			
			border: 0px solid transparent;
			border-radius: 3px;
			padding: 0px;
			background-color: none;
			
		}
		
		QPushButton:disabled, QComboBox:disabled {

			color: $foregroundFaded;

		}
		
		QComboBox {
		
			padding: 0;
			padding-left:3px;
			
		}
		
		QComboBox::drop-down {
			width: 15px;
			image: url($GAFFER_ROOT/graphics/arrowDown10.png);
		}
		
		QComboBox QAbstractItemView {
					
			border: 1px solid $backgroundDark;
			selection-background-color: $backgroundLighter;
			background-color: $backgroundMid;
			height:40px;
			margin:0;
			
		}
		
		QComboBox QAbstractItemView::item {
		
			border: none;
			padding: 2px;
			font-weight: bold;
			
		}

		QTabWidget::tab-bar {

			left: 0px;

		}

		QTabBar {
			
			color: $foreground;
			font-weight: bold;
			outline:none;
			background-color: transparent;
			
		}

		QTabBar::tab {

			border: 1px solid $backgroundDark;
			padding: 4px;
			padding-left: 8px;
			padding-right: 8px;
			border-top-left-radius: 3px;
			border-top-right-radius: 3px;
			margin: 0px;
			margin-left: -1px; /* share edge with previous tab */

		}

		/* indent the first tab. can't do this using QTabWidget::tab-bar:left */
		/* as that messes up the alignment of the corner widget (makes it overlap) */
		QTabBar::tab:first, QTabBar::tab:only-one {
		
			margin-left: 10px;
		
		}

		QTabBar::tab:selected {

			border-bottom-color: $backgroundMid; /* blend into frame below */

		}

		QTabBar::tab:!selected {
		
			color: $foregroundFaded;
			background-color: $backgroundDark;
		
		}
		
		QSplitter::handle:vertical {
		
			background-color: $backgroundDark;
			height: 2px;
			margin-top: 2px;
			margin-bottom: 2px;
			/* i don't know why the padding has to be here */
			padding-top: -2px;
			padding-bottom: -2px;
		}
		
		QSplitter::handle:horizontal {
		
			background-color: $backgroundDark;
			width: 2px;
			margin-left: 2px;
			margin-right: 2px;

		}

		/* I'm not sure why this is necessary, but it works around a problem where the */
		/* style for QSplitter::handle:hover isn't always accepted.                    */
		QSplitterHandle:hover {}

		QTabBar::tab:hover, QMenu::item:selected, QMenuBar::item:selected, QSplitter::handle:hover,
		QPushButton:pressed, QComboBox QAbstractItemView::item:hover {

			color: white;
			background-color:	$brightColor;

		}

		/* tab widget frame has a line at the top, tweaked up 1 pixel */
		/* so that it sits underneath the bottom of the tabs.         */
		/* this means the active tab can blend into the frame.        */
		QTabWidget::pane {
			border: 1px solid $backgroundDark;
			border-top: 1px solid $backgroundDark;
			top: -1px;
		}

		QCheckBox#gafferCollapsibleToggle {
		
			font-weight: bold;
		}

		QCheckBox#gafferCollapsibleToggle::indicator {

			width: 12px;
			height: 12px;
			background-color: none;

		}

		QCheckBox#gafferCollapsibleToggle::indicator:unchecked {

			image: url($GAFFER_ROOT/graphics/collapsibleArrowDown.png);

		}

		QCheckBox#gafferCollapsibleToggle::indicator:checked {

			image: url($GAFFER_ROOT/graphics/collapsibleArrowRight.png);

		}
		
		QCheckBox#gafferCollapsibleToggle::indicator:unchecked:hover, QCheckBox#gafferCollapsibleToggle::indicator:unchecked:focus {

			image: url($GAFFER_ROOT/graphics/collapsibleArrowDownHover.png);

		}

		QCheckBox#gafferCollapsibleToggle::indicator:checked:hover, QCheckBox#gafferCollapsibleToggle::indicator:checked:focus {

			image: url($GAFFER_ROOT/graphics/collapsibleArrowRightHover.png);

		}
		
		QHeaderView {
		
			border: 0px;
			margin: 0px;
		
		}
		
		QHeaderView::section {
		
			border: 1px solid $backgroundDark;
			padding: 6px;
			font-weight: bold;
			margin: 0px;
		
		}
		
		/* tuck adjacent header sections beneath one another so we only get */
		/* a single width line between them                                 */
		QHeaderView::section:horizontal:!first {
		
			margin-left: -1px;
		
		}
		
		QHeaderView::section:horizontal:only-one {
		
			margin-left: 0px;
		
		}
		
		QHeaderView::section:vertical:!first {
		
			margin-top: -1px;
		
		}
		
		QHeaderView::section:vertical:only-one {
		
			margin-top: 0px;
		
		}
		
		QHeaderView::down-arrow {
			
			image: url($GAFFER_ROOT/graphics/headerSortDown.png);
			
		}
		
		QHeaderView::up-arrow {
			
			image: url($GAFFER_ROOT/graphics/headerSortUp.png);
		
		}

		QScrollBar {
		
			border: 1px solid $backgroundDark;
			background-color: $backgroundDark;
			
		}
		
		QScrollBar:vertical {
		
			width: 14px;
			margin: 0px 0px 28px 0px;
			
		}
		
		QScrollBar:horizontal {
		
			height: 14px;
			margin: 0px 28px 0px 0px;
			
		}
		
		QScrollBar::add-page, QScrollBar::sub-page {
			background: none;
 			border: none;
		}
		
		QScrollBar::add-line, QScrollBar::sub-line {
			background-color: $backgroundLight;
			border: 1px solid $backgroundDark;
		}
		
		QScrollBar::add-line:vertical {
			height: 14px;
			subcontrol-position: bottom;
			subcontrol-origin: margin;
		}
		
		QScrollBar::add-line:horizontal {
			width: 14px;
			subcontrol-position: right;
			subcontrol-origin: margin;
		}

		QScrollBar::sub-line:vertical {
			height: 14px;
			subcontrol-position: bottom right;
			subcontrol-origin: margin;
			position: absolute;
			bottom: 15px;
		}
		
		QScrollBar::sub-line:horizontal {
			width: 14px;
			subcontrol-position: top right;
			subcontrol-origin: margin;
			position: absolute;
			right: 15px;
		}
		
		QScrollBar::down-arrow {
			image: url($GAFFER_ROOT/graphics/arrowDown10.png);
		}
		
		QScrollBar::up-arrow {
			image: url($GAFFER_ROOT/graphics/arrowUp10.png);
		}
		
		QScrollBar::left-arrow {
			image: url($GAFFER_ROOT/graphics/arrowLeft10.png);
		}
		
		QScrollBar::right-arrow {
			image: url($GAFFER_ROOT/graphics/arrowRight10.png);
		}

		QScrollBar::handle {
			background-color: $backgroundLight;			
			border: 1px solid $backgroundDark;
		}
		
		QScrollBar::handle:vertical {
			min-height: 14px;
			border-left: none;
			border-right: none;			
			margin-top: -1px;		
		}
		
		QScrollBar::handle:horizontal {
			min-width: 14px;
			border-top: none;
			border-bottom: none;
			margin-left: -1px;		
		}
		
		QScrollBar::handle:hover, QScrollBar::add-line:hover, QScrollBar::sub-line:hover {
			background-color: $brightColor;
		}
		
		QScrollArea {
			border: none;
		}
		
		QCheckBox {
			spacing: 5px;
		}

		QTreeView QHeaderView {
			/* tuck header border inside the treeview border */
			margin-top: -1px;
			margin-left: -1px;
			margin-right: -1px;
		}
		
		QTreeView::branch {
			border-image : none;
			image : none;		
		}

		QTreeView::branch:closed:has-children {
			border-image : none;
			image : url($GAFFER_ROOT/graphics/collapsibleArrowRight.png);
		}
		
		QTreeView::branch:open:has-children {
			border-image : none;
			image : url($GAFFER_ROOT/graphics/collapsibleArrowDown.png);
		}
		
		QCheckBox::indicator {
			width: 20px;
			height: 20px;
			background-color: transparent;			
		}
		
		QCheckBox::indicator:unchecked {
			image: url($GAFFER_ROOT/graphics/checkBoxUnchecked.png);
		}
		
		QCheckBox::indicator:unchecked:hover, QCheckBox::indicator:unchecked:focus {
			image: url($GAFFER_ROOT/graphics/checkBoxUncheckedHover.png);
		}
		QCheckBox::indicator:checked:hover, QCheckBox::indicator:checked:focus {
			image: url($GAFFER_ROOT/graphics/checkBoxCheckedHover.png);
		}
		
		QCheckBox::indicator:checked {
			image: url($GAFFER_ROOT/graphics/checkBoxChecked.png);
		}

		.QFrame#borderStyleNone {
			border: 1px solid transparent;
			border-radius: 4px;
			padding: 2px;
		}
		
		.QFrame#borderStyleFlat {
			border: 1px solid $backgroundDark;
			border-radius: 4px;
			padding: 2px;
		}
		
		QToolTip {
			background-clip: border;
			color: $backgroundDarkest;
			background-color: $brightColor2;
			border: 1px solid $backgroundDark;
			padding: 2px;

		}

		QTreeView {
			border: 1px solid $backgroundDark;
			padding: 0px;
		}

		QTreeView::item:selected {
			background-color: $brightColor;
		}

		QTableView {
		
			border: 0px solid transparent;
		
		}

		QTableView::item:selected {
			background-color: $brightColor;
		}
		
		QTableView QTableCornerButton::section {
			background-color: $backgroundMid;
			border: 1px solid $backgroundMid;
		}
	
		QTableView#vectorDataWidget {
			border: 1px solid $backgroundDark;
			gridline-color: $backgroundDark;
			padding: 0px;
			background-color: transparent;
		}
		
		QTableView#vectorDataWidgetEditable {
			padding: 0px;
			gridline-color: $backgroundDark;
		}

		QTableView::item#vectorDataWidgetEditable {
			background-color: $backgroundLighter;
		}
		
		QTableView::item:selected#vectorDataWidgetEditable {
			background-color: $brightColor;
		}
			
		QHeaderView::section#vectorDataWidgetVerticalHeader {
			background-color: transparent;
		}
		
		QTableView::indicator {
			background-color: transparent;
		}
		
		QTableView::indicator:unchecked {
			image: url($GAFFER_ROOT/graphics/checkBoxUnchecked.png);		
		}
		
		QTableView::indicator:unchecked:hover {
			image: url($GAFFER_ROOT/graphics/checkBoxUncheckedHover.png);		
		}
		
		QTableView::indicator:checked {
			image: url($GAFFER_ROOT/graphics/checkBoxChecked.png);
		}
		
		QTableView::indicator:checked:hover {
			image: url($GAFFER_ROOT/graphics/checkBoxCheckedHover.png);
		}
		
		QTableView::indicator:selected {
			background-color: $brightColor;
		}
		
		QProgressBar {
		
			border: 1px solid $backgroundDark;
			background: $backgroundLighter;
			padding: 1px;
			text-align: center;
			
		}
		
		QProgressBar::chunk:horizontal {
		
			background-color: $brightColor;
		
		}
		
		"""
		
	).substitute( {
	
		"GAFFER_ROOT" : os.environ["GAFFER_ROOT"],
		"backgroundDarkest" : "#000000",
		"backgroundDark" : "#3c3c3c",
		"backgroundMid" : "#4c4c4c",
		"backgroundLighter" : "#6c6c6c",
		"backgroundLight" : "#7d7d7d",
		"brightColor" : "#779cbd",
		"brightColor2" : "#e5c618",
		"foreground" : "#f0f0f0",
		"foregroundFaded" : "#999999",
		"alternateColor" : "#454545",
	
	} )
	
class _EventFilter( QtCore.QObject ) :

	def __init__( self ) :
	
		QtCore.QObject.__init__( self )
	
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
		) )
	
	def eventFilter( self, qObject, qEvent ) :
				
		qEventType = qEvent.type() # for speed it's best not to keep calling this below
		# early out as quickly as possible for the majority of cases where we have literally
		# no interest in the event.
		if qEventType not in self.__eventMask :
			return False
		
		# we display tooltips and emit visibility events even on disabled widgets
		if qEventType==qEvent.ToolTip :
		
			widget = Widget._owner( qObject )
			QtGui.QToolTip.showText( qEvent.globalPos(), widget.getToolTip(), qObject )
			return True
			
		elif qEventType==qEvent.Show or qEventType==qEvent.Hide :
				
			widget = Widget._owner( qObject )
			if widget is not None and widget._visibilityChangedSignal is not None :
				widget._visibilityChangedSignal( widget )
			return False

		# but for anything else we ignore disabled widgets
		if not qObject.isEnabled() :
			return False
			
		if qEventType==qEvent.KeyPress :
						
			widget = Widget._owner( qObject )
			if widget._keyPressSignal is not None :

				event = GafferUI.KeyEvent(
					Widget._key( qEvent.key() ),
					Widget._modifiers( qEvent.modifiers() ),
				)

				return widget._keyPressSignal( widget, event )

		elif qEventType==qEvent.KeyRelease :
						
			widget = Widget._owner( qObject )
			if widget._keyReleaseSignal is not None :

				event = GafferUI.KeyEvent(
					Widget._key( qEvent.key() ),
					Widget._modifiers( qEvent.modifiers() ),
				)

				return widget._keyReleaseSignal( widget, event )
		
		elif qEventType==qEvent.MouseButtonPress :
					
			widget = Widget._owner( qObject )
			if widget._buttonPressSignal is not None :
				event = GafferUI.ButtonEvent(
					Widget._buttons( qEvent.buttons() ),
					IECore.LineSegment3f(
						IECore.V3f( qEvent.x(), qEvent.y(), 1 ),
						IECore.V3f( qEvent.x(), qEvent.y(), 0 )
					),
					0.0,
					Widget._modifiers( qEvent.modifiers() ),
				)
	
				if event.buttons  :
					return widget._buttonPressSignal( widget, event )
			
		elif qEventType==qEvent.MouseButtonRelease :
				
			widget = Widget._owner( qObject )
			if widget._buttonReleaseSignal is not None :

				event = GafferUI.ButtonEvent(
					Widget._buttons( qEvent.buttons() ),
					IECore.LineSegment3f(
						IECore.V3f( qEvent.x(), qEvent.y(), 1 ),
						IECore.V3f( qEvent.x(), qEvent.y(), 0 )
					),
					0.0,
					Widget._modifiers( qEvent.modifiers() ),
				)

				return widget._buttonReleaseSignal( widget, event )
				
		elif qEventType==qEvent.MouseButtonDblClick :
				
			widget = Widget._owner( qObject )
			if widget._buttonDoubleClickSignal is not None :

				event = GafferUI.ButtonEvent(
					Widget._buttons( qEvent.buttons() ),
					IECore.LineSegment3f(
						IECore.V3f( qEvent.x(), qEvent.y(), 1 ),
						IECore.V3f( qEvent.x(), qEvent.y(), 0 )
					),
					0.0,
					Widget._modifiers( qEvent.modifiers() ),
				)

				return widget._buttonDoubleClickSignal( widget, event )		
			
		elif qEventType==qEvent.MouseMove :
				
			widget = Widget._owner( qObject )
			if widget._mouseMoveSignal is not None :

				event = GafferUI.ButtonEvent(
					Widget._buttons( qEvent.buttons() ),
					IECore.LineSegment3f(
						IECore.V3f( qEvent.x(), qEvent.y(), 1 ),
						IECore.V3f( qEvent.x(), qEvent.y(), 0 )
					),
					0.0,
					Widget._modifiers( qEvent.modifiers() ),
				)

				return widget._mouseMoveSignal( widget, event )
		
		elif qEventType==qEvent.Enter :
				
			widget = Widget._owner( qObject )
			if widget._enterSignal is not None :
				return widget._enterSignal( widget )
			
		elif qEventType==qEvent.Leave :
				
			widget = Widget._owner( qObject )
			if widget._leaveSignal is not None :
				return widget._leaveSignal( widget )
			
		elif qEventType==qEvent.Wheel :
				
			widget = Widget._owner( qObject )
			if widget._wheelSignal is not None :
			
				event = GafferUI.ButtonEvent(
					Widget._buttons( qEvent.buttons() ),
					IECore.LineSegment3f(
						IECore.V3f( qEvent.x(), qEvent.y(), 1 ),
						IECore.V3f( qEvent.x(), qEvent.y(), 0 )
					),
					qEvent.delta() / 8.0,
					Widget._modifiers( qEvent.modifiers() ),
				)
	
				return widget._wheelSignal( widget, event )
				
		elif qEventType==qEvent.ContextMenu :
		
			widget = Widget._owner( qObject )
			if widget._contextMenuSignal is not None :
				return widget._contextMenuSignal( widget )
			
		return False

# this single instance is used by all widgets
_eventFilter = _EventFilter()

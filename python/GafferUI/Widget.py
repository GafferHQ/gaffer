##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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
	def __init__( self, topLevelWidget, toolTip="" ) :
	
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
				
		self.__qtWidget.installEventFilter( _eventFilter )

		# disable different focus appearance on os x
		## \todo If we have a style class for Widget at some point, then perhaps
		# this should go in there.
		self.__qtWidget.setAttribute( QtCore.Qt.WA_MacShowFocusRect, False )
		
		self.__keyPressSignal = GafferUI.WidgetEventSignal()
		self.__buttonPressSignal = GafferUI.WidgetEventSignal()
		self.__buttonReleaseSignal = GafferUI.WidgetEventSignal()
		self.__mouseMoveSignal = GafferUI.WidgetEventSignal()
		self.__enterSignal = GafferUI.WidgetSignal()
		self.__leaveSignal = GafferUI.WidgetSignal()
		self.__wheelSignal = GafferUI.WidgetEventSignal()
		
		self.setToolTip( toolTip )
		
		if len( self.__parentStack ) :
			self.__parentStack[-1].addChild( self )
				
	def setVisible( self, visible ) :
	
		self.__qtWidget.setVisible( visible )
	
	## \todo Make these functions consistent with the enabled ones below,
	# and document them.
	def getVisible( self ) :
	
		return self.__qtWidget.isVisible()

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
	
		return self.__keyPressSignal
	
	## \todo Should these be renamed to mousePressSignal and mouseReleaseSignal?	
	def buttonPressSignal( self ) :
	
		return self.__buttonPressSignal
	
	def buttonReleaseSignal( self ) :
	
		return self.__buttonReleaseSignal
	
	def mouseMoveSignal( self ) :
	
		return self.__mouseMoveSignal
	
	def enterSignal( self ) :
	
		return self.__enterSignal
		
	def leaveSignal( self ) :
	
		return self.__leaveSignal
		
	def wheelSignal( self ) :
	
		return self.__wheelSignal
	
	## Returns the tooltip to be displayed. This may be overriden
	# by derived classes to provide sensible default behaviour, but
	# allow custom behaviour when setToolTip( nonEmptyString ) has
	# been called.
	def getToolTip( self ) :
	
		return self.__toolTip
	
	## Sets the tooltip to be displayed for this Widget. This
	# will override any default behaviour until setToolTip( "" )
	# is called.
	def setToolTip( self, toolTip ) :
	
		assert( isinstance( toolTip, basestring ) )
		
		self.__toolTip = toolTip
		
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
	
	## Used by the ContainerWidget classes to implement the automatic parenting
	# using the with statement.
	@classmethod
	def _pushParent( cls, container ) :
	
		assert( isinstance( container, GafferUI.ContainerWidget ) )
	
		cls.__parentStack.append( container )
	
	@classmethod
	def _popParent( cls ) :
	
		return cls.__parentStack.pop()
	
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
		if qtButtons & QtCore.Qt.MiddleButton :
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
	
	def _setStyleSheet( self ):

		self.__qtWidget.setStyleSheet( self.__styleSheet )

	## \todo Unify with GafferUI.Style for colours at least.
	__styleSheet = string.Template( 

		"""
		QWidget#gafferWindow {

			color: $foreground;
			font-size: 10px;
			etch-disabled-text: 0;
			background-color: $backgroundMid;
			border: 1px solid #555555;
		}

		QWidget {
		
			background-color: transparent;
			
		}
		
		QLabel, QCheckBox, QPushButton, QComboBox, QMenu, QMenuBar, QTabBar, QLineEdit, QAbstractItemView, QPlainTextEdit {
		
			color: $foreground;
			font-size: 10px;
			etch-disabled-text: 0;
			alternate-background-color: $backgroundLighter;
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

			border: 1px solid $backgroundDarkest;
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
			background: $backgroundDarkest;
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
					
			border: 1px solid $backgroundDarkest;
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

			left: 10px;

		}

		QTabBar {
			
			color: $foreground;
			font-weight: bold;
			outline:none;
			background-color: $backgroundMid;
			
		}

		QTabBar::tab {

			border: 1px solid $backgroundDarkest;
			padding: 4px;
			padding-left: 8px;
			padding-right: 8px;
			border-top-left-radius: 3px;
			border-top-right-radius: 3px;

		}

		QTabBar::tab:selected {

			border-bottom-color: transparent; /* blend into frame below */

		}

		QTabBar::tab:!selected, QSplitter::handle {

			background-color: $backgroundDark;

		}
		
		QSplitter::handle:horizontal {
			width: 4px;
		}

		QSplitter::handle:vertical {
			height: 4px;
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
			border-top: 1px solid $backgroundDarkest;
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
		
		QHeaderView::section {
		
			border: 1px solid transparent;
			border-bottom: 1px solid $backgroundDarkest;
			padding: 4px;
			font-weight: bold;
		
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
			border: 1px solid $backgroundDarkest;
			border-radius: 4px;
			padding: 2px;
		}
		
		QToolTip {
			background-clip: border;
			color: $backgroundDarkest;
			background-color: $brightColor2;
			border: 1px solid $backgroundDarkest;
			padding: 2px;

		}

		QTreeView {
			border: 1px solid $backgroundDark;
			padding: 0px;
		}

		QTreeView::item:selected {
			background-color: $brightColor;
		}

		QTableView::item:selected {
			background-color: $brightColor;
		}
		
		QTableView QTableCornerButton::section {
			background-color: $backgroundMid;
			border: 1px solid $backgroundMid;
		}
	
		QTableView#vectorDataWidget {
			border: 0px solid transparent;
			padding: 0px;
		}
		
		QTableView#vectorDataWidgetEditable {
			border: 0px solid transparent;
			padding: 0px;
			background-color: $backgroundLighter;
			gridline-color: $backgroundMid;
		}
			
		QHeaderView::section#vectorDataWidgetVerticalHeader {
			background-color: transparent;
			border: 0px solid transparent;
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
	
	} )
	
class _EventFilter( QtCore.QObject ) :

	def __init__( self ) :
	
		QtCore.QObject.__init__( self )
		
	def eventFilter( self, qObject, qEvent ) :
		
		# we display tooltips even on disabled widgets
		if qEvent.type()==QtCore.QEvent.ToolTip :
		
			widget = Widget._owner( qObject )
			QtGui.QToolTip.showText( qEvent.globalPos(), widget.getToolTip(), qObject )
			return True
		
		# but for anything else we ignore disabled widgets
		if not qObject.isEnabled() :
			return False
			
		if qEvent.type()==QtCore.QEvent.KeyPress :
						
			widget = Widget._owner( qObject )
			event = GafferUI.KeyEvent(
				Widget._key( qEvent.key() ),
				Widget._modifiers( qEvent.modifiers() ),
			)

			return widget.keyPressSignal()( widget, event )
		
		elif qEvent.type()==QtCore.QEvent.MouseButtonPress :
					
			widget = Widget._owner( qObject )
			event = GafferUI.ButtonEvent(
				Widget._buttons( qEvent.buttons() ),
				IECore.LineSegment3f(
					IECore.V3f( qEvent.x(), qEvent.y(), 1 ),
					IECore.V3f( qEvent.x(), qEvent.y(), 0 )
				),
				0.0,
				Widget._modifiers( qEvent.modifiers() ),
			)

			if event.buttons :
				return widget.buttonPressSignal()( widget, event )
			
		elif qEvent.type()==QtCore.QEvent.MouseButtonRelease :
				
			widget = Widget._owner( qObject )
			event = GafferUI.ButtonEvent(
				Widget._buttons( qEvent.buttons() ),
				IECore.LineSegment3f(
					IECore.V3f( qEvent.x(), qEvent.y(), 1 ),
					IECore.V3f( qEvent.x(), qEvent.y(), 0 )
				),
				0.0,
				Widget._modifiers( qEvent.modifiers() ),
			)

			return widget.buttonReleaseSignal()( widget, event )
			
		elif qEvent.type()==QtCore.QEvent.MouseMove :
				
			widget = Widget._owner( qObject )
			event = GafferUI.ButtonEvent(
				Widget._buttons( qEvent.buttons() ),
				IECore.LineSegment3f(
					IECore.V3f( qEvent.x(), qEvent.y(), 1 ),
					IECore.V3f( qEvent.x(), qEvent.y(), 0 )
				),
				0.0,
				Widget._modifiers( qEvent.modifiers() ),
			)

			return widget.mouseMoveSignal()( widget, event )
		
		elif qEvent.type()==QtCore.QEvent.Enter :
				
			widget = Widget._owner( qObject )

			return widget.enterSignal()( widget)
			
		elif qEvent.type()==QtCore.QEvent.Leave :
				
			widget = Widget._owner( qObject )

			return widget.leaveSignal()( widget)
			
		elif qEvent.type()==QtCore.QEvent.Wheel :
				
			widget = Widget._owner( qObject )
			event = GafferUI.ButtonEvent(
				Widget._buttons( qEvent.buttons() ),
				IECore.LineSegment3f(
					IECore.V3f( qEvent.x(), qEvent.y(), 1 ),
					IECore.V3f( qEvent.x(), qEvent.y(), 0 )
				),
				qEvent.delta() / 8.0,
				Widget._modifiers( qEvent.modifiers() ),
			)

			return widget.wheelSignal()( widget, event )	
			
		return False

# this single instance is used by all widgets
_eventFilter = _EventFilter()

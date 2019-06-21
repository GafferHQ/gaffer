##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2014, Image Engine Design Inc. All rights reserved.
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

import os
import string

from Qt import QtGui

_styleColors = {

	"backgroundDarkest" : (0, 0, 0),

	"backgroundDarker" : (45, 45, 45),

	"backgroundDark" : (56, 56, 56),
	"backgroundDarkTransparent" : (56, 56, 56, 100),
	"backgroundDarkHighlight" : (62, 62, 62),

	"backgroundLowlight" : (68, 68, 68),
	"background" : (76, 76, 76),
	"backgroundHighlight" : (88, 88, 88),

	"backgroundRaisedLowlight" : (70, 70, 70),
	"backgroundRaised" : (82, 82, 82),
	"backgroundRaisedHighlight" : (96, 96, 96),

	"backgroundLightLowlight" : (82, 82, 82),
	"backgroundLight" : (96, 96, 96),
	"backgroundLightHighlight" : (106, 106, 106),

	"backgroundLighter" : (125, 125, 125),

	"brightColor" : (119, 156, 189),
	"brightColorTransparent" : (119, 156, 189, 100),

	"foreground" : (224, 224, 224),
	"foregroundFaded" : (153, 153, 153),

	"errorColor" : (255, 85, 85),
	"animatedColor" : (128, 152, 94),

	"tintLighter" :         ( 255, 255, 255, 20 ),
	"tintLighterStrong" :   ( 255, 255, 255, 40 ),
	"tintLighterStronger" : ( 255, 255, 255, 100 ),
	"tintDarker" :          ( 0, 0, 0, 20 ),
	"tintDarkerStrong" :    ( 0, 0, 0, 40 ),
}

_themeVariables = {
	"widgetCornerRadius" : "4px",
	"controlCornerRadius" : "2px"
}

substitutions = {
	"GAFFER_ROOT" : os.environ["GAFFER_ROOT"]
}

for k, v in _styleColors.items() :
	if len( v ) == 3 :
		substitutions[k] = "rgb({0}, {1}, {2})".format( *v )
	elif len( v ) == 4 :
		substitutions[k] = "rgba({0}, {1}, {2}, {3})".format( *v )

substitutions.update( _themeVariables )

def styleColor( key ) :
	color = _styleColors.get( key, (0, 0, 0,) )

	if len( color ) == 3 :
		return QtGui.QColor.fromRgb( *color )
	elif len( color ) == 4 :
		return QtGui.QColor.fromRgba( *color )

	return QtGui.QColor()

## \todo Unify with GafferUI.Style for colours at least.
_styleSheet = string.Template(

	"""
	QWidget#gafferWindow {
		color: $foreground;
		font: 10px;
		etch-disabled-text: 0;
		background-color: $backgroundLowlight;
		border: 1px solid #555555;
	}

	QWidget {
		background-color: transparent;
	}

	QLabel, QCheckBox, QPushButton, QComboBox, QMenu, QMenuBar,
	QTabBar, QLineEdit, QAbstractItemView, QPlainTextEdit, QDateTimeEdit {
		color: $foreground;
		font: 10px;
		etch-disabled-text: 0;
		selection-background-color: $brightColor;
		outline: none;
	}

	QLabel[gafferHighlighted=\"true\"] {
		color: #b0d8fb;
	}

	QLabel#gafferPlugLabel[gafferValueChanged=\"true\"] {
		background-image: url($GAFFER_ROOT/graphics/valueChanged.png);
		background-repeat: no-repeat;
		background-position: left;
		padding-left: 20px;
	}


	QLabel[gafferItemName="true"] {
		font-weight: bold;
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
		background-color: $backgroundLight;
	}

	QMenu[gafferHasTitle=\"true\"] {
		/* make sure the title widget sits at the very top.
		   infuriatingly, qt uses padding-top for the bottom
		   as well, and is ignoring padding-bottom. that makes
		   menus with title just a little bit poorly padded
		   at the bottom. we hack around that by adding a little
		   spacing widget in GafferUI.Menu. */
		padding-top: 0px;
	}

	QLabel#gafferMenuTitle {
		background-color: $backgroundDarkest;
		font-weight: bold;
		padding: 5px 25px 5px 20px;
		margin-bottom: 6px;
	}

	QLabel#gafferMenuTitle:disabled {
		color: $foreground;
	}

	QMenu::item {
		color: $foreground;
		background-color: transparent;
		border: 0px;
		padding: 2px 25px 2px 20px;
	}

	QMenu::item:disabled {
		color: $tintLighterStronger;
	}

	QMenu::right-arrow {
		image: url($GAFFER_ROOT/graphics/subMenuArrow.png);
		padding: 0px 7px 0px 0px;
	}

	QMenu::separator {
		height: 1px;
		background: $backgroundLowlight;
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

	QLineEdit, QPlainTextEdit {
		padding: 0px;
		border: 1px solid transparent;
		border-bottom-color: $backgroundLightLowlight;
		border-right-color: $backgroundLightLowlight;
		background-color: $backgroundLight;
		border-radius: ${controlCornerRadius};
	}


	QLineEdit[readOnly="true"], QPlainTextEdit[readOnly="true"] {
		padding: 0px;
		background-color: transparent;
		border-color: transparent;
	}

	QLineEdit[gafferError="true"], QPlainTextEdit[gafferError="true"] {
		background-color: $errorColor;
	}

	QLineEdit[gafferAnimated="true"] {
		padding: 0px;
		border: 1px solid transparent;
		background-color: $animatedColor;
	}

	QPlainTextEdit[gafferRole="Code"] {
		font-family: monospace;
	}

	QLineEdit:focus, QPlainTextEdit[readOnly="false"]:focus, QLineEdit[gafferHighlighted=\"true\"] {
		border: 1px solid $brightColor;
		padding: 0px;
	}

	QLineEdit:disabled {
		color: $foregroundFaded;
	}

	QLineEdit#search{
		background-image: url($GAFFER_ROOT/graphics/search.png);
		background-repeat:no-repeat;
		background-position: left center;
		padding-left: 20px;
		height:20px;
		border-radius:5px;
		margin-left: 4px;
		margin-right: 4px;
	}

	QWidget#gafferSplineWidget {
		border: 1px solid $backgroundDark;
	}

	QWidget#gafferSplineWidget[gafferHighlighted=\"true\"] {
		border: 1px solid $brightColor;
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

	/* buttons */

	QPushButton#gafferWithFrame,
	QComboBox {
		border: 1px solid $backgroundDarkHighlight;
		border-top-color: $backgroundLightHighlight;
		border-left-color: $backgroundLightHighlight;
		background-color : qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 $backgroundLightHighlight, stop: 0.1 $backgroundLight, stop: 0.90 $backgroundLightLowlight);
		border-radius: 4px;
		padding: 4px;
		margin: 1px;
		font-weight: bold;
	}

	QPushButton#gafferWithFrame[gafferMenuButton="true"] {
		padding: 2px;
	}

	*[gafferPlugValueWidget="true"] QPushButton#gafferWithFrame[gafferMenuButton="true"] {
		font-weight: normal;
		text-align: left;
	}

	QPushButton#gafferWithFrame:focus {
		border: 1px solid $brightColor;
	}

	QPushButton#gafferWithFrame:pressed {
		color: white;
		background-color:	$brightColor;
	}

	QPushButton#gafferWithoutFrame {
		border: 0px solid transparent;
		border-radius: 0px;
		padding: 0px;
		margin: 0px;
		/* negative margins to counteract the annoying
		   hardcoded padding in QPushButton::sizeHint() */
		margin-left: -2px;
		margin-right: -2px;
		background-color: none;
	}

	QPushButton:disabled, QComboBox:disabled, QLabel::disabled {
		color: $foregroundFaded;
	}

	QPushButton#gafferWithFrame:disabled {
		color: $tintLighterStrong;
		background-color: $tintDarker;
		border-color: transparent;
	}

	QPushButton::menu-indicator {
		image: url($GAFFER_ROOT/graphics/arrowDown10.png);
		subcontrol-position: right center;
		subcontrol-origin: padding;
		left: -4px;
	}

	QPushButton#gafferWithFrame[gafferMenuIndicator="true"] {
		background-image: url($GAFFER_ROOT/graphics/menuIndicator.png);
		background-repeat: none;
		background-position: center right;
		padding-right: 20px
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
		background-color: $background;
		height:40px;
		margin:0;
		text-align: left;
	}

	QComboBox QAbstractItemView::item {
		border: none;
		padding: 2px;
	}

	/* tabs */

	QTabWidget::tab-bar {
		left: 0px;
	}

	QTabWidget #gafferCompoundEditorTools  {
		margin: 0;
		padding: 0;
		border: none;
	}

	QTabBar {
		color: $foreground;
		font-weight: bold;
		outline:none;
		background-color: transparent;
	}

	QTabBar::tab {
		padding: 4px;
		padding-left: 8px;
		padding-right: 8px;
		border-top-left-radius: 4px;
		border-top-right-radius: 4px;
		margin: 0px;
		margin-right: 1px;
		border: 1px solid $backgroundHighlight;
		border-right-color: $backgroundLowlight;
		border-bottom-color: $background /* blend into frame below */
	}

	QTabBar::tab:disabled {
		color: $tintLighter;
	}

	QTabBar::tab:selected {
		background-color: $background;
	}

	QTabWidget QTabWidget > QTabBar::tab:selected {
		background-color: $backgroundRaised;
		border-color: $backgroundRaisedHighlight;
		border-right-color: $backgroundRaisedLowlight;
		border-bottom-color: $backgroundRaised; /* blend into frame below */
	}

	QTabBar::tab:!selected {
		color: $tintLighterStronger;
		background-color: $backgroundDark;
		border-color: transparent;
		border-bottom-color: $background;
	}

	QTabBar::tab:!selected:hover {
		background-color: $backgroundDarkHighlight;
	}

	QTabWidget QTabWidget > QTabBar::tab:!selected {
		color: $tintLighterStronger;
		background-color: $backgroundDarkHighlight;
		border-color: transparent;
		border-bottom-color: $backgroundRaisedHighlight;
	}

	QTabWidget QTabWidget > QTabBar::tab:!selected:hover {
		background-color: $backgroundDarkHighlight;
	}

	QSplitter[gafferHighlighted="true"] {

		border: 1px solid $brightColor;
	}

	QTabWidget::pane {
		background-color: $background;
		/* tab widget frame has a line at the top, tweaked up 1 pixel */
		/* so that it sits underneath the bottom of the tabs.         */
		/* this means the active tab can blend into the frame.        */
		top: -1px;
		border-radius: 2px;
		border-top-left-radius: 0;
		border: 1px solid $backgroundHighlight;
		border-right-color: $backgroundLowlight;
		border-bottom-color: $backgroundLowlight;
	}

	QTabWidget[gafferNumChildren="0"]::pane {
		background-color: $backgroundDarker;
		border-color: $backgroundDarker;
	}

	QTabWidget QTabWidget::pane {
		background-color: $backgroundRaised;
		border-radius: $widgetCornerRadius;
		border-top-left-radius: 0;
		border-color: $backgroundRaisedHighlight;
		border-right-color: $backgroundRaisedLowlight;
		border-bottom-color: $backgroundRaisedLowlight;
	}

	/* Ensures the QSplitter border is visible if we need to highlight */
	QSplitter#gafferCompoundEditor[gafferNumChildren="1"] {
		padding: 1px;
	}

	QSplitter::handle:vertical {
		height: 2px;
		border: 1px;
		margin: 1px;
		padding: -2px;
	}

	QSplitter::handle:horizontal {
		width: 2px;
		border: 1px;
		margin: 1px;
		padding: -2px;
	}

	/* I'm not sure why this is necessary, but it works around a problem where the */
	/* style for QSplitter::handle:hover isn't always accepted.                    */
	QSplitterHandle:hover {}

	QMenu::item:selected, QMenuBar::item:selected, QSplitter::handle:hover {
		color: white;
		background-color: $brightColor;
	}
	QTabWidget[gafferHighlighted=\"true\"]::pane {
		border: 1px solid $brightColor;
		border-top: 1px solid $brightColor;
		top: -1px;
	}

	QTabWidget[gafferHighlighted=\"true\"] > QTabBar::tab:selected {
		border-bottom-color: $background; /* blend into frame below */
	}

	QTabwidget QTabWidget[gafferHighlighted=\"true\"] > QTabBar::tab:selected {
		border-bottom-color: $backgroundRaised; /* blend into frame below */
	}

	QTabWidget[gafferHighlighted=\"true\"] > QTabBar::tab:!selected {
		border-bottom-color: $brightColor;
	}

	QCheckBox#gafferCollapsibleToggle {
		font-weight: bold;
	}

	QWidget#gafferCollapsible QWidget#gafferCollapsible > QCheckBox#gafferCollapsibleToggle {
		margin-left: 10px;
	}

	QCheckBox#gafferCollapsibleToggle:disabled {
		color: $foregroundFaded;
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

	QCheckBox#gafferCollapsibleToggle::indicator:unchecked:hover,
	QCheckBox#gafferCollapsibleToggle::indicator:unchecked:focus {
		image: url($GAFFER_ROOT/graphics/collapsibleArrowDownHover.png);
	}

	QCheckBox#gafferCollapsibleToggle::indicator:checked:hover,
	QCheckBox#gafferCollapsibleToggle::indicator:checked:focus {
		image: url($GAFFER_ROOT/graphics/collapsibleArrowRightHover.png);
	}

	QHeaderView {
		border: 0px;
		margin: 0px;
	}

	QHeaderView::section {
		border: 1px solid $backgroundLowlight;
		border-radius: 0;
		padding: 3px;
		font-weight: bold;
		margin: 0px;
		background-color: $tintLighter;
	}

	QHeaderView::section:first#vectorDataWidgetVerticalHeader {
		border-top-left-radius: $widgetCornerRadius;
	}

	QHeaderView::section:last#vectorDataWidgetVerticalHeader {
		border-bottom-left-radius: $widgetCornerRadius;
	}

	QHeaderView::section:only-one#vectorDataWidgetVerticalHeader {
		border-top-left-radius: $widgetCornerRadius;
		border-bottom-left-radius: $widgetCornerRadius;
	}

	QHeaderView::section:first#vectorDataWidgetHorizontalHeader {
		border-top-left-radius: $widgetCornerRadius;
	}

	QHeaderView::section:last#vectorDataWidgetHorizontalHeader {
		border-top-right-radius: $widgetCornerRadius;
	}

	QHeaderView::section:only-one#vectorDataWidgetHorizontalHeader {
		border-top-left-radius: $widgetCornerRadius;
		border-top-right-radius: $widgetCornerRadius;
	}

	/* tuck adjacent header sections beneath one another so we only get */
	/* a single width line between them                                 */

	QHeaderView::section:horizontal:!first:!only-one {
		margin-left: -1px;
	}

	QHeaderView::section:vertical:!first:!only-one {
		margin-top: -1px;
	}

	QHeaderView::down-arrow {
		image: url($GAFFER_ROOT/graphics/headerSortDown.png);
	}

	QHeaderView::up-arrow {
		image: url($GAFFER_ROOT/graphics/headerSortUp.png);
	}

	QScrollBar {
		border: none;
		border-radius: 4px;
		background-color: $tintDarker;
	}

	QScrollBar:vertical {
		width: 16px;
		margin: 4px;
	}

	QScrollBar:horizontal {
		height: 16px;
		margin: 4px;
	}

	QScrollBar::add-page, QScrollBar::sub-page {
		background: none;
		border: none;
	}

	QScrollBar::add-line, QScrollBar::sub-line {
		background-color: none;
		border: none;
	}

	QScrollBar::add-line:vertical {
		height: 8px;
		subcontrol-position: bottom;
		subcontrol-origin: margin;
	}

	QScrollBar::add-line:horizontal {
		width: 8px;
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

	QScrollBar::handle {
		background-color: $tintLighterStrong;
		border-radius: 4px;
		border: none;
	}

	QScrollBar::handle:vertical {
		min-height: 14px;
	}

	QScrollBar::handle:horizontal {
		min-width: 14px;
	}

	QScrollBar::handle:hover, QScrollBar::add-line:hover,
	QScrollBar::sub-line:hover {
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

	/* checkbox */

	QCheckBox::indicator {
		width: 20px;
		height: 20px;
		background-color: transparent;
		border-radius: 2px;
	}

	QCheckBox::indicator:unchecked {
		image: url($GAFFER_ROOT/graphics/checkBoxUnchecked.png);
	}

	QCheckBox::indicator:unchecked:hover,
	QCheckBox::indicator:unchecked:focus,
	QCheckBox[gafferHighlighted=\"true\"]::indicator:unchecked {
		image: url($GAFFER_ROOT/graphics/checkBoxUncheckedHover.png);
	}
	QCheckBox::indicator:checked:hover,
	QCheckBox::indicator:checked:focus,
	QCheckBox[gafferHighlighted=\"true\"]::indicator:checked {
		image: url($GAFFER_ROOT/graphics/checkBoxCheckedHover.png);
	}

	QCheckBox::indicator:checked {
		image: url($GAFFER_ROOT/graphics/checkBoxChecked.png);
	}

	QCheckBox::indicator:checked:disabled {
		image: url($GAFFER_ROOT/graphics/checkBoxCheckedDisabled.png);
	}

	QCheckBox::indicator:unchecked:disabled {
		image: url($GAFFER_ROOT/graphics/checkBoxUncheckedDisabled.png);
	}

	QCheckBox[gafferAnimated="true"]::indicator {
		background-color: $animatedColor;
	}

	QCheckBox[gafferError="true"]::indicator {
		background-color: $errorColor;
	}

	/* boolwidget drawn as switch */

	QCheckBox[gafferDisplayMode=\"Switch\"]::indicator:unchecked {
		image: url($GAFFER_ROOT/graphics/toggleOff.png);
	}

	QCheckBox[gafferDisplayMode=\"Switch\"]::indicator:unchecked:hover,
	QCheckBox[gafferDisplayMode=\"Switch\"]::indicator:unchecked:focus,
	QCheckBox[gafferDisplayMode=\"Switch\"][gafferHighlighted=\"true\"]::indicator:unchecked {
		image: url($GAFFER_ROOT/graphics/toggleOffHover.png);
	}
	QCheckBox[gafferDisplayMode=\"Switch\"]::indicator:checked:hover,
	QCheckBox[gafferDisplayMode=\"Switch\"]::indicator:checked:focus,
	QCheckBox[gafferDisplayMode=\"Switch\"][gafferHighlighted=\"true\"]::indicator:checked {
		image: url($GAFFER_ROOT/graphics/toggleOnHover.png);
	}

	QCheckBox[gafferDisplayMode=\"Switch\"]::indicator:checked {
		image: url($GAFFER_ROOT/graphics/toggleOn.png);
	}

	QCheckBox[gafferDisplayMode=\"Switch\"]::indicator:checked:disabled {
		image: url($GAFFER_ROOT/graphics/toggleOnDisabled.png);
	}

	QCheckBox[gafferDisplayMode=\"Switch\"]::indicator:unchecked:disabled {
		image: url($GAFFER_ROOT/graphics/toggleOffDisabled.png);
	}

	/* boolwidget drawn as tool */

	QCheckBox {
		border-radius: 5px;
	}

	QCheckBox[gafferDisplayMode=\"Tool\"]::indicator {
		width: 0px;
		height: 0px;
	}

	QCheckBox[gafferDisplayMode=\"Tool\"] {
		background-color: $backgroundDarkTransparent;
		spacing: 0px;
		width: 30px;
		height: 30px;
		border: 1px solid $backgroundDark;
		padding-left: 4px;
	}

	QCheckBox[gafferDisplayMode=\"Tool\"]:checked {
		background-color: $brightColorTransparent;
	}

	QCheckBox[gafferDisplayMode=\"Tool\"]:hover {
		border-color: $brightColor;
		border-width: 2px;
		padding-left: 3px;
	}

	/* frame */

	.QFrame#borderStyleNone {
		border: 1px solid transparent;
		border-radius: $widgetCornerRadius;
		padding: 2px;
	}

	.QFrame#borderStyleFlat {
		border: 1px solid $backgroundDark;
		border-radius: $widgetCornerRadius;
		padding: 2px;
	}

	.QFrame[gafferHighlighted=\"true\"]#borderStyleFlat {
		border: 1px solid $brightColor;
	}

	.QFrame#gafferDivider {
		color: $tintDarkerStrong;
		margin-left: 10px;
		margin-right: 10px;
	}

	QToolTip {
		background-clip: border;
		color: $backgroundDarkest;
		background-color: $foreground;
		padding: 2px;
	}


	/* Tree/Table views */

	QTreeView {
		background-color: $backgroundRaised;
		border: 1px solid $backgroundRaisedHighlight;
		border-bottom-color: $backgroundRaisedLowlight;
		border-right-color: $backgroundRaisedLowlight;
		padding: 0;
		alternate-background-color: $backgroundLowlight;
	}

	QTreeView::item {
		padding-top: 2px;
		padding-bottom: 2px;
	}

	QTreeView::item:selected {
		background-color: $brightColor;
	}

	QTableView {
		border: 1px solid transparent;
	}

	QTableView::item {
		background-color: $background;
	}

	QTableView::item:selected {
		background-color: $brightColor;
	}

	QTableView QTableCornerButton::section {
		background-color: transparent;
		border: none;
	}

	QTableView#vectorDataWidget {
		gridline-color: $backgroundLowlight;
		padding: 0px;
		background-color: $backgroundRaised;
	}

	QTableView#vectorDataWidgetEditable {
		padding: 0px;
		gridline-color: $backgroundLowlight;
	}

	QTableView::item#vectorDataWidgetEditable {
		background-color: $backgroundLight;
	}

	QTableView::item:selected#vectorDataWidgetEditable {
		background-color: $brightColor;
	}

	QHeaderView::section#vectorDataWidgetVerticalHeader {
		padding: 2px;
	}

	/* checkboxes within table views */

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

	/* highlighted state for VectorDataWidget and tree views */

	QTableView[gafferHighlighted=\"true\"]#vectorDataWidget,
	QTableView[gafferHighlighted=\"true\"]#vectorDataWidgetEditable {
		gridline-color: $brightColor;
	}

	QTreeView[gafferHighlighted=\"true\"],
	QTableView[gafferHighlighted=\"true\"] QHeaderView::section#vectorDataWidgetVerticalHeader {
		border-color: $brightColor;
	}

	/* progress bars */

	QProgressBar {
		border: 1px solid $backgroundDark;
		background: $backgroundLighter;
		padding: 1px;
		text-align: center;
	}

	QProgressBar::chunk:horizontal {
		background-color: $brightColor;
	}

	/* gl widget */

	QGraphicsView#gafferGLWidget {
		border: 0px;
	}

	/* frame variants */

	QFrame#gafferDiffA {
		background: solid rgba( 181, 30, 0, 80 );
	}

	QFrame#gafferDiffB {
		background: solid rgba( 34, 159, 0, 80 );
	}

	QFrame#gafferDiffAB {
		background: solid rgba( 170, 170, 170, 60 );
	}

	QFrame#gafferDiffOther {
		background: solid rgba( 70, 184, 255, 25 );
	}

	QFrame#gafferLighter {
		background: solid rgba( 255, 255, 255, 10 );
	}

	QFrame#gafferDarker {
		background: solid rgba( 0, 0, 0, 80 );
		border-radius: 2px;
		padding: 2px;
	}

	QFrame[gafferHighlighted=\"true\"]#gafferDiffA, QFrame[gafferHighlighted=\"true\"]#gafferDiffB, QFrame[gafferHighlighted=\"true\"]#gafferDiffAB {
		background-color: $brightColor;
	}

	/* turn off rounded corners based on adjacency of other widgets */

	*[gafferRounded="true"] {
		border-radius: 6px;
	}

	*[gafferFlatTop="true"] {
		border-top-left-radius: 0px;
		border-top-right-radius: 0px;
	}

	*[gafferFlatBottom="true"] {
		border-bottom-left-radius: 0px;
		border-bottom-right-radius: 0px;
	}

	*[gafferFlatLeft="true"] {
		border-top-left-radius: 0px;
		border-bottom-left-radius: 0px;
	}

	*[gafferFlatRight="true"] {
		border-top-right-radius: 0px;
		border-bottom-right-radius: 0px;
	}

	/* PythonEditor */

	QSplitter#gafferPythonEditor {
		background-color: $background;
	}

	QPlainTextEdit#gafferPythonEditorOutput {
		border-radius: 0;
		border-top-left-radius: $widgetCornerRadius;
		border-top-right-radius: $widgetCornerRadius;
		background-color: rbg( 30, 30, 30 );
	}

	QPlainTextEdit#gafferPythonEditorInput {
		border-radius: 0;
		border-bottom-left-radius: $widgetCornerRadius;
		border-bottom-right-radius: $widgetCornerRadius;
	}

	"""

).substitute( substitutions )


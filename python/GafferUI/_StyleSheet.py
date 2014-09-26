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

## \todo Unify with GafferUI.Style for colours at least.
_styleSheet = string.Template(

	"""
	QWidget#gafferWindow {

		color: $foreground;
		font: 10px;
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

	QLabel[gafferHighlighted=\"true\"] {

		color: $brightColor;

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

	QMenu, QTabBar::tab:selected, QHeaderView::section {

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

	QLineEdit:focus, QPlainTextEdit[readOnly="false"]:focus, QLineEdit[gafferHighlighted=\"true\"] {

		border: 2px solid $brightColor;
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

	QWidget#gafferSplineWidget
	{
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

	QPushButton, QComboBox {

		font-weight: bold;

	}

	QPushButton#gafferWithFrame, QComboBox {

		border: 1px solid $backgroundDark;
		border-radius: 3px;
		padding: 4px;
		margin: 1px;
		background-color : qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 $backgroundLight, stop: 0.5 $backgroundLighter);

	}

	QPushButton#gafferWithFrame:hover, QPushButton#gafferWithFrame:focus, QComboBox:hover {

		border: 2px solid $brightColor;
		margin: 0px;
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

		background-color: $backgroundLighter;

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
		background-color: $backgroundMid;
		height:40px;
		margin:0;

	}

	QComboBox QAbstractItemView::item {

		border: none;
		padding: 2px;
		font-weight: bold;

	}

	/* tabs */

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
		border-color: transparent;
		border-radius: 0px;
		padding-bottom: 2px;
		padding-top: 2px;
		margin-top: 4px;
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
	QComboBox QAbstractItemView::item:hover {

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

	QTabWidget[gafferHighlighted=\"true\"]::pane {
		border: 1px solid $brightColor;
		border-top: 1px solid $brightColor;
		top: -1px;
	}

	QTabWidget[gafferHighlighted=\"true\"] > QTabBar::tab:selected {
		border: 1px solid $brightColor;
		border-bottom-color: $backgroundMid; /* blend into frame below */
	}

	QTabWidget[gafferHighlighted=\"true\"] > QTabBar::tab:!selected {
		border-bottom-color: $brightColor;
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

	/* checkbox */

	QCheckBox::indicator {
		width: 20px;
		height: 20px;
		background-color: transparent;
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

	/* boolwidget drawn as switch */

	QCheckBox#gafferBoolWidgetSwitch::indicator:unchecked {
		image: url($GAFFER_ROOT/graphics/toggleOff.png);
	}

	QCheckBox#gafferBoolWidgetSwitch::indicator:unchecked:hover,
	QCheckBox#gafferBoolWidgetSwitch::indicator:unchecked:focus,
	QCheckBox#gafferBoolWidgetSwitch[gafferHighlighted=\"true\"]::indicator:unchecked {
		image: url($GAFFER_ROOT/graphics/toggleOffHover.png);
	}
	QCheckBox#gafferBoolWidgetSwitch::indicator:checked:hover,
	QCheckBox#gafferBoolWidgetSwitch::indicator:checked:focus,
	QCheckBox#gafferBoolWidgetSwitch[gafferHighlighted=\"true\"]::indicator:checked {
		image: url($GAFFER_ROOT/graphics/toggleOnHover.png);
	}

	QCheckBox#gafferBoolWidgetSwitch::indicator:checked {
		image: url($GAFFER_ROOT/graphics/toggleOn.png);
	}

	QCheckBox#gafferBoolWidgetSwitch::indicator:checked:disabled {
		image: url($GAFFER_ROOT/graphics/toggleOnDisabled.png);
	}

	QCheckBox#gafferBoolWidgetSwitch::indicator:unchecked:disabled {
		image: url($GAFFER_ROOT/graphics/toggleOffDisabled.png);
	}

	/* frame */

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

	.QFrame[gafferHighlighted=\"true\"]#borderStyleFlat {
		border: 1px solid $brightColor;
	}

	.QFrame#gafferDivider {
		color: $backgroundDark;
	}

	QToolTip {
		background-clip: border;
		color: $backgroundDarkest;
		background-color: $foreground;
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

	/* highlighted state for VectorDataWidget */

	QTableView[gafferHighlighted=\"true\"]#vectorDataWidget,
	QTableView[gafferHighlighted=\"true\"]#vectorDataWidgetEditable {

		gridline-color: $brightColor;

	}

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

	QFrame#gafferDiffCommon {

		background: solid rgba( 170, 170, 170, 80 );

	}

	QFrame#gafferLighter {

		background: solid rgba( 255, 255, 255, 10 );

	}

	QFrame[gafferHighlighted=\"true\"]#gafferDiffA, QFrame[gafferHighlighted=\"true\"]#gafferDiffB, QFrame[gafferHighlighted=\"true\"]#gafferDiffCommon {
		background-color: $brightColor;
	}

	/* turn off rounded corners based on adjacency of other widgets */

	*[gafferRounded="true"] {

		border-radius: 8px;

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

	"""

).substitute( {

	"GAFFER_ROOT" : os.environ["GAFFER_ROOT"],
	"backgroundDarkest" : "#000000",
	"backgroundDark" : "#3c3c3c",
	"backgroundMid" : "#4c4c4c",
	"backgroundLighter" : "#6c6c6c",
	"backgroundLight" : "#7d7d7d",
	"brightColor" : "#779cbd",
	"foreground" : "#f0f0f0",
	"foregroundFaded" : "#999999",
	"alternateColor" : "#454545",

} )

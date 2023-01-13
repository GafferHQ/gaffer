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

from Qt import QtCore
from Qt import QtGui

# Load resource file containing all the files referenced by the stylesheet. In
# an ideal world we'd be able to trust Qt to load regular `.png` files directly
# from the filesystem. But we can't : QStyleSheetStyle repeatedly accesses the
# same files over and over again, and this can lead to UI stalls when Gaffer is
# installed on a server under heavy load.
QtCore.QResource.registerResource( os.path.expandvars( "$GAFFER_ROOT/graphics/resources.rcc" ) )

_styleColors = {

	# The theme is built on the principal of using tonal variation and
	# subtle embossing instead of lines to differentiate UI elements.
	# There are a few holes in this, but it hopefully results in a lower overall
	# visual complexity compared to a flat + borders approach.
	#
	# The base background color for UI elements is $background, and this should
	# be used for 'default' height elements - ie: the main user interaction
	# surface background in any window/panel. This is usually a top-level
	# TabContainer or ListContainer. Depending on the nesting level of
	# subsequent elements, the Light/Lighter variants should be used instead.
	# Dark/Darker variants are for 'lower' elements, such as the background
	# behind something considered as the primary surface.
	#
	# For each base background color, in order to facilitate relief effects,
	# there are 'highlight' and 'lowlight' options. Highlight should be used
	# on top/left borders and lowlight on bottom/right.
	#
	# The 'alt' suffixed colors are for use in UI elements such as table views
	# that require subtle variation of the base background color.

	"backgroundDarkest" : (0, 0, 0),

	"backgroundDarker" : (35, 35, 35),

	"backgroundDark" : (52, 52, 52),
	"backgroundDarkTransparent" : (52, 52, 52, 100),
	"backgroundDarkHighlight" : (62, 62, 62),

	"backgroundLowlight" : (56, 56, 56),
	"backgroundMidLowlight" : (61, 61, 61),
	"background" : (66, 66, 66),
	"backgroundAlt" : (60, 60, 60),
	"backgroundHighlight" : (76, 76, 76),

	"backgroundRaisedLowlight" : (60, 60, 60),
	"backgroundRaised" : (72, 72, 72),
	"backgroundRaisedAlt" : (66, 66, 66),
	"backgroundRaisedHighlight" : (82, 82, 82),

	"backgroundLightLowlight" : (82, 82, 82),
	"backgroundLight" : (96, 96, 96),
	"backgroundLightHighlight" : (106, 106, 106),

	"backgroundLighter" : (125, 125, 125),

	# $brightColor should be used to illustrated a selected or highlighted
	# state, such as during a drag-hover or click-selection operation.

	"brightColor" : (119, 156, 189),
	"brightColorTransparent" : (119, 156, 189, 100),

	# $foreground is the standard Text/marker color.

	"foreground" : (224, 224, 224),
	"foregroundFaded" : (163, 163, 163),

	"errorColor" : (255, 85, 85),
	"animatedColor" : (128, 152, 94),

	"foregroundError" : ( 255, 80, 80 ),
	"foregroundWarning" : ( 239, 129, 24 ),
	"foregroundInfo" : ( 128, 179, 254 ),
	"foregroundDebug" : ( 163, 163, 163 ),

	# Controls and other UI elements may have to sit on a variety of background
	# colors and as such should make use of the $tint* colors for tonal
	# variation. This should be in preference to using $background* colors
	# unless there are compositing issues or other overriding reasons as the
	# control will not be portable across different backgrounds.

	"tintLighterSubtle" :   ( 255, 255, 255, 10 ),
	"tintLighter" :         ( 255, 255, 255, 20 ),
	"tintLighterStrong" :   ( 255, 255, 255, 40 ),
	"tintLighterStronger" : ( 255, 255, 255, 100 ),
	"tintDarkerSubtle" :    ( 0, 0, 0, 10 ),
	"tintDarker" :          ( 0, 0, 0, 20 ),
	"tintDarkerStrong" :    ( 0, 0, 0, 40 ),
	"tintDarkerStronger" :    ( 0, 0, 0, 70 ),

	# Adjoined edges need to be opaque so they don't  show through to the
	# background behind the control.
	"backgroundLightHighlightAdjoined" :  ( 88, 88, 88 ),
	"backgroundDarkHighlightAdjoined" : ( 78, 78, 78 ),

	# Value Inspectors

	"inspectorSourceUpstream" : ( 255, 255, 255, 20 ),
	"inspectorSourceEditScope" : ( 48, 100, 153, 60 ),
	"inspectorSourceDownstream" : ( 239, 198, 24, 104 ),

}

_themeVariables = {
	"roundedCornerRadius" : "6px",
	"widgetCornerRadius" : "4px",
	"controlCornerRadius" : "2px",
	"toolOverlayInset" : "44px",
	## \todo Use a font that we bundle with Gaffer, so that it's the same on all platforms.
	"monospaceFontFamily" : '"Menlo", "SFMono-Regular", "Consolas", "Liberation Mono", monospace'
}

substitutions = {}

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

	# General Rules:
	#
	#   - Custom properties should be used for compositional behaviour, in the
	#     way traditional CSS classes are used.
	#
	#   - Custom objectNames should be used to allow the customisation of
	#     specific instances of a widget, in the way traditional CSS IDs are
	#     used.
	#
	#   - Custom objectNames or properties should all be prefixed with `gaffer`
	#     and use camelCase.
	#
	#   - Any objectNames or properties set from the underlying implementation
	#     should only convey information about the context of use, and not any
	#     styling hints. For example, in the case of allowing control over the
	#     styling of widgets based on their proximity to others, Gaffer sets the
	#     appropriate `gafferAdjoined(Top|Bottom|Left|Right)` properties rather
	#     than `gafferRounded`/`gafferFlat*`.
	#
	#   - All icons should be referenced as `url(:/<fileName>.png)`, where
	#    `<fileName>` is one of the icons exported from `resources/graphics.svg`.
	#    The build process will collect these icons and pack them into the `.rcc`
	#    resource file automatically.
	#
	# We can't use `.<class>` selectors in the stylesheet in many cases as
	# these reference the Qt Class hierarchy. To help here, GafferUI.Widgets
	# set two custom properties on their QWidget:
	#
	#   - `gafferClass` : The class path of the widget, eg: `GafferUI.Button`
	#
	#   - `gafferClasses` : An array of classes in the widgets hierarchy, eg:
	#        `[ 'GafferUI.Button', 'GafferUI.Widget' ]`
	#
	# This allows class-scope selectors in the style sheet, via property
	# queries eg:
	#
	#   - `[gafferClass="GafferUI.Button"]` For an exact class.
	#   - `[gafferClasses~="GafferUI.Window"]` For an inheritance match.
	#
	"""
	*[gafferClasses~="GafferUI.Window"] {
		color: $foreground;
		font: 10px;
		etch-disabled-text: 0;
		background-color: $backgroundDarker;
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

	QLabel[gafferHighlighted="true"] {
		color: #b0d8fb;
	}

	QLabel#gafferPlugLabel {
		/*
		QLabel's text layout seems to lurch from one approach
		to another in the presence of non-zero padding. So we
		need some padding here so that we get a layout that
		matches the `gafferValueChanged="true"` styling below.
		*/
		padding-left: 1px;
	}

	QLabel#gafferPlugLabel[gafferValueChanged="true"] {
		background-image: url(:/valueChanged.png);
		background-repeat: no-repeat;
		background-position: left;
		padding-left: 16px;
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

	QMenu::icon {
		padding-left: 10px;
	}

	QMenu[gafferHasTitle="true"],
	QMenu[gafferHasLeadingLabelledDivider="true"] {
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

	QMenu[gafferHasLeadingLabelledDivider="true"] QLabel#gafferMenuTitle {
		/* If the first item is a labeled section, we don't want any
		   space under the title. */
		margin-bottom: 0;
	}


	QLabel#gafferMenuLabeledDivider {
		background-color: $backgroundLightLowlight;
		font-weight: bold;
		padding: 3px 25px 3px 20px;
		margin-bottom: 4px;
		margin-top: 0;
		color: $foreground;
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
		image: url(:/subMenuArrow.png);
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
		width: 15px;
		padding: 0px 0px 0px 3px;
		/*
		Work around https://bugreports.qt.io/browse/QTBUG-90242. In Qt 5.12,
		indicators are not accounted for in the text layout, instead they are
		rendered into the space reserved by the left padding of `QMenu::item`. In
		Qt 5.15.2, indicators are accounted for in the layout, shunting
		the text to the right. This _is_ logical, but it causes misalignment
		between checkable and non-checkable items. This negative margin negates
		the shunt in Qt 5.15 and has no effect in Qt 5.12.
		*/
		margin-right: -18px;
	}

	QMenu::indicator:non-exclusive:checked {
		image: url(:/menuChecked.png);
	}

	QMenu::indicator:exclusive:checked:selected {
		image: url(:/arrowRight10.png);
	}

	QLineEdit, QPlainTextEdit {
		padding: 0px;
		border: 1px solid transparent;
		border-bottom-color: $tintDarkerStronger;
		border-right-color: $tintDarkerStronger;
		background-color: $backgroundLight;
		border-radius: $controlCornerRadius;
	}

	QLineEdit[readOnly="true"], QPlainTextEdit[readOnly="true"] {
		padding: 0px;
		background-color: $tintLighterSubtle;
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
		font-family: $monospaceFontFamily;
		font-size: 11px;
		background-color: $backgroundDark;
	}

	QLineEdit:focus, QPlainTextEdit[readOnly="false"]:focus, QLineEdit[gafferHighlighted="true"] {
		border: 1px solid $brightColor;
		padding: 0px;
	}

	QLineEdit:disabled {
		color: $foregroundFaded;
	}

	#gafferSearchField {
		background-image: url(:/search.png);
		background-repeat:no-repeat;
		background-position: left center;
		padding-left: 20px;
		height:20px;
		border-radius:5px;
		margin-left: 4px;
		margin-right: 4px;
	}

	QWidget[gafferClass="GafferUI.SplineWidget"] {
		border: 1px solid $backgroundDark;
	}

	QWidget[gafferClass="GafferUI.SplineWidget"][gafferHighlighted="true"] {
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
		image: url(:/arrowDown10.png);
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

	QPushButton[gafferWithFrame="true"],
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

	QPushButton[gafferWithFrame="true"][gafferClass="GafferUI.MenuButton"] {
		padding: 2px;
	}

	QPushButton[gafferWithFrame="true"][gafferThinButton="true"] {
		background-color : qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 $backgroundLighter, stop: 0.1 $backgroundLightHighlight, stop: 0.90 $backgroundLightLowlight);
		padding: 2px;
	}

	*[gafferPlugValueWidget="true"] QPushButton[gafferWithFrame="true"][gafferClass="GafferUI.MenuButton"] {
		background-color : qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 $backgroundLighter, stop: 0.1 $backgroundLightHighlight, stop: 0.90 $backgroundLightLowlight);
		font-weight: normal;
		text-align: left;
	}

	*[gafferPlugValueWidget="true"] QPushButton[gafferClass="GafferUI.MenuButton"][gafferError="true"] {
		background-color : $errorColor;
	}

	QPushButton[gafferWithFrame="true"]:focus {
		border: 1px solid $brightColor;
	}

	QPushButton[gafferWithFrame="true"]:pressed {
		color: white;
		background-color:	$brightColor;
	}

	QPushButton[gafferWithFrame="false"] {
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
		color: $tintLighterStrong;
	}

	QPushButton[gafferWithFrame="true"]:disabled, QPushButton[gafferWithFrame="true"][gafferClass="GafferUI.MenuButton"]:disabled {
		color: $tintLighterStrong;
		background-color: $backgroundHighlight;
	}

	QPushButton::menu-indicator {
		image: url(:/arrowDown10.png);
		subcontrol-position: right center;
		subcontrol-origin: padding;
		left: -4px;
	}

	QPushButton[gafferWithFrame="true"][gafferMenuIndicator="true"] {
		background-image: url(:/menuIndicator.png);
		background-repeat: none;
		background-position: center right;
		padding-right: 20px
	}

	QPushButton[gafferWithFrame="true"][gafferMenuIndicator="true"]:disabled {
		color: $foregroundFaded;
		background-image: url(:/menuIndicatorDisabled.png);
	}

	QComboBox {
		padding: 0;
		padding-left:3px;
	}

	QComboBox::drop-down {
		width: 15px;
		image: url(:/arrowDown10.png);
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

	/* Tabs */
	/* ==== */

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

	QTabBar[gafferHasTabCloseButtons="true"]::tab {
		padding-right: 5px;
	}

	QTabBar::close-button {
		margin: 10px;
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
		background-color: transparent;
		border-color: transparent;
		border-bottom-color: $backgroundHighlight;
	}

	QTabBar::tab:!selected:hover {
		background-color: $tintLighter;
	}

	QTabWidget QTabWidget > QTabBar::tab:!selected {
		color: $tintLighterStronger;
		background-color: transparent;
		border-color: transparent;
		border-bottom-color: $backgroundRaisedHighlight;
	}

	QTabWidget QTabWidget > QTabBar::tab:!selected:hover {
		background-color: $tintLighterSubtle;
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
		background-color: transparent;
		border-color: transparent;
	}

	QTabWidget QTabWidget::pane {
		background-color: $backgroundRaised;
		border-radius: $widgetCornerRadius;
		border-top-left-radius: 0;
		border-color: $backgroundRaisedHighlight;
		border-right-color: $backgroundRaisedLowlight;
		border-bottom-color: $backgroundRaisedLowlight;
	}

	QTabWidget[gafferHighlighted="true"]::pane {
		border: 1px solid $brightColor;
		border-top: 1px solid $brightColor;
		top: -1px;
	}

	QTabWidget[gafferHighlighted="true"] > QTabBar::tab:selected {
		border-color: $brightColor;
		border-bottom-color: $background; /* blend into frame below */
	}

	QTabWidget QTabWidget[gafferHighlighted="true"] > QTabBar::tab:selected {
		border-color: $brightColor;
		border-bottom-color: $backgroundRaised; /* blend into frame below */
	}

	QTabWidget[gafferHighlighted="true"] > QTabBar::tab:!selected {
		border-bottom-color: $brightColor;
	}

	QTabWidget[gafferClasses~="GafferUI.TabbedContainer"] > QTabBar::scroller {
		/* Hide scroll buttons - see TabbedContainer.__init__ for motivation */
		width: 0px;
	}

	QTabBar::tear {
		image: none;
	}

	/*
	TabBars not inside a QTabWidget. Currently these are only used by
	SpreadsheetUI.
	*/

	QTabBar[gafferClass="GafferUI.SpreadsheetUI._SectionChooser"]::tab {

		border-color: $tintDarkerStronger;
		background-color: $tintDarkerStrong;
		border-radius: 0px;
		margin-right: -1px;

	}

	QTabBar[gafferClass="GafferUI.SpreadsheetUI._SectionChooser"]::tab:selected {

		background-color: $tintDarkerStronger;

	}

	QTabBar[gafferClass="GafferUI.SpreadsheetUI._SectionChooser"]::tab:first {

		border-top-left-radius: $widgetCornerRadius;
		border-bottom-left-radius: $widgetCornerRadius;

	}

	QTabBar[gafferClass="GafferUI.SpreadsheetUI._SectionChooser"]::tab:last {

		border-top-right-radius: $widgetCornerRadius;
		border-bottom-right-radius: $widgetCornerRadius;
		margin-right: 0px;

	}

	QTabBar[gafferClass="GafferUI.SpreadsheetUI._SectionChooser"]::tab:only-one {

		border-radius: $widgetCornerRadius;

	}

	/* The interaction between stylesheets and QTabBar sub controls is somewhat */
	/* 'delicate'. Some selectors only seem to support a sub-set of properties. */
	/* The presentation of the selectors below isn't ideal, but represents a    */
	/* pragmatic compromise that was more readily achievable.                   */

	QTabBar[gafferClass="GafferUI.SpreadsheetUI._SectionChooser"]::scroller {
		width: 40px;
	}

	QTabBar[gafferClass="GafferUI.SpreadsheetUI._SectionChooser"] QToolButton {
		background: $backgroundHighlight;
		border: 1px solid $backgroundDark;
	}

	QTabBar[gafferClass="GafferUI.SpreadsheetUI._SectionChooser"] QToolButton::left-arrow {
		image: url(:/arrowLeft10.png);
	}

	QTabBar[gafferClass="GafferUI.SpreadsheetUI._SectionChooser"] QToolButton::left-arrow:disabled {
		image: url(:/arrowLeftDisabled10.png);
	}

	QTabBar[gafferClass="GafferUI.SpreadsheetUI._SectionChooser"] QToolButton::right-arrow { /* the arrow mark in the tool buttons */
		image: url(:/arrowRight10.png);
	}

	QTabBar[gafferClass="GafferUI.SpreadsheetUI._SectionChooser"] QToolButton::right-arrow:disabled { /* the arrow mark in the tool buttons */
		image: url(:/arrowRightDisabled10.png);
	}

	/* Splitters */
	/* ========= */

	QSplitter[gafferHighlighted="true"] {

		border: 1px solid $brightColor;
	}

	/* Ensures the QSplitter border is visible if we need to highlight */
	QSplitter[gafferClass="GafferUI.CompoundEditor._SplitContainer"][gafferNumChildren="1"] {
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

	QCheckBox#gafferCollapsibleToggle {
		font-weight: bold;
	}

	QWidget[gafferClass="GafferUI.Collapsible"] QWidget[gafferClass="GafferUI.Collapsible"] > QCheckBox#gafferCollapsibleToggle {
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
		image: url(:/collapsibleArrowDown.png);
	}

	QCheckBox#gafferCollapsibleToggle::indicator:checked {
		image: url(:/collapsibleArrowRight.png);
	}

	QCheckBox#gafferCollapsibleToggle::indicator:unchecked:hover,
	QCheckBox#gafferCollapsibleToggle::indicator:unchecked:focus {
		image: url(:/collapsibleArrowDownHover.png);
	}

	QCheckBox#gafferCollapsibleToggle::indicator:checked:hover,
	QCheckBox#gafferCollapsibleToggle::indicator:checked:focus {
		image: url(:/collapsibleArrowRightHover.png);
	}

	*[gafferValueChanged="true"] > QCheckBox#gafferCollapsibleToggle::indicator:unchecked,
	*[gafferValueChanged="true"] > QCheckBox#gafferCollapsibleToggle::indicator:unchecked:hover,
	*[gafferValueChanged="true"] > CheckBox#gafferCollapsibleToggle::indicator:unchecked:focus {
		image: url(:/collapsibleArrowDownValueChanged.png);
	}

	*[gafferValueChanged="true"] > QCheckBox#gafferCollapsibleToggle::indicator:checked,
	*[gafferValueChanged="true"] > QCheckBox#gafferCollapsibleToggle::indicator:checked:hover,
	*[gafferValueChanged="true"] > QCheckBox#gafferCollapsibleToggle::indicator:checked:focus {
		image: url(:/collapsibleArrowRightValueChanged.png);
	}

	QHeaderView {
		border: 0px;
		margin: 0px;
	}

	QHeaderView::section {
		border: 1px solid $backgroundLowlight;
		border-radius: 0;
		padding-top: 0px;
		padding-bottom: 0px;
		padding-left: 3px;
		padding-right: 3px;
		font-weight: bold;
		margin: 0px;
		background-color: $tintLighter;
	}

	_TableView QHeaderView::section:vertical:first {
		border-top-left-radius: $widgetCornerRadius;
	}

	_TableView QHeaderView::section:vertical:last {
		border-bottom-left-radius: $widgetCornerRadius;
	}

	_TableView QHeaderView::section:vertical:only-one {
		border-top-left-radius: $widgetCornerRadius;
		border-bottom-left-radius: $widgetCornerRadius;
	}

	_TableView QHeaderView::section:horizontal:first {
		border-top-left-radius: $widgetCornerRadius;
	}

	_TableView QHeaderView::section:horizontal:last {
		border-top-right-radius: $widgetCornerRadius;
	}

	_TableView QHeaderView::section:horizontal:only-one {
		border-top-left-radius: $widgetCornerRadius;
		border-top-right-radius: $widgetCornerRadius;
	}

	/* Remove left/top borders so we don't get a double-width line between columns */

	QHeaderView::section:horizontal:!first:!only-one {
		border-left-color: transparent;
	}

	QHeaderView::section:vertical:!first:!only-one {
		border-top-color: transparent;
	}

	QHeaderView::down-arrow {
		image: url(:/headerSortDown.png);
	}

	QHeaderView::up-arrow {
		image: url(:/headerSortUp.png);
	}

	QScrollBar {
		border: none;
		border-radius: 4px;
		background-color: $tintDarker;
	}

	QScrollBar:vertical {
		width: 16px;
		margin: 4px;
		margin-bottom: 30px;
	}

	QScrollBar:horizontal {
		height: 16px;
		margin: 4px;
		margin-right: 30px;
	}

	QScrollBar::add-page, QScrollBar::sub-page {
		background: $tintDarker;
		border: none;
	}

	QScrollBar::add-line, QScrollBar::sub-line {
		background: transparent;
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

	QScrollBar::down-arrow {
		image: url(:/arrowDown10.png);
	}
	QScrollBar::up-arrow {
		image: url(:/arrowUp10.png);
	}
	QScrollBar::left-arrow {
		image: url(:/arrowLeft10.png);
	}
	QScrollBar::right-arrow {
		image: url(:/arrowRight10.png);
	}

	QScrollArea {
		border: none;
	}

	QAbstractScrollArea::corner {
		background: transparent;
	}

	QCheckBox {
		spacing: 5px;
	}

	/* Avoid a double border with the tree view's border */

	QTreeView QHeaderView::section:horizontal {
		border-top-color: transparent;
	}

	QTreeView QHeaderView::section:horizontal:only-one {
		border-left-color: transparent;
		border-right-color: transparent;
	}

	QTreeView QHeaderView::section:horizontal:first {
		border-left-color: transparent;
	}

	QTreeView QHeaderView::section:horizontal:last {
		border-right-color: transparent;
	}

	QTreeView QHeaderView::section:vertical {
		border-left-color: transparent;
	}

	QTreeView QHeaderView::section:vertical:only-one {
		border-top-color: transparent;
		border-bottom-color: transparent;
	}

	QTreeView QHeaderView::section:vertical:first {
		border-top-color: transparent;
	}

	QTreeView QHeaderView::section:vertical:last {
		border-bottom-color: transparent;
	}

	QTreeView::branch {
		border-image : none;
		image : none;
	}

	QTreeView::branch:closed:has-children {
		border-image : none;
		image : url(:/collapsibleArrowRight.png);
	}

	QTreeView::branch:open:has-children {
		border-image : none;
		image : url(:/collapsibleArrowDown.png);
	}

	/* CheckBoxes */
	/* ========== */

	QCheckBox::indicator {
		width: 20px;
		height: 20px;
		background-color: transparent;
		border-radius: 2px;
	}

	/* Unchecked */
	/* --------- */

	QCheckBox::indicator:unchecked {
		image: url(:/checkBoxUnchecked.png);
	}

	QCheckBox::indicator:unchecked:hover,
	QCheckBox::indicator:unchecked:focus,
	QCheckBox[gafferHighlighted="true"]::indicator:unchecked {
		image: url(:/checkBoxUncheckedHover.png);
	}

	QCheckBox::indicator:unchecked:disabled {
		image: url(:/checkBoxUncheckedDisabled.png);
	}

	/* Checked */
	/* ------- */

	QCheckBox::indicator:checked {
		image: url(:/checkBoxChecked.png);
	}

	QCheckBox::indicator:checked:hover,
	QCheckBox::indicator:checked:focus,
	QCheckBox[gafferHighlighted="true"]::indicator:checked {
		image: url(:/checkBoxCheckedHover.png);
	}

	QCheckBox::indicator:checked:disabled {
		image: url(:/checkBoxCheckedDisabled.png);
	}

	/* Indeterminate */
	/* ------------- */

	QCheckBox::indicator:indeterminate {
		image: url(:/checkBoxIndeterminate.png);
	}

	QCheckBox::indicator:indeterminate:hover,
	QCheckBox::indicator:indeterminate:focus,
	QCheckBox[gafferHighlighted="true"]::indicator:indeterminate {
		image: url(:/checkBoxIndeterminateHover.png);
	}

	QCheckBox::indicator:indeterminate:disabled {
		image: url(:/checkBoxIndeterminateDisabled.png);
	}

	/* Animated/Errored */
	/* ---------------- */

	QCheckBox[gafferAnimated="true"]::indicator {
		background-color: $animatedColor;
	}

	QCheckBox[gafferError="true"]::indicator {
		background-color: $errorColor;
	}

	/* BoolWidget drawn as switch */
	/* ========================== */

	/* Unchecked */
	/* --------- */

	QCheckBox[gafferDisplayMode="Switch"]::indicator:unchecked {
		image: url(:/toggleOff.png);
	}

	QCheckBox[gafferDisplayMode="Switch"]::indicator:unchecked:hover,
	QCheckBox[gafferDisplayMode="Switch"]::indicator:unchecked:focus,
	QCheckBox[gafferDisplayMode="Switch"][gafferHighlighted="true"]::indicator:unchecked {
		image: url(:/toggleOffHover.png);
	}

	QCheckBox[gafferDisplayMode="Switch"]::indicator:unchecked:disabled {
		image: url(:/toggleOffDisabled.png);
	}

	/* Checked */
	/* ------- */

	QCheckBox[gafferDisplayMode="Switch"]::indicator:checked {
		image: url(:/toggleOn.png);
	}

	QCheckBox[gafferDisplayMode="Switch"]::indicator:checked:hover,
	QCheckBox[gafferDisplayMode="Switch"]::indicator:checked:focus,
	QCheckBox[gafferDisplayMode="Switch"][gafferHighlighted="true"]::indicator:checked {
		image: url(:/toggleOnHover.png);
	}

	QCheckBox[gafferDisplayMode="Switch"]::indicator:checked:disabled {
		image: url(:/toggleOnDisabled.png);
	}

	/* Indeterminate */
	/* ------------- */

	QCheckBox[gafferDisplayMode="Switch"]::indicator:indeterminate {
		image: url(:/toggleIndeterminate.png);
	}

	QCheckBox[gafferDisplayMode="Switch"]::indicator:indeterminate:hover,
	QCheckBox[gafferDisplayMode="Switch"]::indicator:indeterminate:focus,
	QCheckBox[gafferDisplayMode="Switch"][gafferHighlighted="true"]::indicator:indeterminate {
		image: url(:/toggleIndeterminateHover.png);
	}

	QCheckBox[gafferDisplayMode="Switch"]::indicator:indeterminate:disabled {
		image: url(:/toggleIndeterminateDisabled.png);
	}

	/* BoolWidget drawn as tool */
	/* ======================== */

	QCheckBox {
		border-radius: 5px;
	}

	QCheckBox[gafferDisplayMode="Tool"]::indicator {
		width: 0px;
		height: 0px;
	}

	QCheckBox[gafferDisplayMode="Tool"] {
		background-color: $backgroundDarkTransparent;
		spacing: 0px;
		width: 30px;
		height: 30px;
		border: 1px solid $backgroundDark;
		padding-left: 4px;
	}

	QCheckBox[gafferDisplayMode="Tool"]:checked {
		background-color: $brightColorTransparent;
	}

	QCheckBox[gafferDisplayMode="Tool"]:hover {
		border-color: $brightColor;
		border-width: 2px;
		padding-left: 3px;
	}

	/* frame */

	*[gafferBorderStyle="None_"] {
		border: none;
		border-radius: $widgetCornerRadius;
		padding: 2px;
	}

	*[gafferBorderStyle="Flat"] {
		border: 1px solid $backgroundDark;
		border-radius: $widgetCornerRadius;
		padding: 2px;
	}

	*[gafferHighlighted="true"][gafferBorderStyle="Flat"] {
		border: 1px solid $brightColor;
	}

	QFrame[gafferClass="GafferUI.Divider"] {
		color: $tintDarkerStrong;
		margin-left: 10px;
		margin-right: 10px;
	}

	QFrame[gafferClass="GafferUI.Divider"][gafferHighlighted="true"] {
		color: $brightColor;
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
		alternate-background-color: $tintDarker;
		paint-alternating-row-colors-for-empty-area: 1;
	}

	*[gafferClass="GafferSceneUI.HierarchyView"] QTreeView::item {
		height: 18px;
		padding-top: 0px;
		padding-bottom: 0px;
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

	QTableView::item:selected {
		background-color: $brightColor;
	}

	QTableView QTableCornerButton::section {
		background-color: transparent;
		border: none;
	}

	_TableView {
		gridline-color: $backgroundLowlight;
		padding: 0px;
		background-color: $backgroundRaised;
	}

	_TableView:disabled {
		color: $foregroundFaded;
	}

	_TableView[gafferEditable="true"] {
		padding: 0px;
		gridline-color: $backgroundLowlight;
	}

	_TableView[gafferEditable="true"]::item {
		background-color: $backgroundLight;
	}

	_TableView::item:selected {
		background-color: $brightColor;
	}

	_TableView QHeaderView::section:vertical {
		padding: 2px;
	}

	*[gafferClass="GafferUI.MessageWidget._MessageTableView"] {
		font-family: $monospaceFontFamily;
		background-color: $background;
		border: 1px solid $backgroundHighlight;
		border-top-color: $backgroundLowlight;
		border-left-color: $backgroundLowlight;
		padding: 0;
	}

	*[gafferClass="GafferUI.MessageWidget.MessageSummaryWidget"] QPushButton {
		padding-left: 4px;
		padding-right: 4px;
	}

	/* checkboxes within table views */

	QTableView::indicator {
		background-color: transparent;
	}

	QTableView::indicator:unchecked {
		image: url(:/checkBoxUnchecked.png);
	}

	QTableView::indicator:unchecked:hover {
		image: url(:/checkBoxUncheckedHover.png);
	}

	QTableView::indicator:checked {
		image: url(:/checkBoxChecked.png);
	}

	QTableView::indicator:checked:hover {
		image: url(:/checkBoxCheckedHover.png);
	}

	QTableView::indicator:selected {
		background-color: $brightColor;
	}

	QTableView[gafferToggleIndicator="true"]::indicator:unchecked {
		image: url(:/toggleOff.png);
	}

	QTableView[gafferToggleIndicator="true"]::indicator:unchecked:hover {
		image: url(:/toggleOffHover.png);
	}

	QTableView[gafferToggleIndicator="true"]::indicator:checked {
		image: url(:/toggleOn.png);
	}

	QTableView[gafferToggleIndicator="true"]::indicator:checked:hover {
		image: url(:/toggleOnHover.png);
	}

	/* highlighted state for VectorDataWidget and tree views */

	_TableView[gafferHighlighted="true"] {
		gridline-color: $brightColor;
	}

	QTreeView[gafferHighlighted="true"],
	_TableView[gafferHighlighted="true"] QHeaderView::section {
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

	QGraphicsView {
		border: none;
	}

	/*
	 * Frame variants
	 * --------------
	 *
	 * \todo Add a `setRole/getRole` methods to GafferUI.Frame
	 * and use that to drive the styling.
	 */

	*[gafferDiff="A"] {
		background: solid rgba( 181, 30, 0, 80 );
	}

	*[gafferDiff="B"] {
		background: solid rgba( 34, 159, 0, 80 );
	}

	*[gafferDiff="AB"] {
		background: solid rgba( 170, 170, 170, 60 );
	}

	*[gafferDiff="Other"] {
		background: solid rgba( 70, 184, 255, 25 );
	}

	*[gafferAlternate="true"] {
		background-color: $backgroundAlt;
	}

	*[gafferDiff="A"][gafferHighlighted="true"],
	*[gafferDiff="B"][gafferHighlighted="true"],
	*[gafferDiff="AB"][gafferHighlighted="true"] {
		background-color: $brightColor;
	}

	#gafferColorInspector,
	*[gafferClass="GafferSceneUI.TransformToolUI._SelectionWidget"],
	*[gafferClass="GafferSceneUI.CropWindowToolUI._StatusWidget"],
	*[gafferClass="GafferUI.EditScopeUI.EditScopePlugValueWidget"] > QFrame,
	*[gafferClass="GafferSceneUI.InteractiveRenderUI._ViewRenderControlUI"] > QFrame,
	*[gafferClass="GafferSceneUI._SceneViewInspector"] > QFrame
	{
		background: rgba( 42, 42, 42, 240 );
		border-color: rgba( 30, 30, 30, 240 );
		border-radius: 2px;
		padding: 2px;
	}

	*[gafferClass="GafferUI.EditScopeUI.EditScopePlugValueWidget"][editScopeActive="true"] QPushButton[gafferWithFrame="true"][gafferMenuIndicator="true"]
	{
		border: 1px solid rgb( 46, 75, 107 );
		border-top-color: rgb( 75, 113, 155 );
		border-left-color: rgb( 75, 113, 155 );
		background-color : qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgb( 69, 113, 161 ), stop: 0.1 rgb( 48, 99, 153 ), stop: 0.90 rgb( 54, 88, 125 ));
	}

	*[gafferClass="GafferSceneUI.InteractiveRenderUI._ViewRenderControlUI"] QPushButton[gafferWithFrame="true"] {
		padding: 1px;
	}

	*[gafferClass="GafferSceneUI.CropWindowToolUI._StatusWidget"]
	{
		margin-left: $toolOverlayInset;
		margin-right: auto;
	}

	#gafferColorInspector
	{
		margin-left: $toolOverlayInset;
		margin-right: $toolOverlayInset;
	}

	*[gafferClass="GafferSceneUI.InstancerUI._VariationsPlugValueWidget"] #gafferVariationCount
	{
		font-family: $monospaceFontFamily;
		font-weight:bold;
		font-size: 11px;
		background: $background;
		border: 1px solid $background;
		border-top-color: $backgroundMidLowlight;
		border-left-color: $backgroundMidLowlight;
		border-radius: 6px;
	}

	/* Corner Rounding - also allow squaring based on adjacency of other widgets */

	*[gafferClass="GafferSceneUI.PrimitiveInspector"] #gafferNodeFrame,
	*[gafferClass="GafferSceneUI.PrimitiveInspector"] #gafferLocationFrame {
		border-radius: $roundedCornerRadius;
	}

	/* Selector specificity bites us here as we can't easily layer this on */
	/* rules like the above, as they are more specific, so we require that */
	/* classes that wish to make use of specific-edge styling to set the   */
	/* relevant adjoining properties to false, rather than omitting them   */

	*[gafferAdjoinedTop="true"] {
		border-top-left-radius: 1px;
		border-top-right-radius: 1px;
	}

	*[gafferAdjoinedTop="false"] {
		border-top-left-radius: $widgetCornerRadius;
		border-top-right-radius: $widgetCornerRadius;
	}

	*[gafferAdjoinedBottom="true"] {
		border-bottom-left-radius: 1px;
		border-bottom-right-radius: 1px;
	}

	*[gafferAdjoinedBottom="false"] {
		border-bottom-left-radius: $widgetCornerRadius;
		border-bottom-right-radius: $widgetCornerRadius;
	}

	*[gafferAdjoinedLeft="true"] {
		border-top-left-radius: 1px;
		border-bottom-left-radius: 1px;
	}

	*[gafferAdjoinedLeft="false"] {
		border-top-left-radius: $widgetCornerRadius;
		border-bottom-left-radius: $widgetCornerRadius;
	}

	*[gafferAdjoinedRight="true"] {
		border-top-right-radius: 1px;
		border-bottom-right-radius: 1px;
	}

	*[gafferAdjoinedRight="false"] {
		border-top-right-radius: $widgetCornerRadius;
		border-bottom-right-radius: $widgetCornerRadius;
	}

	/* Adjoined buttons */
	/* Selector specificity requires radius to be re-specified as the base */
	/* QPushButton[gafferWithFrame="true"] radius overrides those above. */

	QPushButton[gafferAdjoinedTop="true"] {
		border-top-left-radius: 1px;
		border-top-right-radius: 1px;
		border-top-color: $backgroundLightHighlightAdjoined;
		margin-top: 0;
	}

	QPushButton[gafferAdjoinedBottom="true"] {
		border-bottom-left-radius: 1px;
		border-bottom-right-radius: 1px;
		border-bottom-color: $backgroundDarkHighlightAdjoined;
		margin-bottom: 0;
	}

	QPushButton[gafferAdjoinedLeft="true"] {
		border-top-left-radius: 1px;
		border-bottom-left-radius: 1px;
		border-left-color: $backgroundLightHighlightAdjoined;
		margin-left: 0;
	}

	QPushButton[gafferAdjoinedRight="true"] {
		border-top-right-radius: 1px;
		border-bottom-right-radius: 1px;
		border-right-color: $backgroundDarkHighlightAdjoined;
		margin-right: 0;
	}

	/* PathChooseWidget */

	*[gafferClass="GafferUI.PathChooserWidget"] #gafferPathListingContainer {
		border-radius: $widgetCornerRadius;
		background-color: $background;
		border: 1px solid $backgroundHighlight;
		border-right-color: $backgroundLowlight;
		border-bottom-color: $backgroundLowlight;
	}

	/* SceneInspector */

	*[gafferClass="GafferSceneUI.SceneInspector.Row"] > QFrame
	{
		/* Needed to avoid unwanted gaps between sections in the
		 * HistorySection and InheritanceSection.
		 */
		padding: 0px;
	}

	/* SceneViewInspector */

	*[gafferClass="GafferSceneUI._SceneViewInspector"] > QFrame
	{
		margin-right: 1px;
	}

	*[gafferClass="GafferSceneUI._SceneViewInspector._ValueWidget"] {
		font-family: $monospaceFontFamily;
		border-radius: 10px;
		background-color: $inspectorSourceUpstream;
	}

	QLabel[gafferInspectorSourceType="EditScope"] {
		background-color: $inspectorSourceEditScope;
	}

	QLabel[gafferInspectorSourceType="Downstream"] {
		background-color : $inspectorSourceDownstream;
	}

	QLabel[gafferInspectorSourceType="EditScope|Upstream"] {
		background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0.49 $inspectorSourceUpstream, stop:0.51 $inspectorSourceEditScope);
	}

	QLabel[gafferInspectorSourceType="Downstream|EditScope"] {
		background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0.49 $inspectorSourceEditScope, stop:0.51 $inspectorSourceDownstream);
	}

	QLabel[gafferInspectorSourceType="Downstream|EditScope|Upstream"] {
		background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 $inspectorSourceUpstream, stop:0.32 $inspectorSourceUpstream, stop:0.34 $inspectorSourceEditScope, stop:0.65 $inspectorSourceEditScope, stop:0.67 $inspectorSourceDownstream);
	}

	QLabel[gafferInspectorSourceType="Downstream|Upstream"] {
		background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0.49 $inspectorSourceUpstream, stop:0.51 $inspectorSourceDownstream);
	}

	/* PinningWidget */

	QFrame[gafferClass="GafferUI.CompoundEditor._PinningWidget"] #menuDownArrow {
		margin-top: 1px;
		margin-left: 2px;
		margin-right: 1px;
	}

	QFrame[gafferClass="GafferUI.CompoundEditor._PinningWidget"] {
		padding: 1px;
		padding-left: 4px;
		border-radius: 2px;
		border: none;
		background: $background;
	}

	QFrame[gafferClass="GafferImageUI.ImageViewUI._CompareImageWidget"] #menuDownArrow {
		margin-top: 1px;
		margin-left: 2px;
		margin-right: 1px;
	}

	QFrame[gafferClass="GafferImageUI.ImageViewUI._CompareImageWidget"] {
		padding: 2px;
		padding-left: 4px;
		border-radius: 2px;
		border: 1px solid $backgroundDarkHighlight;
		border-top-color: $backgroundLightHighlight;
		background-color : qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 $backgroundLighter, stop: 0.1 $backgroundLightHighlight, stop: 0.90 $backgroundLightLowlight);
		border-top-left-radius: 1px;
		border-bottom-left-radius: 1px;
		border-left-color: $backgroundLightHighlightAdjoined;
		border-top-right-radius: 4px;
		border-bottom-right-radius: 4px;
	}

	QFrame[gafferClass="GafferImageUI.ImageViewUI._CompareImageWidget"]:disabled {
		background-color: $backgroundHighlight;
	}

	QFrame[gafferClass="GafferImageUI.ImageViewUI._CompareImageWidget"]:disabled {
		background-color: $backgroundHighlight;
	}

	QFrame[gafferClass="GafferImageUI.ImageViewUI._CompareImageWidget"][gafferHighlighted="true"] {
		border: 1px solid $brightColor;
	}

	"""

).substitute( substitutions )

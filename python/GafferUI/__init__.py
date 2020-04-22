##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2015, Image Engine Design Inc. All rights reserved.
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

# Work around a bug which causes segfaults if uuid is imported after
# PyQt. See here for details :
#
# https://bugs.gentoo.org/show_bug.cgi?id=317557
# http://www.riverbankcomputing.com/pipermail/pyqt/2010-December/028773.html
#
# Using __import__ rather than import so that we don't pollute the GafferUI
# namespace.
__import__( "uuid" )

## Deprecated. This legacy function only supports use with Qt4. For
# combined Qt4/Qt5 support use `from Qt import name` instead.
# Also note that the lazy argument is no longer effective, because Qt.py
# imports all modules at startup.
__qtModuleName = None
def _qtImport( name, lazy=False ) :

	# decide which qt bindings to use, and apply any fix-ups we need
	# to shield us from PyQt/PySide differences.
	global __qtModuleName
	if __qtModuleName is None :
		import os
		if "GAFFERUI_QT_BINDINGS" in os.environ :
			__qtModuleName = os.environ["GAFFERUI_QT_BINDINGS"]
		else :
			# no preference stated via environment - see what we shipped with
			if os.path.exists( os.environ["GAFFER_ROOT"] + "/python/PySide" ) :
				__qtModuleName = "PySide"
			else :
				__qtModuleName = "PyQt4"

		# PyQt unfortunately uses an implementation-specific
		# naming scheme for its new-style signal and slot classes.
		# We use this to make it compatible with PySide, according to :
		#
		#     http://qt-project.org/wiki/Differences_Between_PySide_and_PyQt
		if "PyQt" in __qtModuleName :
			QtCore = __import__( __qtModuleName + ".QtCore" ).QtCore
			QtCore.Signal = QtCore.pyqtSignal

	# import the submodule from those bindings and return it
	if lazy :
		import Gaffer
		return Gaffer.lazyImport( __qtModuleName + "." + name )
	else :
		qtModule = __import__( __qtModuleName + "." + name )
		return getattr( qtModule, name )

##########################################################################
# Function to return the C++ address of a wrapped Qt object. This can
# be useful if needing to implement part of the UI in C++ and the rest
# in Python.
##########################################################################

def _qtAddress( o ) :

	import Qt
	if "PyQt" in Qt.__binding__ :
		import sip
		return sip.unwrapinstance( o )
	else :
		return __shiboken().getCppPointer( o )[0]

##########################################################################
# Function to return a wrapped Qt object from the given C++ address.
# This can be useful if needing to implement part of the UI in C++ and
# the rest in Python.
##########################################################################

def _qtObject( address, type ) :

	import Qt
	if "PyQt" in Qt.__binding__ :
		import sip
		return sip.wrapinstance( address, type )
	else :
		return __shiboken().wrapInstance( address, type )

##########################################################################
# Determines if the wrapped Qt object is still valid
# Useful when having to deal with the consequences of C++/Python deletion
# order challeneges, see:
#    https://github.com/GafferHQ/gaffer/pull/3179
##########################################################################

def _qtObjectIsValid( o ) :

	import Qt
	if "PyQt" in Qt.__binding__ :
		import sip
		return not sip.isdeleted( o )
	else :
		return __shiboken().isValid( o )

##########################################################################
# Shiboken lives in a variety of places depending on which PySide it is.
##########################################################################

def __shiboken() :

	import Qt
	assert( "PyQt" not in Qt.__binding__ )

	if Qt.__binding__ == "PySide2" :
		try :
			import PySide2.shiboken2 as shiboken
		except ImportError :
			import shiboken2 as shiboken
	else :
		try :
			import PySide.shiboken
		except ImportError :
			import shiboken

	return shiboken

##########################################################################
# now import our actual functionality
##########################################################################

# Import modules that must be imported before _GafferUI, using __import__
# to avoid polluting the GafferUI namespace.
__import__( "IECore" )
__import__( "Gaffer" )

from ._GafferUI import *

# general ui stuff first

from .Enums import *
from .Widget import Widget
from .LazyMethod import LazyMethod
from .Menu import Menu
from .ContainerWidget import ContainerWidget
from .Window import Window
from .SplitContainer import SplitContainer
from .ListContainer import ListContainer
from .GridContainer import GridContainer
from .MenuBar import MenuBar
from .EventLoop import EventLoop
from .TabbedContainer import TabbedContainer
from .TextWidget import TextWidget
from .NumericWidget import NumericWidget
from .Button import Button
from .MultiLineTextWidget import MultiLineTextWidget
from .Label import Label
from .GLWidget import GLWidget
from .ScrolledContainer import ScrolledContainer
from .PathWidget import PathWidget
from .PathListingWidget import PathListingWidget
from .PathChooserWidget import PathChooserWidget
from .Dialogue import Dialogue
from .PathChooserDialogue import PathChooserDialogue
from .TextInputDialogue import TextInputDialogue
from .Collapsible import Collapsible
from .ColorSwatch import ColorSwatch
from .Slider import Slider
from .ShowURL import showURL
from .Spacer import Spacer
from .BoolWidget import BoolWidget, CheckBox
from .Image import Image
from .ErrorDialogue import ErrorDialogue
from ._Variant import _Variant
from .VectorDataWidget import VectorDataWidget
from .PathVectorDataWidget import PathVectorDataWidget
from .ProgressBar import ProgressBar
from .SelectionMenu import SelectionMenu
from .PathFilterWidget import PathFilterWidget
from .CompoundPathFilterWidget import CompoundPathFilterWidget
from .InfoPathFilterWidget import InfoPathFilterWidget
from .MatchPatternPathFilterWidget import MatchPatternPathFilterWidget
from .FileSequencePathFilterWidget import FileSequencePathFilterWidget
from .BusyWidget import BusyWidget
from .NumericSlider import NumericSlider
from .ColorChooser import ColorChooser
from .ColorChooserDialogue import ColorChooserDialogue
from .MessageWidget import MessageWidget
from .NotificationMessageHandler import NotificationMessageHandler
from .MenuButton import MenuButton
from .MultiSelectionMenu import MultiSelectionMenu
from .PopupWindow import PopupWindow
from .ConfirmationDialogue import ConfirmationDialogue
from .DisplayTransform import DisplayTransform
from .Divider import Divider
from . import _Pointer
from .SplineWidget import SplineWidget
from .Bookmarks import Bookmarks
from . import WidgetAlgo

# then all the PathPreviewWidgets. note that the order
# of import controls the order of display.

from .PathPreviewWidget import PathPreviewWidget
from .CompoundPathPreview import CompoundPathPreview
from .DeferredPathPreview import DeferredPathPreview
from .InfoPathPreview import InfoPathPreview
from .HeaderPathPreview import HeaderPathPreview
from .DataPathPreview import DataPathPreview

# then stuff specific to graph uis

from .BackgroundMethod import BackgroundMethod
from .PlugValueWidget import PlugValueWidget
from .StringPlugValueWidget import StringPlugValueWidget
from .NumericPlugValueWidget import NumericPlugValueWidget
from .BoolPlugValueWidget import BoolPlugValueWidget
from .PathPlugValueWidget import PathPlugValueWidget
from .FileSystemPathPlugValueWidget import FileSystemPathPlugValueWidget
from .VectorDataPlugValueWidget import VectorDataPlugValueWidget
from .PathVectorDataPlugValueWidget import PathVectorDataPlugValueWidget
from .FileSystemPathVectorDataPlugValueWidget import FileSystemPathVectorDataPlugValueWidget
from .PlugWidget import PlugWidget
from .PlugLayout import PlugLayout
from .Editor import Editor
from .PythonEditor import PythonEditor
from .GadgetWidget import GadgetWidget
from .GraphEditor import GraphEditor
from .ScriptWindow import ScriptWindow
from .CompoundEditor import CompoundEditor
from .NameWidget import NameWidget
from .NameLabel import NameLabel
from .NodeSetEditor import NodeSetEditor
from .NodeEditor import NodeEditor
from .Layouts import Layouts
from .NodeMenu import NodeMenu
from . import FileMenu
from . import LayoutMenu
from . import EditMenu
from . import UserPlugs
from .Frame import Frame
from .CompoundNumericPlugValueWidget import CompoundNumericPlugValueWidget
from .BoxPlugValueWidget import BoxPlugValueWidget
from .NodeUI import NodeUI
from .StandardNodeUI import StandardNodeUI
from .NodeToolbar import NodeToolbar
from .StandardNodeToolbar import StandardNodeToolbar
from .Viewer import Viewer
from .ColorSwatchPlugValueWidget import ColorSwatchPlugValueWidget
from .ColorPlugValueWidget import ColorPlugValueWidget
from .AboutWindow import AboutWindow
from . import ApplicationMenu
from .BrowserEditor import BrowserEditor
from .Timeline import Timeline
from .MultiLineStringPlugValueWidget import MultiLineStringPlugValueWidget
from .PresetsPlugValueWidget import PresetsPlugValueWidget
from .GraphComponentBrowserMode import GraphComponentBrowserMode
from .ToolPlugValueWidget import ToolPlugValueWidget
from .LabelPlugValueWidget import LabelPlugValueWidget
from .CompoundDataPlugValueWidget import CompoundDataPlugValueWidget
from .LayoutPlugValueWidget import LayoutPlugValueWidget
from . import ScriptNodeUI
from .RefreshPlugValueWidget import RefreshPlugValueWidget
from . import PreferencesUI
from .SplinePlugValueWidget import SplinePlugValueWidget
from .RampPlugValueWidget import RampPlugValueWidget
from .NodeFinderDialogue import NodeFinderDialogue
from .ConnectionPlugValueWidget import ConnectionPlugValueWidget
from .ButtonPlugValueWidget import ButtonPlugValueWidget
from . import ViewUI
from . import ToolUI
from .Playback import Playback
from . import MetadataWidget
from .UIEditor import UIEditor
from . import GraphBookmarksUI
from . import DocumentationAlgo
from . import _PlugAdder
from .Backups import Backups
from .AnimationEditor import AnimationEditor
from . import CompoundNumericNoduleUI
from . import Examples
from .NameValuePlugValueWidget import NameValuePlugValueWidget
from .ShufflePlugValueWidget import ShufflePlugValueWidget
from .ShufflePlugValueWidget import ShufflesPlugValueWidget

# and then specific node uis

from . import DependencyNodeUI
from . import ComputeNodeUI
from . import RandomUI
from . import SpreadsheetUI
from . import ExpressionUI
from . import BoxUI
from . import ReferenceUI
from . import BackdropUI
from . import DotUI
from . import SubGraphUI
from . import SwitchUI
from . import ContextProcessorUI
from . import ContextVariablesUI
from . import DeleteContextVariablesUI
from . import TimeWarpUI
from . import LoopUI
from . import AnimationUI
from . import BoxIOUI
from . import BoxInUI
from . import BoxOutUI
from . import NameSwitchUI
from . import EditScopeUI

# backwards compatibility
## \todo Remove me
Metadata = __import__( "Gaffer" ).Metadata

__import__( "IECore" ).loadConfig( "GAFFER_STARTUP_PATHS", subdirectory = "GafferUI" )

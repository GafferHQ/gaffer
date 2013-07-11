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

##########################################################################
# Function to import a module from the qt bindings. This must be used
# rather than importing the module directly. This allows us to support
# the use of both PyQt and PySide.
##########################################################################

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
			import glob
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
# now import our actual functionality
##########################################################################

import IECore

from _GafferUI import *

# general ui stuff first

from Enums import *
from Widget import Widget
from Menu import Menu
from ContainerWidget import ContainerWidget
from Window import Window
from SplitContainer import SplitContainer
from ListContainer import ListContainer
from GridContainer import GridContainer
from MenuBar import MenuBar
from EventLoop import EventLoop
from TabbedContainer import TabbedContainer
from TextWidget import TextWidget
from NumericWidget import NumericWidget
from Button import Button
from MultiLineTextWidget import MultiLineTextWidget
from Label import Label
from GLWidget import GLWidget
from ScrolledContainer import ScrolledContainer
from PathWidget import PathWidget
from PathListingWidget import PathListingWidget
from PathChooserWidget import PathChooserWidget
from Dialogue import Dialogue
from PathChooserDialogue import PathChooserDialogue
from TextInputDialogue import TextInputDialogue
from Collapsible import Collapsible
from ColorSwatch import ColorSwatch
from Slider import Slider
from ShowURL import showURL
from Spacer import Spacer
from CheckBox import CheckBox
from Image import Image
from ErrorDialogue import ErrorDialogue
from _Variant import _Variant
from VectorDataWidget import VectorDataWidget
from PathVectorDataWidget import PathVectorDataWidget
from ProgressBar import ProgressBar
from SelectionMenu import SelectionMenu
from MultiSelectionMenu import MultiSelectionMenu
from PathFilterWidget import PathFilterWidget
from CompoundPathFilterWidget import CompoundPathFilterWidget
from InfoPathFilterWidget import InfoPathFilterWidget
from BusyWidget import BusyWidget
from PathPreviewWidget import PathPreviewWidget
from CompoundPathPreview import CompoundPathPreview
from DeferredPathPreview import DeferredPathPreview
from HeaderPathPreview import HeaderPathPreview
from InfoPathPreview import InfoPathPreview
from ReaderPathPreview import ReaderPathPreview
from FileIndexedIOPathPreview import FileIndexedIOPathPreview
from DataPathPreview import DataPathPreview
from OpPathPreview import OpPathPreview
from NumericSlider import NumericSlider
from ColorChooser import ColorChooser
from ColorChooserDialogue import ColorChooserDialogue
from NotificationMessageHandler import NotificationMessageHandler
from AttributeCachePathPreview import AttributeCachePathPreview
from MenuButton import MenuButton
from PopupWindow import PopupWindow
from ConfirmationDialogue import ConfirmationDialogue
from DisplayTransform import DisplayTransform
from Divider import Divider
import _Pointer
from SplineWidget import SplineWidget

# then stuff specific to graph uis

from Metadata import Metadata
from PlugValueWidget import PlugValueWidget
from StringPlugValueWidget import StringPlugValueWidget
from NumericPlugValueWidget import NumericPlugValueWidget
from BoolPlugValueWidget import BoolPlugValueWidget
from PathPlugValueWidget import PathPlugValueWidget
from VectorDataPlugValueWidget import VectorDataPlugValueWidget
from PathVectorDataPlugValueWidget import PathVectorDataPlugValueWidget
from PlugWidget import PlugWidget
from EditorWidget import EditorWidget
from ScriptEditor import ScriptEditor
from GadgetWidget import GadgetWidget
from NodeGraph import NodeGraph
from ScriptWindow import ScriptWindow
from CompoundEditor import CompoundEditor
from NameWidget import NameWidget
from NameLabel import NameLabel
from NodeSetEditor import NodeSetEditor
from NodeEditor import NodeEditor
from Layouts import Layouts
from NodeMenu import NodeMenu
import FileMenu
import LayoutMenu
import EditMenu
from Viewer import Viewer
from Frame import Frame
from CompoundNumericPlugValueWidget import CompoundNumericPlugValueWidget
from NodeUI import NodeUI
from StandardNodeUI import StandardNodeUI
from ColorPlugValueWidget import ColorPlugValueWidget
from AboutWindow import AboutWindow
import ApplicationMenu
from BrowserEditor import BrowserEditor
from Timeline import Timeline
from MultiLineStringPlugValueWidget import MultiLineStringPlugValueWidget
from CompoundPlugValueWidget import CompoundPlugValueWidget
from EnumPlugValueWidget import EnumPlugValueWidget
from GraphComponentBrowserMode import GraphComponentBrowserMode
from ToolPlugValueWidget import ToolPlugValueWidget
from LabelPlugValueWidget import LabelPlugValueWidget
from CompoundDataPlugValueWidget import CompoundDataPlugValueWidget
from SectionedCompoundDataPlugValueWidget import SectionedCompoundDataPlugValueWidget
import ExecuteUI
import ScriptNodeUI
from TransformPlugValueWidget import TransformPlugValueWidget
from IncrementingPlugValueWidget import IncrementingPlugValueWidget
from SectionedCompoundPlugValueWidget import SectionedCompoundPlugValueWidget
from UserPlugValueWidget import UserPlugValueWidget
import PreferencesUI
from SplinePlugValueWidget import SplinePlugValueWidget
from RampPlugValueWidget import RampPlugValueWidget

# then stuff specific to parameterised objects

from OpDialogue import OpDialogue
from ParameterisedHolderNodeUI import ParameterisedHolderNodeUI
from ParameterValueWidget import ParameterValueWidget
from PresetsOnlyParameterValueWidget import PresetsOnlyParameterValueWidget
from CompoundParameterValueWidget import CompoundParameterValueWidget
from PathParameterValueWidget import PathParameterValueWidget
from PathVectorParameterValueWidget import PathVectorParameterValueWidget
from StringParameterValueWidget import StringParameterValueWidget
from CompoundVectorParameterValueWidget import CompoundVectorParameterValueWidget
from FileSequenceParameterValueWidget import FileSequenceParameterValueWidget
from DateTimeParameterValueWidget import DateTimeParameterValueWidget
from ClassParameterValueWidget import ClassParameterValueWidget
from FileSequenceVectorParameterValueWidget import FileSequenceVectorParameterValueWidget
from ClassVectorParameterValueWidget import ClassVectorParameterValueWidget
from TimeCodeParameterValueWidget import TimeCodeParameterValueWidget
from ToolParameterValueWidget import ToolParameterValueWidget
import ParameterPresets

# and specific node uis

import ReadNodeUI
import WriteNodeUI
import RandomUI
import ExpressionUI
import BoxUI
import ReferenceUI

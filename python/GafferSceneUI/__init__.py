##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2012-2014, Image Engine Design Inc. All rights reserved.
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

from _GafferSceneUI import *

from SceneHierarchy import SceneHierarchy
from SceneInspector import SceneInspector
from FilterPlugValueWidget import FilterPlugValueWidget
import SceneNodeUI
import SceneReaderUI
import SceneProcessorUI
import FilteredSceneProcessorUI
import PruneUI
import SubTreeUI
import OutputsUI
import OptionsUI
import OpenGLAttributesUI
import SceneContextVariablesUI
import SceneWriterUI
import StandardOptionsUI
import StandardAttributesUI
import ShaderUI
import OpenGLShaderUI
import ObjectSourceUI
import TransformUI
import AttributesUI
import LightUI
import InteractiveRenderUI
import SphereUI
import MapProjectionUI
import MapOffsetUI
import CustomAttributesUI
import CustomOptionsUI
import SceneViewToolbar
import SceneSwitchUI
import ShaderSwitchUI
import ShaderAssignmentUI
import ParentConstraintUI
import ParentUI
import PrimitiveVariablesUI
import DuplicateUI
import GridUI
import SetFilterUI
import DeleteGlobalsUI
import DeleteOptionsUI
import DeleteSetsUI
import ExternalProceduralUI
import ExecutableRenderUI
import IsolateUI
import SelectionToolUI
import CropWindowToolUI
import CameraUI
import SetUI
import ClippingPlaneUI
import FilterUI
import FilterSwitchUI
import PointsTypeUI

# then all the PathPreviewWidgets. note that the order
# of import controls the order of display.

from AlembicPathPreview import AlembicPathPreview
from SceneReaderPathPreview import SceneReaderPathPreview

__import__( "IECore" ).loadConfig( "GAFFER_STARTUP_PATHS", {}, subdirectory = "GafferSceneUI" )

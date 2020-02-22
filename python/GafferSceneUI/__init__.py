##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2012-2016, Image Engine Design Inc. All rights reserved.
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

__import__( "GafferImageUI" )
__import__( "GafferScene" )

from _GafferSceneUI import *

from HierarchyView import HierarchyView
from SceneInspector import SceneInspector
from PrimitiveInspector import PrimitiveInspector
from UVInspector import UVInspector
from FilterPlugValueWidget import FilterPlugValueWidget
from ScenePathPlugValueWidget import ScenePathPlugValueWidget
from TweakPlugValueWidget import TweakPlugValueWidget
import SceneHistoryUI
import EditScopeUI

import SceneNodeUI
import SceneReaderUI
import SceneProcessorUI
import FilteredSceneProcessorUI
import PruneUI
import SubTreeUI
import OutputsUI
import OptionsUI
import OpenGLAttributesUI
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
import SceneViewUI
import ShaderViewUI
import ShaderAssignmentUI
import ParentConstraintUI
import ParentUI
import PrimitiveVariablesUI
import DuplicateUI
import GridUI
import SetFilterUI
import DeleteGlobalsUI
import DeleteOptionsUI
import CopyOptionsUI
import DeleteSetsUI
import ExternalProceduralUI
import IsolateUI
import SelectionToolUI
import CropWindowToolUI
import CameraUI
import SetUI
import ClippingPlaneUI
import FilterUI
import PointsTypeUI
import ParametersUI
import TextUI
import AimConstraintUI
import CoordinateSystemUI
import DeleteAttributesUI
import SeedsUI
import UnionFilterUI
import PathFilterUI
import GroupUI
import OpenGLRenderUI
import PrimitiveVariableProcessorUI
import DeletePrimitiveVariablesUI
import MeshTypeUI
import DeleteOutputsUI
import InstancerUI
import ObjectToSceneUI
import FreezeTransformUI
import SceneElementProcessorUI
import PointConstraintUI
import BranchCreatorUI
import ConstraintUI
import PlaneUI
import CubeUI
import AttributeVisualiserUI
import FilterProcessorUI
import MeshToPointsUI
import RenderUI
import ShaderBallUI
import ShaderTweaksUI
import CameraTweaksUI
import LightToCameraUI
import FilterResultsUI
import TransformToolUI
import TranslateToolUI
import ScaleToolUI
import RotateToolUI
import MeshTangentsUI
import ResamplePrimitiveVariablesUI
import DeleteFacesUI
import DeleteCurvesUI
import DeletePointsUI
import CollectScenesUI
import EncapsulateUI
import GlobalShaderUI
import CameraToolUI
import ReverseWindingUI
import MeshDistortionUI
import DeleteObjectUI
import CopyAttributesUI
import CollectPrimitiveVariablesUI
import PrimitiveVariableExistsUI
import CollectTransformsUI
import UDIMQueryUI
import WireframeUI
import SetVisualiserUI
import LightFilterUI
import OrientationUI
import DeformerUI
import CopyPrimitiveVariablesUI
import MergeScenesUI
import ShuffleAttributesUI
import ShufflePrimitiveVariablesUI
import LocaliseAttributesUI
import PrimitiveSamplerUI
import ClosestPointSamplerUI

# then all the PathPreviewWidgets. note that the order
# of import controls the order of display.

from SceneReaderPathPreview import SceneReaderPathPreview

__import__( "IECore" ).loadConfig( "GAFFER_STARTUP_PATHS", subdirectory = "GafferSceneUI" )

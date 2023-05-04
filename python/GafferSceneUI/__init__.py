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
__import__( "GafferDispatchUI" )
__import__( "GafferScene" )

from ._GafferSceneUI import *

from .HierarchyView import HierarchyView
from .SceneInspector import SceneInspector
from .PrimitiveInspector import PrimitiveInspector
from .UVInspector import UVInspector
from .FilterPlugValueWidget import FilterPlugValueWidget
from .ScenePathPlugValueWidget import ScenePathPlugValueWidget
from .LightEditor import LightEditor
from .SetEditor import SetEditor
from . import SceneHistoryUI
from . import EditScopeUI

from . import SceneNodeUI
from . import SceneReaderUI
from . import SceneProcessorUI
from . import FilteredSceneProcessorUI
from . import PruneUI
from . import SubTreeUI
from . import OutputsUI
from . import OptionsUI
from . import OpenGLAttributesUI
from . import SceneWriterUI
from . import StandardOptionsUI
from . import StandardAttributesUI
from . import ShaderUI
from . import OpenGLShaderUI
from . import ObjectSourceUI
from . import TransformUI
from . import AttributesUI
from . import LightUI
from . import InteractiveRenderUI
from . import SphereUI
from . import MapProjectionUI
from . import MapOffsetUI
from . import CustomAttributesUI
from . import CustomOptionsUI
from . import SceneViewUI
from . import ShaderViewUI
from . import ShaderAssignmentUI
from . import ParentConstraintUI
from . import ParentUI
from . import PrimitiveVariablesUI
from . import DuplicateUI
from . import GridUI
from . import SetFilterUI
from . import DeleteGlobalsUI
from . import DeleteOptionsUI
from . import CopyOptionsUI
from . import DeleteSetsUI
from . import ExternalProceduralUI
from . import IsolateUI
from . import SelectionToolUI
from . import CropWindowToolUI
from . import CameraUI
from . import SetUI
from . import ClippingPlaneUI
from . import FilterUI
from . import PointsTypeUI
from . import ParametersUI
from . import TextUI
from . import AimConstraintUI
from . import CoordinateSystemUI
from . import DeleteAttributesUI
from . import ScatterUI
from . import UnionFilterUI
from . import PathFilterUI
from . import GroupUI
from . import OpenGLRenderUI
from . import PrimitiveVariableProcessorUI
from . import DeletePrimitiveVariablesUI
from . import MeshTypeUI
from . import DeleteOutputsUI
from . import InstancerUI
from . import ObjectToSceneUI
from . import FreezeTransformUI
from . import SceneElementProcessorUI
from . import PointConstraintUI
from . import BranchCreatorUI
from . import ConstraintUI
from . import PlaneUI
from . import CubeUI
from . import AttributeVisualiserUI
from . import FilterProcessorUI
from . import MeshToPointsUI
from . import RenderUI
from . import ShaderBallUI
from . import ShaderTweaksUI
from . import CameraTweaksUI
from . import LightToCameraUI
from . import FilterResultsUI
from . import TransformToolUI
from . import TranslateToolUI
from . import ScaleToolUI
from . import RotateToolUI
from . import MeshTangentsUI
from . import ResamplePrimitiveVariablesUI
from . import DeleteFacesUI
from . import DeleteCurvesUI
from . import DeletePointsUI
from . import CollectScenesUI
from . import EncapsulateUI
from . import GlobalShaderUI
from . import CameraToolUI
from . import ReverseWindingUI
from . import MeshDistortionUI
from . import DeleteObjectUI
from . import CopyAttributesUI
from . import CollectPrimitiveVariablesUI
from . import PrimitiveVariableExistsUI
from . import CollectTransformsUI
from . import UDIMQueryUI
from . import WireframeUI
from . import SetVisualiserUI
from . import LightFilterUI
from . import OrientationUI
from . import DeformerUI
from . import CopyPrimitiveVariablesUI
from . import MergeScenesUI
from . import ShuffleAttributesUI
from . import ShufflePrimitiveVariablesUI
from . import LocaliseAttributesUI
from . import PrimitiveSamplerUI
from . import ClosestPointSamplerUI
from . import CurveSamplerUI
from . import UnencapsulateUI
from . import MotionPathUI
from . import FilterQueryUI
from . import TransformQueryUI
from . import BoundQueryUI
from . import ExistenceQueryUI
from . import AttributeQueryUI
from . import UVSamplerUI
from . import CryptomatteUI
from . import ShaderQueryUI
from . import AttributeTweaksUI
from . import OptionTweaksUI
from . import OptionQueryUI
from . import RenameUI
from . import PrimitiveVariableQueryUI
from . import SetQueryUI
from . import MeshSegmentsUI
from . import ImageToPointsUI
from . import MeshSplitUI
from . import FramingConstraintUI
from . import MeshNormalsUI

# then all the PathPreviewWidgets. note that the order
# of import controls the order of display.

from .SceneReaderPathPreview import SceneReaderPathPreview

__import__( "IECore" ).loadConfig( "GAFFER_STARTUP_PATHS", subdirectory = "GafferSceneUI" )

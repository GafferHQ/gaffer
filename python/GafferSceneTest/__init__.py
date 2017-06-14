##########################################################################
#
#  Copyright (c) 2012-2014, John Haddon. All rights reserved.
#  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

import GafferScene

from _GafferSceneTest import *

from SceneTestCase import SceneTestCase
from ScenePlugTest import ScenePlugTest
from GroupTest import GroupTest
from SceneTimeWarpTest import SceneTimeWarpTest
from SceneProceduralTest import SceneProceduralTest
from CubeTest import CubeTest
from PlaneTest import PlaneTest
from SphereTest import SphereTest
from InstancerTest import InstancerTest
from ObjectToSceneTest import ObjectToSceneTest
from CameraTest import CameraTest
from OutputsTest import OutputsTest
from CustomOptionsTest import CustomOptionsTest
from DeleteOptionsTest import DeleteOptionsTest
from CopyOptionsTest import CopyOptionsTest
from SceneNodeTest import SceneNodeTest
from PathMatcherTest import PathMatcherTest
from PathFilterTest import PathFilterTest
from ShaderAssignmentTest import ShaderAssignmentTest
from CustomAttributesTest import CustomAttributesTest
from AlembicSourceTest import AlembicSourceTest
from DeletePrimitiveVariablesTest import DeletePrimitiveVariablesTest
from SeedsTest import SeedsTest
from SceneContextVariablesTest import SceneContextVariablesTest
from DeleteSceneContextVariablesTest import DeleteSceneContextVariablesTest
from SubTreeTest import SubTreeTest
from OpenGLAttributesTest import OpenGLAttributesTest
from StandardOptionsTest import StandardOptionsTest
from ScenePathTest import ScenePathTest
from PathMatcherDataTest import PathMatcherDataTest
from LightTest import LightTest
from TestRender import TestRender
from RenderTest import RenderTest
from OpenGLShaderTest import OpenGLShaderTest
from OpenGLRenderTest import OpenGLRenderTest
from TransformTest import TransformTest
from AimConstraintTest import AimConstraintTest
from PruneTest import PruneTest
from ShaderTest import ShaderTest
from TextTest import TextTest
from MapProjectionTest import MapProjectionTest
from MapOffsetTest import MapOffsetTest
from PointConstraintTest import PointConstraintTest
from SceneReaderTest import SceneReaderTest
from SceneWriterTest import SceneWriterTest
from IsolateTest import IsolateTest
from DeleteAttributesTest import DeleteAttributesTest
from UnionFilterTest import UnionFilterTest
from SceneSwitchTest import SceneSwitchTest
from ShaderSwitchTest import ShaderSwitchTest
from ParentConstraintTest import ParentConstraintTest
from ParentTest import ParentTest
from StandardAttributesTest import StandardAttributesTest
from PrimitiveVariablesTest import PrimitiveVariablesTest
from DuplicateTest import DuplicateTest
from ModuleTest import ModuleTest
from GridTest import GridTest
from SetTest import SetTest
from FreezeTransformTest import FreezeTransformTest
from SetFilterTest import SetFilterTest
from FilterTest import FilterTest
from SceneAlgoTest import SceneAlgoTest
from CoordinateSystemTest import CoordinateSystemTest
from DeleteOutputsTest import DeleteOutputsTest
from ExternalProceduralTest import ExternalProceduralTest
from ClippingPlaneTest import ClippingPlaneTest
from FilterSwitchTest import FilterSwitchTest
from PointsTypeTest import PointsTypeTest
from ParametersTest import ParametersTest
from SceneFilterPathFilterTest import SceneFilterPathFilterTest
from AttributeVisualiserTest  import AttributeVisualiserTest
from SceneLoopTest import SceneLoopTest
from SceneProcessorTest import SceneProcessorTest
from MeshToPointsTest import MeshToPointsTest
from InteractiveRenderTest import InteractiveRenderTest
from FilteredSceneProcessorTest import FilteredSceneProcessorTest
from ShaderBallTest import ShaderBallTest
from LightTweaksTest import LightTweaksTest
from FilterResultsTest import FilterResultsTest
from RendererAlgoTest import RendererAlgoTest
from SetAlgoTest import SetAlgoTest
from EvaluateLightLinksTest import EvaluateLightLinksTest
from MeshTangentsTest import MeshTangentsTest
from ResamplePrimitiveVariablesTest import ResamplePrimitiveVariablesTest
from DeleteFacesTest import DeleteFacesTest
from DeleteCurvesTest import DeleteCurvesTest
from DeletePointsTest import DeletePointsTest

if __name__ == "__main__":
	import unittest
	unittest.main()

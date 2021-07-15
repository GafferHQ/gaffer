##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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

from ._GafferImageTest import *

from .ImageTestCase import ImageTestCase
from .ImagePlugTest import ImagePlugTest
from .OpenImageIOReaderTest import OpenImageIOReaderTest
from .ImageReaderTest import ImageReaderTest
from .ColorSpaceTest import ColorSpaceTest
from .FormatTest import FormatTest
from .AtomicFormatPlugTest import AtomicFormatPlugTest
from .MergeTest import MergeTest
from .GradeTest import GradeTest
from .ConstantTest import ConstantTest
from .CheckerboardTest import CheckerboardTest
from .RampTest import RampTest
from .ImageWriterTest import ImageWriterTest
from .SamplerTest import SamplerTest
from .DisplayTest import DisplayTest
from .ImageStatsTest import ImageStatsTest
from .ImageTransformTest import ImageTransformTest
from .DeleteChannelsTest import DeleteChannelsTest
from .ClampTest import ClampTest
from .ImageSwitchTest import ImageSwitchTest
from .ImageTimeWarpTest import ImageTimeWarpTest
from .ImageSamplerTest import ImageSamplerTest
from .ImageNodeTest import ImageNodeTest
from .FormatDataTest import FormatDataTest
from .ImageMetadataTest import ImageMetadataTest
from .DeleteImageMetadataTest import DeleteImageMetadataTest
from .CopyImageMetadataTest import CopyImageMetadataTest
from .ImageLoopTest import ImageLoopTest
from .ImageProcessorTest import ImageProcessorTest
from .ShuffleTest import ShuffleTest
from .PremultiplyTest import PremultiplyTest
from .UnpremultiplyTest import UnpremultiplyTest
from .CropTest import CropTest
from .ResampleTest import ResampleTest
from .ResizeTest import ResizeTest
from .LUTTest import LUTTest
from .CDLTest import CDLTest
from .ImageAlgoTest import ImageAlgoTest
from .BufferAlgoTest import BufferAlgoTest
from .DisplayTransformTest import DisplayTransformTest
from .FormatPlugTest import FormatPlugTest
from .OffsetTest import OffsetTest
from .BlurTest import BlurTest
from .TextTest import TextTest
from .OpenColorIOTransformTest import OpenColorIOTransformTest
from .VectorWarpTest import VectorWarpTest
from .MirrorTest import MirrorTest
from .CopyChannelsTest import CopyChannelsTest
from .FilterAlgoTest import FilterAlgoTest
from .MedianTest import MedianTest
from .ErodeTest import ErodeTest
from .DilateTest import DilateTest
from .MixTest import MixTest
from .CatalogueTest import CatalogueTest
from .CollectImagesTest import CollectImagesTest
from .CatalogueSelectTest import CatalogueSelectTest
from .BleedFillTest import BleedFillTest
from .RectangleTest import RectangleTest
from .ModuleTest import ModuleTest
from .FlatToDeepTest import FlatToDeepTest
from .DeepMergeTest import DeepMergeTest
from .DeepStateTest import DeepStateTest
from .EmptyTest import EmptyTest
from .DeepHoldoutTest import DeepHoldoutTest
from .DeepRecolorTest import DeepRecolorTest
from .ContextSanitiserTest import ContextSanitiserTest
from .SaturationTest import SaturationTest

if __name__ == "__main__":
	import unittest
	unittest.main()

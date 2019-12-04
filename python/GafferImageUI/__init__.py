##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2012-2015, Image Engine Design Inc. All rights reserved.
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

__import__( "GafferUI" )

from _GafferImageUI import *

import DisplayUI
from FormatPlugValueWidget import FormatPlugValueWidget
from ChannelMaskPlugValueWidget import ChannelMaskPlugValueWidget
from RGBAChannelsPlugValueWidget import RGBAChannelsPlugValueWidget
from ChannelPlugValueWidget import ChannelPlugValueWidget

import ImageReaderPathPreview

import OpenImageIOReaderUI
import ImageReaderUI
import ImageViewUI
import ImageTransformUI
import ConstantUI
import CheckerboardUI
import RampUI
import ColorSpaceUI
import ImageStatsUI
import DeleteChannelsUI
import ClampUI
import ImageWriterUI
import GradeUI
import ImageSamplerUI
import MergeUI
import ImageNodeUI
import FlatImageSourceUI
import ChannelDataProcessorUI
import ImageProcessorUI
import FlatImageProcessorUI
import ImageMetadataUI
import DeleteImageMetadataUI
import CopyImageMetadataUI
import ShuffleUI
import PremultiplyUI
import UnpremultiplyUI
import CropUI
import ResizeUI
import ResampleUI
import LUTUI
import CDLUI
import DisplayTransformUI
import OpenColorIOTransformUI
import OffsetUI
import BlurUI
import ShapeUI
import TextUI
import WarpUI
import VectorWarpUI
import MirrorUI
import CopyChannelsUI
import MedianUI
import RankFilterUI
import ErodeUI
import DilateUI
import ColorProcessorUI
import MixUI
import CatalogueUI
import CollectImagesUI
import CatalogueSelectUI
import BleedFillUI
import RectangleUI
import FlatToDeepUI
import DeepMergeUI
import DeepStateUI
import EmptyUI
import DeepSampleCountsUI
import DeepSamplerUI
import DeepToFlatUI
import DeepTidyUI
import DeepHoldoutUI
import DeepRecolorUI

__import__( "IECore" ).loadConfig( "GAFFER_STARTUP_PATHS", subdirectory = "GafferImageUI" )

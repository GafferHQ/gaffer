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
__import__( "GafferDispatchUI" )

from ._GafferImageUI import *

from . import DisplayUI
from .FormatPlugValueWidget import FormatPlugValueWidget
from .ChannelMaskPlugValueWidget import ChannelMaskPlugValueWidget
from .RGBAChannelsPlugValueWidget import RGBAChannelsPlugValueWidget
from .ChannelPlugValueWidget import ChannelPlugValueWidget
from .ViewPlugValueWidget import ViewPlugValueWidget
from .ImageInspector import ImageInspector

from . import ImageReaderPathPreview

from . import OpenImageIOReaderUI
from . import ImageReaderUI
from . import ImageViewUI
from . import ImageTransformUI
from . import ConstantUI
from . import CheckerboardUI
from . import RampUI
from . import ColorSpaceUI
from . import ImageStatsUI
from . import DeleteChannelsUI
from . import ClampUI
from . import ImageWriterUI
from . import GradeUI
from . import ImageSamplerUI
from . import MergeUI
from . import ImageNodeUI
from . import FlatImageSourceUI
from . import ChannelDataProcessorUI
from . import ImageProcessorUI
from . import FlatImageProcessorUI
from . import ImageMetadataUI
from . import DeleteImageMetadataUI
from . import CopyImageMetadataUI
from . import ShuffleUI
from . import PremultiplyUI
from . import UnpremultiplyUI
from . import CropUI
from . import ResampleUI
from . import ResizeUI
from . import LUTUI
from . import CDLUI
from . import DisplayTransformUI
from . import OpenColorIOTransformUI
from . import OffsetUI
from . import BlurUI
from . import ShapeUI
from . import TextUI
from . import WarpUI
from . import VectorWarpUI
from . import MirrorUI
from . import CopyChannelsUI
from . import MedianUI
from . import RankFilterUI
from . import ErodeUI
from . import DilateUI
from . import ColorProcessorUI
from . import MixUI
from . import CatalogueUI
from . import CollectImagesUI
from . import CatalogueSelectUI
from . import BleedFillUI
from . import RectangleUI
from . import FlatToDeepUI
from . import DeepMergeUI
from . import DeepStateUI
from . import EmptyUI
from . import DeepSampleCountsUI
from . import DeepSamplerUI
from . import DeepToFlatUI
from . import DeepTidyUI
from . import DeepHoldoutUI
from . import DeepRecolorUI
from . import SaturationUI
from . import FormatQueryUI
from . import CreateViewsUI
from . import SelectViewUI
from . import DeleteViewsUI
from . import CopyViewsUI
from . import AnaglyphUI
from . import LookTransformUI
from . import OpenColorIOContextUI
from . import OpenColorIOConfigPlugUI
from . import DeepSliceUI
from . import ContactSheetCoreUI

__import__( "IECore" ).loadConfig( "GAFFER_STARTUP_PATHS", subdirectory = "GafferImageUI" )

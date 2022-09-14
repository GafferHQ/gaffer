//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//      * Redistributions of source code must retain the above
//        copyright notice, this list of conditions and the following
//        disclaimer.
//
//      * Redistributions in binary form must reproduce the above
//        copyright notice, this list of conditions and the following
//        disclaimer in the documentation and/or other materials provided with
//        the distribution.
//
//      * Neither the name of John Haddon nor the names of
//        any other contributors to this software may be used to endorse or
//        promote products derived from this software without specific prior
//        written permission.
//
//  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
//  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
//  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
//  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
//  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
//  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
//  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
//  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
//  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
//  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
//  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
//////////////////////////////////////////////////////////////////////////

#ifndef GAFFERIMAGE_TYPEIDS_H
#define GAFFERIMAGE_TYPEIDS_H

namespace GafferImage
{

enum TypeId
{
	ImagePlugTypeId = 110750,
	ImageNodeTypeId = 110751,
	ImageReaderTypeId = 110752,
	ImagePrimitiveNodeTypeId = 110753, // Obsolete - available for reuse
	DisplayTypeId = 110754,
	GafferDisplayDriverTypeId = 110755,
	ImageProcessorTypeId = 110756,
	ChannelDataProcessorTypeId = 110757,
	ColorSpaceTypeId = 110758,
	LookTransformTypeId = 110759,
	FormatDataTypeId = 110760,
	AtomicFormatPlugTypeId = 110761,
	MergeTypeId = 110762,
	GradeTypeId = 110763,
	ShuffleTypeId = 110764,
	ConstantTypeId = 110765,
	ShuffleChannelPlugTypeId = 110766,
	ChannelMaskPlugTypeId = 110767,
	WarpTypeId = 110768,
	VectorWarpTypeId = 110769,
	ImageWriterTypeId = 110770,
	ImageTransformTypeId = 110771,
	CatalogueTypeId = 110772,
	CatalogueImageTypeId = 110773,
	CheckerboardTypeId = 110774,
	FlatImageSourceTypeId = 110775,
	CreateViewsTypeId = 110776,
	SelectViewTypeId = 110777,
	DeleteViewsTypeId = 110778,
	CopyViewsTypeId = 110779,
	CatmullRomFilterTypeId = 110780, // Obsolete - available for reuse
	SincFilterTypeId = 110781, // Obsolete - available for reuse
	LanczosFilterTypeId = 110782, // Obsolete - available for reuse
	ImageStatsTypeId = 110783,
	ImageTransformImplementationTypeId = 110784, // Obsolete - available for reuse
	DeleteChannelsTypeId = 110785,
	ColorProcessorTypeId = 110786,
	ClampTypeId = 110787,
	UnpremultiplyTypeId = 110788,
	ImageContextProcessorTypeId = 110789,
	ImageTimeWarpTypeId = 110790,
	ImageContextVariablesTypeId = 110791,
	ImageSwitchTypeId = 110792, // Obsolete - available for reuse
	ImageSamplerTypeId = 110793,
	MetadataProcessorTypeId = 110794,
	ImageMetadataTypeId = 110795,
	DeleteImageMetadataTypeId = 110796,
	CopyImageMetadataTypeId = 110797,
	ImageLoopTypeId = 110798, // Obsolete - available for reuse
	PremultiplyTypeId = 110799,
	CropTypeId = 110800,
	ResampleTypeId = 110801,
	ResizeTypeId = 110802,
	OpenColorIOTransformTypeId = 110803,
	LUTTypeId = 110804,
	CDLTypeId = 110805,
	DisplayTransformTypeId = 110806,
	FormatPlugTypeId = 110807,
	OffsetTypeId = 110808,
	FormatQueryTypeId = 110809,
	BlurTypeId = 110810,
	ShapeTypeId = 110811,
	TextTypeId = 110812,
	OpenImageIOReaderTypeId = 110813,
	MirrorTypeId = 110814,
	CopyChannelsTypeId = 110815,
	MedianTypeId = 110816,
	MixTypeId = 110817,
	CollectImagesTypeId = 110818,
	DeleteImageContextVariablesTypeId = 110819,
	RankFilterTypeId = 110820,
	ErodeTypeId = 110821,
	DilateTypeId = 110822,
	RampTypeId = 110823,
	RectangleTypeId = 110824,
	FlatToDeepTypeId = 110825,
	DeepMergeTypeId = 110826,
	DeepStateTypeId = 110827,
	EmptyTypeId = 110828,
	FlatImageProcessorTypeId = 110829,
	DeepSampleCountsTypeId = 110830,
	DeepSamplerTypeId = 110831,
	DeepToFlatTypeId = 110832,
	DeepHoldoutTypeId = 110833,
	DeepRecolorTypeId = 110834,
	SaturationTypeId = 110835,

	LastTypeId = 110849
};

} // namespace GafferImage

#endif // GAFFERIMAGE_TYPEIDS_H

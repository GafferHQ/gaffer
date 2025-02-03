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

#pragma once

namespace GafferImage
{

enum TypeId
{
	ImagePlugTypeId = 121400,
	ImageNodeTypeId = 121401,
	ImageReaderTypeId = 121402,
	OpenColorIOContextTypeId = 121403,
	ImageProcessorTypeId = 121404,
	ChannelDataProcessorTypeId = 121405,
	ColorSpaceTypeId = 121406,
	LookTransformTypeId = 121407,
	FormatDataTypeId = 121408,
	AtomicFormatPlugTypeId = 121409,
	MergeTypeId = 121410,
	GradeTypeId = 121411,
	ShuffleTypeId = 121412,
	ConstantTypeId = 121413,
	ShuffleImageMetadataTypeId = 121414,
	ChannelMaskPlugTypeId = 121415,
	WarpTypeId = 121416,
	VectorWarpTypeId = 121417,
	ImageWriterTypeId = 121418,
	ImageTransformTypeId = 121419,
	CheckerboardTypeId = 121420,
	FlatImageSourceTypeId = 121421,
	CreateViewsTypeId = 121422,
	SelectViewTypeId = 121423,
	DeleteViewsTypeId = 121424,
	CopyViewsTypeId = 121425,
	OpenColorIOConfigPlugTypeId = 121426,
	ContactSheetCoreTypeId = 121427,
	ImageStatsTypeId = 121428,
	DeleteChannelsTypeId = 121429,
	ColorProcessorTypeId = 121430,
	ClampTypeId = 121431,
	UnpremultiplyTypeId = 121432,
	ImageContextProcessorTypeId = 121433,
	ImageTimeWarpTypeId = 121434,
	ImageContextVariablesTypeId = 121435,
	ImageSamplerTypeId = 121436,
	MetadataProcessorTypeId = 121437,
	ImageMetadataTypeId = 121438,
	DeleteImageMetadataTypeId = 121439,
	CopyImageMetadataTypeId = 121440,
	PremultiplyTypeId = 121441,
	CropTypeId = 121442,
	ResampleTypeId = 121443,
	ResizeTypeId = 121444,
	OpenColorIOTransformTypeId = 121445,
	LUTTypeId = 121446,
	CDLTypeId = 121447,
	DisplayTransformTypeId = 121448,
	FormatPlugTypeId = 121449,
	OffsetTypeId = 121450,
	FormatQueryTypeId = 121451,
	BlurTypeId = 121452,
	ShapeTypeId = 121453,
	TextTypeId = 121454,
	OpenImageIOReaderTypeId = 121455,
	MirrorTypeId = 121456,
	CopyChannelsTypeId = 121457,
	MedianTypeId = 121458,
	MixTypeId = 121459,
	CollectImagesTypeId = 121460,
	DeleteImageContextVariablesTypeId = 121461,
	RankFilterTypeId = 121462,
	ErodeTypeId = 121463,
	DilateTypeId = 121464,
	RampTypeId = 121465,
	RectangleTypeId = 121466,
	FlatToDeepTypeId = 121467,
	DeepMergeTypeId = 121468,
	DeepStateTypeId = 121469,
	EmptyTypeId = 121470,
	FlatImageProcessorTypeId = 121471,
	DeepSampleCountsTypeId = 121472,
	DeepSamplerTypeId = 121473,
	DeepToFlatTypeId = 121474,
	DeepHoldoutTypeId = 121475,
	DeepRecolorTypeId = 121476,
	SaturationTypeId = 121477,
	DeepSliceTypeId = 121478,
	DiskBlurTypeId = 121479,

	LastTypeId = 121999
};

} // namespace GafferImage

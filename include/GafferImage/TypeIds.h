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
	DisplayTypeId = 121404,
	GafferDisplayDriverTypeId = 121405,
	ImageProcessorTypeId = 121406,
	ChannelDataProcessorTypeId = 121407,
	ColorSpaceTypeId = 121408,
	LookTransformTypeId = 121409,
	FormatDataTypeId = 121410,
	AtomicFormatPlugTypeId = 121411,
	MergeTypeId = 121412,
	GradeTypeId = 121413,
	ShuffleTypeId = 121414,
	ConstantTypeId = 121415,
	ShuffleImageMetadataTypeId = 121416,
	ChannelMaskPlugTypeId = 121417,
	WarpTypeId = 121418,
	VectorWarpTypeId = 121419,
	ImageWriterTypeId = 121420,
	ImageTransformTypeId = 121421,
	CatalogueTypeId = 121422,
	CatalogueImageTypeId = 121423,
	CheckerboardTypeId = 121424,
	FlatImageSourceTypeId = 121425,
	CreateViewsTypeId = 121426,
	SelectViewTypeId = 121427,
	DeleteViewsTypeId = 121428,
	CopyViewsTypeId = 121429,
	OpenColorIOConfigPlugTypeId = 121430,
	ContactSheetCoreTypeId = 121431,
	ImageStatsTypeId = 121432,
	DeleteChannelsTypeId = 121433,
	ColorProcessorTypeId = 121434,
	ClampTypeId = 121435,
	UnpremultiplyTypeId = 121436,
	ImageContextProcessorTypeId = 121437,
	ImageTimeWarpTypeId = 121438,
	ImageContextVariablesTypeId = 121439,
	ImageSamplerTypeId = 121440,
	MetadataProcessorTypeId = 121441,
	ImageMetadataTypeId = 121442,
	DeleteImageMetadataTypeId = 121443,
	CopyImageMetadataTypeId = 121444,
	PremultiplyTypeId = 121445,
	CropTypeId = 121446,
	ResampleTypeId = 121447,
	ResizeTypeId = 121448,
	OpenColorIOTransformTypeId = 121449,
	LUTTypeId = 121450,
	CDLTypeId = 121451,
	DisplayTransformTypeId = 121452,
	FormatPlugTypeId = 121453,
	OffsetTypeId = 121454,
	FormatQueryTypeId = 121455,
	BlurTypeId = 121456,
	ShapeTypeId = 121457,
	TextTypeId = 121458,
	OpenImageIOReaderTypeId = 121459,
	MirrorTypeId = 121460,
	CopyChannelsTypeId = 121461,
	MedianTypeId = 121462,
	MixTypeId = 121463,
	CollectImagesTypeId = 121464,
	DeleteImageContextVariablesTypeId = 121465,
	RankFilterTypeId = 121466,
	ErodeTypeId = 121467,
	DilateTypeId = 121468,
	RampTypeId = 121469,
	RectangleTypeId = 121470,
	FlatToDeepTypeId = 121471,
	DeepMergeTypeId = 121472,
	DeepStateTypeId = 121473,
	EmptyTypeId = 121474,
	FlatImageProcessorTypeId = 121475,
	DeepSampleCountsTypeId = 121476,
	DeepSamplerTypeId = 121477,
	DeepToFlatTypeId = 121478,
	DeepHoldoutTypeId = 121479,
	DeepRecolorTypeId = 121480,
	SaturationTypeId = 121481,
	DeepSliceTypeId = 121482,

	LastTypeId = 121999
};

} // namespace GafferImage

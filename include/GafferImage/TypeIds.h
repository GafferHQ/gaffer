//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
	ImagePrimitiveNodeTypeId = 110753,
	DisplayTypeId = 110754,
	GafferDisplayDriverTypeId = 110755,
	ImageProcessorTypeId = 110756,
	ChannelDataProcessorTypeId = 110757,
	OpenColorIOTypeId = 110758,
	ObjectToImageTypeId = 110759,
	FormatTypeId = 110760,
	FormatPlugTypeId = 110761,
	MergeTypeId = 110762,
	GradeTypeId = 110763,
	FilterProcessorTypeId = 110764,
	ConstantTypeId = 110765,
	SelectTypeId = 110766,
	ChannelMaskPlugTypeId = 110767,
	ReformatTypeId = 110768,
	FilterPlugTypeId = 110769,
	ImageWriterTypeId = 110770,
	ImageTransformTypeId = 110771,
	FilterTypeId = 110772,
	BoxFilterTypeId = 110773,
	BilinearFilterTypeId = 110774,
	SplineFilterTypeId = 110775,
	BSplineFilterTypeId = 110776,
	HermiteFilterTypeId = 110777,
	CubicFilterTypeId = 110778,
	MitchellFilterTypeId = 110779,
	CatmullRomFilterTypeId = 110780,
	SincFilterTypeId = 110781,
	LanczosFilterTypeId = 110782,
	ImageStatsTypeId = 110783,
	ImageTransformImplementationTypeId = 110784,
	
	LastTypeId = 110849
};

} // namespace GafferImage

#endif // GAFFERIMAGE_TYPEIDS_H

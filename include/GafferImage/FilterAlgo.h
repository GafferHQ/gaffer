//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design. All rights reserved.
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

#ifndef GAFFERIMAGE_FILTERALGO_H
#define GAFFERIMAGE_FILTERALGO_H

#include "GafferImage/Sampler.h"
#include "OpenEXR/ImathVec.h"
#include "OpenImageIO/filter.h"

namespace GafferImage
{

namespace FilterAlgo
{

GAFFERIMAGE_API const std::vector<std::string> &filterNames();

GAFFERIMAGE_API const OIIO::Filter2D* acquireFilter( const std::string &name );


// Find the region covered by a filter with a given width, given a position and axis-aligned derivatives
// to compute the bounding rectangle
GAFFERIMAGE_API inline Imath::Box2f filterSupport( const Imath::V2f &p, float dx, float dy, float filterWidth );

// Filter over a rectangle shaped region of the image defined by a center point and two axis-aligned derivatives.
// The sampler must have been initialized to cover all pixels with centers lying with the support of the filter,
// filterSupport above may be used to compute an appropriate bound.
GAFFERIMAGE_API float sampleBox( Sampler &sampler, const Imath::V2f &p, float dx, float dy, const OIIO::Filter2D *filter, std::vector<float> &scratchMemory );

// Sample over a parallelogram shaped region defined by a center point and two derivative directions.
// The sampler must have been initialized to cover all pixels with centers lying with the support of the filter
// I haven't actually exposed anything that would make this easy to compute at the moment, because it doesn't
// seem like the cost of this method is worth ever using it.  Currently it is only used in FilterAlgoTest,
// where it provides a nice visual comparison to the filter shapes you get from sampleBox
GAFFERIMAGE_API float sampleParallelogram( Sampler &sampler, const Imath::V2f &p, const Imath::V2f &dpdx, const Imath::V2f &dpdy, const OIIO::Filter2D *filter );

// If you have a point and derivatives defining a region to filter over, but you want to use sampleBox
// instead of sampleParallelogram for performance reasons, you can use this function to get axis-aligned
// derivatives which will approximate the result of sampleParallelogram
GAFFERIMAGE_API inline Imath::V2f derivativesToAxisAligned( const Imath::V2f &p, const Imath::V2f &dpdx, const Imath::V2f &dpdy );

} // namespace FilterAlgo

} // namespace GafferImage

#include "GafferImage/FilterAlgo.inl"

#endif // GAFFERIMAGE_FILTERALGO_H

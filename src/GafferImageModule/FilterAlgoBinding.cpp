//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#include "boost/python.hpp"

#include "FilterAlgoBinding.h"

#include "GafferImage/FilterAlgo.h"

using namespace boost::python;

namespace
{
	float sampleBoxWrapper( GafferImage::Sampler &sampler, const Imath::V2f &p, float dx, float dy, const std::string &filter )
	{
		const OIIO::Filter2D *f = GafferImage::FilterAlgo::acquireFilter( filter );
		std::vector<float> scratchMemory;
		return GafferImage::FilterAlgo::sampleBox( sampler, p, dx, dy, f, scratchMemory );
	}

	float sampleParallelogramWrapper( GafferImage::Sampler &sampler, const Imath::V2f &p, const Imath::V2f &dpdx, const Imath::V2f &dpdy, const std::string &filter )
	{
		const OIIO::Filter2D *f = GafferImage::FilterAlgo::acquireFilter( filter );
		return GafferImage::FilterAlgo::sampleParallelogram( sampler, p, dpdx, dpdy, f );
	}

	list filterNamesWrapper()
	{
		list result;
		const std::vector<std::string> &filters = GafferImage::FilterAlgo::filterNames();
		for ( unsigned i=0; i < filters.size(); i++ )
		{
			result.append( filters[i] );
		}
		return result;
	}
}

void GafferImageModule::bindFilterAlgo()
{
	object module( borrowed( PyImport_AddModule( "GafferImage.FilterAlgo" ) ) );
	scope().attr( "FilterAlgo" ) = module;
	scope moduleScope( module );

	def( "filterNames", &filterNamesWrapper );
	def( "derivativesToAxisAligned", &GafferImage::FilterAlgo::derivativesToAxisAligned );
	def( "sampleBox", &sampleBoxWrapper );
	def( "sampleParallelogram", &sampleParallelogramWrapper );

}

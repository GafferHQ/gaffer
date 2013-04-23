//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2013, Luke Goddard. All rights reserved.
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

#ifndef GAFFERIMAGE_SAMPLER_H
#define GAFFERIMAGE_SAMPLER_H

#include <vector>
#include "GafferImage/ImagePlug.h"

namespace GafferImage
{

class Sampler
{

public : 

	Sampler( const GafferImage::ImagePlug *plug, const std::string &channelName );

	float sample( int x, int y );
		
	template< typename F >
	float sample( F filter, float x, float y )
	{
		const int width( filter.width() );
		
		int ySample = filter.construct( y );
		float weights[width];
		memcpy( weights, filter.weights(), width*sizeof(float) );	
		
		float result = 0.;
		for ( int j = 0; j < width; ++j )
		{
			int xSample = filter.construct( x );
			float v = 0.;
			for ( int i = 0; i < width; ++i )
			{
				v += sample( xSample+i, ySample+j ) * filter[i];
			}
			result += v * weights[j];
		}
			
		return result;
	}

private:

	const ImagePlug *m_plug;
	const Imath::Box2i m_dataWindow;
	const std::string &m_channelName;
	Imath::V2i m_cacheSize;
	std::vector< IECore::ConstFloatVectorDataPtr > m_dataCache;
	bool m_valid;

};

}; // namespace GafferImage

#endif


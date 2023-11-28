//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, Image Engine Design Inc. All rights reserved.
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
//      * Neither the name of Image Engine Design nor the names of
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

#include "GafferImage/ImagePlug.h"
#include "GafferImage/Sampler.h"

#include <boost/core/span.hpp>
#include <vector>

namespace GafferImage
{

/// Utility class for sampling pixel values from a deep image.
/// The interface mostly matches Sampler for flat images.
class GAFFERIMAGE_API DeepPixelAccessor
{

	public :

		/// Sampler Constructor
		/// @param plug The image plug to sample from.
		/// @param channelName The channel to sample ( or empty string, if you only need sample counts )
		/// @param sampleWindow The area from which samples may be requested. It is an error to request samples outside this area.
		/// @param boundingMode The method of handling samples that fall outside the data window.
		DeepPixelAccessor( const GafferImage::ImagePlug *plug, const std::string &channelName, const Imath::Box2i &sampleWindow, Sampler::BoundingMode boundingMode = Sampler::Black );

		/// Construct from another DeepPixelAccessor with a different channelName, in order to reuse the
		/// sample offsets data.
		DeepPixelAccessor( const DeepPixelAccessor &source, const std::string &channelName );

		/// Uses `parallelProcessTiles()` to fill the internal tile cache
		/// with all tiles in the sample window. Allows `sample()` and
		/// `visitPixels()` to subsequently be called concurrently.
		void populate();

		/// Gets the list of channel values at the specified integer pixel coordinate.
		/// It is the caller's responsibility to ensure that this point is contained
		/// within the sample window passed to the constructor, and that the channel name is set.
		boost::span<const float> sample( int x, int y );

		/// Like above, but only returns the count, and may be called with an empty channel name.
		unsigned int sampleCount( int x, int y );

		/// Appends a hash that represent all the pixel
		/// values within the requested sample area.
		void hash( IECore::MurmurHash &h ) const;
		/// Convenience function to append into an
		/// empty hash object and return it.
		IECore::MurmurHash hash() const;

	private :

		/// Cached data access
		/// @param p Any point within the cache that we wish to retrieve the data for.
		/// @param tileData Is set to the tile's channel data.
		/// @param tilePixelIndex Is set to the index used to access the colour value of point 'p' from tileData.
		void cachedData( Imath::V2i p, const float *& tileData, const int *& tileOffsets, int &tilePixelIndex );

		const ImagePlug *m_plug;
		const std::string m_channelName;
		Imath::Box2i m_sampleWindow;
		Imath::Box2i m_dataWindow;

		std::vector< IECore::ConstFloatVectorDataPtr > m_dataCache;
		std::vector< IECore::ConstIntVectorDataPtr > m_offsetsCache;
		Imath::Box2i m_cacheWindow;
		int m_cacheOriginIndex;
		int m_cacheWidth;

		int m_boundingMode;

};

}; // namespace GafferImage

#include "GafferImage/DeepPixelAccessor.inl"

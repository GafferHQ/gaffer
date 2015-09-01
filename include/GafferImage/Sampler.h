//////////////////////////////////////////////////////////////////////////
//
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

#ifndef GAFFERIMAGE_SAMPLER_H
#define GAFFERIMAGE_SAMPLER_H

#include <vector>

#include "GafferImage/ImagePlug.h"
#include "GafferImage/Filter.h"

namespace GafferImage
{

/// A utility class for pixel access of an image plug.
class Sampler
{

	public :

		enum BoundingMode
		{
			Black = 0,
			Clamp = 1
		};

		/// Sampler Constructor
		/// @param plug The image plug to sample from.
		/// @param channelName The channel to sample.
		/// @param boundingMode The method of handling samples that fall out of the sample window.
		Sampler( const GafferImage::ImagePlug *plug, const std::string &channelName, const Imath::Box2i &sampleWindow, BoundingMode boundingMode = Black );

		/// \deprecated We are phasing out use of GafferImage::Filter.
		Sampler( const GafferImage::ImagePlug *plug, const std::string &channelName, const Imath::Box2i &sampleWindow, GafferImage::ConstFilterPtr filter, BoundingMode boundingMode = Black );

		/// Samples a colour value from the channel at x, y.
		inline float sample( int x, int y );

		/// Sub-samples the image using a filter.
		inline float sample( float x, float y );

		/// Computes the hash of the sample area, including the effects
		/// of the bounding mode.
		void hash( IECore::MurmurHash &h ) const;

	private:

		// Initialisation required by both constructors.
		void init( const Imath::Box2i &sampleWindow );

		/// Cached data access
		/// @param p Any point within the cache that we wish to retrieve the data for.
		/// @param tileData Is set to the tile's channel data.
		/// @param tileOrigin The coordinate of the tile's  minimum corner.
		/// @param tileIndex XY indices that can be used to access the colour value of point 'p' from tileData.
		inline void cachedData( Imath::V2i p, const float *& tileData, Imath::V2i &tileOrigin, Imath::V2i &tileIndex );

		const ImagePlug *m_plug;
		const std::string m_channelName;
		Imath::Box2i m_sampleWindow;
		Imath::Box2i m_userSampleWindow;

		std::vector< IECore::ConstFloatVectorDataPtr > m_dataCache;
		Imath::Box2i m_cacheWindow;
		int m_cacheWidth;

		BoundingMode m_boundingMode;
		ConstFilterPtr m_filter;

};

}; // namespace GafferImage

#include "GafferImage/Sampler.inl"

#endif


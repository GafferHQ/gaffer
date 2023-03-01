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

#include "GafferImage/ImagePlug.h"

#include <vector>

namespace GafferImage
{

/// Utility class for sampling pixel values from an image. It
/// abstracts away the underlying tiles and instead provides
/// access via pixel coordinates, dealing with pixels outside
/// the data window by either clamping or returning black.
///
/// The Sampler is sensitive to the Context which is current
/// during its operation, so a sampler should only be used in
/// the context in which it is constructed.
class GAFFERIMAGE_API Sampler
{

	public :

		/// Defines how values are sampled for pixels
		/// outside the data window.
		enum BoundingMode
		{
			/// Returns 0
			Black = 0,
			/// Returns the value of the closest pixel
			/// inside the data window.
			Clamp = 1
		};

		/// Sampler Constructor
		/// @param plug The image plug to sample from.
		/// @param channelName The channel to sample.
		/// @param sampleWindow The area from which samples may be requested. It is an error to request samples outside this area.
		/// @param boundingMode The method of handling samples that fall outside the data window.
		Sampler( const GafferImage::ImagePlug *plug, const std::string &channelName, const Imath::Box2i &sampleWindow, BoundingMode boundingMode = Black );

		/// Samples the channel value at the specified
		/// integer pixel coordinate. It is the caller's
		/// responsibility to ensure that this point is
		/// contained within the sample window passed
		/// to the constructor.
		float sample( int x, int y );

		/// Samples the channel value at the specified
		/// subpixel location using bilinear interpolation.
		/// It is the caller's responsibility to ensure that
		/// this point is contained within the sample window
		/// passed to the constructor.
		///
		/// \note The centres of pixels (where no interpolation
		/// is needed) are located at N + 0.5 where N is the integer
		/// pixel location. For instance, the centre of the
		/// pixel at the bottom left of the image has coordinate
		/// 0.5, 0.5.
		float sample( float x, float y );

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
		/// @param tilePixelIndex XY indices that can be used to access the colour value of point 'p' from tileData.
		void cachedData( Imath::V2i p, const float *& tileData, Imath::V2i &tilePixelIndex );

		const ImagePlug *m_plug;
		const std::string m_channelName;
		Imath::Box2i m_sampleWindow;
		Imath::Box2i m_dataWindow;

		std::vector< IECore::ConstFloatVectorDataPtr > m_dataCache;
		std::vector< const float * > m_dataCacheRaw;
		Imath::Box2i m_cacheWindow;
		int m_cacheWidth;

		int m_boundingMode;

};

}; // namespace GafferImage

#include "GafferImage/Sampler.inl"

#endif // GAFFERIMAGE_SAMPLER_H

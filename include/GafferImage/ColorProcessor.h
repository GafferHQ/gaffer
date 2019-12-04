//////////////////////////////////////////////////////////////////////////
//
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

#ifndef GAFFERIMAGE_COLORPROCESSOR_H
#define GAFFERIMAGE_COLORPROCESSOR_H

#include "GafferImage/ImageProcessor.h"

#include "Gaffer/StringPlug.h"

namespace GafferImage
{

/// Forms a useful base class for nodes which must process R,G and B channels at the same time
/// to perform some sort of channel mixing.
class GAFFERIMAGE_API ColorProcessor : public ImageProcessor
{

	public :

		ColorProcessor( const std::string &name=defaultName<ColorProcessor>() );
		~ColorProcessor() override;

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferImage::ColorProcessor, ColorProcessorTypeId, ImageProcessor );

		Gaffer::BoolPlug *processUnpremultipliedPlug();
		const Gaffer::BoolPlug *processUnpremultipliedPlug() const;

		Gaffer::StringPlug *channelsPlug();
		const Gaffer::StringPlug *channelsPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;

		/// Implemented to process the color data and stash the results on colorDataPlug()
		/// format, dataWindow, metadata, and channelNames are passed through via direct connection to the input values.
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;
		Gaffer::ValuePlug::CachePolicy computeCachePolicy( const Gaffer::ValuePlug *output ) const override;
		/// Implemented to use the results of colorDataPlug() via processColorData()
		IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const override;

		/// May be implemented by derived classes to return true if the specified input is used in processColorData().
		/// Must first call the base class implementation and return true if it does.
		virtual bool affectsColorData( const Gaffer::Plug *input ) const;
		/// May be implemented by derived classes to compute the hash for the color processing - all implementations
		/// must call their base class implementation first.
		virtual void hashColorData( const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		/// Must be implemented by derived classes to modify R, G and B in place.
		virtual void processColorData( const Gaffer::Context *context, IECore::FloatVectorData *r, IECore::FloatVectorData *g, IECore::FloatVectorData *b ) const = 0;

	private :

		// Used to store the result of processColorData(), so that it can be reused in computeChannelData().
		// Evaluated in a context with an "image:colorProcessor:__layerName" variable, so we can cache
		// different results per layer.
		Gaffer::ObjectPlug *colorDataPlug();
		const Gaffer::ObjectPlug *colorDataPlug() const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( ColorProcessor )

} // namespace GafferImage

#endif // GAFFERIMAGE_CHANNELDATAPROCESSOR_H

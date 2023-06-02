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

#pragma once

#include "GafferImage/ImageProcessor.h"

#include "Gaffer/StringPlug.h"

namespace GafferImage
{

/// Forms a useful base class for nodes which must process R,G and B channels at the same time
/// to perform some sort of channel mixing.
class GAFFERIMAGE_API ColorProcessor : public ImageProcessor
{

	public :

		explicit ColorProcessor( const std::string &name=defaultName<ColorProcessor>() );
		~ColorProcessor() override;

		GAFFER_NODE_DECLARE_TYPE( GafferImage::ColorProcessor, ColorProcessorTypeId, ImageProcessor );

		Gaffer::BoolPlug *processUnpremultipliedPlug();
		const Gaffer::BoolPlug *processUnpremultipliedPlug() const;

		Gaffer::StringPlug *channelsPlug();
		const Gaffer::StringPlug *channelsPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;
		Gaffer::ValuePlug::CachePolicy computeCachePolicy( const Gaffer::ValuePlug *output ) const override;

		/// Function object used to implement the processing of color values.
		using ColorProcessorFunction = std::function<void ( IECore::FloatVectorData *r, IECore::FloatVectorData *g, IECore::FloatVectorData *b )>;

		/// Must be implemented by derived classes to return true if the specified input is used in `colorProcessor()`.
		virtual bool affectsColorProcessor( const Gaffer::Plug *input ) const = 0;
		/// Must be implemented by derived classes to compute the hash for the color processor.
		virtual void hashColorProcessor( const Gaffer::Context *context, IECore::MurmurHash &h ) const = 0;
		/// Must be implemented by derived classes to return a ColorProcessorFunction. An empty function
		/// may be returned, in which case the node will pass through the input image data unchanged.
		virtual ColorProcessorFunction colorProcessor( const Gaffer::Context *context ) const = 0;

	private :

		void hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const final;
		IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const final;

		Gaffer::ObjectPlug *colorProcessorPlug();
		const Gaffer::ObjectPlug *colorProcessorPlug() const;

		// Used to store the result of processColorData(), so that it can be reused in computeChannelData().
		// Evaluated in a context with an "image:colorProcessor:__layerName" variable, so we can cache
		// different results per layer.
		Gaffer::ObjectPlug *colorDataPlug();
		const Gaffer::ObjectPlug *colorDataPlug() const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( ColorProcessor )

} // namespace GafferImage

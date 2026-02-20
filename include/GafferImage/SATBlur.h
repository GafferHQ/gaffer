//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Image Engine Design Inc. All rights reserved.
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
#include "GafferImage/Sampler.h"

#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/TypedObjectPlug.h"

#include "IECore/Object.h"

namespace GafferImage
{

class GAFFERIMAGE_API SATBlur : public ImageProcessor
{
	public :

		// This is similar to Sampler::BoundingMode, but Normalize isn't supported by the
		// sampler interface, and we haven't figured out yet how to unify these.
		enum class BoundingMode
		{
			/// Returns 0 outside the data window
			Black = Sampler::BoundingMode::Black,
			/// Evenly increase all valid contributions to edge pixels that are missing contributions
			/// from outside the data window.
			Normalize = 10
		};

		explicit SATBlur( const std::string &name=defaultName<SATBlur>() );
		~SATBlur() override;

		GAFFER_NODE_DECLARE_TYPE( GafferImage::SATBlur, SATBlurTypeId, ImageProcessor );

		Gaffer::V2fPlug *radiusPlug();
		const Gaffer::V2fPlug *radiusPlug() const;

		Gaffer::StringPlug *radiusChannelPlug();
		const Gaffer::StringPlug *radiusChannelPlug() const;

		Gaffer::FloatPlug *maxRadiusPlug();
		const Gaffer::FloatPlug *maxRadiusPlug() const;

		Gaffer::IntPlug *boundingModePlug();
		const Gaffer::IntPlug *boundingModePlug() const;

		Gaffer::StringPlug *filterPlug();
		const Gaffer::StringPlug *filterPlug() const;

		Gaffer::IntPlug *diskRectanglesPlug();
		const Gaffer::IntPlug *diskRectanglesPlug() const;


		Gaffer::FloatVectorDataPlug *layerBoundariesPlug();
		const Gaffer::FloatVectorDataPlug *layerBoundariesPlug() const;

		Gaffer::StringPlug *depthChannelPlug();
		const Gaffer::StringPlug *depthChannelPlug() const;

		Gaffer::StringPlug *depthLookupChannelPlug();
		const Gaffer::StringPlug *depthLookupChannelPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

		Gaffer::ValuePlug::CachePolicy computeCachePolicy( const Gaffer::ValuePlug *output ) const override;

		void hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const override;

	private :

		Gaffer::FloatVectorDataPlug *satPlug();
		const Gaffer::FloatVectorDataPlug *satPlug() const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( SATBlur )

} // namespace GafferImage

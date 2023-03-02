//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/FlatImageProcessor.h"

#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/NumericPlug.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( StringPlug )

} // namespace Gaffer

namespace GafferImage
{

/// Utility node designed for internal use in other node implementations.
/// It resamples all the data from the input data window into a new
/// data window in the output image, using a chosen filter. Uses OIIO::Filter2D
/// to provide the filter implementation, and is based heavily on OIIO's
/// ImageBufAlgo resize() function.
class GAFFERIMAGE_API Resample : public FlatImageProcessor
{
	public :

		Resample( const std::string &name=defaultName<Resample>() );
		~Resample() override;

		GAFFER_NODE_DECLARE_TYPE( GafferImage::Resample, ResampleTypeId, FlatImageProcessor );

		enum Debug
		{
			Off,
			HorizontalPass,
			SinglePass
		};

		/// Atomic plug, since values for this will most
		/// commonly be computed by a wrapping class, rather
		/// than set directly by a user. Input matrices must
		/// not contain rotation.
		Gaffer::M33fPlug *matrixPlug();
		const Gaffer::M33fPlug *matrixPlug() const;

		Gaffer::StringPlug *filterPlug();
		const Gaffer::StringPlug *filterPlug() const;

		Gaffer::V2fPlug *filterScalePlug();
		const Gaffer::V2fPlug *filterScalePlug() const;

		Gaffer::IntPlug *boundingModePlug();
		const Gaffer::IntPlug *boundingModePlug() const;

		Gaffer::BoolPlug *expandDataWindowPlug();
		const Gaffer::BoolPlug *expandDataWindowPlug() const;

		Gaffer::IntPlug *debugPlug();
		const Gaffer::IntPlug *debugPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hashDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;

		Imath::Box2i computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const override;
		IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const override;

	private :

		ImagePlug *horizontalPassPlug();
		const ImagePlug *horizontalPassPlug() const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Resample )

} // namespace GafferImage

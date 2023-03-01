//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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
#include "Gaffer/StringPlug.h"
#include "Gaffer/TypedObjectPlug.h"

namespace GafferImage
{

class GAFFERIMAGE_API RankFilter : public FlatImageProcessor
{

	public :

		~RankFilter() override;

		GAFFER_NODE_DECLARE_TYPE( GafferImage::RankFilter, RankFilterTypeId, FlatImageProcessor );

		Gaffer::V2iPlug *radiusPlug();
		const Gaffer::V2iPlug *radiusPlug() const;

		Gaffer::IntPlug *boundingModePlug();
		const Gaffer::IntPlug *boundingModePlug() const;

		Gaffer::BoolPlug *expandDataWindowPlug();
		const Gaffer::BoolPlug *expandDataWindowPlug() const;

		Gaffer::StringPlug *masterChannelPlug();
		const Gaffer::StringPlug *masterChannelPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		enum Mode
		{
			MedianRank,
			ErodeRank,
			DilateRank
		};

		RankFilter( const std::string &name=defaultName<RankFilter>(), Mode mode=MedianRank );

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

		void hashDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		Imath::Box2i computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const override;

		void hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const override;

	private:

		// This private plug stores an offset for each pixel to where the rank is located
		// It should only be evaluated if masterChannelPlug is set, and it should only be evaluated
		// with the correct driver channel set in the context
		Gaffer::V2iVectorDataPlug *pixelOffsetsPlug();
		const Gaffer::V2iVectorDataPlug *pixelOffsetsPlug() const;

		static size_t g_firstPlugIndex;
		int m_mode;
};

IE_CORE_DECLAREPTR( RankFilter );

} // namespace GafferImage

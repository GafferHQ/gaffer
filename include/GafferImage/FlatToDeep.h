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

#ifndef GAFFERIMAGE_ADDDEPTH_H
#define GAFFERIMAGE_ADDDEPTH_H

#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/StringPlug.h"

#include "GafferImage/ImageProcessor.h"
#include "GafferImage/FormatPlug.h"

namespace GafferImage
{

class GAFFERIMAGE_API FlatToDeep : public ImageProcessor
{

	public :
		enum class ZMode
		{
			Constant,
			Channel,
		};

		enum class ZBackMode
		{
			None,
			Thickness,
			Channel,
		};

		FlatToDeep( const std::string &name=defaultName<FlatToDeep>() );
		~FlatToDeep() override;

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferImage::FlatToDeep, FlatToDeepTypeId, ImageProcessor );

		Gaffer::IntPlug *zModePlug();
		const Gaffer::IntPlug *zModePlug() const;
		Gaffer::FloatPlug *depthPlug();
		const Gaffer::FloatPlug *depthPlug() const;
		Gaffer::StringPlug *zChannelPlug();
		const Gaffer::StringPlug *zChannelPlug() const;

		Gaffer::IntPlug *zBackModePlug();
		const Gaffer::IntPlug *zBackModePlug() const;
		Gaffer::FloatPlug *thicknessPlug();
		const Gaffer::FloatPlug *thicknessPlug() const;
		Gaffer::StringPlug *zBackChannelPlug();
		const Gaffer::StringPlug *zBackChannelPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hashChannelNames( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;

		IECore::ConstStringVectorDataPtr computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const override;
		IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const override;

		void hashDeep( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		bool computeDeep( const Gaffer::Context *context, const ImagePlug *parent ) const override;

		void hashSampleOffsets( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstIntVectorDataPtr computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const override;

	private :

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( FlatToDeep )

} // namespace GafferImage

#endif // GAFFERIMAGE_ADDDEPTH_H

//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, John Haddon. All rights reserved.
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

#ifndef GAFFEROSL_OSLIMAGE_H
#define GAFFEROSL_OSLIMAGE_H

#include "GafferOSL/Export.h"
#include "GafferOSL/OSLCode.h"
#include "GafferOSL/TypeIds.h"

#include "GafferScene/ShaderPlug.h"

#include "GafferImage/ImageProcessor.h"
#include "GafferImage/Constant.h"

namespace GafferOSL
{

class GAFFEROSL_API OSLImage : public GafferImage::ImageProcessor
{

	public :

		OSLImage( const std::string &name=defaultName<OSLImage>() );
		~OSLImage() override;

		GAFFER_NODE_DECLARE_TYPE( GafferOSL::OSLImage, OSLImageTypeId, GafferImage::ImageProcessor );

		GafferImage::FormatPlug *defaultFormatPlug();
		const GafferImage::FormatPlug *defaultFormatPlug() const;

		Gaffer::Plug *channelsPlug();
		const Gaffer::Plug *channelsPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		bool enabled() const override;

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;

		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;
		Gaffer::ValuePlug::CachePolicy computeCachePolicy( const Gaffer::ValuePlug *output ) const override;
		IECore::ConstStringVectorDataPtr computeChannelNames( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const override;
		IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const override;
		GafferImage::Format computeFormat( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const override;
		Imath::Box2i computeDataWindow( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const override;

	private :

		GafferScene::ShaderPlug *shaderPlug();
		const GafferScene::ShaderPlug *shaderPlug() const;

		// computeChannelData() is called for individual channels at a time, but when we run a
		// shader we get all the outputs at once. we therefore use this plug to compute (and
		// automatically cache) the shading and then access it from computeChannelData(), which
		// simply extracts the right part of the data.
		/// \todo Investigate turning off caching for the channelData plug, since we're currently
		/// caching once there and once in the shadingPlug.
		Gaffer::ObjectPlug *shadingPlug();
		const Gaffer::ObjectPlug *shadingPlug() const;

		// Sorted list of affected channels, used to calculate outPlug()->channelNames(), and
		// bypass computeChannelData for channels which we don't affect.  This can usually be
		// evaluated without evaluating the shading, but if closure plugs are present, evaluating
		// this will also evaluate shadingPlug()
		Gaffer::StringVectorDataPlug *affectedChannelsPlug();
		const Gaffer::StringVectorDataPlug *affectedChannelsPlug() const;

		void hashShading( const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		IECore::ConstCompoundDataPtr computeShading( const Gaffer::Context *context ) const;

		GafferOSL::OSLCode *oslCode();
		const GafferOSL::OSLCode *oslCode() const;

		GafferImage::Constant *defaultConstant();
		const GafferImage::Constant *defaultConstant() const;

		GafferImage::ImagePlug *defaultInPlug();
		const GafferImage::ImagePlug *defaultInPlug() const;

		// The in plug, set to the default if left unconnected
		const GafferImage::ImagePlug *defaultedInPlug() const;

		void channelsAdded( const Gaffer::GraphComponent *parent, Gaffer::GraphComponent *child );
		void channelsRemoved( const Gaffer::GraphComponent *parent, Gaffer::GraphComponent *child );

		void updateChannels();

		static size_t g_firstPlugIndex;

};

} // namespace GafferOSL

#endif // GAFFEROSL_OSLIMAGE_H

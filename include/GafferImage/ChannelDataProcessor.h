//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2012-2015, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERIMAGE_CHANNELDATAPROCESSOR_H
#define GAFFERIMAGE_CHANNELDATAPROCESSOR_H

#include "GafferImage/ImageProcessor.h"

#include "Gaffer/StringPlug.h"

namespace GafferImage
{

/// The ChannelDataProcessor provides a useful base class for nodes that manipulate individual channels
/// of an image and leave their image dimensions, channel names, and metadata unchanged.
class GAFFERIMAGE_API ChannelDataProcessor : public ImageProcessor
{

	public :

		ChannelDataProcessor( const std::string &name=defaultName<ChannelDataProcessor>(), bool premultiplyPlug = false );
		~ChannelDataProcessor() override;

		GAFFER_NODE_DECLARE_TYPE( GafferImage::ChannelDataProcessor, ChannelDataProcessorTypeId, ImageProcessor );

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

		Gaffer::StringPlug *channelsPlug();
		const Gaffer::StringPlug *channelsPlug() const;

		Gaffer::BoolPlug *processUnpremultipliedPlug();
		const Gaffer::BoolPlug *processUnpremultipliedPlug() const;

	protected :

		/// This implementation queries whether or not the requested channel is masked by the channelMaskPlug().
		bool channelEnabled( const std::string &channel ) const override;

		/// Implemented to initialize the output tile and then call processChannelData()
		/// All other ImagePlug children are passed through via direct connection to the input values.
		IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const override;

		/// Should be implemented by derived classes to processes each channel's data.
		/// @param context The context that the channel data is being requested for.
		/// @param parent The parent image plug that the output is being processed for.
		/// @param channelIndex An index in the range of 0-3 which indicates whether the channel to be processed is R, G, B or A.
		///                     It is useful for querying Color4f plugs for the value that coresponds to the channel being processed.
		/// @param outData The tile where the result of the operation should be written. It is initialized with the coresponding tile data from inPlug() which should be used as the input data.
		virtual void processChannelData( const Gaffer::Context *context, const ImagePlug *parent, const std::string &channel, IECore::FloatVectorDataPtr outData ) const = 0;

		void hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;

	private :
		bool m_hasUnpremultPlug;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( ChannelDataProcessor )

} // namespace GafferImage

#endif // GAFFERIMAGE_CHANNELDATAPROCESSOR_H

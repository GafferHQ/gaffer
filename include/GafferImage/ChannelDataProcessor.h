//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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
#include "GafferImage/ChannelMaskPlug.h"

namespace GafferImage
{

/// The ChannelDataProcessor provides a useful base class for nodes that manipulate individual channels
/// of an image and leave their image dimensions and channel names unchanged.
class ChannelDataProcessor : public ImageProcessor
{

	public :

		ChannelDataProcessor( const std::string &name=defaultName<ChannelDataProcessor>() );
		virtual ~ChannelDataProcessor();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::ChannelDataProcessor, ChannelDataProcessorTypeId, ImageProcessor );

		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;
		
		//! @name Plug Accessors
		/// Returns a pointer to the node's plugs.
		//////////////////////////////////////////////////////////////
		//@{
			GafferImage::ChannelMaskPlug *channelMaskPlug();
			const GafferImage::ChannelMaskPlug *channelMaskPlug() const;
		//@}
		
	protected :
	
		/// This implementation queries whether or not the requested channel is masked by the channelMaskPlug().
		virtual bool channelEnabled( const std::string &channel ) const;
	
		/// Reimplemented to pass through the hashes from the input plug as they don't change.
		virtual void hashFormatPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashDataWindowPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashChannelNamesPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		
		/// Implemented to pass through the input values. Derived classes need only implement computeChannelData().
		virtual GafferImage::Format computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const;
		virtual Imath::Box2i computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const;
		virtual IECore::ConstStringVectorDataPtr computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const;

		/// Implemented to initialize the output tile and then call processChannelData() 
		virtual IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const;

		/// Should be implemented by derived classes to processes each channel's data.
		/// @param context The context that the channel data is being requested for.
		/// @param parent The parent image plug that the output is being processed for.
		/// @param channelIndex An index in the range of 0-3 which indicates whether the channel to be processed is R, G, B or A. 
		///                     It is useful for querying Color4f plugs for the value that coresponds to the channel being processed. 
		/// @param outData The tile where the result of the operation should be written. It is initialized with the coresponding tile data from inPlug() which should be used as the input data.
		virtual void processChannelData( const Gaffer::Context *context, const ImagePlug *parent, const std::string &channel, IECore::FloatVectorDataPtr outData ) const = 0;

	private :
		
		static size_t g_firstPlugIndex;

};

} // namespace GafferImage

#endif // GAFFERIMAGE_CHANNELDATAPROCESSOR_H

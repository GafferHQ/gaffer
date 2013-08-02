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

#ifndef GAFFERIMAGE_REMOVECHANNELS_H
#define GAFFERIMAGE_REMOVECHANNELS_H

#include "GafferImage/ImageProcessor.h"
#include "GafferImage/ImagePlug.h"
#include "GafferImage/ChannelMaskPlug.h"
#include "Gaffer/PlugType.h"

namespace GafferImage
{

/// The Remove channels node provides a simple mechanism for removing channels from an image by specifying which to keep or remove.
class RemoveChannels : public ImageProcessor
{

	public :

		enum RemoveChannelsMode
		{
			Remove = 0,
			Keep = 1
		};

		RemoveChannels( const std::string &name=defaultName<RemoveChannels>() );
		virtual ~RemoveChannels();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::RemoveChannels, RemoveChannelsTypeId, ImageProcessor );

		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;

		//! @name Plug Accessors
		/// Returns a pointer to the node's plugs.
		//////////////////////////////////////////////////////////////
		//@{
			Gaffer::IntPlug *modePlug();
			const Gaffer::IntPlug *modePlug() const;
			GafferImage::ChannelMaskPlug *channelSelectionPlug();
			const GafferImage::ChannelMaskPlug *channelSelectionPlug() const;
		//@}

	protected :

		/// This implementation disables all channels as we don't need to recompute the data.
		virtual bool channelEnabled( const std::string &channel ) const;

		/// Reimplemented to pass through the hashes from the input plug as they don't change.
		virtual void hashFormatPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashDataWindowPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashChannelNamesPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashChannelDataPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;

		/// Implemented to pass through the input values.
		virtual GafferImage::Format computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const;
		virtual Imath::Box2i computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const;
		virtual IECore::ConstStringVectorDataPtr computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const;
		virtual IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const;

	private :

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( RemoveChannels );

} // namespace GafferImage

#endif // GAFFERIMAGE_REMOVECHANNELS_H

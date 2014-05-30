//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
//  Copyright (c) 2014, Luke Goddard. All rights reserved.
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
#ifndef GAFFERIMAGE_POSITION_H
#define GAFFERIMAGE_POSITION_H

#include "GafferImage/ImageProcessor.h"
#include "GafferImage/FilterPlug.h"
#include "GafferImage/Scale.h"

namespace GafferImage
{

/// Adjusts the position of the data window by an integer offset.
class Position : public ImageProcessor
{

	public :

		Position( const std::string &name=defaultName<Position>() );
		virtual ~Position();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::Position, PositionTypeId, ImageProcessor );
	
		Gaffer::V2iPlug *offsetPlug();
		const Gaffer::V2iPlug *offsetPlug() const;

		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;
		virtual bool enabled() const;

	protected :
		
		virtual void hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;

		virtual GafferImage::Format computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const;
		virtual Imath::Box2i computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const;
		virtual IECore::ConstStringVectorDataPtr computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const;
		virtual IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const;

	private :

		static size_t g_firstPlugIndex;
		
};

IE_CORE_DECLAREPTR( Position )

} // namespace GafferImage

#endif // GAFFERIMAGE_POSITION_H

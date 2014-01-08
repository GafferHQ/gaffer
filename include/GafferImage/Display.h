//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#ifndef GAFFERIMAGE_DISPLAY_H
#define GAFFERIMAGE_DISPLAY_H

#include "IECore/DisplayDriverServer.h"

#include "Gaffer/NumericPlug.h"

#include "GafferImage/ImageNode.h"

namespace GafferImage
{

IE_CORE_FORWARDDECLARE( GafferDisplayDriver )

class Display : public ImageNode
{

	public :

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::Display, DisplayTypeId, ImageNode );

		Display( const std::string &name = defaultName<Display>() );
		virtual ~Display();
		
		Gaffer::IntPlug *portPlug();
		const Gaffer::IntPlug *portPlug() const;
				
		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;
		
		/// Emitted when a new bucket is received.
		static UnaryPlugSignal &dataReceivedSignal();
		/// Emitted when a complete image has been received.
		static UnaryPlugSignal &imageReceivedSignal();
		
	protected :
		
		virtual void hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual GafferImage::Format computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const;

		virtual void hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual IECore::ConstStringVectorDataPtr computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const;

		virtual void hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual Imath::Box2i computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const;

		virtual void hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const;
		
	private :
	
		IECore::DisplayDriverServerPtr m_server;
		GafferDisplayDriverPtr m_driver;

		Gaffer::IntPlug *updateCountPlug();
		const Gaffer::IntPlug *updateCountPlug() const;
				
		void plugSet( Gaffer::Plug *plug );
		void setupServer();
		void driverCreated( GafferDisplayDriver *driver );
		void setupDriver( GafferDisplayDriverPtr driver );
		void dataReceived( GafferDisplayDriver *driver, const Imath::Box2i &bound );
		void imageReceived( GafferDisplayDriver *driver );
		
		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Display );

} // namespace GafferImage

#endif // GAFFERIMAGE_DISPLAY_H

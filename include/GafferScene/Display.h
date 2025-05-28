//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "GafferScene/Export.h"
#include "GafferScene/TypeIds.h"

#include "GafferImage/ImageNode.h"

#include "Gaffer/NumericPlug.h"

#include "IECoreImage/DisplayDriver.h"

#include <functional>

namespace GafferScene
{

IE_CORE_FORWARDDECLARE( GafferDisplayDriver )

class GAFFERSCENE_API Display : public GafferImage::ImageNode
{

	public :

		GAFFER_NODE_DECLARE_TYPE( GafferScene::Display, DisplayTypeId, GafferImage::ImageNode );

		explicit Display( const std::string &name = defaultName<Display>() );
		~Display() override;

		/// Sets the driver used to provide the image to this node. If `copy` is
		/// true then a static copy of the current state of the driver is taken,
		/// in which case `driverClosed()` will return `true`.
		void setDriver( IECoreImage::DisplayDriverPtr driver, bool copy = false );
		IECoreImage::DisplayDriver *getDriver();
		const IECoreImage::DisplayDriver *getDriver() const;

		/// Returns true if this node has a driver and it has been closed, and
		/// therefore won't be receiving any more image data.
		bool driverClosed() const;

		/// Emitted when a new driver has been created. This can
		/// then be passed to `Display::setDriver()` to populate
		/// a Display with an incoming image.
		using DriverCreatedSignal = Gaffer::Signals::Signal<void ( IECoreImage::DisplayDriver *driver, const IECore::CompoundData *parameters )>;
		static DriverCreatedSignal &driverCreatedSignal();

		/// Emitted when a complete image has been received.
		/// \todo It would make more sense to call this `driverClosedSignal()`.
		static UnaryPlugSignal &imageReceivedSignal();

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hashViewNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstStringVectorDataPtr computeViewNames( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const override;

		void hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		GafferImage::Format computeFormat( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const override;

		void hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstStringVectorDataPtr computeChannelNames( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const override;

		void hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		Imath::Box2i computeDataWindow( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const override;

		void hashMetadata( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstCompoundDataPtr computeMetadata( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const override;

		void hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const override;

		void hashDeep( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		bool computeDeep( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const override;

		void hashSampleOffsets( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstIntVectorDataPtr computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const override;

	private :

		GafferDisplayDriverPtr m_driver;
		Gaffer::Signals::Connection m_dataReceivedConnection;
		Gaffer::Signals::Connection m_imageReceivedConnection;

		Gaffer::IntPlug *driverCountPlug();
		const Gaffer::IntPlug *driverCountPlug() const;

		Gaffer::IntPlug *channelDataCountPlug();
		const Gaffer::IntPlug *channelDataCountPlug() const;

		void setupDriver( GafferDisplayDriverPtr driver );
		void dataReceived();
		void imageReceived();
		static void dataReceivedUI();
		static void imageReceivedUI( Ptr display );

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Display );

} // namespace GafferImage

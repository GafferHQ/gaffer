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

#ifndef GAFFERIMAGE_DISPLAY_H
#define GAFFERIMAGE_DISPLAY_H

#include "IECore/DisplayDriverServer.h"

#include "Gaffer/NumericPlug.h"

#include "GafferImage/ImageNode.h"

namespace GafferImage
{

IE_CORE_FORWARDDECLARE( GafferDisplayDriver )

/// \todo Remove portPlug() and the internal server
/// \todo Pass GafferDisplayDriver rather than IECore::DisplayDriver
/// in setDriver/getDriver/driverCreatedSignal.
class Display : public ImageNode
{

	public :

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::Display, DisplayTypeId, ImageNode );

		Display( const std::string &name = defaultName<Display>() );
		virtual ~Display();

		Gaffer::IntPlug *portPlug();
		const Gaffer::IntPlug *portPlug() const;

		/// Sets the driver used to provide the
		/// image to this node.
		void setDriver( IECore::DisplayDriverPtr driver );
		/// \todo Default copy to false and remove method above
		void setDriver( IECore::DisplayDriverPtr driver, bool copy );
		IECore::DisplayDriver *getDriver();
		const IECore::DisplayDriver *getDriver() const;

		/// Emitted when a new driver has been created. This can
		/// then be passed to `Display::setDriver()` to populate
		/// a Display with an incoming image.
		typedef boost::signal<void ( IECore::DisplayDriver *driver, const IECore::CompoundData *parameters )> DriverCreatedSignal;
		static DriverCreatedSignal &driverCreatedSignal();

		/// Emitted when a complete image has been received.
		static UnaryPlugSignal &imageReceivedSignal();

		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;

		/// Used to trigger UI updates when image data is received
		/// via a driver on a background thread. Exposed publicly
		/// for the use of the Catalogue node.
		typedef boost::function<void ()> UIThreadFunction;
		static void executeOnUIThread( UIThreadFunction function );

	protected :

		virtual void hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual GafferImage::Format computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const;

		virtual void hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual IECore::ConstStringVectorDataPtr computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const;

		virtual void hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual Imath::Box2i computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const;

		// Don't need to re-implement hashMetadata() because we always return the same value.
		virtual IECore::ConstCompoundDataPtr computeMetadata( const Gaffer::Context *context, const ImagePlug *parent ) const;

		virtual void hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const;

		// Signal used to request the execution of a function on the UI thread.
		// We service these requests in DisplayUI.py.
		typedef boost::signal<void ( UIThreadFunction )> ExecuteOnUIThreadSignal;
		static ExecuteOnUIThreadSignal &executeOnUIThreadSignal();

	private :

		IECore::DisplayDriverServerPtr m_server;
		GafferDisplayDriverPtr m_driver;

		Gaffer::IntPlug *updateCountPlug();
		const Gaffer::IntPlug *updateCountPlug() const;

		void plugSet( Gaffer::Plug *plug );
		void setupServer();
		void driverCreated( IECore::DisplayDriver *driver );
		void setupDriver( GafferDisplayDriverPtr driver );
		void dataReceived();
		void imageReceived();
		static void dataReceivedUI();
		static void imageReceivedUI( Ptr display );

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Display );

typedef Gaffer::FilteredChildIterator<Gaffer::TypePredicate<Display> > DisplayIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::TypePredicate<Display> > RecursiveDisplayIterator;

} // namespace GafferImage

#endif // GAFFERIMAGE_DISPLAY_H

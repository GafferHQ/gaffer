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

#include "boost/bind.hpp"
#include "boost/bind/placeholders.hpp"
#include "boost/lexical_cast.hpp"

#include "IECore/LRUCache.h"
#include "IECore/DisplayDriverServer.h"
#include "IECore/ImageDisplayDriver.h"
#include "IECore/MessageHandler.h"

#include "GafferImage/Display.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// Implementation of a cache of DisplayDriverServers. We use the cache
// as many nodes may want to use the same port number, and this allows us
// to share the servers between the nodes.
//////////////////////////////////////////////////////////////////////////

typedef LRUCache<int, DisplayDriverServerPtr> DisplayDriverServerCache;

static DisplayDriverServerPtr cacheGetter( int key, size_t cost )
{
	cost = 1;
	return new DisplayDriverServer( key );
}

static DisplayDriverServerCache g_serverCache( cacheGetter, 10 );

//////////////////////////////////////////////////////////////////////////
// Implementation of a DisplayDriver to support the node itself
//////////////////////////////////////////////////////////////////////////

namespace GafferImage
{

class GafferDisplayDriver : public IECore::ImageDisplayDriver
{

	public :
	
		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::GafferDisplayDriver, GafferDisplayDriverTypeId, ImageDisplayDriver );

		GafferDisplayDriver( const Imath::Box2i &displayWindow, const Imath::Box2i &dataWindow,
			const vector<string> &channelNames, ConstCompoundDataPtr parameters )
			:	ImageDisplayDriver( displayWindow, dataWindow, channelNames, parameters )
		{
			m_parameters = parameters ? parameters->copy() : CompoundDataPtr( new CompoundData );
			instanceCreatedSignal()( this );
		}

		virtual ~GafferDisplayDriver()
		{
		}
		
		const CompoundData *parameters() const
		{
			return m_parameters.get();
		}
		
		virtual void imageData( const Imath::Box2i &box, const float *data, size_t dataSize )
		{
			ImageDisplayDriver::imageData( box, data, dataSize );
			dataReceivedSignal()( this, box );
		}
		
		virtual void imageClose()
		{
			ImageDisplayDriver::imageClose();
			imageReceivedSignal()( this );
		}

		typedef boost::signal<void ( GafferDisplayDriver *, const Imath::Box2i & )> DataReceivedSignal;
		DataReceivedSignal &dataReceivedSignal()
		{
			return m_dataReceivedSignal;
		}
		
		typedef boost::signal<void ( GafferDisplayDriver * )> ImageReceivedSignal;
		ImageReceivedSignal &imageReceivedSignal()
		{
			return m_imageReceivedSignal;
		}

		typedef boost::signal<void ( GafferDisplayDriver * )> InstanceCreatedSignal;
		static InstanceCreatedSignal &instanceCreatedSignal()
		{
			static InstanceCreatedSignal s;
			return s;
		}

	private :
	
		static const DisplayDriverDescription<GafferDisplayDriver> g_description;

		IECore::ConstCompoundDataPtr m_parameters;
		DataReceivedSignal m_dataReceivedSignal;
		ImageReceivedSignal m_imageReceivedSignal;

};

const DisplayDriver::DisplayDriverDescription<GafferDisplayDriver> GafferDisplayDriver::g_description;

} // namespace GafferImage

//////////////////////////////////////////////////////////////////////////
// Implementation of the Display class itself
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( Display );

size_t Display::g_firstPlugIndex = 0;

Display::Display( const std::string &name )
	:	ImagePrimitiveNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild(
		new IntPlug(
			"port",
			Plug::In,
			1559,
			1,
			65535,
			// disabling input connections because they could be used
			// to create a port number which changes with context. we 
			// can't allow that because we can only have a single server
			// associated with a given node.
			Plug::Default & ~Plug::AcceptsInputs
		)
	);
	
	// this plug is incremented when new data is received, triggering dirty signals
	// and prompting reevaluation in the viewer. see GafferImageUI.DisplayUI for
	// details of how it is set (we can't set it from dataReceived() because we're
	// not on the ui thread at that point.
	addChild(
		new IntPlug(
			"__updateCount",
			Plug::In,
			0,
			0,
			Imath::limits<int>::max(),
			Plug::Default & ~Plug::Serialisable
		)
	);
	
	// we don't want caching for the output image, because we're basically
	// caching the whole thing internally ourselves anyway.
	imagePrimitivePlug()->setFlags( Plug::Cacheable, false );
		
	plugSetSignal().connect( boost::bind( &Display::plugSet, this, ::_1 ) );
	GafferDisplayDriver::instanceCreatedSignal().connect( boost::bind( &Display::driverCreated, this, ::_1 ) );
	setupServer();
}

Display::~Display()
{
}
		
Gaffer::IntPlug *Display::portPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *Display::portPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *Display::updateCountPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *Display::updateCountPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}
				
void Display::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImagePrimitiveNode::affects( input, outputs );
	
	if( input == portPlug() || input == updateCountPlug() )
	{
		for( ValuePlugIterator it( outPlug() ); it != it.end(); it++ )
		{
			outputs.push_back( it->get() );
		}
	}
}

Node::UnaryPlugSignal &Display::dataReceivedSignal()
{
	static UnaryPlugSignal s;
	return s;
}

Node::UnaryPlugSignal &Display::imageReceivedSignal()
{
	static UnaryPlugSignal s;
	return s;
}

void Display::hashImagePrimitive( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	updateCountPlug()->hash( h );
}

IECore::ConstImagePrimitivePtr Display::computeImagePrimitive( const Gaffer::Context *context ) const
{
	return m_driver ? m_driver->image() : 0;
}

void Display::plugSet( Gaffer::Plug *plug )
{
	if( plug == portPlug() )
	{
		setupServer();
	}
}

void Display::setupServer()
{
	try
	{
		m_server = g_serverCache.get( portPlug()->getValue() );	
	}
	catch( const std::exception &e )
	{
		m_server = 0;
		msg( Msg::Error, "Display::setupServer", e.what() );
	}
}

void Display::driverCreated( GafferDisplayDriver *driver )
{
	ConstStringDataPtr portNumber = driver->parameters()->member<StringData>( "displayPort" );
	if( portNumber && boost::lexical_cast<int>( portNumber->readable() ) == portPlug()->getValue() )
	{
		setupDriver( driver );
	}
}

void Display::setupDriver( GafferDisplayDriverPtr driver )
{
	if( m_driver )
	{
		m_driver->dataReceivedSignal().disconnect( boost::bind( &Display::dataReceived, this, _1, _2 ) );
		m_driver->imageReceivedSignal().disconnect( boost::bind( &Display::imageReceived, this, _1 ) );
	}
	
	m_driver = driver;
	if( m_driver )
	{
		m_driver->dataReceivedSignal().connect( boost::bind( &Display::dataReceived, this, _1, _2 ) );	
		m_driver->imageReceivedSignal().connect( boost::bind( &Display::imageReceived, this, _1 ) );	
	}
}

void Display::dataReceived( GafferDisplayDriver *driver, const Imath::Box2i &bound )
{
	dataReceivedSignal()( outPlug() );
}

void Display::imageReceived( GafferDisplayDriver *driver )
{
	imageReceivedSignal()( outPlug() );
}

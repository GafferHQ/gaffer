//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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
//      * Neither the name of Image Engine Design nor the names of
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

#include "IECore/MessageHandler.h"
#include "IECore/NullObject.h"

#include "Gaffer/Context.h"

#include "GafferImage/Warp.h"
#include "GafferImage/Sampler.h"

using namespace std;
using namespace boost;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// Engine
//////////////////////////////////////////////////////////////////////////

Warp::Engine::~Engine()
{
}

const V2f Warp::Engine::black( std::numeric_limits<float>::infinity() );

//////////////////////////////////////////////////////////////////////////
// EngineData
//////////////////////////////////////////////////////////////////////////

// Custom Data derived class used to store an Engine.
// We are deliberately omitting a custom TypeId etc because
// this is just a private class.
class Warp::EngineData : public Data
{

	public :

		EngineData( const Engine *engine )
			:	engine( engine )
		{
		}

		virtual ~EngineData()
		{
			delete engine;
		}

		const Engine *engine;

	protected :

		virtual void copyFrom( const Object *other, CopyContext *context )
		{
			Data::copyFrom( other, context );
			msg( Msg::Warning, "EngineData::copyFrom", "Not implemented" );
		}

		virtual void save( SaveContext *context ) const
		{
			Data::save( context );
			msg( Msg::Warning, "EngineData::save", "Not implemented" );
		}

		virtual void load( LoadContextPtr context )
		{
			Data::load( context );
			msg( Msg::Warning, "EngineData::load", "Not implemented" );
		}

};

//////////////////////////////////////////////////////////////////////////
// Warp
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( Warp );

size_t Warp::g_firstPlugIndex = 0;

Warp::Warp( const std::string &name )
	:	FlatImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new IntPlug( "boundingMode", Plug::In, Sampler::Black, Sampler::Black, Sampler::Clamp ) );
	addChild( new ObjectPlug( "__engine", Plug::Out, NullObject::defaultNullObject() ) );

	// Pass through the things we don't change at all.
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	outPlug()->channelNamesPlug()->setInput( inPlug()->channelNamesPlug() );

}

Warp::~Warp()
{
}

Gaffer::IntPlug *Warp::boundingModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *Warp::boundingModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

Gaffer::ObjectPlug *Warp::enginePlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::ObjectPlug *Warp::enginePlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 1 );
}

void Warp::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FlatImageProcessor::affects( input, outputs );

	// TypeId comparison is necessary to avoid calling pure virtual
	// methods below if we're called before being fully constructed.
	if( typeId() == staticTypeId() )
	{
		return;
	}

	if( affectsEngine( input ) )
	{
		outputs.push_back( enginePlug() );
	}

	if(
		input == inPlug()->channelDataPlug() ||
		input == boundingModePlug() ||
		input == enginePlug()
	)
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

void Warp::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( output == enginePlug() )
	{
		hashEngine(
			context->get<string>( ImagePlug::channelNameContextName ),
			context->get<V2i>( ImagePlug::tileOriginContextName ),
			context,
			h
		);
		return;
	}

	FlatImageProcessor::hash( output, context, h );
}

void Warp::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == enginePlug() )
	{
		static_cast<ObjectPlug *>( output )->setValue(
			new EngineData(
				computeEngine(
					context->get<string>( ImagePlug::channelNameContextName ),
					context->get<V2i>( ImagePlug::tileOriginContextName ),
					context
				)
			)
		);
		return;
	}

	FlatImageProcessor::compute( output, context );
}

void Warp::hashFlatChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageProcessor::hashFlatChannelData( parent, context, h );

	const IECore::MurmurHash engineHash = enginePlug()->hash();
	h.append( engineHash );

	ConstEngineDataPtr engineData = static_pointer_cast<const EngineData>( enginePlug()->getValue( &engineHash ) );

	Sampler sampler(
		inPlug(),
		context->get<string>( ImagePlug::channelNameContextName ),
		engineData->engine->inputWindow( context->get<V2i>( ImagePlug::tileOriginContextName ) ),
		(Sampler::BoundingMode)boundingModePlug()->getValue()
	);
	sampler.hash( h );

	outPlug()->dataWindowPlug()->hash( h );
}

IECore::ConstFloatVectorDataPtr Warp::computeFlatChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ConstEngineDataPtr engineData = static_pointer_cast<const EngineData>( enginePlug()->getValue() );
	const Engine *e = engineData->engine;

	Sampler sampler(
		inPlug(),
		channelName,
		e->inputWindow( tileOrigin ),
		(Sampler::BoundingMode)boundingModePlug()->getValue()
	);

	const Box2i dataWindow = outPlug()->dataWindowPlug()->getValue();

	FloatVectorDataPtr resultData = new FloatVectorData;
	vector<float> &result = resultData->writable();
	result.reserve( ImagePlug::tileSize() * ImagePlug::tileSize() );

	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
	V2i oP;
	for( oP.y = tileBound.min.y; oP.y < tileBound.max.y; ++oP.y )
	{
		for( oP.x = tileBound.min.x; oP.x < tileBound.max.x; ++oP.x )
		{
			float v = 0.0f;
			if( contains( dataWindow, oP ) )
			{
				const V2f iP = e->inputPixel( V2f( oP.x + 0.5, oP.y + 0.5 ) );
				if( iP != Engine::black )
				{
					v = sampler.sample( iP.x, iP.y );
				}
			}
			result.push_back( v );
		}
	}

	return resultData;
}

bool  Warp::affectsEngine( const Gaffer::Plug *input ) const
{
	return false;
}

void Warp::hashEngine( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageProcessor::hash( enginePlug(), context, h );
}


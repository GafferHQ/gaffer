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

#include "GafferImage/Warp.h"

#include "GafferImage/FilterAlgo.h"
#include "GafferImage/Sampler.h"

#include "Gaffer/Context.h"

#include "IECore/MessageHandler.h"
#include "IECore/NullObject.h"

using namespace std;
using namespace boost;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

namespace
{
	static IECore::InternedString g_tileInputBoundName( "tileInputBound"  );
	static IECore::InternedString g_pixelInputPositionsName( "pixelInputPositions"  );
	static IECore::InternedString g_pixelInputDerivativesName( "pixelInputDerivatives"  );

	const CompoundObject *sampleRegionsEmptyTile()
	{
		static ConstCompoundObjectPtr g_sampleRegionsEmptyTile( new CompoundObject() );
		return g_sampleRegionsEmptyTile.get();
	}

	void hashEngineIfTileValid( ImagePlug::ChannelDataScope &tileScope, const ObjectPlug *plug, const Box2i &dataWindow, const V2i &tileOrigin, IECore::MurmurHash &h )
	{
		if( BufferAlgo::intersects( dataWindow, Box2i( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) ) ) )
		{
			tileScope.setTileOrigin( tileOrigin );
			plug->hash( h );
		}
	}

	ConstObjectPtr computeEngineIfTileValid( ImagePlug::ChannelDataScope &tileScope, const ObjectPlug *plug, const Box2i &dataWindow, const V2i &tileOrigin )
	{
		if( BufferAlgo::intersects( dataWindow, Box2i( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) ) ) )
		{
			tileScope.setTileOrigin( tileOrigin );
			return plug->getValue();
		}
		else
		{
			return nullptr;
		}
	}
}

float Warp::approximateDerivative( float upper, float center, float lower )
{
	if( center == Engine::black.x )
	{
		return 0.0f;						// Sample is totally invalid
	}
	else if( upper != Engine::black.x && lower != Engine::black.x )
	{
		float high = upper - center;
		float low = center - lower;

		// We have valid derivatives on both sides
		// The accurate thing to do would be to average them, but here we take the minimum
		// instead.  This may underfilter sometimes, but there are two arguments for it:
		// * A large jump on one side could represent a discontinuity that we shouldn't filter across
		// * Keeping the filter size lower is good for performance ( in the case of a large discontinuity,
		//   filtering across it could be disasterous for performance )
		return fabs( high ) < fabs( low ) ? high : low;
	}
	else if( upper != Engine::black.x )
	{
		return upper - center;				// One sided derivative
	}
	else if( lower != Engine::black.x )
	{
		return center - lower;				// One sided derivative
	}
	else
	{
		return 1.0f;						// Sample is valid, but no derivative information
	}
}

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

		~EngineData() override
		{
			delete engine;
		}

		const Engine *engine;

	protected :

		void copyFrom( const Object *other, CopyContext *context ) override
		{
			Data::copyFrom( other, context );
			msg( Msg::Warning, "EngineData::copyFrom", "Not implemented" );
		}

		void save( SaveContext *context ) const override
		{
			Data::save( context );
			msg( Msg::Warning, "EngineData::save", "Not implemented" );
		}

		void load( LoadContextPtr context ) override
		{
			Data::load( context );
			msg( Msg::Warning, "EngineData::load", "Not implemented" );
		}

};

//////////////////////////////////////////////////////////////////////////
// Warp
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( Warp );

size_t Warp::g_firstPlugIndex = 0;

Warp::Warp( const std::string &name )
	:	FlatImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new IntPlug( "boundingMode", Plug::In, Sampler::Black, Sampler::Black, Sampler::Clamp ) );
	addChild( new StringPlug( "filter", Plug::In, "cubic" ) );
	addChild( new BoolPlug( "useDerivatives", Plug::In, true ) );

	addChild( new ObjectPlug( "__engine", Plug::Out, NullObject::defaultNullObject() ) );
	addChild( new CompoundObjectPlug( "__sampleRegions", Plug::Out, new CompoundObject, Plug::Default ) );

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

Gaffer::StringPlug *Warp::filterPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *Warp::filterPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::BoolPlug *Warp::useDerivativesPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::BoolPlug *Warp::useDerivativesPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

Gaffer::ObjectPlug *Warp::enginePlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::ObjectPlug *Warp::enginePlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 3 );
}

CompoundObjectPlug *Warp::sampleRegionsPlug()
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 4 );
}

const CompoundObjectPlug *Warp::sampleRegionsPlug() const
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 4 );
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

	if( input == enginePlug() ||
		input == filterPlug() ||
		input == useDerivativesPlug() )
	{
		outputs.push_back( sampleRegionsPlug() );
	}

	if(
		input == inPlug()->channelDataPlug() ||
		input == boundingModePlug() ||
		input == filterPlug() ||
		input == sampleRegionsPlug()
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
			context->get<V2i>( ImagePlug::tileOriginContextName ),
			context,
			h
		);
		return;
	}
	else if( output == sampleRegionsPlug() )
	{
		ImagePlug::ChannelDataScope tileScope( context );

		V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
		h.append( tileOrigin );
		enginePlug()->hash( h );

		bool useDerivatives = useDerivativesPlug()->getValue();
		h.append( useDerivatives );
		if( useDerivatives )
		{
			Box2i dataWindow;
			{
				ImagePlug::GlobalScope c( context );
				dataWindow = outPlug()->dataWindowPlug()->getValue();
			}

			hashEngineIfTileValid( tileScope, enginePlug(), dataWindow,
				tileOrigin + V2i( ImagePlug::tileSize(), 0 ), h );
			hashEngineIfTileValid( tileScope, enginePlug(), dataWindow,
				tileOrigin - V2i( ImagePlug::tileSize(), 0 ), h );
			hashEngineIfTileValid( tileScope, enginePlug(), dataWindow,
				tileOrigin + V2i( 0, ImagePlug::tileSize() ), h );
			hashEngineIfTileValid( tileScope, enginePlug(), dataWindow,
				tileOrigin - V2i( 0, ImagePlug::tileSize() ), h );
		}

		// The sampleRegionsPlug() includes an overall bound for the tile which depends on the filter
		// support width
		filterPlug()->hash( h );
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
					context->get<V2i>( ImagePlug::tileOriginContextName ),
					context
				)
			)
		);
		return;
	}
	else if( output == sampleRegionsPlug() )
	{
		Box2i dataWindow;
		{
			ImagePlug::GlobalScope c( context );
			dataWindow = outPlug()->dataWindowPlug()->getValue();
		}

		const OIIO::Filter2D *filter = FilterAlgo::acquireFilter( filterPlug()->getValue() );
		const float filterWidth = filter->width();

		const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );

		const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );

		ConstEngineDataPtr engineData = static_pointer_cast<const EngineData>( enginePlug()->getValue() );
		const Engine *engine = engineData->engine;


		// Start by testing if the tile is completely empty
		// We abort this test on the first valid position returned from the engine, but
		// worst case, we could traverse the whole tile, only to find one valid pixel in
		// the last corner we check, and then we will have to revisit the whole tile below.
		// It's still a definite performance win, because in the common cases we usually
		// either abort this test quickly, or we are actually in an invalid tile, and noticing
		// this as soon as possible is a big win.
		bool emptyTile = true;
		for( int y = 0; y < ImagePlug::tileSize(); ++y )
		{
			for( int x = 0; x < ImagePlug::tileSize(); ++x )
			{
				if( BufferAlgo::contains( dataWindow, V2i( tileOrigin.x + x, tileOrigin.y + y ) ) )
				{
					V2f inputPosition = engine->inputPixel( V2f(
						( tileOrigin.x + x ) + 0.5,
						( tileOrigin.y + y ) + 0.5 )
					);

					if( inputPosition != Engine::black )
					{
						emptyTile = false;
						break;
					}
				}
			}
			if( !emptyTile )
			{
				break;
			}
		}

		if( emptyTile )
		{
			static_cast<CompoundObjectPlug *>( output )->setValue( sampleRegionsEmptyTile() );
			return;
		}

		Box2f inputBound;

		V2fVectorDataPtr pixelInputPositionsData = new V2fVectorData();
		std::vector< V2f > &pixelInputPositions = pixelInputPositionsData->writable();
		pixelInputPositions.reserve( ImagePlug::tileSize() * ImagePlug::tileSize() );
		V2fVectorDataPtr pixelInputDerivativesData = new V2fVectorData();
		std::vector< V2f > &pixelInputDerivatives = pixelInputDerivativesData->writable();
		pixelInputDerivatives.reserve( ImagePlug::tileSize() * ImagePlug::tileSize() );

		bool useDerivatives = useDerivativesPlug()->getValue();

		if( useDerivatives )
		{
			// Get engines for the 4 surrounding images tiles ( or leave them null if they're outside the
			// dataWindow )
			ImagePlug::ChannelDataScope tileScope( context );

			ConstEngineDataPtr engineDataPlusX = static_pointer_cast<const EngineData>(
				computeEngineIfTileValid( tileScope, enginePlug(), dataWindow,
					tileOrigin + V2i( ImagePlug::tileSize(), 0 )
				)
			);
			ConstEngineDataPtr engineDataMinusX = static_pointer_cast<const EngineData>(
				computeEngineIfTileValid( tileScope, enginePlug(), dataWindow,
					tileOrigin - V2i( ImagePlug::tileSize(), 0 )
				)
			);
			ConstEngineDataPtr engineDataPlusY = static_pointer_cast<const EngineData>(
				computeEngineIfTileValid( tileScope, enginePlug(), dataWindow,
					tileOrigin + V2i( 0, ImagePlug::tileSize() )
				)
			);
			ConstEngineDataPtr engineDataMinusY = static_pointer_cast<const EngineData>(
				computeEngineIfTileValid( tileScope, enginePlug(), dataWindow,
					tileOrigin - V2i( 0, ImagePlug::tileSize() )
				)
			);

			const Engine *enginePlusX = nullptr, *engineMinusX = nullptr, *enginePlusY = nullptr, *engineMinusY = nullptr;
			if( engineDataPlusX ) enginePlusX = engineDataPlusX->engine;
			if( engineDataMinusX ) engineMinusX = engineDataMinusX->engine;
			if( engineDataPlusY ) enginePlusY = engineDataPlusY->engine;
			if( engineDataMinusY ) engineMinusY = engineDataMinusY->engine;

			std::vector<V2f> threeRowsCache( ImagePlug::tileSize() * 3 );

			// Loop through all the rows of data we need to compute derivatives for this tile
			// ( This includes one row before and after the tile ).  In order to compute forward
			// and backward derivatives, we need to cache three rows, and we only start outputting
			// to pixelInputPositons/Derivatives once the cache is filled
			for( int cacheY = -1; cacheY < ImagePlug::tileSize() + 1; cacheY++ )
			{
				int cacheRow = ( cacheY + 1 ) % 3;

				// Determine which engine we need to use to set up this cache row
				// ( The first and last are outside this tile, and use a different engine )
				const Engine *curEngine = engine;
				if( cacheY == -1 ) curEngine = engineMinusY;
				if( cacheY == ImagePlug::tileSize() ) curEngine = enginePlusY;

				for( int x = 0; x < ImagePlug::tileSize(); x++ )
				{
					if( BufferAlgo::contains( dataWindow, V2i( tileOrigin.x + x, tileOrigin.y + cacheY ) ) )
					{
						threeRowsCache[ cacheRow * ImagePlug::tileSize() + x ] = curEngine->inputPixel( V2f(
							( tileOrigin.x + x ) + 0.5,
							( tileOrigin.y + cacheY ) + 0.5 ) );
					}
					else
					{
						threeRowsCache[ cacheRow * ImagePlug::tileSize() + x ] = Engine::black;
					}
				}


				if( cacheY > 0 )
				{
					// We now have 3 rows of data cached, and can compute one row of derivatives
					int cacheRowPlus = cacheRow;
					int cacheRowMiddle = ( cacheY + 3 ) % 3;
					int cacheRowMinus = ( cacheY + 2 ) % 3;

					int outputY = cacheY - 1;

					for( int x = 0; x < ImagePlug::tileSize(); x++ )
					{
						V2f inputPosition( Engine::black );
						V2f inputDerivatives( 0.0f );
						if( BufferAlgo::contains( dataWindow, V2i( tileOrigin.x + x, tileOrigin.y + outputY ) ) )
						{
							inputPosition = threeRowsCache[ cacheRowMiddle * ImagePlug::tileSize() + x ];

							if( inputPosition != Engine::black )
							{
								V2f xPlus = Engine::black;
								if( x != ImagePlug::tileSize() - 1 )
								{
									// We're not on the border, this offset is cached
									xPlus = threeRowsCache[ cacheRowMiddle * ImagePlug::tileSize() + x + 1 ];
								}
								else if( enginePlusX )
								{
									// This offset goes over the border, fetch it from the other engine
									xPlus = enginePlusX->inputPixel( V2f(
										( tileOrigin.x + x + 1 ) + 0.5,
										( tileOrigin.y + outputY ) + 0.5 ) );
								}
								V2f xMinus = Engine::black;
								if( x != 0 )
								{
									// We're not on the border, this offset is cached
									xMinus = threeRowsCache[ cacheRowMiddle * ImagePlug::tileSize() + x - 1 ];
								}
								else if( engineMinusX )
								{
									// This offset goes over the border, fetch it from the other engine
									xMinus = engineMinusX->inputPixel( V2f(
										( tileOrigin.x + x - 1 ) + 0.5,
										( tileOrigin.y + outputY ) + 0.5 ) );
								}

								V2f yMinus = threeRowsCache[ cacheRowMinus * ImagePlug::tileSize() + x ];
								V2f yPlus = threeRowsCache[ cacheRowPlus * ImagePlug::tileSize() + x ];

								V2f dPdx(
									approximateDerivative(  xPlus.x, inputPosition.x, xMinus.x ),
									approximateDerivative(  xPlus.y, inputPosition.y, xMinus.y ) );

								V2f dPdy(
									approximateDerivative(  yPlus.x, inputPosition.x, yMinus.x ),
									approximateDerivative(  yPlus.y, inputPosition.y, yMinus.y ) );

								inputDerivatives = FilterAlgo::derivativesToAxisAligned( inputPosition, dPdx, dPdy );

								inputBound.extendBy( FilterAlgo::filterSupport( inputPosition, inputDerivatives.x, inputDerivatives.y, filterWidth ) );
							}
						}
						pixelInputPositions.push_back( inputPosition );
						pixelInputDerivatives.push_back( inputDerivatives );
					}

				}
			}
		}
		else
		{
			for( int y = 0; y < ImagePlug::tileSize(); y++ )
			{
				for( int x = 0; x < ImagePlug::tileSize(); x++ )
				{
					V2f inputPosition( Engine::black );
					if( BufferAlgo::contains( dataWindow, V2i( tileOrigin.x + x, tileOrigin.y + y ) ) )
					{
						inputPosition = engine->inputPixel( V2f(
							( tileOrigin.x + x ) + 0.5,
							( tileOrigin.y + y ) + 0.5 ) );

						if( inputPosition != Engine::black )
						{
							inputBound.extendBy( FilterAlgo::filterSupport( inputPosition, 1.0f, 1.0f,  filterWidth ) );
						}
					}
					pixelInputPositions.push_back( inputPosition );
					pixelInputDerivatives.push_back( V2f( 1.0f ) );
				}
			}
		}

		// Include any pixels where the corner max bound is above the pixel center, and
		// the corner min bound is below the pixel center
		Box2i inputPixelBound(
			V2i( (int)ceilf( inputBound.min.x - 0.5 ), (int)ceilf( inputBound.min.y - 0.5 ) ),
			V2i( (int)floorf( inputBound.max.x - 0.5 ) + 1, (int)floorf( inputBound.max.y - 0.5 ) + 1 ) );

		CompoundObjectPtr sampleRegions = new CompoundObject();
		sampleRegions->members()[ g_tileInputBoundName ] = new Box2iData( inputPixelBound );
		sampleRegions->members()[ g_pixelInputPositionsName ] = pixelInputPositionsData;
		sampleRegions->members()[ g_pixelInputDerivativesName ] = pixelInputDerivativesData;
		static_cast<CompoundObjectPlug *>( output )->setValue( sampleRegions );
		return;
	}

	FlatImageProcessor::compute( output, context );
}

void Warp::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	IECore::MurmurHash sampleRegionsHash;
	ConstCompoundObjectPtr sampleRegions;

	{
		Context::EditableScope sampleRegionsScope( context );
		sampleRegionsScope.remove( ImagePlug::channelNameContextName );
		sampleRegionsHash = sampleRegionsPlug()->hash();
		sampleRegions = sampleRegionsPlug()->getValue( &sampleRegionsHash );
	}

	if( sampleRegions.get() == sampleRegionsEmptyTile())
	{
		h = ImagePlug::blackTile()->Object::hash();
		return;
	}

	FlatImageProcessor::hashChannelData( parent, context, h );

	h.append( sampleRegionsHash );

	const Box2i &tileInputBound = sampleRegions->member< Box2iData >( g_tileInputBoundName, true )->readable();

	Sampler sampler(
		inPlug(),
		context->get<string>( ImagePlug::channelNameContextName ),
		tileInputBound,
		(Sampler::BoundingMode)boundingModePlug()->getValue()
	);
	sampler.hash( h );

	{
		ImagePlug::GlobalScope c( context );
		outPlug()->dataWindowPlug()->hash( h );
	}
}

IECore::ConstFloatVectorDataPtr Warp::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ConstCompoundObjectPtr sampleRegions;

	{
		Context::EditableScope sampleRegionsScope( context );
		sampleRegionsScope.remove( ImagePlug::channelNameContextName );
		sampleRegions = sampleRegionsPlug()->getValue();
	}

	if( sampleRegions.get() == sampleRegionsEmptyTile())
	{
		return ImagePlug::blackTile();
	}

	FloatVectorDataPtr resultData = new FloatVectorData;
	vector<float> &result = resultData->writable();
	result.reserve( ImagePlug::tileSize() * ImagePlug::tileSize() );

	const OIIO::Filter2D *filter = FilterAlgo::acquireFilter( filterPlug()->getValue() );


	const Box2i &tileInputBound = sampleRegions->member< Box2iData >( g_tileInputBoundName, true )->readable();
	const std::vector<V2f> &pixelInputPositions = sampleRegions->member< V2fVectorData >( g_pixelInputPositionsName, true )->readable();
	const std::vector<V2f> &pixelInputDerivatives = sampleRegions->member< V2fVectorData >( g_pixelInputDerivativesName, true )->readable();

	Box2i dataWindow;
	{
		ImagePlug::GlobalScope c( context );
		dataWindow = outPlug()->dataWindowPlug()->getValue();
	}

	const Box2i validPixelsRelativeToTile( dataWindow.min - tileOrigin, dataWindow.max - tileOrigin );

	Sampler sampler(
		inPlug(),
		channelName,
		tileInputBound,
		(Sampler::BoundingMode)boundingModePlug()->getValue()
	);

	std::vector<float> scratchMemory;
	int i = 0;
	V2i oP;
	for( oP.y = 0; oP.y < ImagePlug::tileSize(); ++oP.y )
	{
		for( oP.x = 0; oP.x < ImagePlug::tileSize(); ++oP.x, ++i )
		{
			float v = 0;
			if( BufferAlgo::contains( validPixelsRelativeToTile , oP ) )
			{
				const V2f &input = pixelInputPositions[i];
				if( input != Engine::black )
				{
					v = FilterAlgo::sampleBox( sampler, input, pixelInputDerivatives[i].x, pixelInputDerivatives[i].y, filter, scratchMemory );
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

void Warp::hashEngine( const Imath::V2i &tileOrigin, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageProcessor::hash( enginePlug(), context, h );
}


//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#include <algorithm>

#include "Gaffer/Context.h"

#include "GafferImage/Median.h"
#include "GafferImage/Sampler.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

IE_CORE_DEFINERUNTIMETYPED( Median );

size_t Median::g_firstPlugIndex = 0;

Median::Median( const std::string &name )
	:   ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new V2iPlug( "radius", Plug::In, V2i( 0 ), V2i( 0 ) ) );
	addChild( new IntPlug( "boundingMode", Plug::In, Sampler::Black, Sampler::Black, Sampler::Clamp ) );
	addChild( new BoolPlug( "expandDataWindow" ) );

	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	outPlug()->channelNamesPlug()->setInput( inPlug()->channelNamesPlug() );
}

Median::~Median()
{
}

Gaffer::V2iPlug *Median::radiusPlug()
{
	return getChild<V2iPlug>( g_firstPlugIndex );
}

const Gaffer::V2iPlug *Median::radiusPlug() const
{
	return getChild<V2iPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *Median::boundingModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *Median::boundingModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

Gaffer::BoolPlug *Median::expandDataWindowPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::BoolPlug *Median::expandDataWindowPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

void Median::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if(
		input == expandDataWindowPlug() ||
		input == inPlug()->dataWindowPlug() ||
		input->parent<V2iPlug>() == radiusPlug()
	)
	{
		outputs.push_back( outPlug()->dataWindowPlug() );
	}

	if(
		input == inPlug()->channelDataPlug() ||
		input->parent<V2iPlug>() == radiusPlug() ||
		input == boundingModePlug()
	)
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

void Median::hashDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const V2i radius = radiusPlug()->getValue();
	if( radius == V2i( 0 ) || !expandDataWindowPlug()->getValue() )
	{
		h = inPlug()->dataWindowPlug()->hash();
		return;
	}

	ImageProcessor::hashDataWindow( parent, context, h );
	h.append( radius );
}

Imath::Box2i Median::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	const V2i radius = radiusPlug()->getValue();
	if( radius == V2i( 0 ) || !expandDataWindowPlug()->getValue() )
	{
		return inPlug()->dataWindowPlug()->getValue();
	}

	Box2i dataWindow = inPlug()->dataWindowPlug()->getValue();
	if( !BufferAlgo::empty( dataWindow ) )
	{
		dataWindow.min -= radius;
		dataWindow.max += radius;
	}
	return dataWindow;
}

void Median::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const V2i radius = radiusPlug()->getValue();
	if( radius == V2i( 0 ) )
	{
		h = inPlug()->channelDataPlug()->hash();
		return;
	}

	ImageProcessor::hashChannelData( parent, context, h );

	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
	const Box2i inputBound( tileBound.min - radius, tileBound.max + radius );

	Sampler sampler(
		inPlug(),
		context->get<std::string>( ImagePlug::channelNameContextName ),
		inputBound,
		(Sampler::BoundingMode)boundingModePlug()->getValue()
	);
	sampler.hash( h );
	h.append( radius );
	h.append( tileOrigin );

}

IECore::ConstFloatVectorDataPtr Median::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	const V2i radius = radiusPlug()->getValue();
	if( radius == V2i( 0 ) )
	{
		return inPlug()->channelDataPlug()->getValue();
	}

	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
	const Box2i inputBound( tileBound.min - radius, tileBound.max + radius );

	Sampler sampler(
		inPlug(),
		channelName,
		inputBound,
		(Sampler::BoundingMode)boundingModePlug()->getValue()
	);

	FloatVectorDataPtr resultData = new FloatVectorData;
	vector<float> &result = resultData->writable();
	result.reserve( ImagePlug::tileSize() * ImagePlug::tileSize() );

	vector<float> pixels( ( 1 + 2 * radius.x ) * ( 1 + 2 * radius.y ) );
	vector<float>::iterator median = pixels.begin() + pixels.size() / 2;

	V2i p;
	for( p.y = tileBound.min.y; p.y < tileBound.max.y; ++p.y )
	{
		for( p.x = tileBound.min.x; p.x < tileBound.max.x; ++p.x )
		{
			V2i o;
			vector<float>::iterator pixelsIt = pixels.begin();
			for( o.y = -radius.y; o.y <= radius.y; ++o.y )
			{
				for( o.x = -radius.x; o.x <= radius.x; ++o.x )
				{
					*pixelsIt++ = sampler.sample( p.x + o.x, p.y + o.y );
				}
			}
			nth_element( pixels.begin(), median, pixels.end() );
			result.push_back( *median );
		}
	}

	return resultData;
}

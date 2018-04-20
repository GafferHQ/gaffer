//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Lucien Fostier. All rights reserved.
//  Copyright (c) 2012-2018, Image Engine Design Inc. All rights reserved.
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

#include "OSL/oslnoise.h"

#include "Gaffer/Context.h"
#include "Gaffer/Transform2DPlug.h"

#include "GafferImage/Noise.h"
#include "GafferImage/ImageAlgo.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace GafferImage;
using namespace Gaffer;

namespace
{
	float remap( float value, float oldMin, float oldMax, float newMin, float newMax )
	{
		return newMin + (value - oldMin) * (newMax - newMin) / (oldMax - oldMin);
	}

	float fBm( V2f uv, int octaves, V3f freq, float lacunarity, float gain, float depth )
	{
		float v;
		float acc = 0;
		float scale = gain;
		V3f pp;
		V3f p( uv.x, uv.y, depth );

		for( int i=0; i < octaves; i++ )
		{
			pp = p / freq;
			v = OSL::oslnoise::snoise( pp );
			v *= scale;
			acc += v;
			scale *= gain;
			p *= V3f( lacunarity );
		}
		return acc;
	}
}

//////////////////////////////////////////////////////////////////////////
// Noise implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( Noise );

size_t Noise::g_firstPlugIndex = 0;

Noise::Noise( const std::string &name )
	:	ImageNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new FormatPlug( "format" ) );
	addChild( new StringPlug( "layer" ) );
	addChild( new V2fPlug( "size", Plug::In, V2f( 350 ), V2f( 1 ), V2f( 100000 ) ) );
	addChild( new FloatPlug( "depth", Plug::In ) );
	addChild( new IntPlug( "octaves", Plug::In, 8, 1, 10 ) );
	addChild( new FloatPlug( "gain", Plug::In, 0.5, 0.1, 1 ) );
	addChild( new FloatPlug( "lacunarity", Plug::In, 2.5, 1, 3 ) );
	addChild( new FloatPlug( "minOutput", Plug::In, 0, -1, 1 ) );
	addChild( new FloatPlug( "maxOutput", Plug::In, 1, -1, 1 ) );
	addChild( new Transform2DPlug( "transform" ) );
}

Noise::~Noise()
{
}

GafferImage::FormatPlug *Noise::formatPlug()
{
	return getChild<FormatPlug>( g_firstPlugIndex );
}

const GafferImage::FormatPlug *Noise::formatPlug() const
{
	return getChild<FormatPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *Noise::layerPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *Noise::layerPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::V2fPlug *Noise::sizePlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::V2fPlug *Noise::sizePlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex + 2 );
}

Gaffer::FloatPlug *Noise::depthPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::FloatPlug *Noise::depthPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 3 );
}

Gaffer::IntPlug *Noise::octavesPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::IntPlug *Noise::octavesPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 4 );
}

Gaffer::FloatPlug *Noise::gainPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::FloatPlug *Noise::gainPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 5 );
}

Gaffer::FloatPlug *Noise::lacunarityPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::FloatPlug *Noise::lacunarityPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 6 );
}

Gaffer::FloatPlug *Noise::minOutputPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 7 );
}

const Gaffer::FloatPlug *Noise::minOutputPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 7 );
}

Gaffer::FloatPlug *Noise::maxOutputPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 8 );
}

const Gaffer::FloatPlug *Noise::maxOutputPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 8 );
}

Gaffer::Transform2DPlug *Noise::transformPlug()
{
	return getChild<Transform2DPlug>( g_firstPlugIndex + 9 );
}

const Gaffer::Transform2DPlug *Noise::transformPlug() const
{
	return getChild<Transform2DPlug>( g_firstPlugIndex + 9 );
}

void Noise::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageNode::affects( input, outputs );

	if(
		input->parent<V2fPlug>() == sizePlug() ||
		input == depthPlug() ||
		input == octavesPlug() ||
		input == gainPlug() ||
		input == lacunarityPlug() ||
		transformPlug()->isAncestorOf( input ) ||
		input == minOutputPlug() ||
		input == maxOutputPlug()
	)
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}

	if( formatPlug()->displayWindowPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->formatPlug() );
		outputs.push_back( outPlug()->dataWindowPlug() );
	}

	if( input == formatPlug()->pixelAspectPlug() )
	{
		outputs.push_back( outPlug()->formatPlug() );
	}

	if( input == layerPlug() )
	{
		outputs.push_back( outPlug()->channelNamesPlug() );
	}
}

void Noise::hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashFormat( output, context, h );
	h.append( formatPlug()->hash() );
}

GafferImage::Format Noise::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return formatPlug()->getValue();
}

void Noise::hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashDataWindow( output, context, h );
	h.append( formatPlug()->hash() );
}

Imath::Box2i Noise::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return formatPlug()->getValue().getDisplayWindow();
}

IECore::ConstCompoundDataPtr Noise::computeMetadata( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return outPlug()->metadataPlug()->defaultValue();
}

void Noise::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashChannelNames( output, context, h );
	layerPlug()->hash( h );
}

IECore::ConstStringVectorDataPtr Noise::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::string channelNamePrefix = layerPlug()->getValue();
	if( !channelNamePrefix.empty() )
	{
		channelNamePrefix += ".";
	}

	StringVectorDataPtr resultData = new StringVectorData();
	vector<string> &result = resultData->writable();

	result.push_back( channelNamePrefix + "R" );
	result.push_back( channelNamePrefix + "G" );
	result.push_back( channelNamePrefix + "B" );
	result.push_back( channelNamePrefix + "A" );

	return resultData;
}

void Noise::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashChannelData( output, context, h );

	minOutputPlug()->hash( h );
	maxOutputPlug()->hash( h );
	sizePlug()->hash( h );
	depthPlug()->hash( h );
	octavesPlug()->hash( h );
	gainPlug()->hash( h );
	lacunarityPlug()->hash( h );
	transformPlug()->hash( h );

	V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	h.append( tileOrigin );

	string channelName = context->get<std::string>( ImagePlug::channelNameContextName );
	h.append( channelName );
}

IECore::ConstFloatVectorDataPtr Noise::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	const M33f transform = transformPlug()->matrix().inverse();

	FloatVectorDataPtr resultData = new FloatVectorData;
	vector<float> &result = resultData->writable();
	result.reserve( ImagePlug::tileSize() * ImagePlug::tileSize() );
	const V2f size = sizePlug()->getValue();
	const float lacunarity = lacunarityPlug()->getValue();
	const int octaves = octavesPlug()->getValue();
	const float gain = gainPlug()->getValue();
	const float depth = depthPlug()->getValue();
	const float maxOutput = maxOutputPlug()->getValue();
	const float minOutput = minOutputPlug()->getValue();

	float n;
	for( int y = 0; y < ImagePlug::tileSize(); ++y )
	{
		for( int x = 0; x < ImagePlug::tileSize(); ++x )
		{
			// screen space pixel coordinates
			V2f p( tileOrigin.x + x, tileOrigin.y + y );
			p *= transform;
			n = fBm( p, octaves, V3f(size.x, size.y, 1 ), lacunarity, gain, depth );
			result.push_back( remap( n, -.5, .5, minOutput, maxOutput ) );
		}

	}

	return resultData;
}

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
#include "GafferImage/ImageAlgo.h"
#include "GafferImage/Ramp.h"

#include "Gaffer/Context.h"
#include "Gaffer/Transform2DPlug.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace GafferImage;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Ramp implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( Ramp );

size_t Ramp::g_firstPlugIndex = 0;

Ramp::Ramp( const std::string &name )
	:	FlatImageSource( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new FormatPlug( "format" ) );
	addChild( new V2fPlug( "startPosition", Plug::In ) );
	addChild( new V2fPlug( "endPosition", Plug::In ) );
	SplinefColor4fPlug::ValueType rampDefault;
	rampDefault.points.insert( SplinefColor4fPlug::ValueType::Point( 0.0f, Color4f( 0.0f, 0.0f, 0.0f, 0.0f ) ) );
	rampDefault.points.insert( SplinefColor4fPlug::ValueType::Point( 1.0f, Color4f( 1.0f, 1.0f, 1.0f, 1.0f ) ) );
	addChild( new SplinefColor4fPlug( "ramp", Plug::In, rampDefault ) );
	addChild( new StringPlug( "layer" ) );
	addChild( new Transform2DPlug( "transform" ) );
}

Ramp::~Ramp()
{
}

GafferImage::FormatPlug *Ramp::formatPlug()
{
	return getChild<FormatPlug>( g_firstPlugIndex );
}

const GafferImage::FormatPlug *Ramp::formatPlug() const
{
	return getChild<FormatPlug>( g_firstPlugIndex );
}

Gaffer::V2fPlug *Ramp::startPositionPlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::V2fPlug *Ramp::startPositionPlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex + 1 );
}

Gaffer::V2fPlug *Ramp::endPositionPlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::V2fPlug *Ramp::endPositionPlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex + 2 );
}

Gaffer::SplinefColor4fPlug *Ramp::rampPlug()
{
	return getChild<SplinefColor4fPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::SplinefColor4fPlug *Ramp::rampPlug() const
{
	return getChild<SplinefColor4fPlug>( g_firstPlugIndex + 3 );
}

Gaffer::StringPlug *Ramp::layerPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::StringPlug *Ramp::layerPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

Gaffer::Transform2DPlug *Ramp::transformPlug()
{
	return getChild<Transform2DPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::Transform2DPlug *Ramp::transformPlug() const
{
	return getChild<Transform2DPlug>( g_firstPlugIndex + 5 );
}

void Ramp::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FlatImageSource::affects( input, outputs );

	if(
		rampPlug()->isAncestorOf( input ) ||
		input->parent<V2fPlug>() == startPositionPlug() ||
		input->parent<V2fPlug>() == endPositionPlug() ||
		transformPlug()->isAncestorOf( input )
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

void Ramp::hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageSource::hashFormat( output, context, h );
	h.append( formatPlug()->hash() );
}

GafferImage::Format Ramp::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return formatPlug()->getValue();
}

void Ramp::hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageSource::hashDataWindow( output, context, h );
	h.append( formatPlug()->hash() );
}

Imath::Box2i Ramp::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return formatPlug()->getValue().getDisplayWindow();
}

IECore::ConstCompoundDataPtr Ramp::computeMetadata( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return outPlug()->metadataPlug()->defaultValue();
}

void Ramp::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageSource::hashChannelNames( output, context, h );
	layerPlug()->hash( h );
}

IECore::ConstStringVectorDataPtr Ramp::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
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

void Ramp::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageSource::hashChannelData( output, context, h );

	V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	h.append( tileOrigin );

	string channelName = context->get<std::string>( ImagePlug::channelNameContextName );
	h.append( channelName );

	rampPlug()->hash( h );
	transformPlug()->hash( h );

	startPositionPlug()->hash( h );
	endPositionPlug()->hash( h );
}

IECore::ConstFloatVectorDataPtr Ramp::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	const int channelIndex = ImageAlgo::colorIndex( context->get<std::string>( ImagePlug::channelNameContextName ) );

	const SplinefColor4f ramp = rampPlug()->getValue().spline();

	const M33f inverseTransform = transformPlug()->matrix().inverse();
	const V2f startPosition = startPositionPlug()->getValue();
	const V2f endPosition = endPositionPlug()->getValue();

	V3f startPosition3f( startPosition.x, startPosition.y, 0 );
	V3f endPosition3f( endPosition.x, endPosition.y, 0 );

	const LineSegment3f line( startPosition3f, endPosition3f );

	FloatVectorDataPtr resultData = new FloatVectorData;
	vector<float> &result = resultData->writable();
	result.reserve( ImagePlug::tileSize() * ImagePlug::tileSize() );

	V3f closest;
	float pos;
	Color4f color;
	for( int y = 0; y < ImagePlug::tileSize(); ++y )
	{
		for( int x = 0; x < ImagePlug::tileSize(); ++x )
		{

			// screen space pixel coordinates
			V2f p( tileOrigin.x + x + .5f, tileOrigin.y + y + .5f);
			p *= inverseTransform;

			V3f p3f( p.x, p.y, 0 );
			closest = line.closestPointTo( p3f );

			pos = (closest - startPosition3f).length() / line.length();
			color = ramp( pos );

			result.push_back( color[channelIndex] );
		}

	}

	return resultData;
}

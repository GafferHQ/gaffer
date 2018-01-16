//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Lucien Fostier. All rights reserved.
//  Copyright (c) 2012-2017, Image Engine Design Inc. All rights reserved.
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

#include "OpenEXR/ImathFun.h"

#include "Gaffer/Context.h"
#include "Gaffer/Transform2DPlug.h"

#include "GafferImage/Checkerboard.h"
#include "GafferImage/ImageAlgo.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace GafferImage;
using namespace Gaffer;


namespace
{

	float filteredStripes( float x, float period, float width )
	{
		float edge = 0.5f;
		float w = width / period;
		float x0 = x / period - w / 2;
		float x1 = x0 + w;
		float edgeComp = 1 - edge;
		float floorX1 = floor( x1 );
		float floorX0 = floor( x0 );
	
		return ( ( edgeComp * floorX1 + max( 0.f, x1 - floorX1 - edge ) ) - ( edgeComp * floorX0 + max( 0.f, x0 - floorX0 - edge ) ) ) / ( w );
	
	}

}

//////////////////////////////////////////////////////////////////////////
// Checkerboard implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( Checkerboard );

size_t Checkerboard::g_firstPlugIndex = 0;

Checkerboard::Checkerboard( const std::string &name )
	:	ImageNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new FormatPlug( "format" ) );
	addChild( new V2iPlug( "size", Plug::In, V2i( 64 ), V2i( 1 ), V2i( 4096 ) ) );
	addChild( new FloatPlug( "softness", Plug::In, 1.f, 1.f, 10.f ) );
	addChild( new Color4fPlug( "colorA", Plug::In, Color4f( 0.1, 0.1, 0.1, 1 ) ) );
	addChild( new Color4fPlug( "colorB", Plug::In, Color4f( .5, 0.5, 0.5, 1 ) ) );
	addChild( new StringPlug( "layer" ) );
	addChild( new Transform2DPlug( "transform" ) );
}

Checkerboard::~Checkerboard()
{
}

GafferImage::FormatPlug *Checkerboard::formatPlug()
{
	return getChild<FormatPlug>( g_firstPlugIndex );
}

const GafferImage::FormatPlug *Checkerboard::formatPlug() const
{
	return getChild<FormatPlug>( g_firstPlugIndex );
}

Gaffer::V2iPlug *Checkerboard::sizePlug()
{
	return getChild<V2iPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::V2iPlug *Checkerboard::sizePlug() const
{ 
	return getChild<V2iPlug>( g_firstPlugIndex + 1 );
}

Gaffer::FloatPlug *Checkerboard::softnessPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::FloatPlug *Checkerboard::softnessPlug() const
{ 
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

Gaffer::Color4fPlug *Checkerboard::colorPlugA()
{
	return getChild<Color4fPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::Color4fPlug *Checkerboard::colorPlugA() const
{
	return getChild<Color4fPlug>( g_firstPlugIndex + 3 );
}

Gaffer::Color4fPlug *Checkerboard::colorPlugB()
{
	return getChild<Color4fPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::Color4fPlug *Checkerboard::colorPlugB() const
{
	return getChild<Color4fPlug>( g_firstPlugIndex + 4 );
}

Gaffer::StringPlug *Checkerboard::layerPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::StringPlug *Checkerboard::layerPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 5 );
}

Gaffer::Transform2DPlug *Checkerboard::transformPlug()
{
	return getChild<Transform2DPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::Transform2DPlug *Checkerboard::transformPlug() const
{
	return getChild<Transform2DPlug>( g_firstPlugIndex + 6 );
}

void Checkerboard::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageNode::affects( input, outputs );

	if(
		input->parent<Plug>() == colorPlugA() ||
		input->parent<Plug>() == colorPlugB() ||
		input->parent<V2iPlug>() == sizePlug() ||
		transformPlug()->isAncestorOf( input ) ||
		input == softnessPlug()
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

void Checkerboard::hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashFormat( output, context, h );
	h.append( formatPlug()->hash() );
}

GafferImage::Format Checkerboard::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return formatPlug()->getValue();
}

void Checkerboard::hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashDataWindow( output, context, h );
	h.append( formatPlug()->hash() );
}

Imath::Box2i Checkerboard::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return formatPlug()->getValue().getDisplayWindow();
}

IECore::ConstCompoundDataPtr Checkerboard::computeMetadata( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return outPlug()->metadataPlug()->defaultValue();
}

void Checkerboard::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashChannelNames( output, context, h );
	layerPlug()->hash( h );
}

IECore::ConstStringVectorDataPtr Checkerboard::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
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

void Checkerboard::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashChannelData( output, context, h );

	V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	h.append( tileOrigin );

	string channelName = context->get<std::string>( ImagePlug::channelNameContextName );
	h.append( channelName );

	const int channelIndex = ImageAlgo::colorIndex( channelName );
	colorPlugA()->getChild( channelIndex )->hash( h );
	colorPlugB()->getChild( channelIndex )->hash( h );

	h.append( sizePlug()->getValue() );
	transformPlug()->hash( h );
	softnessPlug()->hash( h );
}

IECore::ConstFloatVectorDataPtr Checkerboard::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	const int channelIndex = ImageAlgo::colorIndex( context->get<std::string>( ImagePlug::channelNameContextName ) );

	const float valueA = colorPlugA()->getChild( channelIndex )->getValue();
	const float valueB = colorPlugB()->getChild( channelIndex )->getValue();
	const V2i size = sizePlug()->getValue();
	float softness = softnessPlug()->getValue();
	const M33f transform = transformPlug()->matrix();

	FloatVectorDataPtr resultData = new FloatVectorData;
	vector<float> &result = resultData->writable();
	result.reserve( ImagePlug::tileSize() * ImagePlug::tileSize() );

	float w0;
	float h0;
	float w1;
	float h1;
	float v;

	for( int y = 0; y < ImagePlug::tileSize(); ++y )
	{
		for( int x = 0; x < ImagePlug::tileSize(); ++x )
		{
			// screen space pixel coordinates
			V2f p( tileOrigin.x + x, tileOrigin.y + y );
			p *= transform.inverse();

			w0 = filteredStripes( p.x , size.x, softness );
			h0 = filteredStripes( p.y , size.y, softness );
			w1 = filteredStripes( p.x  + size.x / 2.f, size.x, softness );
			h1 = filteredStripes( p.y  + size.y / 2.f, size.y, softness );
			v = w0 * h0 + w1 * h1;

			result.push_back( lerp<float>( valueA, valueB, v ) );
		}

	}

	return resultData;
}

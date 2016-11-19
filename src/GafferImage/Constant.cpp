//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2012-2015, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/Context.h"

#include "GafferImage/Constant.h"
#include "GafferImage/ImageAlgo.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace GafferImage;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Constant implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( Constant );

size_t Constant::g_firstPlugIndex = 0;

Constant::Constant( const std::string &name )
	:	ImageNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new FormatPlug( "format" ) );
	addChild( new Color4fPlug( "color", Plug::In, Color4f( 0, 0, 0, 1 ) ) );
	addChild( new FloatPlug( "z", Plug::In, 1.0 ) );
	addChild( new FloatPlug( "zBack", Plug::In, 1.0 ) );
}

Constant::~Constant()
{
}

GafferImage::FormatPlug *Constant::formatPlug()
{
	return getChild<FormatPlug>( g_firstPlugIndex );
}

const GafferImage::FormatPlug *Constant::formatPlug() const
{
	return getChild<FormatPlug>( g_firstPlugIndex );
}

Gaffer::Color4fPlug *Constant::colorPlug()
{
	return getChild<Color4fPlug>( g_firstPlugIndex+1 );
}

const Gaffer::Color4fPlug *Constant::colorPlug() const
{
	return getChild<Color4fPlug>( g_firstPlugIndex+1 );
}

Gaffer::FloatPlug *Constant::zPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex+2 );
}

const Gaffer::FloatPlug *Constant::zPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex+2 );
}

Gaffer::FloatPlug *Constant::zBackPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex+3 );
}

const Gaffer::FloatPlug *Constant::zBackPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex+3 );
}

void Constant::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageNode::affects( input, outputs );

	// Process the children of the compound plugs.
	for( unsigned int i = 0; i < 4; ++i )
	{
		if( input == colorPlug()->getChild(i) )
		{
			outputs.push_back( outPlug()->channelDataPlug() );
			return;
		}
	}

	if( input == zPlug() ||
	    input == zBackPlug() )
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}

	if( formatPlug()->displayWindowPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->formatPlug() );
		outputs.push_back( outPlug()->dataWindowPlug() );
	}
	else if( input == formatPlug()->pixelAspectPlug() )
	{
		outputs.push_back( outPlug()->formatPlug() );
	}
}

void Constant::hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashFormat( output, context, h );
	h.append( formatPlug()->hash() );
}

GafferImage::Format Constant::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return formatPlug()->getValue();
}

void Constant::hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashDataWindow( output, context, h );
	h.append( formatPlug()->hash() );
}

Imath::Box2i Constant::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return formatPlug()->getValue().getDisplayWindow();
}

IECore::ConstCompoundObjectPtr Constant::computeMetadata( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return outPlug()->metadataPlug()->defaultValue();
}

void Constant::hashDeepState( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashDeepState( output, context, h );
}

int Constant::computeDeepState( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return ImagePlug::Flat;
}

void Constant::hashSampleOffsets( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImagePlug::flatTileSampleOffsets()->hash( h );
}

IECore::ConstIntVectorDataPtr Constant::computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return ImagePlug::flatTileSampleOffsets();
}

void Constant::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashChannelNames( output, context, h );
}

IECore::ConstStringVectorDataPtr Constant::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	IECore::StringVectorDataPtr channelStrVectorData( new IECore::StringVectorData() );
	std::vector<std::string> &channelStrVector( channelStrVectorData->writable() );
	channelStrVector.push_back("R");
	channelStrVector.push_back("G");
	channelStrVector.push_back("B");
	channelStrVector.push_back("A");
	channelStrVector.push_back("Z");
	channelStrVector.push_back("ZBack");
	return channelStrVectorData;
}

void Constant::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashChannelData( output, context, h );
	// Don't bother hashing the format or tile origin here as we couldn't care less about the
	// position on the canvas, only the colour!
	const std::string channelName = context->get<std::string>( ImagePlug::channelNameContextName );
	if ( channelName == "Z" )
	{
		zPlug()->hash( h );
	}
	else if ( channelName == "ZBack" )
	{
		zPlug()->hash( h );
		zBackPlug()->hash( h );
	}
	else
	{
		const int channelIndex = colorIndex( channelName );
		colorPlug()->getChild( channelIndex )->hash( h );
	}
}

IECore::ConstFloatVectorDataPtr Constant::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	float value;
	if ( channelName == "Z" )
	{
		value = zPlug()->getValue();
	}
	else if ( channelName == "ZBack" )
	{
		value = std::max( zBackPlug()->getValue(), zPlug()->getValue() );
	}
	else
	{
		const int channelIndex = colorIndex( channelName );
		value = colorPlug()->getChild( channelIndex )->getValue();
	}

	FloatVectorDataPtr result = new FloatVectorData;
	result->writable().resize( ImagePlug::tileSize() * ImagePlug::tileSize(), value );

	return result;
}

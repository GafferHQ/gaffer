//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
//  Copyright (c) 2014, Luke Goddard. All rights reserved.
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

#include "Gaffer/Context.h"

#include "GafferImage/Position.h"
#include "GafferImage/Sampler.h"

using namespace Gaffer;
using namespace GafferImage;
using namespace IECore;
using namespace Imath;

IE_CORE_DEFINERUNTIMETYPED( Position );

size_t Position::g_firstPlugIndex = 0;

Position::Position( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new V2iPlug( "offset" ) );
}

Position::~Position()
{
}

Gaffer::V2iPlug *Position::offsetPlug()
{
	return getChild<V2iPlug>( g_firstPlugIndex );
}

const Gaffer::V2iPlug *Position::offsetPlug() const
{
	return getChild<V2iPlug>( g_firstPlugIndex );
}

void Position::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if( offsetPlug()->isAncestorOf( input ) || input == inPlug()->dataWindowPlug() || input == inPlug()->channelDataPlug() )
	{
		outputs.push_back( outPlug()->dataWindowPlug() );
		outputs.push_back( outPlug()->channelDataPlug() );
	}
	else if( input == inPlug()->channelNamesPlug() )
	{
		outputs.push_back( outPlug()->channelNamesPlug() );
	}
	else if( input == inPlug()->formatPlug() )
	{
		outputs.push_back( outPlug()->formatPlug() );
	}
}

bool Position::enabled() const
{
	if( !ImageProcessor::enabled() )
	{
		return false;
	}

	Imath::V2i offset( offsetPlug()->getValue() );
	return offset != Imath::V2i( 0 );
}

void Position::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = inPlug()->channelNamesPlug()->hash();
}

void Position::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Imath::V2i offset = offsetPlug()->getValue();
	Imath::V2i tileOrigin( Context::current()->get<Imath::V2i>( ImagePlug::tileOriginContextName ) );
	Imath::Box2i sampleArea( tileOrigin - offset, tileOrigin - offset + Imath::V2i( GafferImage::ImagePlug::tileSize() - 1 )  );

	// If the offset is a multiple of tilesize(), just get the hash of the tile that it is a duplicate of.
	if( offset.x % GafferImage::ImagePlug::tileSize() == 0 && offset.y % GafferImage::ImagePlug::tileSize() == 0 )
	{
		ContextPtr tmpContext = new Context( *Context::current() );

		Imath::V2i newTileOrigin = tileOrigin - ( GafferImage::ImagePlug::tileOrigin( inPlug()->dataWindowPlug()->getValue().min ) + offset );
		tmpContext->set( ImagePlug::tileOriginContextName, newTileOrigin );
		Context::Scope scopedContext( tmpContext );

		h = inPlug()->channelDataPlug()->hash();
	}
	else
	{
		// Hash all of the tiles that we require for this tile.	
		std::string channelName( Context::current()->get<std::string>( ImagePlug::channelNameContextName ) );
	
		Sampler sampler( inPlug(), channelName, sampleArea );
		sampler.hash( h );
		h.append( offset.x % GafferImage::ImagePlug::tileSize() );
		h.append( offset.y % GafferImage::ImagePlug::tileSize() );
	}
}

void Position::hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = inPlug()->formatPlug()->hash();
}

void Position::hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Imath::Box2i dataWindow( inPlug()->dataWindowPlug()->getValue() );
	Imath::V2i offset( offsetPlug()->getValue() );
	dataWindow.min += offset;
	dataWindow.max += offset;
	h.append( dataWindow );
}

GafferImage::Format Position::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return inPlug()->formatPlug()->getValue();
}

Imath::Box2i Position::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	Imath::Box2i dataWindow( inPlug()->dataWindowPlug()->getValue() );
	Imath::V2i offset( offsetPlug()->getValue() );
	dataWindow.min += offset;
	dataWindow.max += offset;
	return dataWindow;
}

IECore::ConstStringVectorDataPtr Position::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return inPlug()->channelNamesPlug()->getValue();
}

IECore::ConstFloatVectorDataPtr Position::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	// Allocate our output tile.
	FloatVectorDataPtr outData = new FloatVectorData;
	std::vector<float> &result = outData->writable();
	result.resize( ImagePlug::tileSize() * ImagePlug::tileSize() );

	// Get the offset that we have to shift the data by.
	Imath::V2i offset( offsetPlug()->getValue() );

	// Get the sample area.
	Imath::Box2i sampleArea( tileOrigin - offset, tileOrigin - offset + Imath::V2i( ImagePlug::tileSize() - 1 ) );
	
	Sampler sampler( inPlug(), channelName, sampleArea );

	float *ptr = &result[0];
	for( int y = sampleArea.min.y; y <= sampleArea.max.y; ++y )
	{
		for( int x = sampleArea.min.x; x <= sampleArea.max.x; ++x )
		{
			*ptr++ = sampler.sample( x, y );
		}
	}

	return outData;
}


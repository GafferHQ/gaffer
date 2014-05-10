//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
//  Copyright (c) 2013-2014, Luke Goddard. All rights reserved.
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

#include "GafferImage/Reformat.h"
#include "GafferImage/Scale.h"
#include "GafferImage/Sampler.h"

using namespace Gaffer;
using namespace GafferImage;
using namespace IECore;
using namespace Imath;

IE_CORE_DEFINERUNTIMETYPED( Reformat );

size_t Reformat::g_firstPlugIndex = 0;

Reformat::Reformat( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new FormatPlug( "format" ) );
	addChild( new FilterPlug( "filter" ) );
	
	addChild( new V2fPlug( "__scale", Gaffer::Plug::Out ) );
	addChild( new V2fPlug( "__origin", Gaffer::Plug::Out ) );
	
	GafferImage::Scale *scale = new GafferImage::Scale( std::string( boost::str( boost::format( "__%sScale" )  % name  ) ) );
	scale->inPlug()->setInput( inPlug() );
	scale->filterPlug()->setInput( filterPlug() );
	scale->enabledPlug()->setInput( enabledPlug() );
	scale->originPlug()->setInput( originPlug() );
	scale->scalePlug()->setInput( scalePlug() );
	addChild( scale );

	outPlug()->formatPlug()->setInput( formatPlug() );
	outPlug()->channelNamesPlug()->setInput( scale->outPlug()->channelNamesPlug() );
}

Reformat::~Reformat()
{
}

GafferImage::FormatPlug *Reformat::formatPlug()
{
	return getChild<FormatPlug>( g_firstPlugIndex );
}

const GafferImage::FormatPlug *Reformat::formatPlug() const
{
	return getChild<FormatPlug>( g_firstPlugIndex );
}

GafferImage::FilterPlug *Reformat::filterPlug()
{
	return getChild<GafferImage::FilterPlug>( g_firstPlugIndex+1 );
}

const GafferImage::FilterPlug *Reformat::filterPlug() const
{
	return getChild<GafferImage::FilterPlug>( g_firstPlugIndex+1 );
}

Gaffer::V2fPlug *Reformat::scalePlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex+2 );
}

const Gaffer::V2fPlug *Reformat::scalePlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex+2 );
}

Gaffer::V2fPlug *Reformat::originPlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex+3 );
}

const Gaffer::V2fPlug *Reformat::originPlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex+3 );
}

GafferImage::Scale *Reformat::scaleNode()
{
	return getChild<Scale>( g_firstPlugIndex + 4 );
}

const GafferImage::Scale *Reformat::scaleNode() const
{
	return getChild<Scale>( g_firstPlugIndex + 4 );
}

void Reformat::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if( input == formatPlug() || input == inPlug()->formatPlug() )
	{
		outputs.push_back( scalePlug()->getChild(0) );
		outputs.push_back( scalePlug()->getChild(1) );
		outputs.push_back( originPlug()->getChild(0) );
		outputs.push_back( originPlug()->getChild(1) );
		return;
	}

	if( input == formatPlug() || input == inPlug()->formatPlug() || input == inPlug()->dataWindowPlug() )
	{
		outputs.push_back( outPlug()->dataWindowPlug() );
	}
}

bool Reformat::enabled() const
{
	if( !ImageProcessor::enabled() )
	{
		return false;
	}

	Format inFormat( inPlug()->formatPlug()->getValue() );
	Format outFormat( formatPlug()->getValue() );

	return inFormat != outFormat;
}

void Reformat::compute( ValuePlug *output, const Context *context ) const
{
	Box2i displayWindow( inPlug()->formatPlug()->getValue().getDisplayWindow() );
	if( output == originPlug()->getChild( 0 ) )
	{
		static_cast<FloatPlug *>( output )->setValue( inPlug()->formatPlug()->getValue().getDisplayWindow().min.x );
		return;
	}
	else if( output == originPlug()->getChild( 1 ) )
	{
		static_cast<FloatPlug *>( output )->setValue( inPlug()->formatPlug()->getValue().getDisplayWindow().min.y );
		return;
	}
	else if( output == scalePlug()->getChild( 0 ) )
	{
		static_cast<FloatPlug *>( output )->setValue( scale().x );
		return;
	}
	else if( output == scalePlug()->getChild( 1 ) )
	{
		static_cast<FloatPlug *>( output )->setValue( scale().y );
		return;
	}

	ImageProcessor::compute( output, context );
}

void Reformat::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hash( output, context, h );

	if( output == scalePlug()->getChild( 0 ) )
	{
		h.append( inPlug()->formatPlug()->getValue().getDisplayWindow().size().x );
		h.append( formatPlug()->getValue().getDisplayWindow().size().x );
	}
	else if( output == scalePlug()->getChild( 1 ) )
	{
		h.append( inPlug()->formatPlug()->getValue().getDisplayWindow().size().y );
		h.append( inPlug()->formatPlug()->getValue().getPixelAspect() );
		h.append( formatPlug()->getValue().getDisplayWindow().size().y );
		h.append( formatPlug()->getValue().getPixelAspect() );
	}
	else if( output == originPlug()->getChild( 0 ) )
	{
		h.append( inPlug()->formatPlug()->getValue().getDisplayWindow().min.x );
	}
	else if( output == originPlug()->getChild( 1 ) )
	{
		h.append( inPlug()->formatPlug()->getValue().getDisplayWindow().min.y );
		h.append( inPlug()->formatPlug()->getValue().getPixelAspect() );
	}
}

void Reformat::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Imath::V2i formatOffset( inPlug()->formatPlug()->getValue().getDisplayWindow().min - formatPlug()->getValue().getDisplayWindow().min );
	if( formatOffset == Imath::V2i(0) )
	{
		h = scaleNode()->outPlug()->channelDataPlug()->hash();
	}
	else
	{
		h = scaleNode()->outPlug()->channelDataPlug()->hash();
		h.append( formatOffset );
	}
}

void Reformat::hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	formatPlug()->hash( h );
}

void Reformat::hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Imath::V2i formatOffset( inPlug()->formatPlug()->getValue().getDisplayWindow().min - formatPlug()->getValue().getDisplayWindow().min );
	if( formatOffset == Imath::V2i(0) )
	{
		h = scaleNode()->outPlug()->dataWindowPlug()->hash();
	}
	else
	{
		h = scaleNode()->outPlug()->dataWindowPlug()->hash();
		h.append( formatOffset );
	}
}

Imath::V2f Reformat::scale() const
{
	Box2i outDisplayWindow( formatPlug()->getValue().getDisplayWindow() );
	Box2i displayWindow( inPlug()->formatPlug()->getValue().getDisplayWindow() );
	return Imath::V2f( ( outDisplayWindow.size().x + 1. ) / ( displayWindow.size().x + 1. ), ( outDisplayWindow.size().y + 1. ) / ( displayWindow.size().y + 1. ) );
}

GafferImage::Format Reformat::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	// This code is never executed as the output format plug is connected directly to the input format plug.
	return inPlug()->formatPlug()->getValue();
}

Imath::Box2i Reformat::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	// If the origin of the input and output formats is different, we need to shift the data window so that it is relative to the new origin.
	Imath::V2i formatOffset( inPlug()->formatPlug()->getValue().getDisplayWindow().min - formatPlug()->getValue().getDisplayWindow().min );
	Imath::Box2i dataWindow( scaleNode()->outPlug()->dataWindowPlug()->getValue() );
	dataWindow.min -= formatOffset;
	dataWindow.max -= formatOffset;
	return dataWindow;
}

IECore::ConstStringVectorDataPtr Reformat::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return inPlug()->channelNamesPlug()->getValue();
}

IECore::ConstFloatVectorDataPtr Reformat::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	// Here we need to shift all of the scaled image data by the offset between the input and output formats.
	// This is required because the tiles are all aligned with a grid that has it's origin at 0x0 and not at the format's origin.
	// If there is no offset between the two formats then the channel data hash just copies the result from the Scale node.

	// Allocate our output tile.
	FloatVectorDataPtr outData = new FloatVectorData;
	std::vector<float> &result = outData->writable();
	result.resize( ImagePlug::tileSize() * ImagePlug::tileSize() );

	// Get the offset that we have to shift the data by.
	Imath::V2i formatOffset( inPlug()->formatPlug()->getValue().getDisplayWindow().min - formatPlug()->getValue().getDisplayWindow().min );

	// Get the sample area.
	Imath::Box2i sampleArea( tileOrigin + formatOffset, tileOrigin + formatOffset + Imath::V2i( ImagePlug::tileSize() - 1 ) );
	
	Sampler sampler( scaleNode()->outPlug(), channelName, sampleArea );

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


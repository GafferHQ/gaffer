//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
#include "GafferImage/Reformat.h"
#include "GafferImage/Filter.h"
#include "GafferImage/FormatPlug.h"
#include "GafferImage/ImagePlug.h"
#include "IECore/BoxAlgo.h"
#include "IECore/BoxOps.h"

using namespace Gaffer;
using namespace IECore;
using namespace GafferImage;

IE_CORE_DEFINERUNTIMETYPED( Reformat );

size_t Reformat::g_firstPlugIndex = 0;

Reformat::Reformat( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new FormatPlug( "format" ) );
	addChild( new IntPlug( "filter" ) );
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

Gaffer::IntPlug *Reformat::filterPlug()
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex+1 );
}

const Gaffer::IntPlug *Reformat::filterPlug() const
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex+1 );
}

void Reformat::affects( const Gaffer::ValuePlug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if( input == formatPlug() )
	{
		outputs.push_back( outPlug()->formatPlug() );
		outputs.push_back( outPlug()->dataWindowPlug() );
		outputs.push_back( outPlug()->channelDataPlug() );
	}
	else if( input == filterPlug() )
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

bool Reformat::enabled() const
{
	if ( !ImageProcessor::enabled() )
	{
		return false;
	}

	Format inFormat( inPlug()->formatPlug()->getValue() );
	Format outFormat( formatPlug()->getValue() );
		
	return inFormat != outFormat;
}

void Reformat::hashFormatPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	formatPlug()->hash( h );
}

void Reformat::hashDataWindowPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Format format = formatPlug()->getValue();
	h.append( format.getDisplayWindow() );
}

void Reformat::hashChannelNamesPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	inPlug()->channelNamesPlug()->hash( h );
}

void Reformat::hashChannelDataPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	inPlug()->channelDataPlug()->hash( h );
	filterPlug()->hash( h );
	Format format = formatPlug()->getValue();
	h.append( format.getDisplayWindow() );
}

Imath::Box2i Reformat::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return formatPlug()->getValue().getDisplayWindow();
}

GafferImage::Format Reformat::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return formatPlug()->getValue();
}

IECore::ConstStringVectorDataPtr Reformat::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return inPlug()->channelNamesPlug()->getValue();
}

IECore::ConstFloatVectorDataPtr Reformat::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	// Allocate the new tile
	FloatVectorDataPtr outDataPtr = new FloatVectorData;
	std::vector<float> &out = outDataPtr->writable();
	out.resize( ImagePlug::tileSize() * ImagePlug::tileSize() );

	// Reformat!
	int filter = filterPlug()->getValue();
	switch( filter )
	{
		default:
		case(0): reformat<ImpulseFilter>( channelName, tileOrigin, out ); break;
		case(1): reformat<BilinearFilter>( channelName, tileOrigin, out ); break;
		case(2): reformat<SineFilter>( channelName, tileOrigin, out ); break;
	}

	return outDataPtr;
}


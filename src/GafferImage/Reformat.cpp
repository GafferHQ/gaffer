//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
//  Copyright (c) 2013, Luke Goddard. All rights reserved.
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
#include "GafferImage/Reformat.h"
#include "GafferImage/Filter.h"
#include "GafferImage/FormatPlug.h"
#include "GafferImage/ImagePlug.h"
#include "GafferImage/Sampler.h"
#include "GafferImage/TypeIds.h"
#include "IECore/BoxAlgo.h"
#include "IECore/BoxOps.h"
#include "IECore/FastFloat.h"

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
	addChild( new FilterPlug( "filter" ) );
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

void Reformat::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if ( input == formatPlug() )
	{
		outputs.push_back( outPlug()->formatPlug() );
		outputs.push_back( outPlug()->dataWindowPlug() );
		outputs.push_back( outPlug()->channelDataPlug() );
	}
	else if ( input == filterPlug() )
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
	else if ( input == inPlug()->channelDataPlug() )
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
	h.append( format.getPixelAspect() );
	
	Format inFormat = inPlug()->formatPlug()->getValue();
	h.append( inFormat.getDisplayWindow() );
	h.append( inFormat.getPixelAspect() );
	
	inPlug()->dataWindowPlug()->hash( h );
}

void Reformat::hashChannelNamesPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	inPlug()->channelNamesPlug()->hash( h );
}

void Reformat::hashChannelDataPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	inPlug()->channelDataPlug()->hash( h );
	filterPlug()->hash( h );
	
	h.append( inPlug()->dataWindowPlug()->getValue() );
	
	Format format = formatPlug()->getValue();
	h.append( format.getDisplayWindow() );
	h.append( format.getPixelAspect() );
	
	Format inFormat = inPlug()->formatPlug()->getValue();
	h.append( inFormat.getDisplayWindow() );
	h.append( inFormat.getPixelAspect() );
}

Imath::Box2i Reformat::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	// Work out the scale factor of the output image and scale the input data window.
	Imath::V2f s( scale() );
	Imath::Box2i inDataWindow( inPlug()->dataWindowPlug()->getValue() );
	Imath::Box2i outDataWindow(
		Imath::V2i( int( floor( (inDataWindow.min.x)*s.x ) ), int( floor( (inDataWindow.min.y)*s.y ) ) ),
		Imath::V2i( int( ceil( (inDataWindow.max.x+1.)*s.x-1. ) ), int( ceil( (inDataWindow.max.y+1.)*s.y-1. ) ) )
	);
	return outDataWindow;
}

GafferImage::Format Reformat::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return formatPlug()->getValue();
}

IECore::ConstStringVectorDataPtr Reformat::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return inPlug()->channelNamesPlug()->getValue();
}

Imath::V2f Reformat::scale() const
{
	Format inFormat( inPlug()->formatPlug()->getValue() );
	Format outFormat( formatPlug()->getValue() );
	Imath::V2i inWH = Imath::V2i( inFormat.getDisplayWindow().max ) + Imath::V2i(1);
	Imath::V2i outWH = Imath::V2i( outFormat.getDisplayWindow().max ) + Imath::V2i(1);
	Imath::V2f scale( float( outWH.x ) / ( inWH.x ), float( outWH.y ) / inWH.y );
	return scale;
}

struct Contribution
{
	int pixel;
	float weight;
};

IECore::ConstFloatVectorDataPtr Reformat::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	// Allocate the new tile
	FloatVectorDataPtr outDataPtr = new FloatVectorData;
	std::vector<float> &out = outDataPtr->writable();
	out.resize( ImagePlug::tileSize() * ImagePlug::tileSize() );

	// Create some useful variables...
	Imath::Box2i tile( tileOrigin, Imath::V2i( tileOrigin.x + ImagePlug::tileSize() - 1, tileOrigin.y + ImagePlug::tileSize() - 1 ) );
	Imath::V2f scaleFactor( scale() );

	// Create our filter.
	FilterPtr f = Filter::create( filterPlug()->getValue(), 1.f / scaleFactor.y );
	
	// If we are filtering with a box filter then just don't bother filtering
	// at all and sample instead...
	if ( static_cast<GafferImage::TypeId>( f->typeId() ) == GafferImage::BoxFilterTypeId )
	{
		Imath::Box2i sampleBox(
			Imath::V2i( IECore::fastFloatFloor( tile.min.x / scaleFactor.x ), IECore::fastFloatCeil( tile.min.y / scaleFactor.y ) ),
			Imath::V2i( IECore::fastFloatFloor( tile.max.x / scaleFactor.x ), IECore::fastFloatCeil( tile.max.y / scaleFactor.y ) )
		);
		Sampler sampler( inPlug(), channelName, sampleBox, f, Sampler::Clamp );
		for ( int y = tile.min.y, ty = 0; y <= tile.max.y; ++y, ++ty )
		{
			for ( int x = tile.min.x, tx = 0; x <= tile.max.x; ++x, ++tx )
			{
				out[ tx + ImagePlug::tileSize() * ty ] = sampler.sample( (x+.5f)/scaleFactor.x, (y+.5f)/scaleFactor.y ); 
			}
		}
		return outDataPtr;
	}

	// Get the dimensions of our filter and create a box that we can use to define the bounds of our input.
	int fHeight = f->width();
	
	int sampleMinY = f->tap( (tile.min.y+.5) / scaleFactor.y );
	int sampleMaxY = f->tap( (tile.max.y+.5) / scaleFactor.y );
		
	f->setScale( 1.f / scaleFactor.x );
	int sampleMinX = f->tap( (tile.min.x+.5) / scaleFactor.x );
	int sampleMaxX = f->tap( (tile.max.x+.5) / scaleFactor.x );
	
	int fWidth = f->width();

	Imath::Box2i sampleBox(
		Imath::V2i( sampleMinX, sampleMinY ),
		Imath::V2i( sampleMaxX + fWidth, sampleMaxY + fHeight )
	);

	int sampleBoxWidth = sampleBox.max.x - sampleBox.min.x + 1;
	int sampleBoxHeight = sampleBox.max.y - sampleBox.min.y + 1;
	
	// Create a temporary buffer that we can write the result of the first pass to.
	// We extend the buffer vertically as we will need additional information in the
	// vertical squash (the second pass) to properly convolve the filter.
	float buffer[ ImagePlug::tileSize() * sampleBoxHeight ];
	
	// Create several buffers for each pixel in the output row (or coloum depending on the pass)
	// into which we can place the indices for the pixels that are contribute to it's result and
	// their weight.
	
	// A buffer that holds a list of pixel contributions and their weights for every pixel in the output buffer.
	// As it gets reused for both passes we make it large enough to hold both so that we don't have to resize it later.
	std::vector<Contribution> contribution( ImagePlug::tileSize() * ( sampleBoxHeight > sampleBoxWidth ? sampleBoxHeight : sampleBoxWidth ) ); 
	
	// The total number of pixels that contribute towards each pixel in th resulting image.
	std::vector<int> coverageTotal( ImagePlug::tileSize() );

	// The total weighted sum of contribution that each pixel in the output gets.
	// This value is used to normalize the result.
	std::vector<float> weightedSum( ImagePlug::tileSize() );

	// Horizontal Pass
	// Here we build a row buffer of contributing pixels and their weights for every pixel in the row.
	int contributionIdx = 0;
	for ( int i = 0; i < ImagePlug::tileSize(); ++i, contributionIdx += fWidth )
	{
		float center = (tile.min.x + i + 0.5) / scaleFactor.x;
		int tap = f->tap( center );
		
		int n = 0;	
		weightedSum[i] = 0.;
		for ( int j = tap; j < tap+fWidth; ++j )
		{
			float weight = f->weight( center, j );
			if ( weight == 0 )
			{
				continue;
			}
			
			contribution[contributionIdx+n].pixel = j; 
			weightedSum[i] += contribution[contributionIdx+n].weight = weight; 
			n++;
		}
		coverageTotal[i] = n;
	}
	
	// Now that we know the contribution of each pixel from the others on the row, compute the
	// horizontally scaled buffer which we will use as input in the vertical scale pass.
	Sampler sampler( inPlug(), channelName, sampleBox, f, Sampler::Clamp );
	for ( int k = 0; k < sampleBoxHeight; ++k )
	{
		for ( int i = 0, contributionIdx = 0; i < ImagePlug::tileSize(); ++i, contributionIdx += fWidth )
		{
			float intensity = 0;

			for ( int j = 0; j < coverageTotal[i]; ++j )
			{
				Contribution &contributor( contribution[ contributionIdx+j ] );

				if ( contributor.weight == 0. )
				{
					continue;
				}

				float value = sampler.sample( contributor.pixel, k + sampleBox.min.y );
				intensity += value * contributor.weight;
			}

			buffer[i + ImagePlug::tileSize() * k] = intensity / weightedSum[i];
		}
	}
	
	// Vertical Pass
	// Build the column buffer of contributing pixels and their weights for each pixel in the column.
	f->setScale( 1.f / scaleFactor.y );
	for ( int i = 0, contributionIdx = 0; i < ImagePlug::tileSize(); ++i, contributionIdx += fHeight )
	{
		float center = (tile.min.y + i + 0.5) / scaleFactor.y - sampleBox.min.y;
		int tap = f->tap( center );
		
		int n = 0;	
		weightedSum[i] = 0.;
		for ( int j = tap; j < tap+fHeight; ++j )
		{
			float weight = f->weight( center, j );
			if ( weight == 0 )
			{
				continue;
			}
			
			contribution[contributionIdx+n].pixel = j; 
			weightedSum[i] += contribution[contributionIdx+n].weight = weight;
			n++;
		}
		coverageTotal[i] = n;
	}
	
	// Use the column buffer of pixel contributions to scale the temporary buffer vertically.
	// Write the result into the output buffer.
	for ( int k = 0; k < ImagePlug::tileSize(); ++k )
	{
		for ( int i = 0, contributionIdx = 0; i < ImagePlug::tileSize(); ++i, contributionIdx += fHeight )
		{
			float intensity = 0;

			for ( int j = 0; j < coverageTotal[i]; ++j )
			{
				Contribution &contributor( contribution[ contributionIdx+j ] );

				if ( contributor.weight == 0. )
				{
					continue;
				}

				intensity += buffer[k + ImagePlug::tileSize() * contributor.pixel] * contributor.weight;
			}

			out[k + ImagePlug::tileSize() * i] = intensity / weightedSum[i];
		}
	}
   
	return outDataPtr;
}


//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/Scale.h"
#include "GafferImage/Sampler.h"

using namespace Gaffer;
using namespace IECore;
using namespace GafferImage;

IE_CORE_DEFINERUNTIMETYPED( Scale );

size_t Scale::g_firstPlugIndex = 0;

Scale::Scale( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new FilterPlug( "filter" ) );
	addChild( new V2fPlug( "scale", Gaffer::Plug::In, Imath::V2f( 1. ) ) );
	addChild( new V2fPlug( "origin", Gaffer::Plug::In, Imath::V2f( 0. ) ) );
	addChild( new BoolPlug( "scaleFormat", Gaffer::Plug::In, false ) );
}

Scale::~Scale()
{
}

GafferImage::FilterPlug *Scale::filterPlug()
{
	return getChild<GafferImage::FilterPlug>( g_firstPlugIndex );
}

const GafferImage::FilterPlug *Scale::filterPlug() const
{
	return getChild<GafferImage::FilterPlug>( g_firstPlugIndex );
}

Gaffer::V2fPlug *Scale::scalePlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex+1 );
}

const Gaffer::V2fPlug *Scale::scalePlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex+1 );
}

Gaffer::V2fPlug *Scale::originPlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex+2 );
}

const Gaffer::V2fPlug *Scale::originPlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex+2 );
}

Gaffer::BoolPlug *Scale::scaleFormatPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex+3 );
}

const Gaffer::BoolPlug *Scale::scaleFormatPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex+3 );
}

void Scale::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if( scalePlug()->isAncestorOf( input ) || originPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->dataWindowPlug() );
		outputs.push_back( outPlug()->channelDataPlug() );
	}
	else if( input == filterPlug() || input == inPlug()->channelDataPlug() )
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
	if( input == scaleFormatPlug() )
	{
		outputs.push_back( outPlug()->formatPlug() );
	}
}

bool Scale::enabled() const
{
	if( !ImageProcessor::enabled() )
	{
		return false;
	}

	Imath::V2f scale = scalePlug()->getValue();
	return scale != Imath::V2f( 1. ) && scale.x > 0. && scale.y > 0.;
}

void Scale::hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	bool scaleDisplay = scaleFormatPlug()->getValue();
	if( !scaleDisplay )
	{
		h = inPlug()->formatPlug()->hash();
		return;
	}
	
	ImageProcessor::hashFormat( output, context, h );
	h.append( inPlug()->formatPlug()->hash() );
	h.append( scalePlug()->hash() );
	h.append( originPlug()->hash() );
}

void Scale::hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashDataWindow( output, context, h );

	h.append( inPlug()->dataWindowPlug()->hash() );
	h.append( scalePlug()->hash() );
	h.append( originPlug()->hash() );
}

void Scale::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = inPlug()->channelNamesPlug()->hash();
}

void Scale::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashChannelData( output, context, h );

	h.append( inPlug()->channelDataPlug()->hash() ) ;
	h.append( scalePlug()->hash() );
	h.append( filterPlug()->hash() ); 
	h.append( inPlug()->dataWindowPlug()->hash() );
	h.append( originPlug()->hash() );
}

Imath::Box2i Scale::computeScaledBox( Imath::Box2i box ) const
{
	Imath::V2d scale( scalePlug()->getValue() );
	Imath::V2d scaleOrigin( originPlug()->getValue() );
	Imath::Box2i displayWindow( inPlug()->formatPlug()->getValue().getDisplayWindow() );

	scaleOrigin -= displayWindow.min;
	box.min -= displayWindow.min;
	box.max -= displayWindow.min;
	
	Imath::Box2i scaledBox(
		Imath::V2i(
			IECore::fastFloatFloor( ( float( box.min.x ) - scaleOrigin.x ) * scale.x + scaleOrigin.x ),
			IECore::fastFloatFloor( ( float( box.min.y ) - scaleOrigin.y ) * scale.y + scaleOrigin.y )
		),
		Imath::V2i(
			IECore::fastFloatCeil( ( float( box.max.x ) - scaleOrigin.x + 1. ) * scale.x + scaleOrigin.x ) - 1,
			IECore::fastFloatCeil( ( float( box.max.y ) - scaleOrigin.y + 1. ) * scale.y + scaleOrigin.y ) - 1
		)
	);

	scaledBox.min += displayWindow.min;
	scaledBox.max += displayWindow.min;

	return scaledBox;
}

GafferImage::Format Scale::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	bool scaleDisplay = scaleFormatPlug()->getValue();
	if( scaleDisplay )
	{
		Imath::Box2i displayWindow = inPlug()->formatPlug()->getValue().getDisplayWindow();
		return GafferImage::Format( computeScaledBox( displayWindow ) );
	}
	
	return inPlug()->formatPlug()->getValue();
}

IECore::ConstStringVectorDataPtr Scale::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return inPlug()->channelNamesPlug()->getValue();
}

Imath::Box2i Scale::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	Imath::Box2i dataWindow( inPlug()->dataWindowPlug()->getValue() );
	return computeScaledBox( dataWindow );
}

struct Contribution
{
	int pixel;
	float weight;
};

IECore::ConstFloatVectorDataPtr Scale::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	// Allocate the new tile
	FloatVectorDataPtr outDataPtr = new FloatVectorData;
	std::vector<float> &out = outDataPtr->writable();
	out.resize( ImagePlug::tileSize() * ImagePlug::tileSize() );

	// Create some useful variables...
	Imath::V2d scaleFactor( scalePlug()->getValue() );
	Imath::V2d scaleOrigin( originPlug()->getValue() );
	Imath::Box2i displayWindow( inPlug()->formatPlug()->getValue().getDisplayWindow() );
	Imath::Box2i tile( tileOrigin, Imath::V2i( tileOrigin.x + ImagePlug::tileSize() - 1, tileOrigin.y + ImagePlug::tileSize() - 1 ) );

	// Create our filter.
	FilterPtr f = Filter::create( filterPlug()->getValue(), 1.f / scaleFactor.y );
	
	// If we are filtering with a box filter then just don't bother filtering
	// at all and just integer sample instead...
	if( static_cast<GafferImage::TypeId>( f->typeId() ) == GafferImage::BoxFilterTypeId )
	{
		Imath::Box2i sampleBox(
			Imath::V2i(
				IECore::fastFloatFloor( double( tile.min.x - scaleOrigin.x ) / scaleFactor.x + scaleOrigin.x ),
				IECore::fastFloatFloor( double( tile.min.y - scaleOrigin.y ) / scaleFactor.y + scaleOrigin.y )
			),
			Imath::V2i(
				IECore::fastFloatCeil( double( tile.max.x - scaleOrigin.x + 1. ) / scaleFactor.x + scaleOrigin.x ) - 1,
				IECore::fastFloatCeil( double( tile.max.y - scaleOrigin.y + 1. ) / scaleFactor.y + scaleOrigin.y ) - 1
			)
		);

		Sampler sampler( inPlug(), channelName, sampleBox, f, Sampler::Clamp );
		for( int y = tile.min.y, ty = 0; y <= tile.max.y; ++y, ++ty )
		{
			for( int x = tile.min.x, tx = 0; x <= tile.max.x; ++x, ++tx )
			{
				out[ tx + ImagePlug::tileSize() * ty ] = sampler.sample(
					IECore::fastFloatFloor( ( x + .5f - scaleOrigin.x ) / scaleFactor.x + scaleOrigin.x ),
					IECore::fastFloatFloor( ( y + .5f - scaleOrigin.y ) / scaleFactor.y + scaleOrigin.y )
				);
			}
		}

		return outDataPtr;
	}

	// Get the dimensions of our filter and create a box that we can use to define the bounds of our input.
	int fHeight = f->width();
	
	int sampleMinY = f->tap( ( tile.min.y - scaleOrigin.y + .5 ) / scaleFactor.y + scaleOrigin.y );
	int sampleMaxY = f->tap( ( tile.max.y - scaleOrigin.y + .5 ) / scaleFactor.y + scaleOrigin.y );
		
	f->setScale( 1.f / scaleFactor.x );
	int sampleMinX = f->tap( ( tile.min.x - scaleOrigin.x + .5 ) / scaleFactor.x + scaleOrigin.x );
	int sampleMaxX = f->tap( ( tile.max.x - scaleOrigin.x + .5 ) / scaleFactor.x + scaleOrigin.x );
	
	int fWidth = f->width();

	Imath::Box2i sampleBox(
		Imath::V2i( sampleMinX, sampleMinY ),
		Imath::V2i( sampleMaxX + fWidth, sampleMaxY + fHeight )
	);

	int sampleBoxWidth = sampleBox.size().x + 1;
	int sampleBoxHeight = sampleBox.size().y + 1;
	
	// Create a temporary buffer that we can write the result of the first pass to.
	// We extend the buffer vertically as we will need additional information in the
	// vertical squash (the second pass) to properly convolve the filter.
	float buffer[ ImagePlug::tileSize() * sampleBoxHeight ];
	
	// Create several buffers for each pixel in the output row (or column depending on the pass),
	// into which we can place the indices for the pixels that contribute to it's result and
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
	for( int i = 0; i < ImagePlug::tileSize(); ++i, contributionIdx += fWidth )
	{
		float center = ( tile.min.x + i - scaleOrigin.x + 0.5 ) / scaleFactor.x + scaleOrigin.x;
		int tap = f->tap( center );
		
		int n = 0;	
		weightedSum[i] = 0.;
		for( int j = tap; j < tap+fWidth; ++j )
		{
			float weight = f->weight( center, j );
			if( weight == 0 )
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
	for( int k = 0; k < sampleBoxHeight; ++k )
	{
		for( int i = 0, contributionIdx = 0; i < ImagePlug::tileSize(); ++i, contributionIdx += fWidth )
		{
			float intensity = 0;

			for( int j = 0; j < coverageTotal[i]; ++j )
			{
				Contribution &contributor( contribution[ contributionIdx+j ] );

				if( contributor.weight == 0. )
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
	for( int i = 0, contributionIdx = 0; i < ImagePlug::tileSize(); ++i, contributionIdx += fHeight )
	{
		float center = ( tile.min.y + i - scaleOrigin.y + 0.5 ) / scaleFactor.y - sampleBox.min.y + scaleOrigin.y;
		int tap = f->tap( center );
		
		int n = 0;	
		weightedSum[i] = 0.;
		for( int j = tap; j < tap+fHeight; ++j )
		{
			float weight = f->weight( center, j );
			if( weight == 0 )
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
	for( int k = 0; k < ImagePlug::tileSize(); ++k )
	{
		for( int i = 0, contributionIdx = 0; i < ImagePlug::tileSize(); ++i, contributionIdx += fHeight )
		{
			float intensity = 0;

			for( int j = 0; j < coverageTotal[i]; ++j )
			{
				Contribution &contributor( contribution[ contributionIdx+j ] );

				if( contributor.weight == 0. )
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


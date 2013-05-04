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
#include "GafferImage/ImageTransform.h"
#include "GafferImage/Filter.h"
#include "GafferImage/FormatPlug.h"
#include "GafferImage/ImagePlug.h"
#include "GafferImage/Sampler.h"
#include "IECore/BoxAlgo.h"
#include "IECore/BoxOps.h"
#include "boost/format.hpp"
#include "boost/bind.hpp"

using namespace Gaffer;
using namespace IECore;
using namespace GafferImage;

IE_CORE_DEFINERUNTIMETYPED( ImageTransform );

size_t ImageTransform::g_firstChildIndex = 0;

ImageTransform::ImageTransform( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstChildIndex );
	
	addChild( new Gaffer::Transform2DPlug( "transform" ) );
}

ImageTransform::~ImageTransform()
{
}

Gaffer::Transform2DPlug *ImageTransform::transformPlug()
{
	return getChild<Gaffer::Transform2DPlug>( g_firstChildIndex );
}

const Gaffer::Transform2DPlug *ImageTransform::transformPlug() const
{
	return getChild<Gaffer::Transform2DPlug>( g_firstChildIndex );
}

void ImageTransform::affects( const Gaffer::ValuePlug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if ( transformPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->dataWindowPlug() );
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

bool ImageTransform::enabled() const
{
	if ( !ImageProcessor::enabled() )
	{
		return false;
	}

	//\todo: 
	// If the transform is an identity matrix then disable it.

	return true;
}

void ImageTransform::hashFormatPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Format format( inPlug()->formatPlug()->getValue() );
	h.append( format.getDisplayWindow() );
	h.append( format.getPixelAspect() );
}

void ImageTransform::hashDataWindowPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	inPlug()->dataWindowPlug()->hash( h );
	transformPlug()->hash( h );
}

void ImageTransform::hashChannelNamesPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	inPlug()->channelNamesPlug()->hash( h );
}

void ImageTransform::hashChannelDataPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	inPlug()->channelDataPlug()->hash( h );
	inPlug()->dataWindowPlug()->hash( h );
	transformPlug()->hash( h );
}

Imath::Box2i ImageTransform::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	Format inFormat( inPlug()->formatPlug()->getValue() );
	Imath::Box2i inWindow( inPlug()->dataWindowPlug()->getValue() );
	Imath::Box2i outWindow( transformBox( transformPlug()->matrix( inFormat ), inWindow ) );
	return outWindow;
}

Imath::Box2i ImageTransform::transformBox( const Imath::M33f &m, const Imath::Box2i &box ) const
{
	Imath::V3f pt[4];
	pt[0] = Imath::V3f( box.min.x, box.min.y, 1. );
	pt[1] = Imath::V3f( box.max.x+1, box.max.y+1, 1. );
	pt[2] = Imath::V3f( box.max.x+1, box.min.y, 1. );
	pt[3] = Imath::V3f( box.min.x, box.max.y+1, 1. );

	int maxX = std::numeric_limits<int>::min();
	int maxY = std::numeric_limits<int>::min();
	int minX = std::numeric_limits<int>::max();
	int minY = std::numeric_limits<int>::max();
	
	for( unsigned int i = 0; i < 4; ++i )
	{
		pt[i] = pt[i] * m;
		maxX = std::max( int( ceil( pt[i].x ) ), maxX );
		maxY = std::max( int( ceil( pt[i].y ) ), maxY );
		minX = std::min( int( floor( pt[i].x ) ), minX );
		minY = std::min( int( floor( pt[i].y ) ), minY );
	}
	
	return Imath::Box2i( Imath::V2i( minX, minY ), Imath::V2i( maxX-1, maxY-1 ) );	
}

GafferImage::Format ImageTransform::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return inPlug()->formatPlug()->getValue();
}

IECore::ConstStringVectorDataPtr ImageTransform::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return inPlug()->channelNamesPlug()->getValue();
}

IECore::ConstFloatVectorDataPtr ImageTransform::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	// Allocate the new tile
	FloatVectorDataPtr outDataPtr = new FloatVectorData;
	std::vector<float> &out = outDataPtr->writable();
	out.resize( ImagePlug::tileSize() * ImagePlug::tileSize() );

	// Work out the bounds of the tile that we are outputting to.
	Imath::Box2i tile( tileOrigin, Imath::V2i( tileOrigin.x + ImagePlug::tileSize() - 1, tileOrigin.y + ImagePlug::tileSize() - 1 ) );

	// Work out the sample area that we require to compute this tile.
	Format inputFormat = inPlug()->formatPlug()->getValue();
	Imath::M33f t( transformPlug()->matrix( inputFormat ).inverse() );
	Imath::Box2i inWindow( inPlug()->dataWindowPlug()->getValue() );
	Imath::Box2i sampleBox( transformBox( t, tile ) );
	
	Sampler sampler( inPlug(), channelName, sampleBox );
	for ( int j = 0; j < ImagePlug::tileSize(); ++j )
	{
		for ( int i = 0; i < ImagePlug::tileSize(); ++i )
		{
			Imath::V3f p( i+tile.min.x+.5, j+tile.min.y+.5, 1. );
			p *= t;
			out[ i + j*ImagePlug::tileSize() ] = sampler.sample( int(p.x), int(p.y) );
		}
	}

	return outDataPtr;
}


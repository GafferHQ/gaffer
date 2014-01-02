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

#include <cstdlib>

#include "boost/format.hpp"

#include "OpenImageIO/imagecache.h"
OIIO_NAMESPACE_USING

#include "IECore/Exception.h"

#include "GafferImageTest/ImageReaderTest.h"

/// Test whether a bug in OIIO is present or not to prove that the issue is not in our code.
/// It appears that the get_pixels function in OIIO does not correctly convert JPG images
/// to Float when using the overloaded version that allows a specific channel to be specified.
/// It does work however when we use the version that returns all of the channels and we manually
/// extract the one we want.
///
/// This Version of get_pixels works :
///
/// virtual bool get_pixels( ustring filename, int subimage, int miplevel,
///                          int xbegin, int xend, int ybegin, int yend,
///                          int zbegin, int zend,
///                          TypeDesc format, void *result);
///
/// This version does not work :
///
/// virtual bool get_pixels( ustring filename,
///                          int subimage, int miplevel, int xbegin, int xend,
///                          int ybegin, int yend, int zbegin, int zend,
///                          int chbegin, int chend, TypeDesc format, void *result,
///                          stride_t xstride=AutoStride, stride_t ystride=AutoStride,
///                          stride_t zstride=AutoStride);
///
/// As an example, the code below reads in a simple JPG image using the two different
/// get_pixels methods and compares the channels to assert that they are equal.
/// What we find instead is that the Red channels are the same, the Green channel is
/// shifted to the left by a single pixel and the Blue channel is shifted to the
/// left by two pixels.
void compareOIIOGetPixelFunctions( std::string fileName )
{
	ustring uFileName( fileName.c_str() );

	ImageCache *cache = ImageCache::create();
	cache->attribute( "max_memory_MB", 500.0 );
	cache->attribute( "autotile", 64 );
	const ImageSpec *spec = cache->imagespec( uFileName );

	int width = spec->width;	
	int height = spec->height;

	// Get all of the available channels so that we can compare the result
	// of this get_pixels call to the one below that only retrieves a single channel
	// at a time.
	int numberOfChannels = spec->channelnames.size();	
	std::vector<float> channelDataRGB( width * height * numberOfChannels );
	cache->get_pixels(
		uFileName,
		0, 0,
		0, width,
		0, height, 
		0, 1,
		TypeDesc::FLOAT,
		&(channelDataRGB[0])
	);
	
	// Get the pixels of each channel and compare it to the result that
	// we retrieved using the other get_pixels call above.	
	for( int channelIndex = 0; channelIndex < numberOfChannels; ++channelIndex )
	{
		std::vector<float> channelData( width * height );
		cache->get_pixels(
				uFileName,
				0, 0,
				0, width,
				0, height, 
				0, 1,
				channelIndex, channelIndex + 1,
				TypeDesc::FLOAT,
				&(channelData[0])
		);

		// Compare every pixel in the channel that we just extracted against the same
		// channel which we acquired using the other get_pixels call.
		for( int i = channelIndex, j = 0; i < width * height * numberOfChannels; i += numberOfChannels, ++j )
		{
			if( channelData[j] != channelDataRGB[i] )
			{
				throw IECore::Exception( boost::str( boost::format( "Comparison of the two OIIO::get_pixels methods failed on channel %s." ) % spec->channelnames[ channelIndex ] ) );
			}
		}
	}
}

void GafferImageTest::testOIIOJpgRead()
{
	const char *root = std::getenv( "GAFFER_ROOT" );
	if( root )
	{
		std::string fileName = boost::str( boost::format( "%s/python/GafferTest/images/circles.jpg" ) % std::string( root ) );
		compareOIIOGetPixelFunctions( fileName );
	}
	else
	{
		throw IECore::Exception( "Failed to find $GAFFER_ROOT env. Has it been set?" );
	}
}

void GafferImageTest::testOIIOExrRead()
{
	const char *root = std::getenv( "GAFFER_ROOT" );
	if( root )
	{
		std::string fileName = boost::str( boost::format( "%s/python/GafferTest/images/circles.exr" ) % std::string( root ) );
		compareOIIOGetPixelFunctions( fileName );
	}
	else
	{
		throw IECore::Exception( "Failed to find $GAFFER_ROOT env. Has it been set?" );
	}
}


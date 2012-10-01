//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "OpenImageIO/imagecache.h"
OIIO_NAMESPACE_USING

#include "GafferImage/ImageReader.h"

using namespace std;
using namespace tbb;
using namespace Imath;
using namespace IECore;
using namespace GafferImage;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// We use an OIIO image cache to deal with all file loading etc. This works
// well for us, as due to the Gaffer architecture we'll be receiving many
// different calls on different threads, each potentially asking for different
// files (expressions and timewarps etc can change the fileName at any time).
// The OIIO image cache is designed for exactly this scenario.
//////////////////////////////////////////////////////////////////////////

spin_rw_mutex g_imageCacheMutex;
static ImageCache *imageCache()
{
	spin_rw_mutex::scoped_lock lock( g_imageCacheMutex, false );
	static ImageCache *cache = 0;
	if( cache == 0 )
	{
		if( lock.upgrade_to_writer() )
		{
			cache = ImageCache::create();
		}
	}
	return cache;
}

//////////////////////////////////////////////////////////////////////////
// ImageReader implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( ImageReader );

ImageReader::ImageReader( const std::string &name )
	:	ImageNode( name )
{
	addChild( new StringPlug( "fileName" ) );
	
	// disable caching on our outputs, as OIIO is already doing caching for us.
	for( OutputPlugIterator it( outPlug() ); it!=it.end(); it++ )
	{
		(*it)->setFlags( Plug::Cacheable, false );
	}
}

ImageReader::~ImageReader()
{
}

Gaffer::StringPlug *ImageReader::fileNamePlug()
{
	return getChild<StringPlug>( "fileName" );
}

const Gaffer::StringPlug *ImageReader::fileNamePlug() const
{
	return getChild<StringPlug>( "fileName" );
}

void ImageReader::affects( const Gaffer::ValuePlug *input, AffectedPlugsContainer &outputs ) const
{
	ImageNode::affects( input, outputs );

	if( input==fileNamePlug() )
	{
		outputs.push_back( outPlug() );
	}
}

void ImageReader::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hash( output, context, h );
	fileNamePlug()->hash( h );
}

Imath::Box2i ImageReader::computeDisplayWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::string fileName = fileNamePlug()->getValue();
	const ImageSpec *spec = imageCache()->imagespec( ustring( fileName.c_str() ) );
	if( !spec )
	{
		return Box2i();
	}
	
	return Box2i(
		V2i( spec->full_x, spec->full_y ),
		V2i( spec->full_x + spec->full_width - 1, spec->full_x + spec->full_height - 1 )
	);
}

Imath::Box2i ImageReader::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::string fileName = fileNamePlug()->getValue();
	const ImageSpec *spec = imageCache()->imagespec( ustring( fileName.c_str() ) );
	if( !spec )
	{
		return Box2i();
	}
	
	return Box2i(
		V2i( spec->x, spec->y ),
		V2i( spec->x + spec->width - 1, spec->x + spec->height - 1 )
	);
}

IECore::ConstStringVectorDataPtr ImageReader::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::string fileName = fileNamePlug()->getValue();
	const ImageSpec *spec = imageCache()->imagespec( ustring( fileName.c_str() ) );
	if( !spec )
	{
		return parent->channelNamesPlug()->defaultValue();
	}
	
	StringVectorDataPtr result = new StringVectorData();
	result->writable() = spec->channelnames;
	return result;
}

IECore::ConstFloatVectorDataPtr ImageReader::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::string fileName = fileNamePlug()->getValue();
	ustring uFileName( fileName.c_str() );
	
	const ImageSpec *spec = imageCache()->imagespec( uFileName );
	if( !spec )
	{
		return parent->channelDataPlug()->defaultValue();
	}
	
	vector<string>::const_iterator channelIt = find( spec->channelnames.begin(), spec->channelnames.end(), channelName );
	if( channelIt == spec->channelnames.end() )
	{
		return parent->channelDataPlug()->defaultValue();
	}
	
	std::vector<float> interleaved;
	interleaved.resize( ImagePlug::tileSize() * ImagePlug::tileSize() * spec->channelnames.size() );
	imageCache()->get_pixels(
		uFileName,
		0, 0, // subimage, miplevel
		tileOrigin.x, tileOrigin.x + ImagePlug::tileSize(),
		tileOrigin.y, tileOrigin.y + ImagePlug::tileSize(),
		0, 1,
		TypeDesc::FLOAT,
		&(interleaved[0])
	);
	
	// extract just the channel we want.
	/// \todo See about getting a version of get_pixels() that just loads a single channel.
	FloatVectorDataPtr resultData = new FloatVectorData;
	vector<float> &result = resultData->writable();
	result.resize( ImagePlug::tileSize() * ImagePlug::tileSize() );
	size_t srcIndex = channelIt - spec->channelnames.begin();
	size_t srcStep = spec->channelnames.size();
	size_t dstIndex = 0;
	for( int i=0; i<ImagePlug::tileSize() * ImagePlug::tileSize(); i++ )
	{
		result[dstIndex++] = interleaved[srcIndex];
		srcIndex += srcStep;
	}
	
	return resultData;
}

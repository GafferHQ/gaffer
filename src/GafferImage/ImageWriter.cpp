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

#include "OpenImageIO/imagecache.h"
OIIO_NAMESPACE_USING

#include "boost/format.hpp"
#include "GafferImage/ImagePlug.h"
#include "GafferImage/ImageWriter.h"
#include "Gaffer/Context.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace GafferImage;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// ImageWriter implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( ImageWriter );

size_t ImageWriter::g_firstPlugIndex = 0;

ImageWriter::ImageWriter( const std::string &name )
	:	Gaffer::ExecutableNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ImagePlug( "in" ) );
	addChild( new StringPlug( "fileName" ) );
}

ImageWriter::~ImageWriter()
{
}

GafferImage::ImagePlug *ImageWriter::inPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

const GafferImage::ImagePlug *ImageWriter::inPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *ImageWriter::fileNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex+1 );
}

const Gaffer::StringPlug *ImageWriter::fileNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex+1 );
}

void ImageWriter::executionRequirements( const Context *context, Tasks &requirements ) const
{
	Executable::defaultRequirements( this, context, requirements );
}
		
IECore::MurmurHash ImageWriter::executionHash( const Context *context ) const
{
	IECore::MurmurHash h = fileNamePlug()->hash();
	h.append( inPlug()->imageHash() );
	return h;
}

///\todo: We need to add additional meta data to the output image.
///\todo: Add support for scanlines, tiles and display windows.
void ImageWriter::execute( const Contexts &contexts ) const
{
	if( !inPlug()->getInput<ImagePlug>() )
	{
		throw IECore::Exception( "No input image." );
		return;
	}

	// Loop over the execution contexts...
	for( Contexts::const_iterator it = contexts.begin(), eIt = contexts.end(); it != eIt; it++ )
	{
		Context::Scope scopedContext( it->get() );
		
		std::string fileName = fileNamePlug()->getValue();
		fileName = (*it)->substitute( fileName );
		
		ImageOutput *out = ImageOutput::create( fileName.c_str() );
		if (!out)
		{
			throw IECore::Exception( boost::str( boost::format( "Invalid filename: %s" ) % fileName ) );
			return;
		}
		
		// Get the image channel data.
		IECore::ImagePrimitivePtr imagePtr( inPlug()->image() );

		// Get the image's display window.
		const Imath::Box2i displayWindow( imagePtr->getDisplayWindow() );
		//const int displayWindowWidth = displayWindow.max.x-displayWindow.min.x+1;
		//const int displayWindowHeight = displayWindow.max.y-displayWindow.min.y+1;
	
		// Get the image's data window.
		const Imath::Box2i dataWindow( imagePtr->getDataWindow() );
		const int dataWindowWidth = dataWindow.max.x-dataWindow.min.x+1;
		const int dataWindowHeight = dataWindow.max.y-dataWindow.min.y+1;
		
		// Get the image's channel names.
		std::vector<std::string> channelNames;
		imagePtr->channelNames( channelNames );
		const int nChannels = channelNames.size();
		
		// Create a buffer for the pixels.
		float *pixels = new float [ nChannels*dataWindowWidth*dataWindowHeight ];
		
		// Create the image header. 
		ImageSpec spec( dataWindowWidth, dataWindowHeight, nChannels, TypeDesc::FLOAT );
		
		// Add the channel names to the header whilst getting pointers to the channel data. 
		std::vector<const float*> channelPtrs;
		spec.channelnames.clear();
		for ( std::vector<std::string>::iterator channelIt( channelNames.begin() ); channelIt != channelNames.end(); channelIt++ )
		{
			spec.channelnames.push_back( *channelIt );
			IECore::FloatVectorDataPtr dataPtr = imagePtr->getChannel<float>( *channelIt );
			channelPtrs.push_back( &(dataPtr->readable()[0]) );

			// OIIO has a special attribute for the Alpha and Z channels. If we find some, we should tag them...
			if ( *channelIt == "A" )
			{
				spec.alpha_channel = channelIt-channelNames.begin();
			} else if ( *channelIt == "Z" )
			{
				spec.z_channel = channelIt-channelNames.begin();
			}
		}
		
		// Interleave the channel data.	
		float *outPtr = &pixels[0];	
		for ( int y = 0; y < dataWindowHeight; ++y )
		{
			for ( int x = 0; x < dataWindowWidth; ++x )
			{
				for ( std::vector<const float *>::iterator channelDataIt( channelPtrs.begin() ); channelDataIt != channelPtrs.end(); channelDataIt++ )
				{
					*outPtr++ = *(*channelDataIt)++;
				}
			}
		}
		
		out->open( fileName, spec );
		out->write_image( TypeDesc::FLOAT, pixels );
		out->close();
		delete out;
		delete [] pixels;
	}
}


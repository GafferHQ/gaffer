//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/ImageProcessor.h"
#include "Gaffer/Context.h"

using namespace Gaffer;
using namespace GafferImage;

IE_CORE_DEFINERUNTIMETYPED( ImageProcessor );

size_t ImageProcessor::g_firstPlugIndex = 0;

ImageProcessor::ImageProcessor( const std::string &name )
	:	ImageNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );	
	addChild( new ImagePlug( "in", Gaffer::Plug::In ) );
}

ImageProcessor::~ImageProcessor()
{
}

ImagePlug *ImageProcessor::inPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

const ImagePlug *ImageProcessor::inPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

void ImageProcessor::hashDisplayWindowPlug( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h.append( inPlug()->displayWindowPlug()->hash() );
}

void ImageProcessor::hashDataWindowPlug( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h.append( inPlug()->dataWindowPlug()->hash() );
}

void ImageProcessor::hashChannelDataPlug( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h.append( inPlug()->channelDataPlug()->hash() );
}

void ImageProcessor::hashChannelNamesPlug( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h.append( inPlug()->channelNamesPlug()->hash() );
}

void ImageProcessor::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	DependencyNode::hash( output, context, h );
	h.append( enabledPlug()->hash() );
	
	if ( enabled() )
	{
		if( output == outPlug()->channelDataPlug() )
		{
			hashChannelDataPlug( context, h );
			h.append( context->get<std::string>( ImagePlug::channelNameContextName ) );
			h.append( context->get<Imath::V2i>( ImagePlug::tileOriginContextName ) );
		}
		else if ( output == outPlug()->displayWindowPlug() )
		{
			hashDisplayWindowPlug( context, h );
		}
		else if ( output == outPlug()->dataWindowPlug() )
		{
			hashDataWindowPlug( context, h );
		}
		else if ( output == outPlug()->channelNamesPlug() )
		{
			hashChannelNamesPlug( context, h );
		}
	}
	else
	{
		if( output == outPlug()->channelDataPlug() )
		{
			h = inPlug()->channelDataPlug()->hash();
		}
		else if ( output == outPlug()->displayWindowPlug() )
		{
			h = inPlug()->displayWindowPlug()->hash();
		}
		else if ( output == outPlug()->dataWindowPlug() )
		{
			h = inPlug()->dataWindowPlug()->hash();
		}
		else if ( output == outPlug()->channelNamesPlug() )
		{
			h = inPlug()->channelNamesPlug()->hash();
		}
	}
}

void ImageProcessor::compute( ValuePlug *output, const Context *context ) const
{
	ImagePlug *imagePlug = output->ancestor<ImagePlug>();
	if (imagePlug)
	{
		if( enabled() )
		{
			computeImagePlugs( output, context );
		}
		else
		{
			if( output == imagePlug->displayWindowPlug() )
			{
				static_cast<AtomicBox2iPlug *>( output )->setValue(
					inPlug()->displayWindowPlug()->getValue()
				);
			}
			else if( output == imagePlug->dataWindowPlug() )
			{
				static_cast<AtomicBox2iPlug *>( output )->setValue(
					inPlug()->dataWindowPlug()->getValue()
				);
			}
			else if( output == imagePlug->channelNamesPlug() )
			{
				static_cast<StringVectorDataPlug *>( output )->setValue(
					inPlug()->channelNamesPlug()->getValue()
				);
			}
			else if( output == imagePlug->channelDataPlug() )
			{
				static_cast<FloatVectorDataPlug *>( output )->setValue(
					inPlug()->channelDataPlug()->getValue()
				);
			}
		}
	}
}

//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

Plug *ImageProcessor::correspondingInput( const Plug *output )
{
	if ( output == outPlug() )
	{
		return inPlug();
	}
	
	return ImageNode::correspondingInput( output );
}

const Plug *ImageProcessor::correspondingInput( const Plug *output ) const
{
	if ( output == outPlug() )
	{
		return inPlug();
	}
	
	return ImageNode::correspondingInput( output );
}

void ImageProcessor::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	/// \todo Can this be simplified using the same logic used in SceneProcessor::hash()? It would
	/// avoid calling ComputeNode::hash only to overwrite the hash if we're disabled.
	ComputeNode::hash( output, context, h );
	
	/// \todo Should this not be done only if we're computing an ImagePlug output?
	/// and doesn't the fact that we call enabled() below mean that we're already
	/// hashing in the effect of the enabled plug anyway?
	h.append( enabledPlug()->hash() );

	const ImagePlug *imagePlug = output->parent<ImagePlug>();
	if ( imagePlug == 0 )
	{
		return;
	} 
	
	if ( enabled() )
	{
		if( output == imagePlug->channelDataPlug() )
		{
			const std::string &channel = context->get<std::string>( ImagePlug::channelNameContextName );
			if ( channelEnabled( channel ) )
			{
				hashChannelDataPlug( imagePlug, context, h );
				h.append( context->get<std::string>( ImagePlug::channelNameContextName ) );
				h.append( context->get<Imath::V2i>( ImagePlug::tileOriginContextName ) );
			}
			else
			{
				h = inPlug()->channelDataPlug()->hash();
			}
		}
		else if ( output == imagePlug->formatPlug() )
		{
			hashFormatPlug( imagePlug, context, h );
		}
		else if ( output == imagePlug->dataWindowPlug() )
		{
			hashDataWindowPlug( imagePlug, context, h );
		}
		else if ( output == imagePlug->channelNamesPlug() )
		{
			hashChannelNamesPlug( imagePlug, context, h );
		}
	}
	else
	{
		if( output == imagePlug->channelDataPlug() )
		{
			h = inPlug()->channelDataPlug()->hash();
		}
		else if ( output == imagePlug->formatPlug() )
		{
			h = inPlug()->formatPlug()->hash();
		}
		else if ( output == imagePlug->dataWindowPlug() )
		{
			h = inPlug()->dataWindowPlug()->hash();
		}
		else if ( output == imagePlug->channelNamesPlug() )
		{
			h = inPlug()->channelNamesPlug()->hash();
		}
	}
}

void ImageProcessor::compute( ValuePlug *output, const Context *context ) const
{
	/// \todo Can this be simplified using the same logic used in SceneProcessor::compute()?
	/// It would remove the need for the computeImagePlugs() method.
	ImagePlug *imagePlug = output->ancestor<ImagePlug>();
	if ( imagePlug )
	{
		if( enabled() )
		{
			if( output == imagePlug->channelDataPlug() )
			{
				const std::string &channel = context->get<std::string>( ImagePlug::channelNameContextName );
				if ( channelEnabled( channel ) )
				{
					computeImagePlugs( output, context );
				}
				else
				{
					static_cast<FloatVectorDataPlug *>( output )->setValue(
						inPlug()->channelDataPlug()->getValue()
					);
				}
			}
			else
			{
				computeImagePlugs( output, context );
			}
		}
		else
		{
			if( output == imagePlug->formatPlug() )
			{
				static_cast<FormatPlug *>( output )->setValue(
					inPlug()->formatPlug()->getValue()
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

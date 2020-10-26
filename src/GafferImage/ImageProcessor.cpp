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

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Context.h"

using namespace Gaffer;
using namespace GafferImage;

GAFFER_NODE_DEFINE_TYPE( ImageProcessor );

size_t ImageProcessor::g_firstPlugIndex = 0;

ImageProcessor::ImageProcessor( const std::string &name )
	:	ImageNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ImagePlug( "in", Gaffer::Plug::In ) );
}

ImageProcessor::ImageProcessor( const std::string &name, size_t minInputs, size_t maxInputs )
	:	ImageNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild(
		new ArrayPlug( "in", Gaffer::Plug::In, new ImagePlug( "in0" ), minInputs, maxInputs )
	);
}

ImageProcessor::~ImageProcessor()
{
}

ImagePlug *ImageProcessor::inPlug()
{
	GraphComponent *p = getChild( g_firstPlugIndex );
	if( ImagePlug *i = IECore::runTimeCast<ImagePlug>( p ) )
	{
		return i;
	}
	else
	{
		return static_cast<ArrayPlug *>( p )->getChild<ImagePlug>( 0 );
	}
}

const ImagePlug *ImageProcessor::inPlug() const
{
	const GraphComponent *p = getChild( g_firstPlugIndex );
	if( const ImagePlug *i = IECore::runTimeCast<const ImagePlug>( p ) )
	{
		return i;
	}
	else
	{
		return static_cast<const ArrayPlug *>( p )->getChild<ImagePlug>( 0 );
	}
}

Gaffer::ArrayPlug *ImageProcessor::inPlugs()
{
	return getChild<Gaffer::ArrayPlug>( g_firstPlugIndex );
}

const Gaffer::ArrayPlug *ImageProcessor::inPlugs() const
{
	return getChild<Gaffer::ArrayPlug>( g_firstPlugIndex );
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
	const ImagePlug *imagePlug = output->parent<ImagePlug>();
	if( !imagePlug )
	{
		ImageNode::hash( output, context, h );
		return;
	}

	// we're computing a component of the output image. if we're disabled,
	// then we wish to pass through the hash from the input.
	bool passThrough;
	{
		ImagePlug::GlobalScope c( context );
		passThrough = !enabled();
	}
	if( !passThrough )
	{
		// even if we're enabled at the image level, the channel might be disabled
		// at the channelData level.
		if( output == imagePlug->channelDataPlug() )
		{
			const std::string &channel = context->get<std::string>( ImagePlug::channelNameContextName );
			passThrough = !channelEnabled( channel );
		}
	}

	if( passThrough )
	{
		h = inPlug()->getChild<ValuePlug>( output->getName() )->hash();
	}
	else
	{
		// normal operation - just let the base class take care of it.
		ImageNode::hash( output, context, h );
	}
}

void ImageProcessor::compute( ValuePlug *output, const Context *context ) const
{
	const ImagePlug *imagePlug = output->parent<ImagePlug>();
	if( !imagePlug )
	{
		ImageNode::compute( output, context );
		return;
	}

	bool passThrough;
	{
		ImagePlug::GlobalScope c( context );
		passThrough = !enabled();
	}
	if( !passThrough )
	{
		// even if we're enabled at the image level, the channel might be disabled
		// at the channelData level.
		if( output == imagePlug->channelDataPlug() )
		{
			const std::string &channel = context->get<std::string>( ImagePlug::channelNameContextName );
			passThrough = !channelEnabled( channel );
		}
	}

	if( passThrough )
	{
		output->setFrom( inPlug()->getChild<ValuePlug>( output->getName() ) );
	}
	else
	{
		// normal operation - just let the base class take care of it.
		ImageNode::compute( output, context );
	}
}

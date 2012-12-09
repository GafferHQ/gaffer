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

#include "Gaffer/Context.h"

#include "GafferImage/ImageNode.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace GafferImage;
using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( ImageNode );

ImageNode::ImageNode( const std::string &name )
	:	DependencyNode( name )
{
	addChild( new ImagePlug( "out", Gaffer::Plug::Out ) );
}

ImageNode::~ImageNode()
{
}

ImagePlug *ImageNode::outPlug()
{
	return getChild<ImagePlug>( "out" );
}

const ImagePlug *ImageNode::outPlug() const
{
	return getChild<ImagePlug>( "out" );
}

void ImageNode::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	DependencyNode::hash( output, context, h );
	if( output == outPlug()->channelDataPlug() )
	{
		h.append( context->get<string>( ImagePlug::channelNameContextName ) );
		h.append( context->get<V2i>( ImagePlug::tileOriginContextName ) );		
	}
}
				
void ImageNode::compute( ValuePlug *output, const Context *context ) const
{
	ImagePlug *imagePlug = output->ancestor<ImagePlug>();
	if( imagePlug )
	{
		if( output == imagePlug->displayWindowPlug() )
		{
			static_cast<AtomicBox2iPlug *>( output )->setValue(
				computeDisplayWindow( context, imagePlug )
			);
		}
		else if( output == imagePlug->dataWindowPlug() )
		{
			static_cast<AtomicBox2iPlug *>( output )->setValue(
				computeDataWindow( context, imagePlug )
			);
		}
		else if( output == imagePlug->channelNamesPlug() )
		{
			static_cast<StringVectorDataPlug *>( output )->setValue(
				computeChannelNames( context, imagePlug )
			);
		}
		else if( output == imagePlug->channelDataPlug() )
		{
			std::string channelName = context->get<string>( ImagePlug::channelNameContextName );
			V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
			if( tileOrigin.x % ImagePlug::tileSize() || tileOrigin.y % ImagePlug::tileSize() )
			{
				throw Exception( "The image:tileOrigin must be a multiple of ImagePlug::tileSize()" );
			}
			static_cast<FloatVectorDataPlug *>( output )->setValue(
				computeChannelData( channelName, tileOrigin, context, imagePlug )
			);
		}
	}
}


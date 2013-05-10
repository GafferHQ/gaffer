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

#include "Gaffer/Context.h"

#include "GafferImage/ImageNode.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace GafferImage;
using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( ImageNode );

size_t ImageNode::g_firstPlugIndex = 0;

ImageNode::ImageNode( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ImagePlug( "out", Gaffer::Plug::Out ) );
	addChild( new BoolPlug( "enabled", Gaffer::Plug::In, true ) );
}

ImageNode::~ImageNode()
{
}

ImagePlug *ImageNode::outPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

const ImagePlug *ImageNode::outPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

BoolPlug *ImageNode::enabledPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

const BoolPlug *ImageNode::enabledPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

bool ImageNode::enabled() const
{
	return enabledPlug()->getValue();
};

void ImageNode::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( output, context, h );
	
	const ImagePlug *imagePlug = output->ancestor<ImagePlug>();
	if( imagePlug )
	{
		/// \todo Perhaps we don't need to hash enabledPlug() because enabled() will
		/// compute its value anyway?
		h.append( enabledPlug()->hash() );
		
		if( enabled() )
		{
			if( output == imagePlug->channelDataPlug() )
			{
				const std::string &channel = context->get<std::string>( ImagePlug::channelNameContextName );
				if ( channelEnabled( channel ) )
				{
					h.append( context->get<string>( ImagePlug::channelNameContextName ) );
					hashChannelDataPlug( imagePlug, context, h );
				}
			}
			else if( output == imagePlug->formatPlug() )
			{
				hashFormatPlug( imagePlug, context, h );
			}
			else if( output == imagePlug->dataWindowPlug() )
			{
				hashDataWindowPlug( imagePlug, context, h );
			}
			else if( output == imagePlug->channelNamesPlug() )
			{
				hashChannelNamesPlug( imagePlug, context, h );
			}
		}
	}
}

void ImageNode::parentChanging( Gaffer::GraphComponent *newParent )
{
	// Initialise the default format and setup any format knobs that are on this node.
	if( newParent )
	{
		if ( static_cast<Gaffer::TypeId>(newParent->typeId()) == ScriptNodeTypeId )
		{
			ScriptNode *scriptNode =  static_cast<Gaffer::ScriptNode*>( newParent );
			Format::addDefaultFormatPlug( scriptNode );
		}
	}
	
	ComputeNode::parentChanging( newParent );
}

void ImageNode::computeImagePlugs( ValuePlug *output, const Context *context ) const
{
	ImagePlug *imagePlug = output->ancestor<ImagePlug>();
	if( output == imagePlug->formatPlug() )
	{
		static_cast<FormatPlug *>( output )->setValue(
			computeFormat( context, imagePlug )
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

void ImageNode::compute( ValuePlug *output, const Context *context ) const
{
	ImagePlug *imagePlug = output->ancestor<ImagePlug>();
	if( imagePlug )
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
						imagePlug->channelDataPlug()->defaultValue()
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
					imagePlug->formatPlug()->defaultValue()
				);
			}
			else if( output == imagePlug->dataWindowPlug() )
			{
				static_cast<AtomicBox2iPlug *>( output )->setValue(
					imagePlug->dataWindowPlug()->defaultValue()
				);
			}
			else if( output == imagePlug->channelNamesPlug() )
			{
				static_cast<StringVectorDataPlug *>( output )->setValue(
					imagePlug->channelNamesPlug()->defaultValue()
				);
			}
			else if( output == imagePlug->channelDataPlug() )
			{
				static_cast<FloatVectorDataPlug *>( output )->setValue(
					imagePlug->channelDataPlug()->defaultValue()
				);
			}
		}
	}
}

void ImageNode::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );
	
	if( input == enabledPlug() )
	{
		for( ValuePlugIterator it( outPlug() ); it != it.end(); it++ )
		{
			outputs.push_back( it->get() );
		}
	}
}

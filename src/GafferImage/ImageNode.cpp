//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2012-2015, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/ImageNode.h"

#include "GafferImage/FormatPlug.h"

#include "Gaffer/Context.h"
#include "Gaffer/ScriptNode.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace GafferImage;
using namespace Gaffer;

GAFFER_NODE_DEFINE_TYPE( ImageNode );

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
	const ImagePlug *imagePlug = output->parent<ImagePlug>();
	bool enabledValue;
	{
		ImagePlug::GlobalScope c( context );
		enabledValue = enabled();
	}
	if( imagePlug && enabledValue )
	{
		// We don't call ComputeNode::hash() immediately here, because for subclasses which
		// want to pass through a specific hash in the hash*() methods it's a waste of time (the
		// hash will get overwritten anyway). Instead we call ComputeNode::hash() in our
		// hash*() implementations, and allow subclass implementations to not call the base class
		// if they intend to overwrite the hash.
		if( output == imagePlug->channelDataPlug() )
		{
			const std::string &channel = context->get<std::string>( ImagePlug::channelNameContextName );
			if( channelEnabled( channel ) )
			{
				hashChannelData( imagePlug, context, h );
			}
			else
			{
				ComputeNode::hash( output, context, h );
			}
		}
		else if( output == imagePlug->formatPlug() )
		{
			hashFormat( imagePlug, context, h );
		}
		else if( output == imagePlug->dataWindowPlug() )
		{
			hashDataWindow( imagePlug, context, h );
		}
		else if( output == imagePlug->metadataPlug() )
		{
			hashMetadata( imagePlug, context, h );
		}
		else if( output == imagePlug->deepPlug() )
		{
			hashDeep( imagePlug, context, h );
		}
		else if( output == imagePlug->sampleOffsetsPlug() )
		{
			hashSampleOffsets( imagePlug, context, h );
		}
		else if( output == imagePlug->channelNamesPlug() )
		{
			hashChannelNames( imagePlug, context, h );
		}
	}
	else
	{
		ComputeNode::hash( output, context, h );
	}
}

void ImageNode::hashFormat( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( parent->formatPlug(), context, h );
}

void ImageNode::hashDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( parent->dataWindowPlug(), context, h );
}

void ImageNode::hashMetadata( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( parent->metadataPlug(), context, h );
}

void ImageNode::hashDeep( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( parent->deepPlug(), context, h );
}

void ImageNode::hashSampleOffsets( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( parent->sampleOffsetsPlug(), context, h );
}

void ImageNode::hashChannelNames( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( parent->channelNamesPlug(), context, h );
}

void ImageNode::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( parent->channelDataPlug(), context, h );
}

void ImageNode::compute( ValuePlug *output, const Context *context ) const
{
	ImagePlug *imagePlug = output->parent<ImagePlug>();
	if( !imagePlug )
	{
		ComputeNode::compute( output, context );
		return;
	}

	// we're computing part of an ImagePlug

	bool enabledValue;
	{
		ImagePlug::GlobalScope c( context );
		enabledValue = enabled();
	}

	if( !enabledValue )
	{
		// disabled nodes just output a default black image.
		output->setToDefault();
		return;
	}

	// node is enabled - defer to our derived classes to perform the appropriate computation

	if( output == imagePlug->formatPlug() )
	{
		static_cast<AtomicFormatPlug *>( output )->setValue(
			computeFormat( context, imagePlug )
		);
	}
	else if( output == imagePlug->dataWindowPlug() )
	{
		static_cast<AtomicBox2iPlug *>( output )->setValue(
			computeDataWindow( context, imagePlug )
		);
	}
	else if( output == imagePlug->metadataPlug() )
	{
		static_cast<AtomicCompoundDataPlug *>( output )->setValue(
			computeMetadata( context, imagePlug )
		);
	}
	else if( output == imagePlug->deepPlug() )
	{
		static_cast<BoolPlug *>( output )->setValue(
			computeDeep( context, imagePlug )
		);
	}
	else if( output == imagePlug->sampleOffsetsPlug() )
	{
		V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
		if( tileOrigin.x % ImagePlug::tileSize() || tileOrigin.y % ImagePlug::tileSize() )
		{
			throw Exception( "The image:tileOrigin must be a multiple of ImagePlug::tileSize()" );
		}
		static_cast<IntVectorDataPlug *>( output )->setValue(
			computeSampleOffsets( tileOrigin, context, imagePlug )
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
		if( channelEnabled( channelName ) )
		{
			V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
			if( tileOrigin.x % ImagePlug::tileSize() || tileOrigin.y % ImagePlug::tileSize() )
			{
				throw Exception( "The image:tileOrigin must be a multiple of ImagePlug::tileSize()" );
			}
			static_cast<FloatVectorDataPlug *>( output )->setValue(
				computeChannelData( channelName, tileOrigin, context, imagePlug )
			);
		}
		else
		{
			output->setToDefault();
		}
	}
}

GafferImage::Format ImageNode::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	throw IECore::NotImplementedException( string( typeName() ) + "::computeFormat" );
}

Imath::Box2i ImageNode::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	throw IECore::NotImplementedException( string( typeName() ) + "::computeDataWindow" );
}

IECore::ConstCompoundDataPtr ImageNode::computeMetadata( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	throw IECore::NotImplementedException( string( typeName() ) + "::computeMetadata" );
}

bool ImageNode::computeDeep( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	throw IECore::NotImplementedException( string( typeName() ) + "::computeDeep" );
}

IECore::ConstIntVectorDataPtr ImageNode::computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	throw IECore::NotImplementedException( string( typeName() ) + "::computeSampleOffsets" );
}

IECore::ConstStringVectorDataPtr ImageNode::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	throw IECore::NotImplementedException( string( typeName() ) + "::computeChannelNames" );
}

IECore::ConstFloatVectorDataPtr ImageNode::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	throw IECore::NotImplementedException( string( typeName() ) + "::computeChannelData" );
}

void ImageNode::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if( input == enabledPlug() )
	{
		for( ValuePlugIterator it( outPlug() ); !it.done(); ++it )
		{
			if( (*it)->getInput() )
			{
				// If the output gets its value from an input connection.
				// there will be no compute for it, so we shouldn't declare
				// a dependency.
				continue;
			}
			outputs.push_back( it->get() );
		}
	}
}

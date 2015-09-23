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

#include "GafferImage/FlatImageProcessor.h"

using namespace Gaffer;
using namespace GafferImage;

IE_CORE_DEFINERUNTIMETYPED( FlatImageProcessor );

FlatImageProcessor::FlatImageProcessor( const std::string &name )
	:	ImageProcessor( name )
{
	// We don't ever want to change these, so we make pass-through connections.
	outPlug()->sampleOffsetsPlug()->setInput( inPlug()->sampleOffsetsPlug() );
	outPlug()->deepStatePlug()->setInput( inPlug()->deepStatePlug() );
}

FlatImageProcessor::FlatImageProcessor( const std::string &name, size_t minInputs, size_t maxInputs )
	:	ImageProcessor( name, minInputs, maxInputs )
{
	// We don't ever want to change these, so we make pass-through connections.
	outPlug()->sampleOffsetsPlug()->setInput( inPlug()->sampleOffsetsPlug() );
	outPlug()->deepStatePlug()->setInput( inPlug()->deepStatePlug() );
}

FlatImageProcessor::~FlatImageProcessor()
{
}

bool FlatImageProcessor::inputsAreFlat() const
{
	return inPlug()->deepStatePlug()->getValue() == ImagePlug::Flat;
}

void FlatImageProcessor::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if( input == inPlug()->deepStatePlug() )
	{
		outputs.push_back( outPlug()->formatPlug() );
		outputs.push_back( outPlug()->dataWindowPlug() );
		outputs.push_back( outPlug()->metadataPlug() );
		outputs.push_back( outPlug()->channelNamesPlug() );
		outputs.push_back( outPlug()->channelDataPlug() );
	}
	else if ( input->parent<ImagePlug>() == inPlug() )
	{
		outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );
	}
}

void FlatImageProcessor::hashFormat( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( inputsAreFlat() )
	{
		hashFlatFormat( parent, context, h );
	}
	else
	{
		h = inPlug()->formatPlug()->hash();
	}
}

void FlatImageProcessor::hashDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( inputsAreFlat() )
	{
		hashFlatDataWindow( parent, context, h );
	}
	else
	{
		h = inPlug()->dataWindowPlug()->hash();
	}
}

void FlatImageProcessor::hashMetadata( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( inputsAreFlat() )
	{
		hashFlatMetadata( parent, context, h );
	}
	else
	{
		h = inPlug()->metadataPlug()->hash();
	}
}

void FlatImageProcessor::hashChannelNames( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( inputsAreFlat() )
	{
		hashFlatChannelNames( parent, context, h );
	}
	else
	{
		h = inPlug()->channelNamesPlug()->hash();
	}
}

void FlatImageProcessor::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( inputsAreFlat() )
	{
		hashFlatChannelData( parent, context, h );
	}
	else
	{
		h = inPlug()->channelDataPlug()->hash();
	}
}

GafferImage::Format FlatImageProcessor::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	if( inputsAreFlat() )
	{
		return computeFlatFormat( context, parent );
	}
	else
	{
		return inPlug()->formatPlug()->getValue();
	}
}

Imath::Box2i FlatImageProcessor::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	if( inputsAreFlat() )
	{
		return computeFlatDataWindow( context, parent );
	}
	else
	{
		return inPlug()->dataWindowPlug()->getValue();
	}
}

IECore::ConstCompoundObjectPtr FlatImageProcessor::computeMetadata( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	if( inputsAreFlat() )
	{
		return computeFlatMetadata( context, parent );
	}
	else
	{
		return inPlug()->metadataPlug()->getValue();
	}
}

IECore::ConstStringVectorDataPtr FlatImageProcessor::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	if( inputsAreFlat() )
	{
		return computeFlatChannelNames( context, parent );
	}
	else
	{
		return inPlug()->channelNamesPlug()->getValue();
	}
}

IECore::ConstFloatVectorDataPtr FlatImageProcessor::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	if( inputsAreFlat() )
	{
		return computeFlatChannelData( channelName, tileOrigin, context, parent );
	}
	else
	{
		return inPlug()->channelDataPlug()->getValue();
	}
}

void FlatImageProcessor::hashFlatFormat( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( parent->formatPlug(), context, h );
}

void FlatImageProcessor::hashFlatDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( parent->dataWindowPlug(), context, h );
}

void FlatImageProcessor::hashFlatMetadata( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( parent->metadataPlug(), context, h );
}

void FlatImageProcessor::hashFlatChannelNames( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( parent->channelNamesPlug(), context, h );
}

void FlatImageProcessor::hashFlatChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( parent->channelDataPlug(), context, h );
}

GafferImage::Format FlatImageProcessor::computeFlatFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	throw IECore::NotImplementedException( std::string( typeName() ) + "::computeFlatFormat" );
}

Imath::Box2i FlatImageProcessor::computeFlatDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	throw IECore::NotImplementedException( std::string( typeName() ) + "::computeFlatDataWindow" );
}

IECore::ConstCompoundObjectPtr FlatImageProcessor::computeFlatMetadata( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	throw IECore::NotImplementedException( std::string( typeName() ) + "::computeFlatMetadata" );
}

IECore::ConstStringVectorDataPtr FlatImageProcessor::computeFlatChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	throw IECore::NotImplementedException( std::string( typeName() ) + "::computeFlatChannelNames" );
}

IECore::ConstFloatVectorDataPtr FlatImageProcessor::computeFlatChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	throw IECore::NotImplementedException( std::string( typeName() ) + "::computeFlatChannelData" );
}


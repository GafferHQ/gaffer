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

#include "Gaffer/Context.h"

#include "GafferImage/Empty.h"
#include "GafferImage/ImageAlgo.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace GafferImage;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Empty implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( Empty );

size_t Empty::g_firstPlugIndex = 0;

Empty::Empty( const std::string &name )
	: ImageNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new FormatPlug( "format" ) );
}

Empty::~Empty()
{
}

GafferImage::FormatPlug *Empty::formatPlug()
{
	return getChild<FormatPlug>( g_firstPlugIndex );
}

const GafferImage::FormatPlug *Empty::formatPlug() const
{
	return getChild<FormatPlug>( g_firstPlugIndex );
}

void Empty::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageNode::affects( input, outputs );

	if( formatPlug()->displayWindowPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->formatPlug() );
		outputs.push_back( outPlug()->dataWindowPlug() );
	}
	else if( input == formatPlug()->pixelAspectPlug() )
	{
		outputs.push_back( outPlug()->formatPlug() );
	}
}

void Empty::hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashFormat( output, context, h );
	h.append( formatPlug()->hash() );
}

GafferImage::Format Empty::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return formatPlug()->getValue();
}

void Empty::hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashDataWindow( output, context, h );
	h.append( formatPlug()->hash() );
}

Imath::Box2i Empty::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return formatPlug()->getValue().getDisplayWindow();
}

IECore::ConstCompoundDataPtr Empty::computeMetadata( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return outPlug()->metadataPlug()->defaultValue();
}

bool Empty::computeDeep( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return true;
}

void Empty::hashSampleOffsets( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = ImagePlug::emptyTileSampleOffsets()->Object::hash();
}

IECore::ConstIntVectorDataPtr Empty::computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return ImagePlug::emptyTileSampleOffsets();
}

void Empty::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashChannelNames( output, context, h );
}

IECore::ConstStringVectorDataPtr Empty::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return new IECore::StringVectorData();
}

void Empty::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = ImagePlug::emptyTile()->Object::hash();
}

IECore::ConstFloatVectorDataPtr Empty::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return ImagePlug::emptyTile();
}

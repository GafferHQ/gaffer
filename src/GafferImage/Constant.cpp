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

#include "GafferImage/Constant.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace GafferImage;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Constant implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( Constant );

size_t Constant::g_firstPlugIndex = 0;

Constant::Constant( const std::string &name )
	:	ImageNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new FormatPlug( "format" ) );
	addChild( new Color4fPlug( "color" ) );
	
	colorPlug()->getChild(3)->setValue( 1.f );
}

Constant::~Constant()
{
}

GafferImage::FormatPlug *Constant::formatPlug()
{
	return getChild<FormatPlug>( g_firstPlugIndex );
}

const GafferImage::FormatPlug *Constant::formatPlug() const
{
	return getChild<FormatPlug>( g_firstPlugIndex );
}

Gaffer::Color4fPlug *Constant::colorPlug()
{
	return getChild<Color4fPlug>( g_firstPlugIndex+1 );
}

const Gaffer::Color4fPlug *Constant::colorPlug() const
{
	return getChild<Color4fPlug>( g_firstPlugIndex+1 );
}

void Constant::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageNode::affects( input, outputs );

	// Process the children of the compound plugs. 
	for( unsigned int i = 0; i < 4; ++i )
	{
		if( input == colorPlug()->getChild(i) )
		{
			outputs.push_back( outPlug()->channelDataPlug() );
			return;
		}
	}
	
	if( input==formatPlug() )
	{
		outputs.push_back( outPlug()->formatPlug() );
		outputs.push_back( outPlug()->dataWindowPlug() );
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

void Constant::hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashFormat( output, context, h );
	h.append( formatPlug()->hash() );
}

void Constant::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashChannelNames( output, context, h );
}

void Constant::hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashDataWindow( output, context, h );
	h.append( formatPlug()->hash() );
}

void Constant::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashChannelData( output, context, h );
	// Don't bother hashing the format or tile origin here as we couldn't care less about the
	// position on the canvas, only the colour!
	h.append( context->get<std::string>( ImagePlug::channelNameContextName ) );
	colorPlug()->hash( h );
}

GafferImage::Format Constant::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return formatPlug()->getValue();
}

Imath::Box2i Constant::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return formatPlug()->getValue().getDisplayWindow();
}

IECore::ConstStringVectorDataPtr Constant::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	IECore::StringVectorDataPtr channelStrVectorData( new IECore::StringVectorData() );
	std::vector<std::string> &channelStrVector( channelStrVectorData->writable() );
	channelStrVector.push_back("R");
	channelStrVector.push_back("G");
	channelStrVector.push_back("B");
	channelStrVector.push_back("A");
	return channelStrVectorData;
}

IECore::ConstFloatVectorDataPtr Constant::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	FloatVectorDataPtr resultData = new FloatVectorData;
	vector<float> &result = resultData->writable();
	result.resize( ImagePlug::tileSize() * ImagePlug::tileSize() );
	
	int idx = channelName == "R" ? 0 : channelName == "G" ? 1 : channelName == "B" ? 2 : 3;
	const float v = colorPlug()->getValue()[idx];
	
	float *ptr = &result[0];
	for( int i = 0; i < ImagePlug::tileSize() * ImagePlug::tileSize(); i++ )
	{
		*ptr++ = v;
	}
	
	return resultData;
}

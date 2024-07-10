//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
//  Copyright (c) 2015, Nvizible Ltd. All rights reserved.
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

#include "GafferImage/Unpremultiply.h"

#include "Gaffer/Context.h"

using namespace IECore;
using namespace Gaffer;

namespace GafferImage
{

GAFFER_NODE_DEFINE_TYPE( Unpremultiply );

size_t Unpremultiply::g_firstPlugIndex = 0;

Unpremultiply::Unpremultiply( const std::string &name )
	:	ChannelDataProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "alphaChannel", Gaffer::Plug::In, "A" ) );
	addChild( new BoolPlug( "ignoreMissingAlpha", Gaffer::Plug::In, false ) );
}

Unpremultiply::~Unpremultiply()
{
}

Gaffer::StringPlug *Unpremultiply::alphaChannelPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *Unpremultiply::alphaChannelPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *Unpremultiply::ignoreMissingAlphaPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *Unpremultiply::ignoreMissingAlphaPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

void Unpremultiply::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ChannelDataProcessor::affects( input, outputs );

	if(
		input == inPlug()->channelDataPlug() ||
		input == alphaChannelPlug() ||
		input == ignoreMissingAlphaPlug()
	)
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

void Unpremultiply::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	std::string alphaChannel;
	ConstStringVectorDataPtr inChannelNamesPtr;
	bool ignoreMissingAlpha;

	{
		ImagePlug::GlobalScope c( context );
		alphaChannel = alphaChannelPlug()->getValue();
		inChannelNamesPtr = inPlug()->channelNamesPlug()->getValue();
		ignoreMissingAlpha = ignoreMissingAlphaPlug()->getValue();
	}

	if( alphaChannel == context->get<std::string>( ImagePlug::channelNameContextName ) )
	{
		h = inPlug()->channelDataPlug()->hash();
		return;
	}

	const std::vector<std::string> &inChannelNames = inChannelNamesPtr->readable();
	if ( std::find( inChannelNames.begin(), inChannelNames.end(), alphaChannel ) == inChannelNames.end() )
	{
		if( ignoreMissingAlpha )
		{
			h = inPlug()->channelDataPlug()->hash();
			return;
		}
		else
		{
			throw IECore::Exception( fmt::format( "Channel '{}' does not exist", alphaChannel ) );
		}
	}

	ChannelDataProcessor::hashChannelData( output, context, h );

	ImagePlug::ChannelDataScope channelDataScope( context );
	channelDataScope.setChannelName( &alphaChannel );

	inPlug()->channelDataPlug()->hash( h );
}

void Unpremultiply::processChannelData( const Gaffer::Context *context, const ImagePlug *parent, const std::string &channel, FloatVectorDataPtr outData ) const
{
	std::string alphaChannel;
	ConstStringVectorDataPtr inChannelNamesPtr;
	bool ignoreMissingAlpha;

	{
		ImagePlug::GlobalScope c( context );
		alphaChannel = alphaChannelPlug()->getValue();
		inChannelNamesPtr = inPlug()->channelNamesPlug()->getValue();
		ignoreMissingAlpha = ignoreMissingAlphaPlug()->getValue();
	}

	if ( channel == alphaChannel )
	{
		return;
	}

	const std::vector<std::string> &inChannelNames = inChannelNamesPtr->readable();
	if ( std::find( inChannelNames.begin(), inChannelNames.end(), alphaChannel ) == inChannelNames.end() )
	{
		if( ignoreMissingAlpha )
		{
			return;
		}
		else
		{
			throw IECore::Exception( fmt::format( "Channel '{}' does not exist", alphaChannel ) );
		}
	}

	ImagePlug::ChannelDataScope channelDataScope( context );
	channelDataScope.setChannelName( &alphaChannel );

	ConstFloatVectorDataPtr aData = inPlug()->channelDataPlug()->getValue();
	const std::vector<float> &a = aData->readable();
	std::vector<float> &out = outData->writable();

	std::vector<float>::const_iterator aIt = a.begin();
	for ( std::vector<float>::iterator outIt = out.begin(), outItEnd = out.end(); outIt != outItEnd; ++outIt, ++aIt )
	{
		if ( *aIt != 0.0f )
		{
			*outIt /= *aIt;
		}
	}
}

} // namespace GafferImage

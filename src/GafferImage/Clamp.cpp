//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/Clamp.h"

#include "GafferImage/ImageAlgo.h"

#include "Gaffer/Context.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

GAFFER_NODE_DEFINE_TYPE( Clamp );

size_t Clamp::g_firstPlugIndex = 0;

Clamp::Clamp( const std::string &name )
	:	ChannelDataProcessor( name, true /* hasUnpremultPlug */ )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new Color4fPlug( "min", Plug::In, Imath::Color4f(0.f, 0.f, 0.f, 0.f) ) );
	addChild( new Color4fPlug( "max", Plug::In, Imath::Color4f(1.f, 1.f, 1.f, 1.f) ) );
	addChild( new Color4fPlug( "minClampTo", Plug::In, Imath::Color4f(0.f, 0.f, 0.f, 0.f) ) );
	addChild( new Color4fPlug( "maxClampTo", Plug::In, Imath::Color4f(1.f, 1.f, 1.f, 1.f) ) );

	addChild( new BoolPlug( "minEnabled", Plug::In, true ) );
	addChild( new BoolPlug( "maxEnabled", Plug::In, true ) );
	addChild( new BoolPlug( "minClampToEnabled", Plug::In, false ) );
	addChild( new BoolPlug( "maxClampToEnabled", Plug::In, false ) );
}

Clamp::~Clamp()
{
}

Gaffer::Color4fPlug *Clamp::minPlug()
{
	return getChild<Color4fPlug>( g_firstPlugIndex );
}

const Gaffer::Color4fPlug *Clamp::minPlug() const
{
	return getChild<Color4fPlug>( g_firstPlugIndex );
}

Gaffer::Color4fPlug *Clamp::maxPlug()
{
	return getChild<Color4fPlug>( g_firstPlugIndex+1 );
}

const Gaffer::Color4fPlug *Clamp::maxPlug() const
{
	return getChild<Color4fPlug>( g_firstPlugIndex+1 );
}

Gaffer::Color4fPlug *Clamp::minClampToPlug()
{
	return getChild<Color4fPlug>( g_firstPlugIndex+2 );
}

const Gaffer::Color4fPlug *Clamp::minClampToPlug() const
{
	return getChild<Color4fPlug>( g_firstPlugIndex+2 );
}

Gaffer::Color4fPlug *Clamp::maxClampToPlug()
{
	return getChild<Color4fPlug>( g_firstPlugIndex+3 );
}

const Gaffer::Color4fPlug *Clamp::maxClampToPlug() const
{
	return getChild<Color4fPlug>( g_firstPlugIndex+3 );
}

Gaffer::BoolPlug *Clamp::minEnabledPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex+4 );
}

const Gaffer::BoolPlug *Clamp::minEnabledPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex+4 );
}

Gaffer::BoolPlug *Clamp::maxEnabledPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex+5 );
}

const Gaffer::BoolPlug *Clamp::maxEnabledPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex+5 );
}

Gaffer::BoolPlug *Clamp::minClampToEnabledPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex+6 );
}

const Gaffer::BoolPlug *Clamp::minClampToEnabledPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex+6 );
}

Gaffer::BoolPlug *Clamp::maxClampToEnabledPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex+7 );
}

const Gaffer::BoolPlug *Clamp::maxClampToEnabledPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex+7 );
}

bool Clamp::enabled() const
{
	if( !ChannelDataProcessor::enabled() )
	{
		return false;
	}

	if(
		minEnabledPlug()->getValue() == false &&
		maxEnabledPlug()->getValue() == false
	)
	{
		return false;
	}

	return true;
}

void Clamp::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ChannelDataProcessor::affects( input, outputs );

	const Plug *inputParent = input->parent<Plug>();
	if(
		inputParent == minPlug() ||
		inputParent == maxPlug() ||
		inputParent == minClampToPlug() ||
		inputParent == maxClampToPlug() ||
		input == inPlug()->channelDataPlug() ||
		input == minEnabledPlug() ||
		input == maxEnabledPlug() ||
		input == minClampToEnabledPlug() ||
		input == maxClampToEnabledPlug()
	)
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

void Clamp::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ChannelDataProcessor::hashChannelData( output, context, h );

	inPlug()->channelDataPlug()->hash( h );

	const std::string &channelName = context->get<std::string>( ImagePlug::channelNameContextName );
	const int channelIndex = std::max( 0, ImageAlgo::colorIndex( channelName ) );

	minPlug()->getChild( channelIndex )->hash( h );
	maxPlug()->getChild( channelIndex )->hash( h );
	minClampToPlug()->getChild( channelIndex )->hash( h );
	maxClampToPlug()->getChild( channelIndex )->hash( h );

	minEnabledPlug()->hash( h );
	maxEnabledPlug()->hash( h );
	minClampToEnabledPlug()->hash( h );
	maxClampToEnabledPlug()->hash( h );
}

void Clamp::processChannelData( const Gaffer::Context *context, const ImagePlug *parent, const std::string &channelName, FloatVectorDataPtr outData ) const
{
	const int channelIndex = std::max( 0, ImageAlgo::colorIndex( channelName ) );

	const float minimum = minPlug()->getChild( channelIndex )->getValue();
	const float maximum = maxPlug()->getChild( channelIndex )->getValue();
	const float minClampTo = minClampToPlug()->getChild( channelIndex )->getValue();
	const float maxClampTo = maxClampToPlug()->getChild( channelIndex )->getValue();
	const bool minimumEnabled = minEnabledPlug()->getValue();
	const bool maximumEnabled = maxEnabledPlug()->getValue();
	const bool minClampToEnabled = minClampToEnabledPlug()->getValue();
	const bool maxClampToEnabled = maxClampToEnabledPlug()->getValue();

	std::vector<float> &out = outData->writable();

	std::vector<float>::iterator outDataIterator;

	for (outDataIterator = out.begin(); outDataIterator != out.end(); ++outDataIterator)
	{

		if (minimumEnabled)
		{
			if (*outDataIterator < minimum)
			{
				if (minClampToEnabled)
				{
					*outDataIterator = minClampTo;
				}
				else
				{
					*outDataIterator = minimum;
				}
			}
		}

		if (maximumEnabled)
		{
			if (*outDataIterator > maximum)
			{
				if (maxClampToEnabled)
				{
					*outDataIterator = maxClampTo;
				}
				else
				{
					*outDataIterator = maximum;
				}
			}
		}

	}
}

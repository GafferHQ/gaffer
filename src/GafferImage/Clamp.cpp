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

#include "Gaffer/Context.h"
#include "GafferImage/Clamp.h"

using namespace IECore;
using namespace Gaffer;

namespace GafferImage
{

IE_CORE_DEFINERUNTIMETYPED( Clamp );

size_t Clamp::g_firstPlugIndex = 0;

Clamp::Clamp( const std::string &name )
	:	ChannelDataProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new Color4fPlug( "minimum", Plug::In, Imath::Color4f(0.f, 0.f, 0.f, 0.f) ) );
	addChild( new Color4fPlug( "maximum", Plug::In, Imath::Color4f(1.f, 1.f, 1.f, 1.f) ) );
	addChild( new Color4fPlug( "minClampTo", Plug::In, Imath::Color4f(0.f, 0.f, 0.f, 0.f) ) );
	addChild( new Color4fPlug( "maxClampTo", Plug::In, Imath::Color4f(1.f, 1.f, 1.f, 1.f) ) );

	addChild( new BoolPlug( "minimumEnabled", Plug::In, true ) );
	addChild( new BoolPlug( "maximumEnabled", Plug::In, true ) );
	addChild( new BoolPlug( "minClampToEnabled", Plug::In, false ) );
	addChild( new BoolPlug( "maxClampToEnabled", Plug::In, false ) );
}

Clamp::~Clamp()
{
}

Gaffer::Color4fPlug *Clamp::minimumPlug()
{
	return getChild<Color4fPlug>( g_firstPlugIndex );
}

const Gaffer::Color4fPlug *Clamp::minimumPlug() const
{
	return getChild<Color4fPlug>( g_firstPlugIndex );
}

Gaffer::Color4fPlug *Clamp::maximumPlug()
{
	return getChild<Color4fPlug>( g_firstPlugIndex+1 );
}

const Gaffer::Color4fPlug *Clamp::maximumPlug() const
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

Gaffer::BoolPlug *Clamp::minimumEnabledPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex+4 );
}

const Gaffer::BoolPlug *Clamp::minimumEnabledPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex+4 );
}

Gaffer::BoolPlug *Clamp::maximumEnabledPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex+5 );
}

const Gaffer::BoolPlug *Clamp::maximumEnabledPlug() const
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

bool Clamp::channelEnabled( const std::string &channel ) const 
{
	if ( !ChannelDataProcessor::channelEnabled( channel ) )
	{
		return false;
	}
	
	if (minimumEnabledPlug()->getValue() == false && 
		maximumEnabledPlug()->getValue() == false )
	{
		return false;
	}

	return true;
}

void Clamp::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ChannelDataProcessor::affects( input, outputs );

	if ( minimumPlug()->isAncestorOf( input ) ||  
		 maximumPlug()->isAncestorOf( input ) ||
		 minClampToPlug()->isAncestorOf( input ) ||
		 maxClampToPlug()->isAncestorOf( input )
	  )
	{
		outputs.push_back( outPlug()->channelDataPlug() );	
		return;
	}

	if( input == inPlug()->channelDataPlug() ||
		input == minimumEnabledPlug() ||
		input == maximumEnabledPlug() ||
		input == minClampToEnabledPlug() ||
		input == maxClampToEnabledPlug()
	  )
	{
		outputs.push_back( outPlug()->channelDataPlug() );	
		return;
	}

}

void Clamp::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const std::string &channelName = context->get<std::string>( ImagePlug::channelNameContextName );

	ContextPtr tmpContext = new Context( *Context::current() );
	Context::Scope scopedContext( tmpContext );	

	tmpContext->set( ImagePlug::channelNameContextName, channelName );
	inPlug()->channelDataPlug()->hash( h );

	minimumPlug()->hash( h );
	maximumPlug()->hash( h );
	minClampToPlug()->hash( h );
	maxClampToPlug()->hash( h );

	minimumEnabledPlug()->hash( h );
	maximumEnabledPlug()->hash( h );
	minClampToEnabledPlug()->hash( h );
	maxClampToEnabledPlug()->hash( h );
}

void Clamp::processChannelData( const Gaffer::Context *context, const ImagePlug *parent, const std::string &channel, FloatVectorDataPtr outData ) const
{
	int channelIndex = ChannelMaskPlug::channelIndex( channel );

	const float minimum = minimumPlug()->getValue()[channelIndex];
	const float maximum = maximumPlug()->getValue()[channelIndex];
	const float minClampTo = minClampToPlug()->getValue()[channelIndex];
	const float maxClampTo = maxClampToPlug()->getValue()[channelIndex];
	const bool minimumEnabled = minimumEnabledPlug()->getValue();
	const bool maximumEnabled = maximumEnabledPlug()->getValue();
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

} // namespace GafferImage


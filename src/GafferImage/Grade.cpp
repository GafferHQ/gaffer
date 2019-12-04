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

#include "GafferImage/Grade.h"

#include "GafferImage/ImageAlgo.h"

#include "Gaffer/Context.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

namespace
{
	struct GradeParametersScope : public Gaffer::Context::EditableScope
	{
		GradeParametersScope( const Gaffer::Context *context )
			:   EditableScope( context )
		{
			remove( GafferImage::ImagePlug::tileOriginContextName );
		}
	};

}

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( Grade );

size_t Grade::g_firstPlugIndex = 0;

Grade::Grade( const std::string &name )
	:	ChannelDataProcessor( name, true /* hasUnpremultPlug */ )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new Color4fPlug( "blackPoint" ) );
	addChild( new Color4fPlug( "whitePoint", Gaffer::Plug::In, Imath::Color4f( 1.0f ) ) );
	addChild( new Color4fPlug( "lift" ) );
	addChild( new Color4fPlug( "gain", Gaffer::Plug::In, Imath::Color4f( 1.0f ) ) );
	addChild( new Color4fPlug( "multiply", Gaffer::Plug::In, Imath::Color4f( 1.0f ) ) );
	addChild( new Color4fPlug( "offset" ) );
	addChild( new Color4fPlug( "gamma", Gaffer::Plug::In, Imath::Color4f( 1.0f ), Imath::Color4f( 0.0f ) ) );
	addChild( new BoolPlug( "blackClamp", Gaffer::Plug::In, true ) );
	addChild( new BoolPlug( "whiteClamp" ) );
}

Grade::~Grade()
{
}

Gaffer::Color4fPlug *Grade::blackPointPlug()
{
	return getChild<Color4fPlug>( g_firstPlugIndex );
}

const Gaffer::Color4fPlug *Grade::blackPointPlug() const
{
	return getChild<Color4fPlug>( g_firstPlugIndex );
}

Gaffer::Color4fPlug *Grade::whitePointPlug()
{
	return getChild<Color4fPlug>( g_firstPlugIndex+1 );
}

const Gaffer::Color4fPlug *Grade::whitePointPlug() const
{
	return getChild<Color4fPlug>( g_firstPlugIndex+1 );
}

Gaffer::Color4fPlug *Grade::liftPlug()
{
	return getChild<Color4fPlug>( g_firstPlugIndex+2 );
}

const Gaffer::Color4fPlug *Grade::liftPlug() const
{
	return getChild<Color4fPlug>( g_firstPlugIndex+2 );
}

Gaffer::Color4fPlug *Grade::gainPlug()
{
	return getChild<Color4fPlug>( g_firstPlugIndex+3 );
}

const Gaffer::Color4fPlug *Grade::gainPlug() const
{
	return getChild<Color4fPlug>( g_firstPlugIndex+3 );
}

Gaffer::Color4fPlug *Grade::multiplyPlug()
{
	return getChild<Color4fPlug>( g_firstPlugIndex+4 );
}

const Gaffer::Color4fPlug *Grade::multiplyPlug() const
{
	return getChild<Color4fPlug>( g_firstPlugIndex+4 );
}

Gaffer::Color4fPlug *Grade::offsetPlug()
{
	return getChild<Color4fPlug>( g_firstPlugIndex+5 );
}

const Gaffer::Color4fPlug *Grade::offsetPlug() const
{
	return getChild<Color4fPlug>( g_firstPlugIndex+5 );
}

Gaffer::Color4fPlug *Grade::gammaPlug()
{
	return getChild<Color4fPlug>( g_firstPlugIndex+6 );
}

const Gaffer::Color4fPlug *Grade::gammaPlug() const
{
	return getChild<Color4fPlug>( g_firstPlugIndex+6 );
}

Gaffer::BoolPlug *Grade::blackClampPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex+7 );
}

const Gaffer::BoolPlug *Grade::blackClampPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex+7 );
}

Gaffer::BoolPlug *Grade::whiteClampPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex+8 );
}

const Gaffer::BoolPlug *Grade::whiteClampPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex+8 );
}

bool Grade::channelEnabled( const std::string &channel ) const
{
	if ( !ChannelDataProcessor::channelEnabled( channel ) )
	{
		return false;
	}

	const int channelIndex = std::max( 0, ImageAlgo::colorIndex( channel ) );

	// And don't bother to process identity transforms or invalid gammas
	float a, b, gamma;
	parameters( channelIndex, a, b, gamma );

	if( gamma == 0.0f )
	{
		// this would result in division by zero,
		// so it must disable processing.
		return false;
	}

	return gamma != 1.0f || a != 1.0f || b != 0.0f || blackClampPlug()->getValue() || whiteClampPlug()->getValue();
}

void Grade::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ChannelDataProcessor::affects( input, outputs );

	// Process the children of the compound plugs.
	for( unsigned int i = 0; i < 4; ++i )
	{
		if( input == blackPointPlug()->getChild(i) ||
				input == whitePointPlug()->getChild(i) ||
				input == liftPlug()->getChild(i) ||
				input == gainPlug()->getChild(i) ||
				input == multiplyPlug()->getChild(i) ||
				input == offsetPlug()->getChild(i) ||
				input == gammaPlug()->getChild(i)
		  )
		{
			outputs.push_back( outPlug()->channelDataPlug() );
			return;
		}
	}

	// Process all other plugs.
	if( input == inPlug()->channelDataPlug() ||
			input == blackClampPlug() ||
			input == whiteClampPlug()
	  )
	{
		outputs.push_back( outPlug()->channelDataPlug() );
		return;
	}

}

void Grade::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ChannelDataProcessor::hashChannelData( output, context, h );

	inPlug()->channelDataPlug()->hash( h );

	const std::string &channelName = context->get<std::string>( ImagePlug::channelNameContextName );
	const int channelIndex = std::max( 0, ImageAlgo::colorIndex( channelName ) );

	GradeParametersScope s( context );
	blackPointPlug()->getChild( channelIndex )->hash( h );
	whitePointPlug()->getChild( channelIndex )->hash( h );
	liftPlug()->getChild( channelIndex )->hash( h );
	gainPlug()->getChild( channelIndex )->hash( h );
	multiplyPlug()->getChild( channelIndex )->hash( h );
	offsetPlug()->getChild( channelIndex )->hash( h );
	gammaPlug()->getChild( channelIndex )->hash( h );
	blackClampPlug()->hash( h );
	whiteClampPlug()->hash( h );
}

void Grade::processChannelData( const Gaffer::Context *context, const ImagePlug *parent, const std::string &channel, FloatVectorDataPtr outData ) const
{
	// Do some pre-processing.
	float A, B, gamma;
	bool whiteClamp, blackClamp;
	{
		GradeParametersScope s( context );
		parameters( std::max( 0, ImageAlgo::colorIndex( channel ) ), A, B, gamma );
		whiteClamp = whiteClampPlug()->getValue();
		blackClamp = blackClampPlug()->getValue();
	}
	const float invGamma = 1. / gamma;

	// Get some useful pointers.
	float *outPtr = &(outData->writable()[0]);
	const float *END = outPtr + outData->writable().size();

	while (outPtr != END)
	{
		// Calculate the colour of the graded pixel.
		float colour = *outPtr;	// As the input has been copied to outData, grab the input colour from there.
		const float c = A * colour + B;
		colour = ( c >= 0.f && invGamma != 1.f ? (float)pow( c, invGamma ) : c );

		// Clamp the white and blacks if necessary.
		if ( blackClamp && colour < 0.f ) colour = 0.f;
		if ( whiteClamp && colour > 1.f ) colour = 1.f;

		// Write back the result.
		*outPtr++ = colour;
	}
}

void Grade::parameters( size_t channelIndex, float &a, float &b, float &gamma ) const
{
	gamma = gammaPlug()->getChild( channelIndex )->getValue();
	const float multiply = multiplyPlug()->getChild( channelIndex )->getValue();
	const float gain = gainPlug()->getChild( channelIndex )->getValue();
	const float lift = liftPlug()->getChild( channelIndex )->getValue();
	const float whitePoint = whitePointPlug()->getChild( channelIndex )->getValue();
	const float blackPoint = blackPointPlug()->getChild( channelIndex )->getValue();
	const float offset = offsetPlug()->getChild( channelIndex )->getValue();

	a = multiply * ( gain - lift ) / ( whitePoint - blackPoint );
	b = offset + lift - a * blackPoint;
}

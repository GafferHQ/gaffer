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
#include "GafferImage/Grade.h"
#include "IECore/BoxOps.h"
#include "IECore/BoxAlgo.h"

using namespace IECore;
using namespace Gaffer;

namespace GafferImage
{

IE_CORE_DEFINERUNTIMETYPED( Grade );

size_t Grade::g_firstPlugIndex = 0;

Grade::Grade( const std::string &name )
	:	ChannelDataProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new Color3fPlug( "blackPoint" ) );
	addChild( new Color3fPlug( "whitePoint" ) );
	addChild( new Color3fPlug( "lift" ) );
	addChild( new Color3fPlug( "gain" ) );
	addChild( new Color3fPlug( "multiply" ) );
	addChild( new Color3fPlug( "offset" ) );
	addChild( new Color3fPlug( "gamma" ) );
	addChild( new BoolPlug( "blackClamp" ) );
	addChild( new BoolPlug( "whiteClamp" ) );

	// Set the default values of the plugs.
	whitePointPlug()->setValue( Imath::V3f(1.f, 1.f, 1.f) );
	gainPlug()->setValue( Imath::V3f(1.f, 1.f, 1.f) );
	multiplyPlug()->setValue( Imath::V3f(1.f, 1.f, 1.f) );
	gammaPlug()->setValue( Imath::V3f(1.f, 1.f, 1.f) );
	blackClampPlug()->setValue( true );
}

Grade::~Grade()
{
}

Gaffer::Color3fPlug *Grade::blackPointPlug()
{
	return getChild<Color3fPlug>( g_firstPlugIndex );
}

const Gaffer::Color3fPlug *Grade::blackPointPlug() const
{
	return getChild<Color3fPlug>( g_firstPlugIndex );
}

Gaffer::Color3fPlug *Grade::whitePointPlug()
{
	return getChild<Color3fPlug>( g_firstPlugIndex+1 );
}

const Gaffer::Color3fPlug *Grade::whitePointPlug() const
{
	return getChild<Color3fPlug>( g_firstPlugIndex+1 );
}

Gaffer::Color3fPlug *Grade::liftPlug()
{
	return getChild<Color3fPlug>( g_firstPlugIndex+2 );
}

const Gaffer::Color3fPlug *Grade::liftPlug() const
{
	return getChild<Color3fPlug>( g_firstPlugIndex+2 );
}

Gaffer::Color3fPlug *Grade::gainPlug()
{
	return getChild<Color3fPlug>( g_firstPlugIndex+3 );
}

const Gaffer::Color3fPlug *Grade::gainPlug() const
{
	return getChild<Color3fPlug>( g_firstPlugIndex+3 );
}

Gaffer::Color3fPlug *Grade::multiplyPlug()
{
	return getChild<Color3fPlug>( g_firstPlugIndex+4 );
}

const Gaffer::Color3fPlug *Grade::multiplyPlug() const
{
	return getChild<Color3fPlug>( g_firstPlugIndex+4 );
}

Gaffer::Color3fPlug *Grade::offsetPlug()
{
	return getChild<Color3fPlug>( g_firstPlugIndex+5 );
}

const Gaffer::Color3fPlug *Grade::offsetPlug() const
{
	return getChild<Color3fPlug>( g_firstPlugIndex+5 );
}

Gaffer::Color3fPlug *Grade::gammaPlug()
{
	return getChild<Color3fPlug>( g_firstPlugIndex+6 );
}

const Gaffer::Color3fPlug *Grade::gammaPlug() const
{
	return getChild<Color3fPlug>( g_firstPlugIndex+6 );
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
	
	int channelIndex = GafferImage::ChannelMaskPlug::channelIndex( channel );
	
	// Never bother to process the alpha channel.
	if ( channelIndex == 3 ) return false;

	return (
		gammaPlug()->getValue()[ channelIndex ] != 0.
		//|| blackPointPlug()->getValue()[ channelIndex ] != 0.
		//|| whitePointPlug()->getValue()[ channelIndex ] != 1.
	);
}

void Grade::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ChannelDataProcessor::affects( input, outputs );

	// Process the children of the compound plugs. 
	for( unsigned int i = 0; i < 3; ++i )
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

void Grade::hashChannelDataPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const std::string &channelName = context->get<std::string>( ImagePlug::channelNameContextName );

	ContextPtr tmpContext = new Context( *Context::current() );
	Context::Scope scopedContext( tmpContext );	

	tmpContext->set( ImagePlug::channelNameContextName, channelName );
	inPlug()->channelDataPlug()->hash( h );

	// Hash all of the inputs.
	blackPointPlug()->hash( h );
	whitePointPlug()->hash( h );
	liftPlug()->hash( h );
	gainPlug()->hash( h );
	multiplyPlug()->hash( h );
	offsetPlug()->hash( h );
	gammaPlug()->hash( h );
	blackClampPlug()->hash( h );
	whiteClampPlug()->hash( h );
}

void Grade::processChannelData( const Gaffer::Context *context, const ImagePlug *parent, const std::string &channel, FloatVectorDataPtr outData ) const
{
	// Calculate the valid data window that we are to merge.
	const int dataWidth = ImagePlug::tileSize()*ImagePlug::tileSize();

	// Do some pre-processing.
	int channelIndex = ChannelMaskPlug::channelIndex( channel );
	const float gamma = gammaPlug()->getValue()[channelIndex];
	const float invGamma = 1. / gamma;	
	const float multiply = multiplyPlug()->getValue()[channelIndex];
	const float gain = gainPlug()->getValue()[channelIndex];
	const float lift = liftPlug()->getValue()[channelIndex];
	const float whitePoint = whitePointPlug()->getValue()[channelIndex];
	const float blackPoint = blackPointPlug()->getValue()[channelIndex];
	const float offset = offsetPlug()->getValue()[channelIndex];
	const bool whiteClamp = whiteClampPlug()->getValue();	
	const bool blackClamp = blackClampPlug()->getValue();	

	const float A = multiply * ( gain - lift ) / ( whitePoint - blackPoint );
	const float B = offset + lift - A * blackPoint;

	// Get some useful pointers.	
	float *outPtr = &(outData->writable()[0]);
	const float *END = outPtr + dataWidth;

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

} // namespace GafferImage


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
#include "GafferImage/Merge.h"
#include "IECore/BoxOps.h"
#include "IECore/BoxAlgo.h"

using namespace IECore;
using namespace Gaffer;

// Create a set of functions to perform the different operations.
float opAdd( float A, float B, float a, float b){ return A + B; }
float opAtop( float A, float B, float a, float b){ return A*b + B*(1.-a); }
float opDivide( float A, float B, float a, float b){ return A / B; }
float opIn( float A, float B, float a, float b){ return A*b; }
float opOut( float A, float B, float a, float b){ return A*(1.-b); }
float opMask( float A, float B, float a, float b){ return B*a; }
float opMatte( float A, float B, float a, float b){ return A*a + B*(1.-a); }
float opMultiply( float A, float B, float a, float b){ return A * B; }
float opOver( float A, float B, float a, float b){ return A + B*(1.-a); }
float opSubtract( float A, float B, float a, float b){ return A - B; }
float opUnder( float A, float B, float a, float b){ return A*(1.-b) + B; }

namespace GafferImage
{

IE_CORE_DEFINERUNTIMETYPED( Merge );

size_t Merge::g_firstPlugIndex = 0;

Merge::Merge( const std::string &name )
	:	ChannelDataProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ImagePlug( "in1", Gaffer::Plug::In ) );
	addChild( new IntPlug( "operation" ) );
}

Merge::~Merge()
{
}

GafferImage::ImagePlug *Merge::inPlug1()
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

const GafferImage::ImagePlug *Merge::inPlug1() const
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *Merge::operationPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex+1 );
}

const Gaffer::IntPlug *Merge::operationPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex+1 );
}

bool Merge::enabled() const
{
	return !inPlug1()->getInput<ValuePlug>() ? false : ChannelDataProcessor::enabled();
}

void Merge::affects( const Gaffer::ValuePlug *input, AffectedPlugsContainer &outputs ) const
{
	ChannelDataProcessor::affects( input, outputs );
	
	if( input == inPlug()->channelDataPlug() ||
		input == inPlug1()->channelDataPlug() ||
		input == operationPlug()
	)
	{
		outputs.push_back( outPlug()->channelDataPlug() );	
	}
}

void Merge::hashChannelDataPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const std::string &channelName = context->get<std::string>( ImagePlug::channelNameContextName );

	ContextPtr tmpContext = new Context( *Context::current() );
	Context::Scope scopedContext( tmpContext );	

	tmpContext->set( ImagePlug::channelNameContextName, channelName );
	inPlug()->channelDataPlug()->hash( h );

	operationPlug()->hash( h );
}

Imath::Box2i Merge::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
		// Calculate the valid data window that we are to merge.
		const Imath::Box2i dataWindow1 = inPlug()->dataWindowPlug()->getValue();
		const Imath::Box2i dataWindow2 = inPlug1()->dataWindowPlug()->getValue();
		const Imath::Box2i validDataWindow = boxIntersection( dataWindow1, dataWindow2 );
		return validDataWindow;
}

bool Merge::hasAlpha( ConstStringVectorDataPtr channelNamesData ) const
{
	const std::vector<std::string> &channelNames = channelNamesData->readable();
	std::vector<std::string>::const_iterator channelIt = std::find( channelNames.begin(), channelNames.end(), "A" );
	return channelIt != channelNames.end();
}

IECore::ConstFloatVectorDataPtr Merge::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ConstFloatVectorDataPtr inData1 = inPlug()->channelData( channelName, tileOrigin );
	ConstFloatVectorDataPtr inData2 = inPlug1()->channelData( channelName, tileOrigin );

	// Check whether the inputs have alpha channels.
	ConstFloatVectorDataPtr inAlpha1 = inPlug()->channelData( "A", tileOrigin );
	ConstFloatVectorDataPtr inAlpha2 = inPlug1()->channelData( "A", tileOrigin );

	// Calculate the valid data window that we are to merge.
	const int tileSize = ImagePlug::tileSize();
	const Imath::Box2i dataWindow1 = inPlug()->dataWindowPlug()->getValue();
	const Imath::Box2i dataWindow2 = inPlug1()->dataWindowPlug()->getValue();
	const Imath::Box2i validDataWindow = boxIntersection( dataWindow1, dataWindow2 );
	Imath::Box2i tileBound( tileOrigin, Imath::V2i( tileOrigin.x + tileSize - 1, tileOrigin.y + tileSize - 1 ) );
	const Imath::Box2i tile = boxIntersection( validDataWindow, tileBound );

	// If the input data windows do not intersect then we just return a black tile.
	if ( tile.isEmpty() )
	{
		return ImagePlug::blackTile();
	}

	// Allocate the new tile
	FloatVectorDataPtr outDataPtr = new FloatVectorData;
	std::vector<float> &outData = outDataPtr->writable();
	outData.resize( tileSize * tileSize, 0.0f );

	// Get a pointer to the operation that we wish to perform.
	float (*op)( float A, float B, float a, float b );
	int operation = operationPlug()->getValue();
	switch( operation )
	{
		default:
		case( kAdd ): op = opAdd; break;
		case( kAtop ): op = opAtop; break;
		case( kDivide ): op = opDivide; break;
		case( kIn ): op = opIn; break;
		case( kOut ): op = opOut; break;
		case( kMask ): op = opMask; break;
		case( kMatte ): op = opMatte; break;
		case( kMultiply ): op = opMultiply; break;
		case( kOver ): op = opOver; break;
		case( kSubtract ): op = opSubtract; break;
		case( kUnder ): op = opUnder; break;
	}
	
	// Perform the operation.
	for( int y = tile.min.y; y<=tile.max.y; y++ )
	{
		const float *tile1Ptr = &(inData1->readable()[0]) + (y - tileOrigin.y) * tileSize + (tile.min.x - tileOrigin.x);
		const float *tile2Ptr = &(inData2->readable()[0]) + (y - tileOrigin.y) * tileSize + (tile.min.x - tileOrigin.x);
		const float *tile1AlphaPtr = &(inAlpha1->readable()[0]) + (y - tileOrigin.y) * tileSize + (tile.min.x - tileOrigin.x);
		const float *tile2AlphaPtr = &(inAlpha2->readable()[0]) + (y - tileOrigin.y) * tileSize + (tile.min.x - tileOrigin.x);
		float *outPtr = &(outData[0]) + ( y - tileOrigin.y ) * tileSize + (tile.min.x - tileOrigin.x);
		for( int x = tile.min.x; x <= tile.max.x; x++ )
		{
			*outPtr++ = op( *tile1Ptr++, *tile2Ptr++, *tile1AlphaPtr++, *tile2AlphaPtr++ );
		}
	}
	
	return outDataPtr;

}

} // namespace GafferImage

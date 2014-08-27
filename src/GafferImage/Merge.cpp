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

using namespace IECore;
using namespace Gaffer;

// Create a set of functions to perform the different operations.
typedef float (*Op)( float A, float B, float a, float b );
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
	:	FilterProcessor( name, 2, 50 )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new IntPlug( "operation" ) );
}

Merge::~Merge()
{
}

Gaffer::IntPlug *Merge::operationPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *Merge::operationPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

void Merge::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	if( input == operationPlug() )
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
	else FilterProcessor::affects( input, outputs );
}

bool Merge::enabled() const
{
	// Call enabled() on the image node as we don't care whether the first input is connected or not.
	if ( !ImageNode::enabled() )
	{
		return false;
	}

	return ( m_inputs.nConnectedInputs() >= 2 );
}

void Merge::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FilterProcessor::hashChannelData( output, context, h );
	operationPlug()->hash( h );
}

IECore::ConstFloatVectorDataPtr Merge::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::vector< ConstFloatVectorDataPtr > inData;
	std::vector< ConstFloatVectorDataPtr > inAlpha;

	const ImagePlugList::const_iterator end( m_inputs.endIterator() );
	for( ImagePlugList::const_iterator it( m_inputs.inputs().begin() ); it != end; it++ )
	{
		if ( (*it)->getInput<ValuePlug>() )
		{
			inData.push_back( (*it)->channelData( channelName, tileOrigin ) );
			inAlpha.push_back( (*it)->channelData( "A", tileOrigin ) );
		}
	}

	// Get a pointer to the operation that we wish to perform.
	int operation = operationPlug()->getValue();
	switch( operation )
	{
		default:
		case( kAdd ): return doMergeOperation( opAdd, inData, inAlpha, tileOrigin ); break;
		case( kAtop ): return doMergeOperation( opAtop, inData, inAlpha, tileOrigin ); break;
		case( kDivide ): return doMergeOperation( opDivide, inData, inAlpha, tileOrigin ); break;
		case( kIn ): return doMergeOperation( opIn, inData, inAlpha, tileOrigin ); break;
		case( kOut ): return doMergeOperation( opOut, inData, inAlpha, tileOrigin ); break;
		case( kMask ): return doMergeOperation( opMask, inData, inAlpha, tileOrigin ); break;
		case( kMatte ): return doMergeOperation( opMatte, inData, inAlpha, tileOrigin ); break;
		case( kMultiply ): return doMergeOperation( opMultiply, inData, inAlpha, tileOrigin ); break;
		case( kOver ): return doMergeOperation( opOver, inData, inAlpha, tileOrigin ); break;
		case( kSubtract ): return doMergeOperation( opSubtract, inData, inAlpha, tileOrigin ); break;
		case( kUnder ): return doMergeOperation( opUnder, inData, inAlpha, tileOrigin ); break;
	}

	// We should never get here...
	return doMergeOperation( opAdd, inData, inAlpha, tileOrigin );
}

bool Merge::hasAlpha( ConstStringVectorDataPtr channelNamesData ) const
{
	const std::vector<std::string> &channelNames = channelNamesData->readable();
	std::vector<std::string>::const_iterator channelIt = std::find( channelNames.begin(), channelNames.end(), "A" );
	return channelIt != channelNames.end();
}

} // namespace GafferImage

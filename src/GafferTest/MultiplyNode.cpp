//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "GafferTest/MultiplyNode.h"

#include "Gaffer/NumericPlug.h"

using namespace GafferTest;
using namespace Gaffer;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( MultiplyNode )

size_t MultiplyNode::g_firstPlugIndex = 0;

MultiplyNode::MultiplyNode( const std::string &name, bool brokenAffects )
	:	ComputeNode( name ), m_brokenAffects( brokenAffects )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new IntPlug( "op1" ) );
	addChild( new IntPlug( "op2" ) );
	addChild( new IntPlug( "product", Plug::Out ) );
}

MultiplyNode::~MultiplyNode()
{
}

Gaffer::IntPlug *MultiplyNode::op1Plug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *MultiplyNode::op1Plug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *MultiplyNode::op2Plug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *MultiplyNode::op2Plug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

Gaffer::IntPlug *MultiplyNode::productPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::IntPlug *MultiplyNode::productPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

void MultiplyNode::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if( m_brokenAffects && input == op2Plug() )
	{
		return;
	}

	if( input == op1Plug() || input == op2Plug() )
	{
		outputs.push_back( productPlug() );
	}
}

void MultiplyNode::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( output, context, h );

	if( output == getChild<IntPlug>( "product" ) )
	{
		op1Plug()->hash( h );
		op2Plug()->hash( h );
	}
}

void MultiplyNode::compute( ValuePlug *output, const Context *context ) const
{
	if( output == productPlug() )
	{
		static_cast<IntPlug *>( output )->setValue(
			op1Plug()->getValue() *
			op2Plug()->getValue()
		);
		return;
	}

	ComputeNode::compute( output, context );
}

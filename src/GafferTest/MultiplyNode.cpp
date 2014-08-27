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

#include "Gaffer/NumericPlug.h"

#include "GafferTest/MultiplyNode.h"

using namespace GafferTest;
using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( MultiplyNode )

MultiplyNode::MultiplyNode( const std::string &name )
	:	ComputeNode( name )
{
	addChild( new IntPlug( "op1" ) );
	addChild( new IntPlug( "op2" ) );
	addChild( new IntPlug( "product", Plug::Out ) );
}

MultiplyNode::~MultiplyNode()
{
}

void MultiplyNode::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if( input == getChild<IntPlug>( "op1" ) || input == getChild<IntPlug>( "op2" ) )
	{
		outputs.push_back( getChild<IntPlug>( "product" ) );
	}
}

void MultiplyNode::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( output, context, h );

	if( output == getChild<IntPlug>( "product" ) )
	{
		getChild<IntPlug>( "op1" )->hash( h );
		getChild<IntPlug>( "op2" )->hash( h );
	}
}

void MultiplyNode::compute( ValuePlug *output, const Context *context ) const
{
	if( output == getChild<IntPlug>( "product" ) )
	{
		static_cast<IntPlug *>( output )->setValue(
			getChild<IntPlug>( "op1" )->getValue() *
			getChild<IntPlug>( "op2" )->getValue()
		);
		return;
	}

	ComputeNode::compute( output, context );
}

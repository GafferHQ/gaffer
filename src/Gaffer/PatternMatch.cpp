//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

#include "Gaffer/PatternMatch.h"

#include "IECore/StringAlgo.h"

using namespace Gaffer;

GAFFER_NODE_DEFINE_TYPE( PatternMatch );

size_t PatternMatch::g_firstPlugIndex = 0;

PatternMatch::PatternMatch( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "string" ) );
	addChild( new StringPlug( "pattern" ) );
	addChild( new BoolPlug( "enabled", Plug::In, true ) );
	addChild( new BoolPlug( "match", Plug::Out ) );
}

PatternMatch::~PatternMatch()
{
}

StringPlug *PatternMatch::stringPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const StringPlug *PatternMatch::stringPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

StringPlug *PatternMatch::patternPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const StringPlug *PatternMatch::patternPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

BoolPlug *PatternMatch::enabledPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

const BoolPlug *PatternMatch::enabledPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

BoolPlug *PatternMatch::matchPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

const BoolPlug *PatternMatch::matchPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

void PatternMatch::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if(
		input == stringPlug() ||
		input == patternPlug() ||
		input == enabledPlug()
	)
	{
		outputs.push_back( matchPlug() );
	}
}

void PatternMatch::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	if( output == matchPlug() )
	{
		ComputeNode::hash( output, context, h );
		stringPlug()->hash( h );
		patternPlug()->hash( h );
		enabledPlug()->hash( h );
	}
	else
	{
		ComputeNode::hash( output, context, h );
	}
}

void PatternMatch::compute( ValuePlug *output, const Context *context) const
{
	ComputeNode::compute( output, context );

	if( output == matchPlug() )
	{
		static_cast<BoolPlug *>( output )->setValue(
			enabledPlug()->getValue() ?
			IECore::StringAlgo::matchMultiple( stringPlug()->getValue(), patternPlug()->getValue() ) :
			false
		);
	}
	else
	{
		ComputeNode::compute( output, context );
	}
}

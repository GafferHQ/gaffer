//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferScene/ShuffleOptions.h"

#include "boost/algorithm/string/predicate.hpp"

#include <unordered_map>

using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( ShuffleOptions );

size_t ShuffleOptions::g_firstPlugIndex = 0;

ShuffleOptions::ShuffleOptions( const std::string &name )
	:	GlobalsProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ShufflesPlug( "shuffles" ) );
}

ShuffleOptions::~ShuffleOptions()
{
}

Gaffer::ShufflesPlug *ShuffleOptions::shufflesPlug()
{
	return getChild<Gaffer::ShufflesPlug>( g_firstPlugIndex );
}

const Gaffer::ShufflesPlug *ShuffleOptions::shufflesPlug() const
{
	return getChild<Gaffer::ShufflesPlug>( g_firstPlugIndex );
}

void ShuffleOptions::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	GlobalsProcessor::affects( input, outputs );

	if( shufflesPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->globalsPlug() );
	}
}

void ShuffleOptions::hashProcessedGlobals( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	shufflesPlug()->hash( h );
}

IECore::ConstCompoundObjectPtr ShuffleOptions::computeProcessedGlobals( const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputGlobals ) const
{
	// Get options from input globals into a separate map with the prefix removed
	// from the name. At the same time, pass through other globals which aren't options.

	const std::string prefix = "option:";
	IECore::CompoundObjectPtr result = new IECore::CompoundObject;
	std::unordered_map<std::string, IECore::ObjectPtr> options;

	for( const auto &[name, value] : inputGlobals->members() )
	{
		if( boost::starts_with( name.string(), prefix ) )
		{
			options[name.string().substr(prefix.size())] = value;
		}
		else
		{
			result->members()[name] = value;
		}
	}

	// Shuffle the options, and put them into the result.
	options = shufflesPlug()->shuffle( options );
	for( const auto &[name, value] : options )
	{
		result->members()[prefix+name] = value;
	}

	return result;
}

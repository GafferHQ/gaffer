//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferScene/FilterQuery.h"

#include "GafferScene/Filter.h"
#include "GafferScene/ScenePlug.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

size_t FilterQuery::g_firstPlugIndex = 0;

GAFFER_NODE_DEFINE_TYPE( FilterQuery )

FilterQuery::FilterQuery( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "scene" ) );
	addChild( new FilterPlug( "filter" ) );
	addChild( new StringPlug( "location" ) );
	addChild( new BoolPlug( "exactMatch", Gaffer::Plug::Out ) );
	addChild( new BoolPlug( "descendantMatch", Gaffer::Plug::Out ) );
	addChild( new BoolPlug( "ancestorMatch", Gaffer::Plug::Out ) );
	addChild( new StringPlug( "closestAncestor", Gaffer::Plug::Out ) );
	addChild( new IntPlug( "__match", Gaffer::Plug::Out ) );
	addChild( new StringPlug( "__closestAncestorInternal", Gaffer::Plug::Out ) );
}

FilterQuery::~FilterQuery()
{
}

ScenePlug *FilterQuery::scenePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const ScenePlug *FilterQuery::scenePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

FilterPlug *FilterQuery::filterPlug()
{
	return getChild<FilterPlug>( g_firstPlugIndex + 1 );
}

const FilterPlug *FilterQuery::filterPlug() const
{
	return getChild<FilterPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *FilterQuery::locationPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *FilterQuery::locationPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::BoolPlug *FilterQuery::exactMatchPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::BoolPlug *FilterQuery::exactMatchPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

Gaffer::BoolPlug *FilterQuery::descendantMatchPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::BoolPlug *FilterQuery::descendantMatchPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 4 );
}

Gaffer::BoolPlug *FilterQuery::ancestorMatchPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::BoolPlug *FilterQuery::ancestorMatchPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 5 );
}

Gaffer::StringPlug *FilterQuery::closestAncestorPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::StringPlug *FilterQuery::closestAncestorPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 6 );
}

Gaffer::IntPlug *FilterQuery::matchPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 7 );
}

const Gaffer::IntPlug *FilterQuery::matchPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 7 );
}

Gaffer::StringPlug *FilterQuery::closestAncestorInternalPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 8 );
}

const Gaffer::StringPlug *FilterQuery::closestAncestorInternalPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 8 );
}

void FilterQuery::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if( input->parent() == scenePlug() )
	{
		filterPlug()->sceneAffects( input, outputs );
	}

	if(
		input == locationPlug() ||
		input == scenePlug()->existsPlug() ||
		input == filterPlug()
	)
	{
		outputs.push_back( matchPlug() );
	}

	if( input == matchPlug() )
	{
		outputs.push_back( exactMatchPlug() );
		outputs.push_back( descendantMatchPlug() );
		outputs.push_back( ancestorMatchPlug() );
	}

	if(
		input == filterPlug()
	)
	{
		outputs.push_back( closestAncestorInternalPlug() );
	}

	if(
		input == locationPlug() ||
		input == scenePlug()->existsPlug() ||
		input == closestAncestorInternalPlug()
	)
	{
		outputs.push_back( closestAncestorPlug() );
	}
}

void FilterQuery::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( output == matchPlug() )
	{
		ComputeNode::hash( output, context, h );
		const string location = locationPlug()->getValue();
		if( !location.empty() )
		{
			const ScenePlug::ScenePath locationPath = ScenePlug::stringToPath( location );
			ScenePlug::PathScope scope( context, &locationPath );
			if( scenePlug()->existsPlug()->getValue() )
			{
				const FilterPlug::SceneScope sceneScope( scope.context(), scenePlug() );
				filterPlug()->hash( h );
			}
		}
	}
	else if( output == exactMatchPlug() )
	{
		ComputeNode::hash( output, context, h );
		matchPlug()->hash( h );
	}
	else if( output == descendantMatchPlug() )
	{
		ComputeNode::hash( output, context, h );
		matchPlug()->hash( h );
	}
	else if( output == ancestorMatchPlug() )
	{
		ComputeNode::hash( output, context, h );
		matchPlug()->hash( h );
	}
	else if( output == closestAncestorPlug() )
	{
		const string location = locationPlug()->getValue();
		if( !location.empty() )
		{
			const ScenePlug::ScenePath locationPath = ScenePlug::stringToPath( location );
			ScenePlug::PathScope scope( context, &locationPath );
			if( scenePlug()->existsPlug()->getValue() )
			{
				h = closestAncestorInternalPlug()->hash();
				return;
			}
		}
		h = output->defaultHash();
	}
	else if( output == closestAncestorInternalPlug() )
	{
		const int m = filterPlug()->match( scenePlug() );
		if( m & PathMatcher::ExactMatch )
		{
			ComputeNode::hash( output, context, h );
			const ScenePlug::ScenePath path = context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
			h.append( path.data(), path.size() );
			return;
		}
		else if( m & PathMatcher::AncestorMatch )
		{
			ScenePlug::ScenePath path = context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
			if( path.size() )
			{
				path.pop_back();
				ScenePlug::PathScope scope( context, &path );
				h = closestAncestorInternalPlug()->hash();
				return;
			}
		}
		h = output->defaultHash();
	}
}

void FilterQuery::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == matchPlug() )
	{
		unsigned match = IECore::PathMatcher::NoMatch;
		const string location = locationPlug()->getValue();
		if( !location.empty() )
		{
			const ScenePlug::ScenePath locationPath = ScenePlug::stringToPath( location );
			ScenePlug::PathScope scope( context, &locationPath );
			if( scenePlug()->existsPlug()->getValue() )
			{
				match = filterPlug()->match( scenePlug() );
			}
		}
		static_cast<IntPlug *>( output )->setValue( match );
	}
	else if( output == exactMatchPlug() )
	{
		static_cast<BoolPlug *>( output )->setValue(
			matchPlug()->getValue() & IECore::PathMatcher::ExactMatch
		);
	}
	else if( output == descendantMatchPlug() )
	{
		static_cast<BoolPlug *>( output )->setValue(
			matchPlug()->getValue() & IECore::PathMatcher::DescendantMatch
		);
	}
	else if( output == ancestorMatchPlug() )
	{
		static_cast<BoolPlug *>( output )->setValue(
			matchPlug()->getValue() & IECore::PathMatcher::AncestorMatch
		);
	}
	else if( output == closestAncestorPlug() )
	{
		const string location = locationPlug()->getValue();
		if( !location.empty() )
		{
			const ScenePlug::ScenePath locationPath = ScenePlug::stringToPath( location );
			ScenePlug::PathScope scope( context, &locationPath );
			if( scenePlug()->existsPlug()->getValue() )
			{
				output->setFrom( closestAncestorInternalPlug() );
				return;
			}
		}
		output->setToDefault();
	}
	else if( output == closestAncestorInternalPlug() )
	{
		string result;
		const int m = filterPlug()->match( scenePlug() );
		if( m & PathMatcher::ExactMatch )
		{
			const ScenePlug::ScenePath path = context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
			ScenePlug::pathToString( path, result );
		}
		else if( m & PathMatcher::AncestorMatch )
		{
			// Ancestor match, but we don't know where exactly. Make recursive
			// calls using the parent location until we find the ancestor with
			// an exact match.
			ScenePlug::ScenePath path = context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
			if( path.size() )
			{
				path.pop_back();
				ScenePlug::PathScope scope( context, &path );
				result = closestAncestorInternalPlug()->getValue();
			}
		}
		static_cast<StringPlug *>( output )->setValue( result );
	}

	ComputeNode::compute( output, context );
}

Gaffer::ValuePlug::CachePolicy FilterQuery::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if(
		output == exactMatchPlug() ||
		output == descendantMatchPlug() ||
		output == ancestorMatchPlug()
	)
	{
		// Not much point caching these since they are so trivial.
		return ValuePlug::CachePolicy::Uncached;
	}
	return ComputeNode::computeCachePolicy( output );
}

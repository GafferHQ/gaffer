//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferScene/SetQuery.h"

#include "GafferScene/ScenePlug.h"

#include "IECore/NullObject.h"

#include <unordered_set>

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

struct MatchesData : public IECore::Data
{
	struct DescendantMatch { InternedString setName; bool inherited; };
	using DescendantMatches = vector<DescendantMatch>;

	MatchesData( const ConstStringVectorDataPtr &matches, DescendantMatches &&descendantMatches, bool inherit )
		:	matches( matches ), descendantMatches( descendantMatches ), inherit( inherit )
	{
	}

	// The result for `SetQuery.matches` at this location.
	ConstStringVectorDataPtr matches;
	// Sets that we need to consider at descendants of this location. By
	// removing these as they become irrelevant, we avoid checking _every_
	// location against _every_ set, which would be `O( n^2 )` (assuming the
	// number of sets is proportional to the number of locations, and all
	// locations are queried). This is the most important reason behind
	// `MatchesData` and `matchesInternalPlug().
	DescendantMatches descendantMatches;
	// True if `matches` should be inherited by descendant locations.
	bool inherit;
};

IE_CORE_DECLAREPTR( MatchesData );

const ConstStringVectorDataPtr g_emptyStringVectorData = new StringVectorData;
const ConstMatchesDataPtr g_emptyMatches = new MatchesData( g_emptyStringVectorData, MatchesData::DescendantMatches(), false );

struct ParentScope : public Context::EditableScope
{
	ParentScope( const Context *context, const ScenePlug::ScenePath &path )
		:	Context::EditableScope( context )
	{
		if( path.size() )
		{
			m_parentPath.assign( path.begin(), path.end() - 1 );
			set( ScenePlug::scenePathContextName, &m_parentPath );
		}
		else
		{
			remove( ScenePlug::scenePathContextName );
		}
	}

	private :

		ScenePlug::ScenePath m_parentPath;

};

vector<InternedString> matchingSetNames( const ScenePlug *scene, const std::string &sets )
{
	ConstInternedStringVectorDataPtr sceneSetNames = scene->setNames();
	unordered_set<InternedString> availableSets(
		sceneSetNames->readable().begin(), sceneSetNames->readable().end()
	);

	vector<InternedString> setTokens;
	IECore::StringAlgo::tokenize( sets, ' ', setTokens );

	vector<InternedString> result;

	for( auto &setToken : setTokens )
	{
		if( !StringAlgo::hasWildcards( setToken.c_str() ) )
		{
			if( availableSets.erase( setToken ) )
			{
				result.push_back( setToken );
			}
		}
		else
		{
			size_t firstAdded = result.size();
			for( auto it = availableSets.begin(); it != availableSets.end(); )
			{
				if( StringAlgo::match( it->c_str(), setToken.c_str() ) )
				{
					result.push_back( *it );
					it = availableSets.erase( it );
				}
				else
				{
					++it;
				}
			}
			std::sort(
				result.begin() + firstAdded, result.end(),
				[] ( const InternedString &a, const InternedString &b ) {
					return a.string() < b.string();
				}
			);
		}
	}

	return result;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// SetQuery node
//////////////////////////////////////////////////////////////////////////

size_t SetQuery::g_firstPlugIndex = 0;

GAFFER_NODE_DEFINE_TYPE( SetQuery )

SetQuery::SetQuery( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "scene" ) );
	addChild( new StringPlug( "location" ) );
	addChild( new StringPlug( "sets" ) );
	addChild( new BoolPlug( "inherit", Plug::In, true ) );
	addChild( new StringVectorDataPlug( "matches", Plug::Out, g_emptyStringVectorData ) );
	addChild( new StringPlug( "firstMatch", Plug::Out ) );
	addChild( new ObjectPlug( "__matchesInternal", Plug::Out, NullObject::defaultNullObject() ) );
}

SetQuery::~SetQuery()
{
}

ScenePlug *SetQuery::scenePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const ScenePlug *SetQuery::scenePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *SetQuery::locationPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *SetQuery::locationPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *SetQuery::setsPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *SetQuery::setsPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::BoolPlug *SetQuery::inheritPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::BoolPlug *SetQuery::inheritPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

Gaffer::StringVectorDataPlug *SetQuery::matchesPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::StringVectorDataPlug *SetQuery::matchesPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 4 );
}

Gaffer::StringPlug *SetQuery::firstMatchPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::StringPlug *SetQuery::firstMatchPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 5 );
}

Gaffer::ObjectPlug *SetQuery::matchesInternalPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::ObjectPlug *SetQuery::matchesInternalPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 6 );
}

void SetQuery::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if( affectsMatchesInternal( input ) )
	{
		outputs.push_back( matchesInternalPlug() );
	}

	if( input == matchesInternalPlug() || input == locationPlug() )
	{
		outputs.push_back( matchesPlug() );
		outputs.push_back( firstMatchPlug() );
	}
}

void SetQuery::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( output == matchesInternalPlug() )
	{
		hashMatchesInternal( context, h );
	}
	else if( output == matchesPlug() )
	{
		const std::string location = locationPlug()->getValue();
		if( !location.empty() )
		{
			ComputeNode::hash( output, context, h );
			auto locationPath = ScenePlug::stringToPath( location );
			ScenePlug::PathScope pathScope( context, &locationPath );
			matchesInternalPlug()->hash( h );
		}
		else
		{
			h = output->defaultHash();
		}
	}
	else if( output == firstMatchPlug() )
	{
		const std::string location = locationPlug()->getValue();
		if( !location.empty() )
		{
			ComputeNode::hash( output, context, h );
			auto locationPath = ScenePlug::stringToPath( location );
			ScenePlug::PathScope pathScope( context, &locationPath );
			matchesInternalPlug()->hash( h );
		}
		else
		{
			h = output->defaultHash();
		}
	}
	else
	{
		ComputeNode::hash( output, context, h );
	}
}

void SetQuery::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == matchesInternalPlug() )
	{
		static_cast<ObjectPlug *>( output )->setValue( computeMatchesInternal( context ) );
	}
	else if( output == matchesPlug() )
	{
		const std::string location = locationPlug()->getValue();
		if( !location.empty() )
		{
			auto locationPath = ScenePlug::stringToPath( location );
			ScenePlug::PathScope pathScope( context, &locationPath );
			auto matchesData = boost::static_pointer_cast<const MatchesData>( matchesInternalPlug()->getValue() );
			static_cast<StringVectorDataPlug *>( output )->setValue( matchesData->matches );
		}
		else
		{
			output->setToDefault();
		}
	}
	else if( output == firstMatchPlug() )
	{
		const std::string location = locationPlug()->getValue();
		if( !location.empty() )
		{
			auto locationPath = ScenePlug::stringToPath( location );
			ScenePlug::PathScope pathScope( context, &locationPath );
			auto matchesData = boost::static_pointer_cast<const MatchesData>( matchesInternalPlug()->getValue() );
			static_cast<StringPlug *>( output )->setValue( matchesData->matches->readable().size() ? matchesData->matches->readable().front() : "" );
		}
		else
		{
			output->setToDefault();
		}
	}
	else
	{
		ComputeNode::compute( output, context );
	}
}

Gaffer::ValuePlug::CachePolicy SetQuery::computeCachePolicy( const ValuePlug *output ) const
{
	if( output == firstMatchPlug() || output == matchesPlug() )
	{
		// Since these computes just delegate directly to `__matchesInternal` there's
		// no benefit in caching the results separately.
		return ValuePlug::CachePolicy::Uncached;
	}
	else
	{
		return ComputeNode::computeCachePolicy( output );
	}
}

bool SetQuery::affectsMatchesInternal( const Gaffer::Plug *input ) const
{
	return
		input == scenePlug()->setNamesPlug() ||
		input == setsPlug() ||
		input == scenePlug()->setPlug() ||
		input == inheritPlug()
	;
}

void SetQuery::hashMatchesInternal( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( matchesInternalPlug(), context, h );

	auto path = context->getIfExists<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
	if( !path )
	{
		for( const auto &setName : matchingSetNames( scenePlug(), setsPlug()->getValue() ) )
		{
			h.append( setName );
			// Note : We don't actually compute the set in the corresponding
			// part of `computeMatchesInternal()` so don't _need_ to hash it
			// here. But doing it here means we only pay for it once, and get
			// to inherit it down to all descendants far more cheaply than we
			// would by repeating it for every location.
			h.append( scenePlug()->setHash( setName ) );
		}
		inheritPlug()->hash( h );
	}
	else
	{
		ParentScope scope( context, *path );
		matchesInternalPlug()->hash( h );
		h.append( *path );
		// Note : Here we _should_ be hashing the relevant sets, but instead we
		// rely on inheriting the hash via the recursive inclusion of
		// `matchesInternalPlug()->hash( h )`.
	}
}

IECore::ConstObjectPtr SetQuery::computeMatchesInternal( const Gaffer::Context *context ) const
{
	auto path = context->getIfExists<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
	if( !path )
	{
		// We are the "ancestor" of the _root_, so our potential descendant matches are all
		// the sets listed in `setsPlug()`, taking into account wildcards.
		MatchesData::DescendantMatches descendantMatches;
		for( const auto &setName : matchingSetNames( scenePlug(), setsPlug()->getValue() ) )
		{
			descendantMatches.push_back( { setName, /* inherited = */ false } );
		}
		return new MatchesData(
			g_emptyStringVectorData,
			std::move( descendantMatches ),
			inheritPlug()->getValue()
		);
	}
	else
	{
		// Recurse to retrieve MatchesData from parent.

		ParentScope scope( context, *path );
		ConstMatchesDataPtr parentMatches = boost::static_pointer_cast<const MatchesData>( matchesInternalPlug()->getValue() );

		// Optimisation for common cases, where we can reuse previous results
		// because there are no additional matches at this location.

		if( parentMatches->descendantMatches.empty() )
		{
			return parentMatches->inherit ? parentMatches : g_emptyMatches;
		}

		// Compute new MatchesData for this location.

		StringVectorDataPtr matchesData = new StringVectorData;
		vector<string> &matches = matchesData->writable();
		MatchesData::DescendantMatches descendantMatches;

		for( const auto &[setName, inherited] : parentMatches->descendantMatches )
		{
			unsigned m;
			if( inherited )
			{
				m = IECore::PathMatcher::ExactMatch | IECore::PathMatcher::DescendantMatch;
			}
			else
			{
				m = scenePlug()->set( setName )->readable().match( *path );
			}

			if( m & PathMatcher::ExactMatch )
			{
				matches.push_back( setName );
			}

			if( parentMatches->inherit && ( m & PathMatcher::ExactMatch ) )
			{
				descendantMatches.push_back( { setName, /* inherited = */ true } );
			}
			else if( m & PathMatcher::DescendantMatch )
			{
				descendantMatches.push_back( { setName, /* inherited = */ false } );
			}
		}

		if( std::all_of( descendantMatches.begin(), descendantMatches.end(), [] ( const auto &m ) { return m.inherited; } ) )
		{
			// All descendant matches are inherited. Clear them to trigger
			// optimisation where this MatchesData is reused for children.
			descendantMatches.clear();
		}

		return new MatchesData( matchesData, std::move( descendantMatches ), parentMatches->inherit );
	}
}

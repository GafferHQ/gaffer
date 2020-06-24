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

#include "GafferScene/Isolate.h"

#include "Gaffer/Context.h"
#include "Gaffer/StringPlug.h"

#include "boost/algorithm/string/predicate.hpp"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

//////////////////////////////////////////////////////////////////////////
// Isolate::SetsToKeep
//////////////////////////////////////////////////////////////////////////

namespace
{

InternedString g_lightsSetName( "__lights" );
InternedString g_camerasSetName( "__cameras" );

} // namespace

struct Isolate::SetsToKeep
{

	SetsToKeep( const Isolate *isolate )
	{
		const ScenePlug *scene = isolate->inPlug();

		for( int i = 0; i < 2; ++i )
		{
			const BoolPlug *p = i == 0 ? isolate->keepLightsPlug() : isolate->keepCamerasPlug();
			if( p->getValue() )
			{
				m_setOwners[i] = scene->set( i == 0 ? g_lightsSetName : g_camerasSetName );
				m_sets[i] = &(m_setOwners[i]->readable());
			}
			else
			{
				m_sets[i] = nullptr;
			}
		}
	}

	unsigned match( const ScenePath &path ) const
	{
		unsigned result = IECore::PathMatcher::NoMatch;
		for( int i = 0; i < 2; ++i )
		{
			if( m_sets[i] )
			{
				result |= m_sets[i]->match( path );
			}
		}

		return result;
	}

	private :

		IECore::ConstPathMatcherDataPtr m_setOwners[2];
		const PathMatcher *m_sets[2];

};

//////////////////////////////////////////////////////////////////////////
// Isolate
//////////////////////////////////////////////////////////////////////////

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( Isolate );

size_t Isolate::g_firstPlugIndex = 0;

Isolate::Isolate( const std::string &name )
	:	FilteredSceneProcessor( name, IECore::PathMatcher::EveryMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "from", Plug::In, "/" ) );
	addChild( new BoolPlug( "keepLights" ) );
	addChild( new BoolPlug( "keepCameras" ) );
	addChild( new BoolPlug( "adjustBounds", Plug::In, false ) );

	// Direct pass-throughs
	outPlug()->transformPlug()->setInput( inPlug()->transformPlug() );
	outPlug()->attributesPlug()->setInput( inPlug()->attributesPlug() );
	outPlug()->objectPlug()->setInput( inPlug()->objectPlug() );
	outPlug()->globalsPlug()->setInput( inPlug()->globalsPlug() );
	outPlug()->setNamesPlug()->setInput( inPlug()->setNamesPlug() );
}

Isolate::~Isolate()
{
}

Gaffer::StringPlug *Isolate::fromPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *Isolate::fromPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *Isolate::keepLightsPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *Isolate::keepLightsPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

Gaffer::BoolPlug *Isolate::keepCamerasPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::BoolPlug *Isolate::keepCamerasPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

Gaffer::BoolPlug *Isolate::adjustBoundsPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::BoolPlug *Isolate::adjustBoundsPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

void Isolate::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FilteredSceneProcessor::affects( input, outputs );

	const ScenePlug *in = inPlug();
	if( input->parent<ScenePlug>() == in )
	{
		outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );
	}
	else if( input == filterPlug() || input == fromPlug() || input == keepLightsPlug() || input == keepCamerasPlug() )
	{
		outputs.push_back( outPlug()->childNamesPlug() );
		outputs.push_back( outPlug()->setPlug() );
	}
	else if( input == adjustBoundsPlug() )
	{
		outputs.push_back( outPlug()->boundPlug() );
	}
}

void Isolate::hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	const SetsToKeep setsToKeep( this );
	if( adjustBoundsPlug()->getValue() && mayPruneChildren( path, context, setsToKeep ) )
	{
		h = outPlug()->childBoundsHash();
		return;
	}

	// pass through
	h = inPlug()->boundPlug()->hash();
}

Imath::Box3f Isolate::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	const SetsToKeep setsToKeep( this );
	if( adjustBoundsPlug()->getValue() && mayPruneChildren( path, context, setsToKeep ) )
	{
		return outPlug()->childBounds();
	}

	return inPlug()->boundPlug()->getValue();
}

void Isolate::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	const SetsToKeep setsToKeep( this );

	if( mayPruneChildren( path, context, setsToKeep ) )
	{
		// we might be computing new childnames for this level.
		FilteredSceneProcessor::hashChildNames( path, context, parent, h );

		const IECore::MurmurHash inputChildNamesHash = inPlug()->childNamesPlug()->hash();
		h.append( inputChildNamesHash );

		ConstInternedStringVectorDataPtr inputChildNamesData = inPlug()->childNamesPlug()->getValue( &inputChildNamesHash );
		const vector<InternedString> &inputChildNames = inputChildNamesData->readable();

		FilterPlug::SceneScope sceneScope( context, inPlug() );

		ScenePath childPath = path;
		childPath.push_back( InternedString() ); // for the child name
		for( vector<InternedString>::const_iterator it = inputChildNames.begin(), eIt = inputChildNames.end(); it != eIt; ++it )
		{
			childPath[path.size()] = *it;
			const unsigned m = setsToKeep.match( childPath );
			if( m == IECore::PathMatcher::NoMatch )
			{
				sceneScope.set( ScenePlug::scenePathContextName, childPath );
				filterPlug()->hash( h );
			}
			else
			{
				h.append( 0 );
			}
		}
	}
	else
	{
		// pass through
		h = inPlug()->childNamesPlug()->hash();
	}
}

IECore::ConstInternedStringVectorDataPtr Isolate::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	const SetsToKeep setsToKeep( this );

	if( mayPruneChildren( path, context, setsToKeep ) )
	{
		// we may need to delete one or more of our children
		ConstInternedStringVectorDataPtr inputChildNamesData = inPlug()->childNamesPlug()->getValue();
		const vector<InternedString> &inputChildNames = inputChildNamesData->readable();

		InternedStringVectorDataPtr outputChildNamesData = new InternedStringVectorData;
		vector<InternedString> &outputChildNames = outputChildNamesData->writable();

		FilterPlug::SceneScope sceneScope( context, inPlug() );

		ScenePath childPath = path;
		childPath.push_back( InternedString() ); // for the child name
		for( vector<InternedString>::const_iterator it = inputChildNames.begin(), eIt = inputChildNames.end(); it != eIt; it++ )
		{
			childPath[path.size()] = *it;
			unsigned m = setsToKeep.match( childPath );
			if( m == IECore::PathMatcher::NoMatch )
			{
				sceneScope.set( ScenePlug::scenePathContextName, childPath );
				m |= filterPlug()->getValue();
			}
			if( m != IECore::PathMatcher::NoMatch )
			{
				outputChildNames.push_back( *it );
			}
		}

		return outputChildNamesData;
	}
	else
	{
		// pass through
		return inPlug()->childNamesPlug()->getValue();
	}
}

void Isolate::hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	const bool keepLights = keepLightsPlug()->getValue();
	const bool keepCameras = keepCamerasPlug()->getValue();
	if(
		( setName == g_lightsSetName && keepLights ) ||
		( setName == g_camerasSetName && keepCameras )
	)
	{
		h = inPlug()->setPlug()->hash();
		return;
	}

	FilteredSceneProcessor::hashSet( setName, context, parent, h );
	inPlug()->setPlug()->hash( h );
	fromPlug()->hash( h );

	if( keepLights )
	{
		h.append( inPlug()->setHash( g_lightsSetName ) );
	}
	if( keepCameras )
	{
		h.append( inPlug()->setHash( g_camerasSetName ) );
	}

	// The sets themselves do not depend on the "scene:path"
	// context entry - the whole point is that they're global.
	// However, the PathFilter is dependent on scene:path, so
	// we must remove the path before hashing in the filter in
	// case we're computed from multiple contexts with different
	// paths (from a SetFilter for instance). If we didn't do this,
	// our different hashes would lead to huge numbers of redundant
	// calls to computeSet() and a huge overhead in recomputing
	// the same sets repeatedly.
	//
	// See further comments in acceptsInput()
	FilterPlug::SceneScope sceneScope( context, inPlug() );
	sceneScope.remove( ScenePlug::scenePathContextName );
	sceneScope.remove( ScenePlug::setNameContextName );
	filterPlug()->hash( h );
}

IECore::ConstPathMatcherDataPtr Isolate::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstPathMatcherDataPtr inputSetData = inPlug()->setPlug()->getValue();
	if(
		( setName == g_lightsSetName && keepLightsPlug()->getValue() ) ||
		( setName == g_camerasSetName && keepCamerasPlug()->getValue() )
	)
	{
		return inputSetData;
	}

	const PathMatcher &inputSet = inputSetData->readable();
	if( inputSet.isEmpty() )
	{
		return inputSetData;
	}

	PathMatcherDataPtr outputSetData = inputSetData->copy();
	PathMatcher &outputSet = outputSetData->writable();

	FilterPlug::SceneScope sceneScope( context, inPlug() );
	sceneScope.remove( ScenePlug::setNameContextName );

	const std::string fromString = fromPlug()->getValue();
	ScenePlug::ScenePath fromPath; ScenePlug::stringToPath( fromString, fromPath );

	const SetsToKeep setsToKeep( this );

	for( PathMatcher::RawIterator pIt = inputSet.begin(), peIt = inputSet.end(); pIt != peIt; )
	{
		sceneScope.set( ScenePlug::scenePathContextName, *pIt );
		const int m = filterPlug()->getValue() | setsToKeep.match( *pIt );
		if( m & ( IECore::PathMatcher::ExactMatch | IECore::PathMatcher::AncestorMatch ) )
		{
			// We want to keep everything below this point, so
			// can just prune our iteration.
			pIt.prune();
			++pIt;
		}
		else if( m & IECore::PathMatcher::DescendantMatch )
		{
			// We might be removing things below here,
			// so just continue our iteration normally
			// so we can find out.
			++pIt;
		}
		else
		{
			assert( m == IECore::PathMatcher::NoMatch );
			if( boost::starts_with( *pIt, fromPath ) )
			{
				// Not going to keep anything below
				// here, so we can prune traversal
				// entirely.
				outputSet.prune( *pIt );
				pIt.prune();
			}
			++pIt;
		}
	}

	return outputSetData;
}

bool Isolate::mayPruneChildren( const ScenePath &path, const Gaffer::Context *context, const SetsToKeep &setsToKeep ) const
{
	const std::string fromString = fromPlug()->getValue();
	ScenePlug::ScenePath fromPath; ScenePlug::stringToPath( fromString, fromPath );
	if( !boost::starts_with( path, fromPath ) )
	{
		return false;
	}

	unsigned filterMatch = filterValue( context ) | setsToKeep.match( path );
	return filterMatch == IECore::PathMatcher::DescendantMatch || filterMatch == IECore::PathMatcher::NoMatch;
}

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

#include "GafferScene/Prune.h"

#include "Gaffer/Context.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( Prune );

size_t Prune::g_firstPlugIndex = 0;

Prune::Prune( const std::string &name )
	:	FilteredSceneProcessor( name, IECore::PathMatcher::NoMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new BoolPlug( "adjustBounds", Plug::In, false ) );

	// Our `out.bound -> out.childBounds -> out.bound` dependency cycle
	// is legitimate, because `childBounds` evaluates `out.bound` in a
	// different context (at child locations).
	outPlug()->childBoundsPlug()->setFlags( Plug::AcceptsDependencyCycles, true );

	// Direct pass-throughs
	outPlug()->transformPlug()->setInput( inPlug()->transformPlug() );
	outPlug()->attributesPlug()->setInput( inPlug()->attributesPlug() );
	outPlug()->objectPlug()->setInput( inPlug()->objectPlug() );
	outPlug()->globalsPlug()->setInput( inPlug()->globalsPlug() );
	outPlug()->setNamesPlug()->setInput( inPlug()->setNamesPlug() );
}

Prune::~Prune()
{
}

Gaffer::BoolPlug *Prune::adjustBoundsPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex );
}

const Gaffer::BoolPlug *Prune::adjustBoundsPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex );
}

void Prune::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FilteredSceneProcessor::affects( input, outputs );

	if(
		input == adjustBoundsPlug() ||
		input == filterPlug() ||
		input == outPlug()->childBoundsPlug() ||
		input == inPlug()->boundPlug()
	)
	{
		outputs.push_back( outPlug()->boundPlug() );
	}

	if(
		input == filterPlug() ||
		input == inPlug()->childNamesPlug()
	)
	{
		outputs.push_back( outPlug()->childNamesPlug() );
	}

	if(
		input == inPlug()->setPlug() ||
		input == filterPlug()
	)
	{
		outputs.push_back( outPlug()->setPlug() );
	}
}

void Prune::hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( adjustBoundsPlug()->getValue() )
	{
		if( filterValue( context ) & IECore::PathMatcher::DescendantMatch )
		{
			FilteredSceneProcessor::hashBound( path, context, parent, h );
			inPlug()->childNamesPlug()->hash( h );
			outPlug()->childBoundsPlug()->hash( h );
			inPlug()->boundPlug()->hash( h );
			return;
		}
	}

	// pass through
	h = inPlug()->boundPlug()->hash();
}

Imath::Box3f Prune::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( adjustBoundsPlug()->getValue() )
	{
		if( filterValue( context ) & IECore::PathMatcher::DescendantMatch )
		{
			if( inPlug()->childNamesPlug()->getValue()->readable().size() )
			{
				return outPlug()->childBoundsPlug()->getValue();
			}
			else
			{
				// Filter claims there is a descendant match, but there can't be
				// because we have no children. This can happen if a PathFilter
				// contains `...` or a reference to a path that doesn't exist.
				// Since we have no children, and we ourselves are not pruned
				// (we can't be, because it is forbidden to compute a location
				// that doesn't exist), we can pass through the input bound.
				return inPlug()->boundPlug()->getValue();
			}
		}
	}

	return inPlug()->boundPlug()->getValue();
}

void Prune::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	const IECore::PathMatcher::Result m = filterValue( context );

	if( m & IECore::PathMatcher::ExactMatch )
	{
		h = inPlug()->childNamesPlug()->defaultValue()->Object::hash();
	}
	else if( m & IECore::PathMatcher::DescendantMatch )
	{
		// we might be computing new childnames for this level.
		FilteredSceneProcessor::hashChildNames( path, context, parent, h );

		ConstInternedStringVectorDataPtr inputChildNamesData = inPlug()->childNamesPlug()->getValue();
		const vector<InternedString> &inputChildNames = inputChildNamesData->readable();

		FilterPlug::SceneScope sceneScope( context, inPlug() );

		ScenePath childPath = path;
		childPath.push_back( InternedString() ); // for the child name
		for( vector<InternedString>::const_iterator it = inputChildNames.begin(), eIt = inputChildNames.end(); it != eIt; ++it )
		{
			childPath[path.size()] = *it;
			sceneScope.set( ScenePlug::scenePathContextName, &childPath );
			filterPlug()->hash( h );
		}
	}
	else
	{
		// pass through
		h = inPlug()->childNamesPlug()->hash();
	}
}

IECore::ConstInternedStringVectorDataPtr Prune::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	const IECore::PathMatcher::Result m = filterValue( context );

	if( m & IECore::PathMatcher::ExactMatch  )
	{
		return inPlug()->childNamesPlug()->defaultValue();
	}
	else if( m & IECore::PathMatcher::DescendantMatch )
	{
		// we may need to delete one or more of our children
		ConstInternedStringVectorDataPtr inputChildNamesData = inPlug()->childNamesPlug()->getValue();
		const vector<InternedString> &inputChildNames = inputChildNamesData->readable();

		InternedStringVectorDataPtr outputChildNamesData = new InternedStringVectorData;
		vector<InternedString> &outputChildNames = outputChildNamesData->writable();

		FilterPlug::SceneScope sceneScope( context, inPlug() );

		ScenePath childPath = path;
		childPath.push_back( InternedString() ); // for the child name
		for( vector<InternedString>::const_iterator it = inputChildNames.begin(), eIt = inputChildNames.end(); it != eIt; ++it )
		{
			childPath[path.size()] = *it;
			sceneScope.set( ScenePlug::scenePathContextName, &childPath );
			if( !(filterPlug()->getValue() & IECore::PathMatcher::ExactMatch) )
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

void Prune::hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	FilteredSceneProcessor::hashSet( setName, context, parent, h );
	inPlug()->setPlug()->hash( h );

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

IECore::ConstPathMatcherDataPtr Prune::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstPathMatcherDataPtr inputSetData = inPlug()->setPlug()->getValue();
	const PathMatcher &inputSet = inputSetData->readable();
	if( inputSet.isEmpty() )
	{
		return inputSetData;
	}

	PathMatcherDataPtr outputSetData = inputSetData->copy();
	PathMatcher &outputSet = outputSetData->writable();

	FilterPlug::SceneScope sceneScope( context, inPlug() );
	sceneScope.remove( ScenePlug::setNameContextName );

	for( PathMatcher::RawIterator pIt = inputSet.begin(), peIt = inputSet.end(); pIt != peIt; )
	{
		sceneScope.set( ScenePlug::scenePathContextName, &(*pIt) );
		const int m = filterPlug()->getValue();
		if( m & ( IECore::PathMatcher::ExactMatch | IECore::PathMatcher::AncestorMatch ) )
		{
			// This path and all below it are pruned, so we can
			// ignore it and prune the traversal to the descendant
			// paths.
			outputSet.prune( *pIt );
			pIt.prune();
			++pIt;
		}
		else if( m & IECore::PathMatcher::DescendantMatch )
		{
			// This path isn't pruned, so we continue our traversal
			// as normal to find out which descendants _are_ pruned.
			++pIt;
		}
		else
		{
			// This path isn't pruned, and neither is anything
			// below it. We can avoid retesting the filter for
			// all descendant paths, since we know they're not
			// pruned.
			assert( m == IECore::PathMatcher::NoMatch );
			pIt.prune();
			++pIt;
		}
	}

	return outputSetData;
}

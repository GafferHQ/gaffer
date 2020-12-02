//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/Encapsulate.h"

#include "GafferScene/Capsule.h"

#include "boost/bind.hpp"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( Encapsulate );

size_t Encapsulate::g_firstPlugIndex = 0;

Encapsulate::Encapsulate( const std::string &name )
	:	FilteredSceneProcessor( name, IECore::PathMatcher::NoMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	outPlug()->boundPlug()->setInput( inPlug()->boundPlug() );
	outPlug()->transformPlug()->setInput( inPlug()->transformPlug() );
	outPlug()->attributesPlug()->setInput( inPlug()->attributesPlug() );
	outPlug()->globalsPlug()->setInput( inPlug()->globalsPlug() );
	outPlug()->setNamesPlug()->setInput( inPlug()->setNamesPlug() );
}

Encapsulate::~Encapsulate()
{
}

void Encapsulate::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	FilteredSceneProcessor::affects( input, outputs );

	if(
		input == filterPlug() ||
		input->parent() == inPlug()
	)
	{
		outputs.push_back( outPlug()->objectPlug() );
	}

	if(
		input == filterPlug() ||
		input == inPlug()->childNamesPlug()
	)
	{
		outputs.push_back( outPlug()->childNamesPlug() );
	}

	if(
		input == filterPlug() ||
		input == inPlug()->setPlug()
	)
	{
		outputs.push_back( outPlug()->setPlug() );
	}
}

IECore::PathMatcher::Result Encapsulate::filterValueChecked( const Gaffer::Context *context ) const
{
	IECore::PathMatcher::Result f = filterValue( context );
	if( f & IECore::PathMatcher::AncestorMatch )
	{
		std::string locationStr;
		ScenePlug::pathToString( context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName ), locationStr );
		throw IECore::Exception(
			"Tried to access path \"" + locationStr + "\", but its ancestor has been converted to a capsule"
		);
	}
	return f;
}

void Encapsulate::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( filterValueChecked( context ) & IECore::PathMatcher::ExactMatch )
	{
		FilteredSceneProcessor::hashObject( path, context, parent, h );
		// What we really want here is a hash uniquely identifying the
		// entire input hierarchy beneath path, in the current context.
		// Currently we could only compute that by traversing the full
		// hierarchy from the root down, which might be prohibitively
		// expensive. Instead we resort to a "poor man's hash" based on our
		// identity, the number of times our input has been dirtied and
		// the _entire_ context. This is less accurate and not stable
		// between processes, but much faster.
		/// \todo Is this the right approach? Should we just suck it
		/// up and compute the accurate hash? Or at least provide the
		/// option?
		h.append( reinterpret_cast<uint64_t>( this ) );

		/// \todo : This shouldn't include the dirtyCount of the globals plug,
		/// once we fix things so that capsules don't depend on the shutter
		/// setting of the source scene
		h.append( inPlug()->dirtyCount() );
		h.append( context->hash() );
		inPlug()->boundPlug()->hash( h );
	}
	else
	{
		h = inPlug()->objectPlug()->hash();
	}
}

IECore::ConstObjectPtr Encapsulate::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( filterValueChecked( context ) & IECore::PathMatcher::ExactMatch )
	{
		return new Capsule(
			inPlug()->source<ScenePlug>(),
			path,
			*context,
			outPlug()->objectPlug()->hash(),
			inPlug()->boundPlug()->getValue()
		);
	}
	else
	{
		return inPlug()->objectPlug()->getValue();
	}
}

void Encapsulate::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( filterValueChecked( context ) & IECore::PathMatcher::ExactMatch )
	{
		h = outPlug()->childNamesPlug()->defaultValue()->Object::hash();
	}
	else
	{
		h = inPlug()->childNamesPlug()->hash();
	}
}

IECore::ConstInternedStringVectorDataPtr Encapsulate::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( filterValueChecked( context ) & IECore::PathMatcher::ExactMatch )
	{
		return outPlug()->childNamesPlug()->defaultValue();
	}
	else
	{
		return inPlug()->childNamesPlug()->getValue();
	}
}

void Encapsulate::hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
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
	filterPlug()->hash( h );
}

IECore::ConstPathMatcherDataPtr Encapsulate::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const
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

	for( PathMatcher::RawIterator pIt = inputSet.begin(), peIt = inputSet.end(); pIt != peIt; )
	{
		sceneScope.set( ScenePlug::scenePathContextName, *pIt );
		const int m = filterPlug()->getValue();
		if( m & ( IECore::PathMatcher::ExactMatch | IECore::PathMatcher::AncestorMatch ) )
		{
			// All paths below here are encapsulated, so we can
			// remove them from the set and prune our traversal.
			PathMatcher::RawIterator cIt = pIt;
			cIt++;
			while( cIt->size() > pIt->size() )
			{
				outputSet.prune( *cIt );
				cIt.prune();
				++cIt;
			}
			pIt.prune();
			++pIt;
		}
		else if( m & IECore::PathMatcher::DescendantMatch )
		{
			// This path isn't encapsulated, so we continue our traversal
			// as normal to find out which descendants _are_ encapsulated.
			++pIt;
		}
		else
		{
			// This path isn't encapsulated, and neither is anything
			// below it. We can prune our traversal.
			assert( m == IECore::PathMatcher::NoMatch );
			pIt.prune();
			++pIt;
		}
	}

	return outputSetData;
}

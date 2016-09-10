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

#include "GafferScene/Prune.h"
#include "GafferScene/PathMatcherData.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( Prune );

size_t Prune::g_firstPlugIndex = 0;

Prune::Prune( const std::string &name )
	:	FilteredSceneProcessor( name, Filter::NoMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new BoolPlug( "adjustBounds", Plug::In, false ) );

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

	const ScenePlug *in = inPlug();
	if( input->parent<ScenePlug>() == in )
	{
		outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );
	}
	else if( input == filterPlug() )
	{
		outputs.push_back( outPlug()->childNamesPlug() );
		outputs.push_back( outPlug()->setPlug() );
	}
	else if( input == adjustBoundsPlug() )
	{
		outputs.push_back( outPlug()->boundPlug() );
	}
}

bool Prune::acceptsInput( const Gaffer::Plug *plug, const Gaffer::Plug *inputPlug ) const
{
	if( !FilteredSceneProcessor::acceptsInput( plug, inputPlug ) )
	{
		return false;
	}

	if( plug == filterPlug() )
	{
		if( const Filter *filter = runTimeCast<const Filter>( inputPlug->source<Plug>()->node() ) )
		{
			if(
				filter->sceneAffectsMatch( inPlug(), inPlug()->boundPlug() ) ||
				filter->sceneAffectsMatch( inPlug(), inPlug()->transformPlug() ) ||
				filter->sceneAffectsMatch( inPlug(), inPlug()->attributesPlug() ) ||
				filter->sceneAffectsMatch( inPlug(), inPlug()->objectPlug() ) ||
				filter->sceneAffectsMatch( inPlug(), inPlug()->childNamesPlug() )
			)
			{
				// We make a single call to filterHash() in hashSet(), to account for
				// the fact that the filter is used in remapping sets. This wouldn't
				// work for filter types which actually vary based on data within the
				// scene hierarchy, because then multiple calls would be necessary.
				// We could make more calls here, but that would be expensive.
				/// \todo In an ideal world we'd be able to compute a hash for the
				/// filter across a whole hierarchy.
				return false;
			}
		}
	}

	return true;
}

void Prune::hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( adjustBoundsPlug()->getValue() )
	{
		if( filterValue( context ) & Filter::DescendantMatch )
		{
			h = hashOfTransformedChildBounds( path, outPlug() );
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
		if( filterValue( context ) & Filter::DescendantMatch )
		{
			return unionOfTransformedChildBounds( path, outPlug() );
		}
	}

	return inPlug()->boundPlug()->getValue();
}

void Prune::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ContextPtr tmpContext = filterContext( context );
	Context::Scope scopedContext( tmpContext.get() );
	const Filter::Result m = (Filter::Result)filterPlug()->getValue();

	if( m & Filter::ExactMatch )
	{
		h = inPlug()->childNamesPlug()->defaultValue()->Object::hash();
	}
	else if( m & Filter::DescendantMatch )
	{
		// we might be computing new childnames for this level.
		FilteredSceneProcessor::hashChildNames( path, context, parent, h );

		ConstInternedStringVectorDataPtr inputChildNamesData = inPlug()->childNamesPlug()->getValue();
		const vector<InternedString> &inputChildNames = inputChildNamesData->readable();

		ScenePath childPath = path;
		childPath.push_back( InternedString() ); // for the child name
		for( vector<InternedString>::const_iterator it = inputChildNames.begin(), eIt = inputChildNames.end(); it != eIt; ++it )
		{
			childPath[path.size()] = *it;
			tmpContext->set( ScenePlug::scenePathContextName, childPath );
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
	ContextPtr tmpContext = filterContext( context );
	Context::Scope scopedContext( tmpContext.get() );
	const Filter::Result m = (Filter::Result)filterPlug()->getValue();

	if( m & Filter::ExactMatch  )
	{
		return inPlug()->childNamesPlug()->defaultValue();
	}
	else if( m & Filter::DescendantMatch )
	{
		// we may need to delete one or more of our children
		ConstInternedStringVectorDataPtr inputChildNamesData = inPlug()->childNamesPlug()->getValue();
		const vector<InternedString> &inputChildNames = inputChildNamesData->readable();

		InternedStringVectorDataPtr outputChildNamesData = new InternedStringVectorData;
		vector<InternedString> &outputChildNames = outputChildNamesData->writable();

		ScenePath childPath = path;
		childPath.push_back( InternedString() ); // for the child name
		for( vector<InternedString>::const_iterator it = inputChildNames.begin(), eIt = inputChildNames.end(); it != eIt; ++it )
		{
			childPath[path.size()] = *it;
			tmpContext->set( ScenePlug::scenePathContextName, childPath );
			if( !(filterPlug()->getValue() & Filter::ExactMatch) )
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
	FilteredSceneProcessor::hashGlobals( context, parent, h );
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
	ContextPtr c = filterContext( context );
	c->remove( ScenePlug::scenePathContextName );
	Context::Scope s( c.get() );
	filterPlug()->hash( h );
}

GafferScene::ConstPathMatcherDataPtr Prune::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstPathMatcherDataPtr inputSetData = inPlug()->setPlug()->getValue();
	const PathMatcher &inputSet = inputSetData->readable();
	if( inputSet.isEmpty() )
	{
		return inputSetData;
	}

	PathMatcherDataPtr outputSetData = inputSetData->copy();
	PathMatcher &outputSet = outputSetData->writable();

	ContextPtr tmpContext = filterContext( context );
	Context::Scope scopedContext( tmpContext.get() );

	for( PathMatcher::RawIterator pIt = inputSet.begin(), peIt = inputSet.end(); pIt != peIt; )
	{
		tmpContext->set( ScenePlug::scenePathContextName, *pIt );
		const int m = filterPlug()->getValue();
		if( m & ( Filter::ExactMatch | Filter::AncestorMatch ) )
		{
			// This path and all below it are pruned, so we can
			// ignore it and prune the traversal to the descendant
			// paths.
			outputSet.prune( *pIt );
			pIt.prune();
			++pIt;
		}
		else if( m & Filter::DescendantMatch )
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
			assert( m == Filter::NoMatch );
			pIt.prune();
			++pIt;
		}
	}

	return outputSetData;
}

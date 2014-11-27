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

#include "boost/algorithm/string/predicate.hpp"

#include "Gaffer/Context.h"

#include "GafferScene/Isolate.h"
#include "GafferScene/PathMatcherData.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( Isolate );

size_t Isolate::g_firstPlugIndex = 0;

Isolate::Isolate( const std::string &name )
	:	FilteredSceneProcessor( name, Filter::EveryMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "from", Plug::In, "/" ) );
	addChild( new BoolPlug( "adjustBounds", Plug::In, false ) );
	
	// Direct pass-throughs
	outPlug()->transformPlug()->setInput( inPlug()->transformPlug() );
	outPlug()->attributesPlug()->setInput( inPlug()->attributesPlug() );
	outPlug()->objectPlug()->setInput( inPlug()->objectPlug() );
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

Gaffer::BoolPlug *Isolate::adjustBoundsPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *Isolate::adjustBoundsPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

void Isolate::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FilteredSceneProcessor::affects( input, outputs );

	const ScenePlug *in = inPlug();
	if( input->parent<ScenePlug>() == in )
	{
		outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );
	}
	else if( input == filterPlug() || input == fromPlug() )
	{
		outputs.push_back( outPlug()->childNamesPlug() );
		outputs.push_back( outPlug()->globalsPlug() );
	}
	else if( input == adjustBoundsPlug() )
	{
		outputs.push_back( outPlug()->boundPlug() );
	}
}

void Isolate::hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( adjustBoundsPlug()->getValue() && mayPruneChildren( path, filterValue( context ) ) )
	{
		h = hashOfTransformedChildBounds( path, outPlug() );
		return;
	}

	// pass through
	h = inPlug()->boundPlug()->hash();
}

Imath::Box3f Isolate::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( adjustBoundsPlug()->getValue() && mayPruneChildren( path, filterValue( context ) ) )
	{
		return unionOfTransformedChildBounds( path, outPlug() );
	}

	return inPlug()->boundPlug()->getValue();
}

void Isolate::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ContextPtr tmpContext = filterContext( context );
	Context::Scope scopedContext( tmpContext.get() );

	if( mayPruneChildren( path, filterPlug()->getValue() ) )
	{
		// we might be computing new childnames for this level.
		FilteredSceneProcessor::hashChildNames( path, context, parent, h );
		inPlug()->childNamesPlug()->hash( h );
		filterPlug()->hash( h );
	}
	else
	{
		// pass through
		h = inPlug()->childNamesPlug()->hash();
	}
}

IECore::ConstInternedStringVectorDataPtr Isolate::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ContextPtr tmpContext = filterContext( context );
	Context::Scope scopedContext( tmpContext.get() );

	if( mayPruneChildren( path, filterPlug()->getValue() ) )
	{
		// we may need to delete one or more of our children
		ConstInternedStringVectorDataPtr inputChildNamesData = inPlug()->childNamesPlug()->getValue();
		const vector<InternedString> &inputChildNames = inputChildNamesData->readable();

		InternedStringVectorDataPtr outputChildNamesData = new InternedStringVectorData;
		vector<InternedString> &outputChildNames = outputChildNamesData->writable();

		ScenePath childPath = path;
		childPath.push_back( InternedString() ); // for the child name
		for( vector<InternedString>::const_iterator it = inputChildNames.begin(), eIt = inputChildNames.end(); it != eIt; it++ )
		{
			childPath[path.size()] = *it;
			tmpContext->set( ScenePlug::scenePathContextName, childPath );
			if( filterPlug()->getValue() != Filter::NoMatch )
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

void Isolate::hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	FilteredSceneProcessor::hashGlobals( context, parent, h );
	inPlug()->globalsPlug()->hash( h );
	fromPlug()->hash( h );

	// The globals themselves do not depend on the "scene:path"
	// context entry - the whole point is that they're global.
	// However, the PathFilter is dependent on scene:path, so
	// we must remove the path before hashing in the filter in
	// case we're computed from multiple contexts with different
	// paths (from a SetFilter for instance). If we didn't do this,
	// our different hashes would lead to huge numbers of redundant
	// calls to computeGlobals() and a huge overhead in recomputing
	// the same sets repeatedly.
	//
	// See further comments in FilteredSceneProcessor::affects().
	ContextPtr c = filterContext( context );
	c->remove( ScenePlug::scenePathContextName );
	Context::Scope s( c.get() );
	filterPlug()->hash( h );
}

IECore::ConstCompoundObjectPtr Isolate::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstCompoundObjectPtr inputGlobals = inPlug()->globalsPlug()->getValue();
	const CompoundData *inputSets = inputGlobals->member<CompoundData>( "gaffer:sets" );
	if( !inputSets )
	{
		return inputGlobals;
	}

	CompoundObjectPtr outputGlobals = inputGlobals->copy();
	CompoundDataPtr outputSets = new CompoundData;
	outputGlobals->members()["gaffer:sets"] = outputSets;

	ContextPtr tmpContext = filterContext( context );
	Context::Scope scopedContext( tmpContext.get() );
	ScenePath path;

	const std::string fromString = fromPlug()->getValue();
	ScenePlug::ScenePath fromPath; ScenePlug::stringToPath( fromString, fromPath );

	for( CompoundDataMap::const_iterator it = inputSets->readable().begin(), eIt = inputSets->readable().end(); it != eIt; ++it )
	{
		/// \todo This could be more efficient if PathMatcher exposed the internal nodes,
		/// and allowed sharing between matchers. Then we could do a really lightweight copy
		/// and just trim out the nodes we didn't want.
		const PathMatcher &inputSet = static_cast<const PathMatcherData *>( it->second.get() )->readable();
		PathMatcher &outputSet = outputSets->member<PathMatcherData>( it->first, /* throwExceptions = */ false, /* createIfMissing = */ true )->writable();

		vector<string> inputPaths;
		inputSet.paths( inputPaths );
		for( vector<string>::const_iterator pIt = inputPaths.begin(), peIt = inputPaths.end(); pIt != peIt; ++pIt )
		{
			path.clear();
			ScenePlug::stringToPath( *pIt, path );
			bool prune = false;
			if( boost::starts_with( path, fromPath ) )
			{
				tmpContext->set( ScenePlug::scenePathContextName, path );
				prune = filterPlug()->getValue() == Filter::NoMatch;
			}
			if( !prune )
			{
				outputSet.addPath( path );
			}
		}
	}

	return outputGlobals;
}

bool Isolate::mayPruneChildren( const ScenePath &path, unsigned filterValue ) const
{
	const std::string fromString = fromPlug()->getValue();
	ScenePlug::ScenePath fromPath; ScenePlug::stringToPath( fromString, fromPath );
	if( !boost::starts_with( path, fromPath ) )
	{
		return false;
	}

	return filterValue == Filter::DescendantMatch;
}

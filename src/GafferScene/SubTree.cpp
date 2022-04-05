//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "GafferScene/SubTree.h"

#include "GafferScene/SceneAlgo.h"

#include "Gaffer/StringPlug.h"

#include "boost/algorithm/string/predicate.hpp"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( SubTree );

size_t SubTree::g_firstPlugIndex = 0;

SubTree::SubTree( const std::string &name )
	:	SceneProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "root", Plug::In, "" ) );
	addChild( new BoolPlug( "includeRoot", Plug::In, false ) );
	addChild( new BoolPlug( "inheritTransform", Plug::In, false ) );
	addChild( new BoolPlug( "inheritAttributes", Plug::In, false ) );
	addChild( new BoolPlug( "inheritSetMembership", Plug::In, false ) );

	outPlug()->childBoundsPlug()->setFlags( Plug::AcceptsDependencyCycles, true );

	// Fast pass-throughs for things we don't modify.
	outPlug()->globalsPlug()->setInput( inPlug()->globalsPlug() );
	outPlug()->setNamesPlug()->setInput( inPlug()->setNamesPlug() );
}

SubTree::~SubTree()
{
}

Gaffer::StringPlug *SubTree::rootPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *SubTree::rootPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *SubTree::includeRootPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *SubTree::includeRootPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

Gaffer::BoolPlug *SubTree::inheritTransformPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::BoolPlug *SubTree::inheritTransformPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

Gaffer::BoolPlug *SubTree::inheritAttributesPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::BoolPlug *SubTree::inheritAttributesPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

Gaffer::BoolPlug *SubTree::inheritSetMembershipPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::BoolPlug *SubTree::inheritSetMembershipPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 4 );
}

void SubTree::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneProcessor::affects( input, outputs );

	const bool affectsSourcePath = input == rootPlug() || input == includeRootPlug() || input == inPlug()->existsPlug();

	if(
		affectsSourcePath ||
		input == inPlug()->boundPlug() ||
		input == outPlug()->childBoundsPlug()
	)
	{
		outputs.push_back( outPlug()->boundPlug() );
	}

	if(
		affectsSourcePath ||
		input == inPlug()->transformPlug() ||
		input == inheritTransformPlug()
	)
	{
		outputs.push_back( outPlug()->transformPlug() );
	}

	if(
		affectsSourcePath ||
		input == inPlug()->attributesPlug() ||
		input == inheritAttributesPlug()
	)
	{
		outputs.push_back( outPlug()->attributesPlug() );
	}

	if( affectsSourcePath || input == inPlug()->objectPlug() )
	{
		outputs.push_back( outPlug()->objectPlug() );
	}

	if( affectsSourcePath || input == inPlug()->childNamesPlug() )
	{
		outputs.push_back( outPlug()->childNamesPlug() );
	}

	if(
		input == inPlug()->setPlug() ||
		input == rootPlug() ||
		input == includeRootPlug() ||
		input == inheritSetMembershipPlug()
	)
	{
		outputs.push_back( outPlug()->setPlug() );
	}
}

void SubTree::hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SourceMode sourceMode = Default;
	ScenePath source = sourcePath( path, sourceMode );
	switch( sourceMode )
	{
		case Default :
			h = inPlug()->boundHash( source );
			break;
		case CreateRoot :
			h = parent->childBoundsPlug()->hash();
			break;
		case EmptyRoot :
			SceneProcessor::hashBound( path, context, parent, h );
			break;
	}
}

Imath::Box3f SubTree::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	SourceMode sourceMode = Default;
	const ScenePath source = sourcePath( path, sourceMode );
	switch( sourceMode )
	{
		case Default :
			return inPlug()->bound( source );
		case CreateRoot :
			return parent->childBoundsPlug()->getValue();
		default : // EmptyRoot
			return Imath::Box3f();
	}
}

void SubTree::hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SourceMode sourceMode = Default;
	ScenePath source = sourcePath( path, sourceMode );
	assert( sourceMode == Default ); // SceneNode::hash() shouldn't call this for the root path
	if( path.size() == 1 && inheritTransformPlug()->getValue() )
	{
		h = inPlug()->fullTransformHash( source );
	}
	else
	{
		h = inPlug()->transformHash( source );
	}
}

Imath::M44f SubTree::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	SourceMode sourceMode = Default;
	const ScenePath source = sourcePath( path, sourceMode );
	assert( sourceMode == Default ); // SceneNode::compute() shouldn't call this for the root path
	if( path.size() == 1 && inheritTransformPlug()->getValue() )
	{
		return inPlug()->fullTransform( source );
	}
	else
	{
		return inPlug()->transform( source );
	}
}

void SubTree::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SourceMode sourceMode = Default;
	ScenePath source = sourcePath( path, sourceMode );
	assert( sourceMode == Default ); // SceneNode::hash() shouldn't call this for the root path
	if( path.size() == 1 && inheritAttributesPlug()->getValue() )
	{
		h = inPlug()->fullAttributesHash( source );
	}
	else
	{
		h = inPlug()->attributesHash( source );
	}
}

IECore::ConstCompoundObjectPtr SubTree::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	SourceMode sourceMode = Default;
	const ScenePath source = sourcePath( path, sourceMode );
	assert( sourceMode == Default ); // SceneNode::compute() shouldn't call this for the root path
	if( path.size() == 1 && inheritAttributesPlug()->getValue() )
	{
		return inPlug()->fullAttributes( source );
	}
	else
	{
		return inPlug()->attributes( source );
	}
}

void SubTree::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SourceMode sourceMode = Default;
	ScenePath source = sourcePath( path, sourceMode );
	assert( sourceMode == Default ); // SceneNode::hash() shouldn't call this for the root path
	h = inPlug()->objectHash( source );
}

IECore::ConstObjectPtr SubTree::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	SourceMode sourceMode = Default;
	const ScenePath source = sourcePath( path, sourceMode );
	assert( sourceMode == Default ); // SceneNode::compute() shouldn't call this for the root path
	return inPlug()->object( source );
}

void SubTree::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SourceMode sourceMode = Default;
	const ScenePath source = sourcePath( path, sourceMode );
	switch( sourceMode )
	{
		case Default :
			h = inPlug()->childNamesHash( source );
			break;
		case CreateRoot :
			SceneProcessor::hashChildNames( path, context, parent, h );
			h.append( *(source.rbegin()) );
			break;
		case EmptyRoot :
			h = inPlug()->childNamesPlug()->defaultValue()->Object::hash();
			break;
	}
}

IECore::ConstInternedStringVectorDataPtr SubTree::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	SourceMode sourceMode = Default;
	const ScenePath source = sourcePath( path, sourceMode );
	switch( sourceMode )
	{
		case Default :
			return inPlug()->childNames( source );
		case CreateRoot : {
			IECore::InternedStringVectorDataPtr result = new IECore::InternedStringVectorData;
			result->writable().push_back( *(source.rbegin()) );
			return result;
		}
		default : // EmptyRoot
			return inPlug()->childNamesPlug()->defaultValue();
	}
}

void SubTree::hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneProcessor::hashSet( setName, context, parent, h );
	inPlug()->setPlug()->hash( h );
	rootPlug()->hash( h );
	includeRootPlug()->hash( h );
	inheritSetMembershipPlug()->hash( h );
	h.append( outPlug()->childNamesHash( {} ) );
}

IECore::ConstPathMatcherDataPtr SubTree::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstPathMatcherDataPtr inputSetData = inPlug()->setPlug()->getValue();
	const PathMatcher &inputSet = inputSetData->readable();
	if( inputSet.isEmpty() )
	{
		return inputSetData;
	}

	ScenePlug::ScenePath root;
	ScenePlug::stringToPath( rootPlug()->getValue(), root );

	const bool includeRoot = includeRootPlug()->getValue();
	ScenePlug::ScenePath prefix;
	if( includeRoot && root.size() )
	{
		prefix.push_back( root.back() );
	}

	PathMatcherDataPtr outputSetData = new PathMatcherData;
	outputSetData->writable().addPaths( inputSet.subTree( root ), prefix );

	if( inheritSetMembershipPlug()->getValue() && root.size() )
	{
		// Remove `/`, because we will be putting all top-level children in
		// explicitly anyway.
		/// \todo Arguably we should be removing `/` even when not inheriting
		/// set membership. The user can't select or see `/` and nodes can't modify
		/// its transform or attributes. So including it is a potential cause of
		/// confusion.
		outputSetData->writable().removePath( ScenePath() );

		const unsigned match = inputSet.match( root );
		if( match & ( PathMatcher::AncestorMatch | PathMatcher::ExactMatch ) )
		{
			if( includeRoot )
			{
				outputSetData->writable().addPath( prefix );
			}
			else
			{
				ConstInternedStringVectorDataPtr rootChildNames = outPlug()->childNames( {} );
				ScenePlug::ScenePath path( 1 );
				for( auto &rootChildName : rootChildNames->readable() )
				{
					path.back() = rootChildName;
					outputSetData->writable().addPath( path );
				}
			}
		}
	}

	return outputSetData;
}

SceneNode::ScenePath SubTree::sourcePath( const ScenePath &outputPath, SourceMode &sourceMode ) const
{
	/// \todo We should introduce a plug type which stores its values as a ScenePath directly.
	string rootAsString = rootPlug()->getValue();
	ScenePath result;
	ScenePlug::stringToPath( rootAsString, result );

	sourceMode = Default;
	if( result.size() && includeRootPlug()->getValue() )
	{
		if( outputPath.size() )
		{
			result.insert( result.end(), outputPath.begin() + 1, outputPath.end() );
		}
		else
		{
			sourceMode = CreateRoot;
		}
	}
	else
	{
		result.insert( result.end(), outputPath.begin(), outputPath.end() );
	}

	if( outputPath.empty() )
	{
		// If the root the user has specified doesn't exist, fall back to EmptyRoot
		// mode so that we output an empty scene. This guarantees that we will never
		// request an invalid source location from our input, provided that we are not
		// asked for an invalid output location.
		if( !inPlug()->exists( result ) )
		{
			sourceMode = EmptyRoot;
		}
	}

	return result;
}

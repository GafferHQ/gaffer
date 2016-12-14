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

#include "boost/algorithm/string/predicate.hpp"

#include "Gaffer/StringPlug.h"

#include "GafferScene/SubTree.h"
#include "GafferScene/PathMatcherData.h"
#include "GafferScene/SceneAlgo.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( SubTree );

size_t SubTree::g_firstPlugIndex = 0;

SubTree::SubTree( const std::string &name )
	:	SceneProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "root", Plug::In, "" ) );
	addChild( new BoolPlug( "includeRoot", Plug::In, false ) );

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

void SubTree::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneProcessor::affects( input, outputs );

	if( input->parent<ScenePlug>() == inPlug() )
	{
		outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );
	}
	else if( input == rootPlug() || input == includeRootPlug() )
	{
		outputs.push_back( outPlug()->boundPlug() );
		outputs.push_back( outPlug()->transformPlug() );
		outputs.push_back( outPlug()->attributesPlug() );
		outputs.push_back( outPlug()->objectPlug() );
		outputs.push_back( outPlug()->childNamesPlug() );
		outputs.push_back( outPlug()->setPlug() );
	}

}

void SubTree::hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	bool createRoot = false;
	ScenePath source = sourcePath( path, createRoot );
	if( createRoot )
	{
		h = hashOfTransformedChildBounds( path, parent );
	}
	else
	{
		h = inPlug()->boundHash( source );
	}
}

Imath::Box3f SubTree::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	bool createRoot = false;
	const ScenePath source = sourcePath( path, createRoot );
	if( createRoot )
	{
		return unionOfTransformedChildBounds( path, parent );
	}
	else
	{
		return inPlug()->bound( source );
	}
}

void SubTree::hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	bool createRoot = false;
	ScenePath source = sourcePath( path, createRoot );
	assert( !createRoot ); // SceneNode::hash() shouldn't call this for the root path
	h = inPlug()->transformHash( source );
}

Imath::M44f SubTree::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	bool createRoot = false;
	const ScenePath source = sourcePath( path, createRoot );
	assert( !createRoot ); // SceneNode::compute() shouldn't call this for the root path
	return inPlug()->transform( source );
}

void SubTree::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	bool createRoot = false;
	ScenePath source = sourcePath( path, createRoot );
	assert( !createRoot ); // SceneNode::hash() shouldn't call this for the root path
	h = inPlug()->attributesHash( source );
}

IECore::ConstCompoundObjectPtr SubTree::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	bool createRoot = false;
	const ScenePath source = sourcePath( path, createRoot );
	assert( !createRoot ); // SceneNode::compute() shouldn't call this for the root path
	return inPlug()->attributes( source );
}

void SubTree::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	bool createRoot = false;
	ScenePath source = sourcePath( path, createRoot );
	assert( !createRoot ); // SceneNode::hash() shouldn't call this for the root path
	h = inPlug()->objectHash( source );
}

IECore::ConstObjectPtr SubTree::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	bool createRoot = false;
	const ScenePath source = sourcePath( path, createRoot );
	assert( !createRoot ); // SceneNode::compute() shouldn't call this for the root path
	return inPlug()->object( source );
}

void SubTree::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	bool createRoot = false;
	const ScenePath source = sourcePath( path, createRoot );
	if( createRoot )
	{
		SceneProcessor::hashChildNames( path, context, parent, h );
		h.append( *(source.rbegin()) );
	}
	else
	{
		h = inPlug()->childNamesHash( source );
	}
}

IECore::ConstInternedStringVectorDataPtr SubTree::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	bool createRoot = false;
	const ScenePath source = sourcePath( path, createRoot );
	if( createRoot )
	{
		IECore::InternedStringVectorDataPtr result = new IECore::InternedStringVectorData;
		result->writable().push_back( *(source.rbegin()) );
		return result;
	}
	else
	{
		return inPlug()->childNames( source );
	}
}

void SubTree::hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneProcessor::hashSet( setName, context, parent, h );
	inPlug()->setPlug()->hash( h );
	rootPlug()->hash( h );
	includeRootPlug()->hash( h );
}

GafferScene::ConstPathMatcherDataPtr SubTree::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstPathMatcherDataPtr inputSetData = inPlug()->setPlug()->getValue();
	const PathMatcher &inputSet = inputSetData->readable();
	if( inputSet.isEmpty() )
	{
		return inputSetData;
	}

	ScenePlug::ScenePath root;
	ScenePlug::stringToPath( rootPlug()->getValue(), root );

	ScenePlug::ScenePath prefix;
	if( includeRootPlug()->getValue() && root.size() )
	{
		prefix.push_back( root.back() );
	}

	PathMatcherDataPtr outputSetData = new PathMatcherData;
	outputSetData->writable().addPaths( inputSet.subTree( root ), prefix );
	return outputSetData;
}

SceneNode::ScenePath SubTree::sourcePath( const ScenePath &outputPath, bool &createRoot ) const
{
	/// \todo We should introduce a plug type which stores its values as a ScenePath directly.
	string rootAsString = rootPlug()->getValue();
	ScenePath result;
	ScenePlug::stringToPath( rootAsString, result );

	createRoot = false;
	if( result.size() && includeRootPlug()->getValue() )
	{
		if( outputPath.size() )
		{
			result.insert( result.end(), outputPath.begin() + 1, outputPath.end() );
		}
		else
		{
			createRoot = true;
		}
	}
	else
	{
		result.insert( result.end(), outputPath.begin(), outputPath.end() );
	}

	if( outputPath.empty() )
	{
		// Validate that the root the user has specified does exist.
		// We only do this when the output path is "/", because we don't
		// want to pay the cost for every location.
		//
		// The unwritten rule of GafferScene is that client code must not query
		// invalid locations, and nodes are therefore free to assume that
		// all queries made to them are valid, all in the name of performance.
		//
		// In its role as a client, the SubTree is therefore required to make
		// only valid queries of the input scene, and it would be useful if it
		// met this obligation even if the user has provided an invalid root
		// path.
		//
		// However, testing only at the root of the output scene is justified
		// because clients of the SubTree have the same obligation to make
		// only valid queries, and this will necessarily involve them computing
		// the child names for the root first.
		if( !SceneAlgo::exists( inPlug(), result ) )
		{
			throw IECore::Exception( boost::str( boost::format( "Root \"%s\" does not exist" ) % rootAsString ) );
		}
	}

	return result;
}

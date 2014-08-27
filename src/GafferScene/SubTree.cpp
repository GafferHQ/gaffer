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

#include <set>

#include "boost/tokenizer.hpp"

#include "Gaffer/Context.h"

#include "GafferScene/SubTree.h"
#include "GafferScene/PathMatcherData.h"

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
		for( ValuePlugIterator it( outPlug() ); it != it.end(); it++ )
		{
			outputs.push_back( it->get() );
		}
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

void SubTree::hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneProcessor::hashGlobals( context, parent, h );
	inPlug()->globalsPlug()->hash( h );
	rootPlug()->hash( h );
	includeRootPlug()->hash( h );
}

IECore::ConstCompoundObjectPtr SubTree::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
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

	std::string root = rootPlug()->getValue();
	if( !root.size() || root[root.size()-1] != '/' )
	{
		root += "/";
	}

	size_t prefixSize = root.size() - 1; // number of characters to remove from front of each declaration
	if( includeRootPlug()->getValue() && prefixSize )
	{
		size_t lastSlashButOne = root.rfind( "/", prefixSize-1 );
		if( lastSlashButOne != string::npos )
		{
			prefixSize = lastSlashButOne;
		}
	}

	for( CompoundDataMap::const_iterator it = inputSets->readable().begin(), eIt = inputSets->readable().end(); it != eIt; ++it )
	{
		/// \todo This could be more efficient if PathMatcher exposed the internal nodes,
		/// and allowed sharing between matchers. Then we could just pick the subtree within
		/// the matcher that we wanted.
		const PathMatcher &inputSet = static_cast<const PathMatcherData *>( it->second.get() )->readable();
		PathMatcher &outputSet = outputSets->member<PathMatcherData>( it->first, /* throwExceptions = */ false, /* createIfMissing = */ true )->writable();

		vector<string> inputPaths;
		inputSet.paths( inputPaths );
		for( vector<string>::const_iterator pIt = inputPaths.begin(), peIt = inputPaths.end(); pIt != peIt; ++pIt )
		{
			const string &inputPath = *pIt;
			if( inputPath.compare( 0, root.size(), root ) == 0 )
			{
				std::string outputPath( inputPath, prefixSize );
				outputSet.addPath( outputPath );
			}
		}
	}

	return outputGlobals;
}

SceneNode::ScenePath SubTree::sourcePath( const ScenePath &outputPath, bool &createRoot ) const
{
	typedef boost::tokenizer<boost::char_separator<char> > Tokenizer;
	/// \todo We should introduce a plug type which stores its values as a ScenePath directly.
	string rootAsString = rootPlug()->getValue();
	Tokenizer rootTokenizer( rootAsString, boost::char_separator<char>( "/" ) );
	ScenePath result;
	for( Tokenizer::const_iterator it = rootTokenizer.begin(), eIt = rootTokenizer.end(); it != eIt; it++ )
	{
		result.push_back( *it );
	}

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

	return result;
}

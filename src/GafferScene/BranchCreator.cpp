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

#include "boost/tokenizer.hpp"

#include "Gaffer/Context.h"

#include "GafferScene/BranchCreator.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( BranchCreator );

size_t BranchCreator::g_firstPlugIndex = 0;

BranchCreator::BranchCreator( const std::string &name, const std::string &namePlugDefaultValue )
	:	SceneProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "parent" ) );
	addChild( new StringPlug( "name", Plug::In, namePlugDefaultValue ) );
}

BranchCreator::~BranchCreator()
{
}

Gaffer::StringPlug *BranchCreator::parentPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *BranchCreator::parentPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *BranchCreator::namePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *BranchCreator::namePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

void BranchCreator::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneProcessor::affects( input, outputs );
	
	if( input->parent<ScenePlug>() == inPlug() )
	{
		outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );
	}
	else if( input == parentPlug() || input == namePlug() )
	{
		for( ValuePlugIterator it( outPlug() ); it != it.end(); it++ )
		{
			outputs.push_back( it->get() );
		}
	}
}

void BranchCreator::hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	/// \todo We could avoid calling the base class method when we know we're going to overwrite the hash anyway.
	/// This could make sense in all the hash*() methods.
	SceneProcessor::hashBound( path, context, parent, h );

	ScenePath parentPath, branchPath;
	bool onBranch = parentAndBranchPaths( path, parentPath, branchPath );
	
	if( onBranch )
	{
		hashBranchBound( parentPath, branchPath, context, h );
	}
	else if( parentPath.size() )
	{
		h = hashOfTransformedChildBounds( path, outPlug() );
	}
	else
	{
		h = inPlug()->boundPlug()->hash();
	}
}

void BranchCreator::hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneProcessor::hashTransform( path, context, parent, h );

	ScenePath parentPath, branchPath;
	bool onBranch = parentAndBranchPaths( path, parentPath, branchPath );
	
	if( onBranch )
	{
		hashBranchTransform( parentPath, branchPath, context, h );				
	}
	else
	{
		h = inPlug()->transformPlug()->hash();
	}
}

void BranchCreator::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneProcessor::hashAttributes( path, context, parent, h );

	ScenePath parentPath, branchPath;
	bool onBranch = parentAndBranchPaths( path, parentPath, branchPath );
	
	if( onBranch )
	{
		hashBranchAttributes( parentPath, branchPath, context, h );
	}
	else
	{
		h = inPlug()->attributesPlug()->hash();
	}
}

void BranchCreator::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneProcessor::hashObject( path, context, parent, h );

	ScenePath parentPath, branchPath;
	bool onBranch = parentAndBranchPaths( path, parentPath, branchPath );
	
	if( onBranch )
	{
		hashBranchObject( parentPath, branchPath, context, h );
	}
	else
	{
		h = inPlug()->objectPlug()->hash();
	}
}

void BranchCreator::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneProcessor::hashChildNames( path, context, parent, h );

	ScenePath parentPath, branchPath;
	bool onBranch = parentAndBranchPaths( path, parentPath, branchPath );
	
	if( onBranch )
	{
		hashBranchChildNames( parentPath, branchPath, context, h );
	}
	else if( path == parentPath )
	{
		namePlug()->hash( h );
	}
	else
	{
		h = inPlug()->childNamesPlug()->hash();
	}
}

void BranchCreator::hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	h = inPlug()->globalsPlug()->hash();
}

Imath::Box3f BranchCreator::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ScenePath parentPath, branchPath;
	bool onBranch = parentAndBranchPaths( path, parentPath, branchPath );
	if( onBranch )
	{
		return computeBranchBound( parentPath, branchPath, context );
	}
	else if( parentPath.size() )
	{
		return unionOfTransformedChildBounds( path, outPlug() );
	}
	else
	{
		return inPlug()->boundPlug()->getValue();
	}
}

Imath::M44f BranchCreator::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ScenePath parentPath, branchPath;
	bool onBranch = parentAndBranchPaths( path, parentPath, branchPath );
	if( onBranch )
	{
		return computeBranchTransform( parentPath, branchPath, context );
	}
	else
	{
		return inPlug()->transformPlug()->getValue();
	}
}

IECore::ConstCompoundObjectPtr BranchCreator::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ScenePath parentPath, branchPath;
	bool onBranch = parentAndBranchPaths( path, parentPath, branchPath );
	if( onBranch )
	{
		return computeBranchAttributes( parentPath, branchPath, context );
	}
	else
	{
		return inPlug()->attributesPlug()->getValue();
	}
}

IECore::ConstObjectPtr BranchCreator::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ScenePath parentPath, branchPath;
	bool onBranch = parentAndBranchPaths( path, parentPath, branchPath );
	if( onBranch )
	{
		return computeBranchObject( parentPath, branchPath, context );
	}
	else
	{
		return inPlug()->objectPlug()->getValue();
	}
}

IECore::ConstInternedStringVectorDataPtr BranchCreator::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ScenePath parentPath, branchPath;
	bool onBranch = parentAndBranchPaths( path, parentPath, branchPath );
	if( onBranch )
	{
		return computeBranchChildNames( parentPath, branchPath, context );
	}
	else if( path == parentPath )
	{
		/// \todo Perhaps allow any existing children to coexist?
		/// If we do that then we know that the bound at the parent is just the union
		/// of the old bound and the bound at the root of the branch. we could then
		/// optimise the propagation of the bound back to the root by just unioning the
		/// appropriately transformed branch bound with the bound from the input scene.
		InternedStringVectorDataPtr result = new InternedStringVectorData;
		result->writable().push_back( namePlug()->getValue() );
		return result;		
	}
	else
	{
		return inPlug()->childNamesPlug()->getValue();
	}
}

IECore::ConstCompoundObjectPtr BranchCreator::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	return inPlug()->globalsPlug()->getValue();
}

bool BranchCreator::parentAndBranchPaths( const ScenePath &path, ScenePath &parentPath, ScenePath &branchPath ) const
{
	typedef boost::tokenizer<boost::char_separator<char> > Tokenizer;
	
	/// \todo We should introduce a plug type which stores its values as a ScenePath directly.
	string parentAsString = parentPlug()->getValue();
	Tokenizer parentTokenizer( parentAsString, boost::char_separator<char>( "/" ) );	
	ScenePath parent;
	for( Tokenizer::const_iterator it = parentTokenizer.begin(), eIt = parentTokenizer.end(); it != eIt; it++ )
	{
		parent.push_back( *it );
	}
	
	string name = namePlug()->getValue();
	
	ScenePath::const_iterator parentIterator, parentIteratorEnd, pathIterator, pathIteratorEnd;
	
	for(
		parentIterator = parent.begin(), parentIteratorEnd = parent.end(),
		pathIterator = path.begin(), pathIteratorEnd = path.end();	
		parentIterator != parentIteratorEnd && pathIterator != pathIteratorEnd;
		parentIterator++, pathIterator++
	)
	{
		if( *parentIterator != *pathIterator )
		{
			return false;
		}
	}
	
	if( pathIterator == pathIteratorEnd )
	{
		// ancestor of parent, or parent itself
		parentPath = parent;
		return false;
	}
	
	if( *pathIterator++ != name )
	{
		// another child of parent, one we don't need to worry about
		return false;
	}
	
	// somewhere on the new branch
	parentPath = parent;
	branchPath.insert( branchPath.end(), pathIterator, pathIteratorEnd );
	return true;
}

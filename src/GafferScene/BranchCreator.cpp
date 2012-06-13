//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

BranchCreator::BranchCreator( const std::string &name )
	:	SceneProcessor( name )
{
	addChild( new StringPlug( "parent" ) );
	addChild( new StringPlug( "name" ) );
}

BranchCreator::~BranchCreator()
{
}

Gaffer::StringPlug *BranchCreator::parentPlug()
{
	return getChild<StringPlug>( "parent" );
}

const Gaffer::StringPlug *BranchCreator::parentPlug() const
{
	return getChild<StringPlug>( "parent" );
}

Gaffer::StringPlug *BranchCreator::namePlug()
{
	return getChild<StringPlug>( "name" );
}

const Gaffer::StringPlug *BranchCreator::namePlug() const
{
	return getChild<StringPlug>( "name" );
}

void BranchCreator::affects( const ValuePlug *input, AffectedPlugsContainer &outputs ) const
{
	SceneProcessor::affects( input, outputs );
	
	if( input->parent<ScenePlug>() == inPlug() )
	{
		outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );
	}
	else if( input == parentPlug() || input == namePlug() )
	{
		outputs.push_back( outPlug() );
	}
}

Imath::Box3f BranchCreator::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ScenePath parentPath, branchPath;
	parentAndBranchPaths( path, parentPath, branchPath );
	if( branchPath.size() )
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
	parentAndBranchPaths( path, parentPath, branchPath );
	if( branchPath.size() )
	{
		return computeBranchTransform( parentPath, branchPath, context );
	}
	else if( parentPath == path )
	{
		return inPlug()->transformPlug()->getValue();
	}
	return M44f();
}

IECore::ObjectPtr BranchCreator::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ScenePath parentPath, branchPath;
	parentAndBranchPaths( path, parentPath, branchPath );
	if( branchPath.size() )
	{
		return computeBranchObject( parentPath, branchPath, context );
	}
	else
	{
		ConstObjectPtr object = inPlug()->objectPlug()->getValue();
		return object ? object->copy() : 0;
	}
}

IECore::StringVectorDataPtr BranchCreator::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ScenePath parentPath, branchPath;
	parentAndBranchPaths( path, parentPath, branchPath );
	if( branchPath.size() )
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
		StringVectorDataPtr result = new StringVectorData;
		result->writable().push_back( namePlug()->getValue() );
		return result;		
	}
	else
	{
		IECore::ConstStringVectorDataPtr inputNames = inPlug()->childNamesPlug()->getValue();
		return inputNames ? inputNames->copy() : 0;
	}
}

IECore::ObjectVectorPtr BranchCreator::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	IECore::ConstObjectVectorPtr globals = inPlug()->globalsPlug()->getValue();
	return globals ? globals->copy() : 0;
}

void BranchCreator::parentAndBranchPaths( const ScenePath &path, ScenePath &parentPath, ScenePath &branchPath ) const
{
	string parent = parentPlug()->getValue();
	string name = namePlug()->getValue();
	
	typedef boost::tokenizer<boost::char_separator<char> > Tokenizer;

	Tokenizer parentTokenizer( parent, boost::char_separator<char>( "/" ) );	
	Tokenizer pathTokenizer( path, boost::char_separator<char>( "/" ) );
	
	Tokenizer::iterator parentIterator, pathIterator;
	
	for(
		parentIterator = parentTokenizer.begin(), pathIterator = pathTokenizer.begin();	
		parentIterator != parentTokenizer.end() && pathIterator != pathTokenizer.end();
		parentIterator++, pathIterator++
	)
	{
		if( *parentIterator != *pathIterator )
		{
			return;
		}
	}
	
	if( pathIterator == pathTokenizer.end() )
	{
		// ancestor of parent, or parent itself
		parentPath = parent;
		return;
	}
	
	if( *pathIterator++ != name )
	{
		// another child of parent, one we don't need to worry about
		return;
	}
	
	// somewhere on the new branch
	parentPath = parent;
	branchPath = "/";
	while( pathIterator != pathTokenizer.end() )
	{
		if( branchPath.size() > 1 )
		{
			branchPath += "/";
		}
		branchPath += *pathIterator++;
	}
}

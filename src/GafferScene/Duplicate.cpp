//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2014, John Haddon. All rights reserved.
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

#include "Gaffer/StringAlgo.h"

#include "GafferScene/Duplicate.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( Duplicate );

size_t Duplicate::g_firstPlugIndex = 0;

Duplicate::Duplicate( const std::string &name )
	:	BranchCreator( name )
{
	
	storeIndexOfNextChild( g_firstPlugIndex );
	
	addChild( new StringPlug( "target" ) );
	addChild( new IntPlug( "copies", Plug::In, 1, 0 ) );
	addChild( new TransformPlug( "transform" ) );
	addChild( new StringPlug( "__outParent", Plug::Out ) );
	addChild( new InternedStringVectorDataPlug( "__outChildNames", Plug::Out, inPlug()->childNamesPlug()->defaultValue() ) );
	
	parentPlug()->setInput( outParentPlug() );
	parentPlug()->setFlags( Plug::ReadOnly, true );
	parentPlug()->setFlags( Plug::Serialisable, false );
	
}

Duplicate::~Duplicate()
{
}

Gaffer::StringPlug *Duplicate::targetPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *Duplicate::targetPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *Duplicate::copiesPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *Duplicate::copiesPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}
		
Gaffer::TransformPlug *Duplicate::transformPlug()
{
	return getChild<TransformPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::TransformPlug *Duplicate::transformPlug() const
{
	return getChild<TransformPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *Duplicate::outParentPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *Duplicate::outParentPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::InternedStringVectorDataPlug *Duplicate::childNamesPlug()
{
	return getChild<InternedStringVectorDataPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::InternedStringVectorDataPlug *Duplicate::childNamesPlug() const
{
	return getChild<InternedStringVectorDataPlug>( g_firstPlugIndex + 4 );
}
		
void Duplicate::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	BranchCreator::affects( input, outputs );
	
	if( input == targetPlug() )
	{
		outputs.push_back( outParentPlug() );
		outputs.push_back( childNamesPlug() );
	}
	else if( input == copiesPlug() )
	{
		outputs.push_back( childNamesPlug() );
	}
	else if( input == childNamesPlug() )
	{
		outputs.push_back( outPlug()->childNamesPlug() );
	}
	else if( transformPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->transformPlug() );
	}
}

void Duplicate::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	BranchCreator::hash( output, context, h );
	
	if( output == outParentPlug() )
	{
		targetPlug()->hash( h );
	}
	else if( output == childNamesPlug() )
	{
		targetPlug()->hash( h );
		copiesPlug()->hash( h );
	}
}

void Duplicate::compute( ValuePlug *output, const Context *context ) const
{
	if( output == outParentPlug() )
	{
		ScenePath target;
		ScenePlug::stringToPath( targetPlug()->getValue(), target );
		string parent;
		for( size_t i = 0; i < target.size(); ++i )
		{
			parent += "/";
			if( i < target.size() - 1 )
			{
				parent += target[i];
			}
		}
		static_cast<StringPlug *>( output )->setValue( parent );
		return;
	}
	else if( output == childNamesPlug() )
	{
		// get the path to our target.
		ScenePath target;
		ScenePlug::stringToPath( targetPlug()->getValue(), target );

		// throw if the target path doesn't exist in the input. we need to compute the input child names at the
		// parent for this, but it's not necessary to represent that in the hash, because it doesn't actually
		// affect our result (if we throw we will have no result).
		ScenePath parent( target ); parent.pop_back();
		ConstInternedStringVectorDataPtr parentChildNamesData = inPlug()->childNames( parent );
		vector<InternedString> parentChildNames = parentChildNamesData->readable();
		if( find( parentChildNames.begin(), parentChildNames.end(), target.back() ) == parentChildNames.end() )
		{
			throw Exception( boost::str( boost::format( "Target \"%s\" does not exist" ) % target.back().string() ) );
		}
		
		// go ahead and generate our childnames by incrementing a numeric suffix on
		// the target name.
		std::string stem;
		int suffix = numericSuffix( target.back(), 0, &stem );
		
		InternedStringVectorDataPtr childNames = new InternedStringVectorData;
		
		boost::format formatter( "%s%d" );
		int copies = copiesPlug()->getValue();
		for( int i = 0; i < copies; ++i )
		{
			childNames->writable().push_back( boost::str( formatter % stem % ++suffix ) );
		}		
		
		static_cast<InternedStringVectorDataPlug *>( output )->setValue( childNames );
		return;
	}

	BranchCreator::compute( output, context );
}

void Duplicate::hashBranchBound( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ScenePath source;
	sourcePath( branchPath, source );
	h = inPlug()->boundHash( source );
}

Imath::Box3f Duplicate::computeBranchBound( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	ScenePath source;
	sourcePath( branchPath, source );
	return inPlug()->bound( source );
}

void Duplicate::hashBranchTransform( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ScenePath source;
	sourcePath( branchPath, source );
	if( branchPath.size() == 1 )
	{
		BranchCreator::hashBranchTransform( parentPath, branchPath, context, h );
		h.append( inPlug()->transformHash( source ) );
		transformPlug()->hash( h );
		childNamesPlug()->hash( h );
		h.append( branchPath[0] );
	}
	else
	{
		h = inPlug()->transformHash( source );
	}
}

Imath::M44f Duplicate::computeBranchTransform( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	ScenePath source;
	sourcePath( branchPath, source );
	Imath::M44f result = inPlug()->transform( source );
	if( branchPath.size() == 1 )
	{
		const Imath::M44f matrix = transformPlug()->matrix();
		ConstInternedStringVectorDataPtr childNamesData = childNamesPlug()->getValue();
		const vector<InternedString> &childNames = childNamesData->readable();
		
		size_t i = 0;
		do
		{
			result = result * matrix;
		} while( i < childNames.size() && branchPath[0] != childNames[i++] );
	}
	return result;
}

void Duplicate::hashBranchAttributes( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ScenePath source;
	sourcePath( branchPath, source );
	h = inPlug()->attributesHash( source );
}

IECore::ConstCompoundObjectPtr Duplicate::computeBranchAttributes( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	ScenePath source;
	sourcePath( branchPath, source );
	return inPlug()->attributes( source );
}

void Duplicate::hashBranchObject( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ScenePath source;
	sourcePath( branchPath, source );
	h = inPlug()->objectHash( source );
}

IECore::ConstObjectPtr Duplicate::computeBranchObject( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	ScenePath source;
	sourcePath( branchPath, source );
	return inPlug()->object( source );
}

void Duplicate::hashBranchChildNames( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() == 0 )
	{
		h = childNamesPlug()->hash();
	}
	else
	{
		ScenePath source;
		sourcePath( branchPath, source );
		h = inPlug()->childNamesHash( source );
	}
}

IECore::ConstInternedStringVectorDataPtr Duplicate::computeBranchChildNames( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	if( branchPath.size() == 0 )
	{
		return childNamesPlug()->getValue();
	}
	else
	{
		ScenePath source;
		sourcePath( branchPath, source );
		return inPlug()->childNames( source );
	}
}

void Duplicate::sourcePath( const ScenePath &branchPath, ScenePath &source ) const
{
	assert( branchPath.size() );
	ScenePlug::stringToPath( targetPlug()->getValue(), source );
	copy( ++branchPath.begin(), branchPath.end(), back_inserter( source ) );
}

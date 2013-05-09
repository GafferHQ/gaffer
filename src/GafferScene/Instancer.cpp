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

#include "boost/lexical_cast.hpp"

#include "IECore/VectorTypedData.h"

#include "Gaffer/Context.h"

#include "GafferScene/Instancer.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( Instancer );

size_t Instancer::g_firstPlugIndex = 0;

Instancer::Instancer( const std::string &name )
	:	BranchCreator( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "instance" ) );
}

Instancer::~Instancer()
{
}

ScenePlug *Instancer::instancePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const ScenePlug *Instancer::instancePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}
		
void Instancer::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	BranchCreator::affects( input, outputs );
	
	if( input->parent<ScenePlug>() == instancePlug() )
	{
		outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );
	}
}

void Instancer::hashBranchBound( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ContextPtr ic = instanceContext( context, branchPath );
	if( ic )
	{
		Context::Scope scopedContext( ic );
		h = instancePlug()->boundPlug()->hash();
		return;
	}
	
	// branchPath == "/"
	
	/// \todo This is a massive cop-out. See if we can improve it.
	h.append( computeBranchBound( parentPath, branchPath, context ) );
	
}

Imath::Box3f Instancer::computeBranchBound( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	ContextPtr ic = instanceContext( context, branchPath );
	if( ic )
	{
		Context::Scope scopedContext( ic );
		return instancePlug()->boundPlug()->getValue();
	}
	
	// branchPath == "/"
	
	Box3f result;
	ConstV3fVectorDataPtr p = sourcePoints( parentPath );
	if( p )
	{
		ScenePath branchChildPath( branchPath );
		branchChildPath.push_back( InternedString() ); // where we'll place the instance index
		for( size_t i=0; i<p->readable().size(); i++ )
		{
			/// \todo We could have a very fast InternedString( int ) constructor rather than all this lexical cast nonsense
			branchChildPath[branchChildPath.size()-1] = boost::lexical_cast<string>( i );
			Box3f branchChildBound = computeBranchBound( parentPath, branchChildPath, context );
			branchChildBound = transform( branchChildBound, computeBranchTransform( parentPath, branchChildPath, context ) );
			result.extendBy( branchChildBound );			
		}
	}

	return result;
}

void Instancer::hashBranchTransform( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ContextPtr ic = instanceContext( context, branchPath );
	if( ic )
	{
		Context::Scope scopedContext( ic );
		h = instancePlug()->transformPlug()->hash();
	}
	
	if( branchPath.size() == 1 )
	{
		h.append( inPlug()->objectHash( parentPath ) );
		h.append( instanceIndex( branchPath ) );
	}
}

Imath::M44f Instancer::computeBranchTransform( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	M44f result;
	ContextPtr ic = instanceContext( context, branchPath );
	if( ic )
	{
		Context::Scope scopedContext( ic );
		result = instancePlug()->transformPlug()->getValue();
	}
	
	if( branchPath.size() == 1 )
	{
		int index = instanceIndex( branchPath );
		ConstV3fVectorDataPtr p = sourcePoints( parentPath );
		if( p && (size_t)index < p->readable().size() )
		{
			M44f t;
			t.translate( p->readable()[index] );
			result *= t;
		}
	}
	return result;
}

void Instancer::hashBranchAttributes( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ContextPtr ic = instanceContext( context, branchPath );
	if( ic )
	{
		Context::Scope scopedContext( ic );
		h = instancePlug()->attributesPlug()->hash();
	}
}

IECore::ConstCompoundObjectPtr Instancer::computeBranchAttributes( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	ContextPtr ic = instanceContext( context, branchPath );
	if( ic )
	{
		Context::Scope scopedContext( ic );
		return instancePlug()->attributesPlug()->getValue();
	}
	return outPlug()->attributesPlug()->defaultValue();
}

void Instancer::hashBranchObject( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ContextPtr ic = instanceContext( context, branchPath );
	if( ic )
	{
		Context::Scope scopedContext( ic );
		h = instancePlug()->objectPlug()->hash();
	}
}

IECore::ConstObjectPtr Instancer::computeBranchObject( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	ContextPtr ic = instanceContext( context, branchPath );
	if( ic )
	{
		Context::Scope scopedContext( ic );
		return instancePlug()->objectPlug()->getValue();
	}
	return outPlug()->objectPlug()->defaultValue();
}

void Instancer::hashBranchChildNames( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() == 0 )
	{
		namePlug()->hash( h );
		h.append( inPlug()->objectHash( parentPath ) );
	}
	else
	{
		ContextPtr ic = instanceContext( context, branchPath );
		Context::Scope scopedContext( ic );
		h = instancePlug()->childNamesPlug()->hash();
	}
}

IECore::ConstInternedStringVectorDataPtr Instancer::computeBranchChildNames( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	if( branchPath.size() == 0 )
	{
		std::string name = namePlug()->getValue();
		if( !name.size() )
		{
			return outPlug()->childNamesPlug()->defaultValue();
		}
		ConstV3fVectorDataPtr p = sourcePoints( parentPath );
		if( !p || !p->readable().size() )
		{
			return outPlug()->childNamesPlug()->defaultValue();
		}
		
		InternedStringVectorDataPtr result = new InternedStringVectorData();
		for( size_t i=0; i<p->readable().size(); i++ )
		{
			result->writable().push_back( boost::lexical_cast<string>( i ) );
		}
		
		return result;
	}
	else
	{
		ContextPtr ic = instanceContext( context, branchPath );
		Context::Scope scopedContext( ic );
		return instancePlug()->childNamesPlug()->getValue();
	}
}

ConstV3fVectorDataPtr Instancer::sourcePoints( const ScenePath &parentPath ) const
{
	ConstPrimitivePtr primitive = runTimeCast<const Primitive>( inPlug()->object( parentPath ) );
	if( !primitive )
	{
		return 0;
	}
	
	return primitive->variableData<V3fVectorData>( "P" );
}

int Instancer::instanceIndex( const ScenePath &branchPath ) const
{
	return boost::lexical_cast<int>( branchPath[0].value() );
}

Gaffer::ContextPtr Instancer::instanceContext( const Gaffer::Context *parentContext, const ScenePath &branchPath ) const
{
	if( branchPath.size() == 0 )
	{
		return 0;
	}
	
	ContextPtr result = new Context( *parentContext );

	InternedStringVectorDataPtr instancePath = new InternedStringVectorData;
	instancePath->writable().insert( instancePath->writable().end(), branchPath.begin() + 1, branchPath.end() );
	result->set( ScenePlug::scenePathContextName, instancePath.get() );
	
	result->set( "instancer:id", instanceIndex( branchPath ) );
	
	return result;
}

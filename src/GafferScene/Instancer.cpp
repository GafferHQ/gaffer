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
	addChild( new StringPlug( "name", Plug::In, "instances" ) );
	addChild( new ScenePlug( "instance" ) );
}

Instancer::~Instancer()
{
}

Gaffer::StringPlug *Instancer::namePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *Instancer::namePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

ScenePlug *Instancer::instancePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex + 1 );
}

const ScenePlug *Instancer::instancePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex + 1 );
}
		
void Instancer::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	BranchCreator::affects( input, outputs );
	
	if( input->parent<ScenePlug>() == instancePlug() )
	{
		outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );
	}
	else if( input == namePlug() )
	{
		outputs.push_back( outPlug()->childNamesPlug() );
	}
}

void Instancer::hashBranchBound( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() <= 1 )
	{
		// "/" or "/name"
	
		BranchCreator::hashBranchBound( parentPath, branchPath, context, h );
	
		/// \todo This is a massive cop-out. See if we can improve it.
		h.append( computeBranchBound( parentPath, branchPath, context ) );
	}
	else
	{
		ContextPtr ic = instanceContext( context, branchPath );
		Context::Scope scopedContext( ic );
		h = instancePlug()->boundPlug()->hash();
	}	
}

Imath::Box3f Instancer::computeBranchBound( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	if( branchPath.size() <= 1 )
	{
		// "/" or "/name"
		Box3f result;
		ConstV3fVectorDataPtr p = sourcePoints( parentPath );
		if( p )
		{
			ScenePath branchChildPath( branchPath );
			if( branchChildPath.size() == 0 )
			{
				branchChildPath.push_back( namePlug()->getValue() );
			}
			branchChildPath.push_back( InternedString() ); // where we'll place the instance index
			for( size_t i=0; i<p->readable().size(); i++ )
			{
				branchChildPath[branchChildPath.size()-1] = InternedString( i );
				Box3f branchChildBound = computeBranchBound( parentPath, branchChildPath, context );
				branchChildBound = transform( branchChildBound, computeBranchTransform( parentPath, branchChildPath, context ) );
				result.extendBy( branchChildBound );			
			}
		}

		return result;
	}
	else
	{
		ContextPtr ic = instanceContext( context, branchPath );
		Context::Scope scopedContext( ic );
		return instancePlug()->boundPlug()->getValue();
	}
}

void Instancer::hashBranchTransform( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() <= 2 )
	{
		// "/", "/name" or "/name/instanceNumber"
		BranchCreator::hashBranchTransform( parentPath, branchPath, context, h );
		if( branchPath.size() == 2 )
		{
			h.append( inPlug()->objectHash( parentPath ) );
			h.append( instanceIndex( branchPath ) );
		}
	}
	else
	{
		ContextPtr ic = instanceContext( context, branchPath );
		Context::Scope scopedContext( ic );
		h = instancePlug()->transformPlug()->hash();
	}
}

Imath::M44f Instancer::computeBranchTransform( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	if( branchPath.size() <= 2 )
	{
		// "/", "/name" or "/name/instanceNumber"
		M44f result;
		if( branchPath.size() == 2 )
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
	else
	{
		ContextPtr ic = instanceContext( context, branchPath );
		Context::Scope scopedContext( ic );
		return instancePlug()->transformPlug()->getValue();
	}
}

void Instancer::hashBranchAttributes( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() <= 1 )
	{
		// "/" or "/name"
		h = outPlug()->attributesPlug()->defaultValue()->Object::hash();
	}
	else
	{
		ContextPtr ic = instanceContext( context, branchPath );
		Context::Scope scopedContext( ic );
		h = instancePlug()->attributesPlug()->hash();
	}	
}

IECore::ConstCompoundObjectPtr Instancer::computeBranchAttributes( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	if( branchPath.size() <= 1 )
	{
		// "/" or "/name"
		return outPlug()->attributesPlug()->defaultValue();	
	}
	else
	{
		ContextPtr ic = instanceContext( context, branchPath );
		Context::Scope scopedContext( ic );
		return instancePlug()->attributesPlug()->getValue();
	}
}

void Instancer::hashBranchObject( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() <= 1 )
	{
		// "/" or "/name"
		h = outPlug()->objectPlug()->defaultValue()->Object::hash();	
	}
	else
	{
		ContextPtr ic = instanceContext( context, branchPath );
		Context::Scope scopedContext( ic );
		h = instancePlug()->objectPlug()->hash();
	}
}

IECore::ConstObjectPtr Instancer::computeBranchObject( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	if( branchPath.size() <= 1 )
	{
		// "/" or "/name"
		return outPlug()->objectPlug()->defaultValue();	
	}
	else
	{
		ContextPtr ic = instanceContext( context, branchPath );
		Context::Scope scopedContext( ic );
		return instancePlug()->objectPlug()->getValue();
	}
}

void Instancer::hashBranchChildNames( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() == 0 )
	{
		// "/"
		BranchCreator::hashBranchChildNames( parentPath, branchPath, context, h );
		namePlug()->hash( h );	
	}
	else if( branchPath.size() == 1 )
	{
		// "/name"
		BranchCreator::hashBranchChildNames( parentPath, branchPath, context, h );
		h.append( inPlug()->objectHash( parentPath ) );
	}
	else
	{
		// "/name/..."
		ContextPtr ic = instanceContext( context, branchPath );
		Context::Scope scopedContext( ic );
		h = instancePlug()->childNamesPlug()->hash();
	}
}

IECore::ConstInternedStringVectorDataPtr Instancer::computeBranchChildNames( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	if( branchPath.size() == 0 )
	{
		// "/"
		std::string name = namePlug()->getValue();
		if( name.empty() )
		{
			return outPlug()->childNamesPlug()->defaultValue();
		}
		InternedStringVectorDataPtr result = new InternedStringVectorData();
		result->writable().push_back( name );		
		return result;
	}
	else if( branchPath.size() == 1 )
	{
		ConstV3fVectorDataPtr p = sourcePoints( parentPath );
		if( !p || !p->readable().size() )
		{
			return outPlug()->childNamesPlug()->defaultValue();
		}
		
		InternedStringVectorDataPtr result = new InternedStringVectorData();
		for( size_t i=0; i<p->readable().size(); i++ )
		{
			result->writable().push_back( InternedString( i ) );
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
	return boost::lexical_cast<int>( branchPath[1].value() );
}

Gaffer::ContextPtr Instancer::instanceContext( const Gaffer::Context *parentContext, const ScenePath &branchPath ) const
{
	if( branchPath.size() < 2 )
	{
		return 0;
	}
	
	ContextPtr result = new Context( *parentContext );

	InternedStringVectorDataPtr instancePath = new InternedStringVectorData;
	instancePath->writable().insert( instancePath->writable().end(), branchPath.begin() + 2, branchPath.end() );
	result->set( ScenePlug::scenePathContextName, instancePath.get() );
	
	result->set( "instancer:id", instanceIndex( branchPath ) );
	
	return result;
}

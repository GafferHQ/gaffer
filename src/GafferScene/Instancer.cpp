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

#include "boost/lexical_cast.hpp"

#include "Gaffer/Context.h"

#include "GafferScene/Instancer.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( Instancer );

Instancer::Instancer( const std::string &name )
	:	BranchCreator( name )
{
	addChild( new ScenePlug( "instance" ) );
}

Instancer::~Instancer()
{
}

ScenePlug *Instancer::instancePlug()
{
	return getChild<ScenePlug>( "instance" );
}

const ScenePlug *Instancer::instancePlug() const
{
	return getChild<ScenePlug>( "instance" );
}
		
void Instancer::affects( const ValuePlug *input, AffectedPlugsContainer &outputs ) const
{
	BranchCreator::affects( input, outputs );
	
	if( input->parent<ScenePlug>() == instancePlug() )
	{
		outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );
	}
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
		for( size_t i=0; i<p->readable().size(); i++ )
		{
			std::string branchChildPath = branchPath + boost::lexical_cast<string>( i );
			Box3f branchChildBound = computeBranchBound( parentPath, branchChildPath, context );
			branchChildBound = transform( branchChildBound, computeBranchTransform( parentPath, branchChildPath, context ) );
			result.extendBy( branchChildBound );			
		}
	}

	return result;
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
	
	if( branchPath.size() > 1 && branchPath.find( '/', 1 ) == string::npos )
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

IECore::PrimitivePtr Instancer::computeBranchGeometry( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	ContextPtr ic = instanceContext( context, branchPath );
	if( ic )
	{
		Context::Scope scopedContext( ic );
		ConstPrimitivePtr instanceGeometry = instancePlug()->geometryPlug()->getValue();
		return instanceGeometry ? instanceGeometry->copy() : 0;
	}
	return 0;
}

IECore::StringVectorDataPtr Instancer::computeBranchChildNames( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	if( branchPath == "/" )
	{
		std::string name = namePlug()->getValue();
		if( !name.size() )
		{
			return 0;
		}
		ConstV3fVectorDataPtr p = sourcePoints( parentPath );
		if( !p || !p->readable().size() )
		{
			return 0;
		}
		
		StringVectorDataPtr result = new StringVectorData();
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
		ConstStringVectorDataPtr instanceChildNames = instancePlug()->childNamesPlug()->getValue();
		return instanceChildNames ? instanceChildNames->copy() : 0;
	}
}

ConstV3fVectorDataPtr Instancer::sourcePoints( const ScenePath &parentPath ) const
{
	ConstPrimitivePtr primitive = inPlug()->geometry( parentPath );
	if( !primitive )
	{
		return 0;
	}
	
	return primitive->variableData<V3fVectorData>( "P" );
}

int Instancer::instanceIndex( const ScenePath &branchPath ) const
{
	size_t p = branchPath.find( '/', 1 );
	std::string number( branchPath, 1, p != string::npos ? p-1 : p );
	return boost::lexical_cast<int>( number );
}

Gaffer::ContextPtr Instancer::instanceContext( const Gaffer::Context *parentContext, const ScenePath &branchPath ) const
{
	if( branchPath=="/" )
	{
		return 0;
	}
	
	ContextPtr result = new Context( *parentContext );

	size_t s = branchPath.find( '/', 1 );
	if( s == string::npos )
	{
		result->set( "scene:path", string( "/" ) );
	}
	else
	{
		result->set( "scene:path", string( branchPath, s ) );
	}	
	
	result->set( "instancer:id", instanceIndex( branchPath ) );
	
	return result;
}
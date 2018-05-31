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

#include "GafferScene/Instancer.h"

#include "Gaffer/Context.h"
#include "Gaffer/StringPlug.h"

#include "IECoreScene/Primitive.h"

#include "IECore/VectorTypedData.h"

#include "boost/lexical_cast.hpp"

#include "tbb/blocked_range.h"
#include "tbb/parallel_reduce.h"

using namespace std;
using namespace tbb;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( Instancer );

size_t Instancer::g_firstPlugIndex = 0;

static const IECore::InternedString idContextName( "instancer:id" );

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
	else if( input == inPlug()->objectPlug() )
	{
		outputs.push_back( outPlug()->childNamesPlug() );
		outputs.push_back( outPlug()->boundPlug() );
		outputs.push_back( outPlug()->transformPlug() );
	}
}

struct Instancer::BoundHash
{

	BoundHash( const Instancer *instancer, const ScenePath &branchPath, const Context *c )
		:	m_instancer( instancer ), m_branchPath( branchPath ), m_context( c ), m_hash()
	{
	}

	BoundHash( const BoundHash &rhs, split )
		:	m_instancer( rhs.m_instancer ), m_branchPath( rhs.m_branchPath ), m_context( rhs.m_context ), m_hash()
	{
	}

	void operator() ( const blocked_range<size_t> &r )
	{
		InstanceScope instanceScope( m_context );

		ScenePath branchChildPath( m_branchPath );
		branchChildPath.push_back( InternedString() ); // where we'll place the instance index

		for( size_t i=r.begin(); i!=r.end(); ++i )
		{
			branchChildPath[branchChildPath.size()-1] = InternedString( i );
			instanceScope.update( branchChildPath, i );
			m_instancer->instancePlug()->boundPlug()->hash( m_hash );
			// no need to hash transform of instance because we know all
			// root transforms are identity.
		}
	}

	void join( const BoundHash &rhs )
	{
		m_hash.append( rhs.m_hash );
	}

	const MurmurHash &result()
	{
		return m_hash;
	}

	private :

		const Instancer *m_instancer;
		const ScenePath &m_branchPath;
		const Context *m_context;
		MurmurHash m_hash;

};

void Instancer::hashBranchBound( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() <= 1 )
	{
		// "/" or "/name"

		BranchCreator::hashBranchBound( parentPath, branchPath, context, h );

		ConstV3fVectorDataPtr p = sourcePoints( parentPath );
		if( p )
		{
			p->hash( h );

			ScenePath branchChildPath( branchPath );
			if( branchChildPath.size() == 0 )
			{
				branchChildPath.push_back( namePlug()->getValue() );
			}

			BoundHash hasher( this, branchChildPath, context );
			task_group_context taskGroupContext( task_group_context::isolated );
			parallel_deterministic_reduce(
				blocked_range<size_t>( 0, p->readable().size(), 100 ),
				hasher,
				// Prevents outer tasks silently cancelling our tasks
				taskGroupContext
			);

			h.append( hasher.result() );
		}
	}
	else
	{
		InstanceScope instanceScope( context, branchPath );
		h = instancePlug()->boundPlug()->hash();
	}
}

struct Instancer::BoundUnion
{

	BoundUnion( const Instancer *instancer, const ScenePath &branchPath, const Context *c, const V3fVectorData *p )
		:	m_instancer( instancer ), m_branchPath( branchPath ), m_context( c ), m_p( p ), m_union()
	{
	}

	BoundUnion( const BoundUnion &rhs, split )
		:	m_instancer( rhs.m_instancer ), m_branchPath( rhs.m_branchPath ), m_context( rhs.m_context ), m_p( rhs.m_p ), m_union()
	{
	}

	void operator() ( const blocked_range<size_t> &r )
	{
		InstanceScope instanceScope( m_context );

		ScenePath branchChildPath( m_branchPath );
		branchChildPath.push_back( InternedString() ); // where we'll place the instance index

		for( size_t i=r.begin(); i!=r.end(); ++i )
		{
			branchChildPath[branchChildPath.size()-1] = InternedString( i );
			instanceScope.update( branchChildPath, i );

			Box3f branchChildBound = m_instancer->instancePlug()->boundPlug()->getValue();
			branchChildBound = transform( branchChildBound, m_instancer->instanceTransform( m_p, i ) );
			m_union.extendBy( branchChildBound );
		}
	}

	void join( const BoundUnion &rhs )
	{
		m_union.extendBy( rhs.m_union );
	}

	const Box3f &result()
	{
		return m_union;
	}

	private :

		const Instancer *m_instancer;
		const ScenePath &m_branchPath;
		const Context *m_context;
		const V3fVectorData *m_p;
		Box3f m_union;

};

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

			BoundUnion unioner( this, branchChildPath, context, p.get() );
			task_group_context taskGroupContext( task_group_context::isolated );
			parallel_reduce(
				blocked_range<size_t>( 0, p->readable().size() ),
				unioner,
				tbb::auto_partitioner(),
				// Prevents outer tasks silently cancelling our tasks
				taskGroupContext
			);

			result = unioner.result();
		}

		return result;
	}
	else
	{
		InstanceScope instanceScope( context, branchPath );
		return instancePlug()->boundPlug()->getValue();
	}
}

void Instancer::hashBranchTransform( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() < 2 )
	{
		// "/" or  "/name"
		BranchCreator::hashBranchTransform( parentPath, branchPath, context, h );
	}
	else if( branchPath.size() == 2 )
	{
		// "/name/instanceNumber"
		BranchCreator::hashBranchTransform( parentPath, branchPath, context, h );
		h.append( inPlug()->objectHash( parentPath ) );
		h.append( instanceIndex( branchPath ) );
	}
	else
	{
		InstanceScope instanceScope( context, branchPath );
		h = instancePlug()->transformPlug()->hash();
	}
}

Imath::M44f Instancer::computeBranchTransform( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	if( branchPath.size() < 2 )
	{
		// "/" or "/name"
		return M44f();
	}
	else if( branchPath.size() == 2 )
	{
		// "/name/instanceNumber"
		int index = instanceIndex( branchPath );
		ConstV3fVectorDataPtr p = sourcePoints( parentPath );
		return instanceTransform( p.get(), index );
	}
	else
	{
		InstanceScope instanceScope( context, branchPath );
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
		InstanceScope instanceScope( context, branchPath );
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
		InstanceScope instanceScope( context, branchPath );
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
		InstanceScope instanceScope( context, branchPath );
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
		InstanceScope instanceScope( context, branchPath );
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
		InstanceScope instanceScope( context, branchPath );
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

		const size_t s = p->readable().size();
		InternedStringVectorDataPtr resultData = new InternedStringVectorData();
		vector<InternedString> &result = resultData->writable();
		result.resize( s );

		for( size_t i = 0; i < s ; ++i )
		{
			result[i] = InternedString( i );
		}

		return resultData;
	}
	else
	{
		InstanceScope instanceScope( context, branchPath );
		return instancePlug()->childNamesPlug()->getValue();
	}
}

ConstV3fVectorDataPtr Instancer::sourcePoints( const ScenePath &parentPath ) const
{
	ConstPrimitivePtr primitive = runTimeCast<const Primitive>( inPlug()->object( parentPath ) );
	if( !primitive )
	{
		return nullptr;
	}

	return primitive->variableData<V3fVectorData>( "P" );
}

int Instancer::instanceIndex( const ScenePath &branchPath )
{
	return boost::lexical_cast<int>( branchPath[1].value() );
}

Instancer::InstanceScope::InstanceScope( const Gaffer::Context *context )
	:	EditableScope( context )
{
}

Instancer::InstanceScope::InstanceScope( const Gaffer::Context *context, const ScenePath &branchPath )
	:	EditableScope( context )
{
	update( branchPath );
}

void Instancer::InstanceScope::update( const ScenePath &branchPath )
{
	update( branchPath, instanceIndex( branchPath ) );
}

void Instancer::InstanceScope::update( const ScenePath &branchPath, int instanceId )
{
	assert( branchPath.size() >= 2 );
	ScenePath instancePath;
	instancePath.insert( instancePath.end(), branchPath.begin() + 2, branchPath.end() );
	set( ScenePlug::scenePathContextName, instancePath );
	set( idContextName, instanceId );
}

Imath::M44f Instancer::instanceTransform( const IECore::V3fVectorData *p, int instanceId ) const
{
	M44f result;
	result.translate( p->readable()[instanceId] );
	return result;
}

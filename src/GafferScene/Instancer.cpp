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

#include "IECore/MessageHandler.h"
#include "IECore/NullObject.h"
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

//////////////////////////////////////////////////////////////////////////
// EngineData
//////////////////////////////////////////////////////////////////////////

// Custom Data derived class used to encapsulate the data and
// logic needed to generate instances. We are deliberately omitting
// a custom TypeId etc because this is just a private class.
class Instancer::EngineData : public Data
{

	public :

		EngineData(
			ConstObjectPtr object,
			const std::string &position,
			const std::string &orientation,
			const std::string &scale
		)
			:	m_positions( nullptr ),
				m_orientations( nullptr ),
				m_scales( nullptr ),
				m_uniformScales( nullptr )
		{
			m_primitive = runTimeCast<const Primitive>( object );
			if( !m_primitive )
			{
				return;
			}

			if( const V3fVectorData *p = m_primitive->variableData<V3fVectorData>( position ) )
			{
				m_positions = &p->readable();
				if( m_positions->size() != numInstances() )
				{
					throw IECore::Exception( "Position primitive variable has incorrect size" );
				}
			}

			if( const QuatfVectorData *o = m_primitive->variableData<QuatfVectorData>( orientation ) )
			{
				m_orientations = &o->readable();
				if( m_orientations->size() != numInstances() )
				{
					throw IECore::Exception( "Orientation primitive variable has incorrect size" );
				}
			}

			if( const V3fVectorData *s = m_primitive->variableData<V3fVectorData>( scale ) )
			{
				m_scales = &s->readable();
				if( m_scales->size() != numInstances() )
				{
					throw IECore::Exception( "Scale primitive variable has incorrect size" );
				}
			}
			else if( const FloatVectorData *s = m_primitive->variableData<FloatVectorData>( scale ) )
			{
				m_uniformScales = &s->readable();
				if( m_uniformScales->size() != numInstances() )
				{
					throw IECore::Exception( "Scale primitive variable has incorrect size" );
				}
			}
		}

		size_t numInstances() const
		{
			return m_primitive ? m_primitive->variableSize( PrimitiveVariable::Vertex ) : 0;
		}

		M44f instanceTransform( size_t instanceIndex ) const
		{
			M44f result;
			if( m_positions )
			{
				result.translate( (*m_positions)[instanceIndex] );
			}
			if( m_orientations )
			{
				result = (*m_orientations)[instanceIndex].toMatrix44() * result;
			}
			if( m_scales )
			{
				result.scale( (*m_scales)[instanceIndex] );
			}
			if( m_uniformScales )
			{
				result.scale( V3f( (*m_uniformScales)[instanceIndex] ) );
			}
			return result;
		}

	protected :

		void copyFrom( const Object *other, CopyContext *context ) override
		{
			Data::copyFrom( other, context );
			msg( Msg::Warning, "EngineData::copyFrom", "Not implemented" );
		}

		void save( SaveContext *context ) const override
		{
			Data::save( context );
			msg( Msg::Warning, "EngineData::save", "Not implemented" );
		}

		void load( LoadContextPtr context ) override
		{
			Data::load( context );
			msg( Msg::Warning, "EngineData::load", "Not implemented" );
		}

	private :

		IECoreScene::ConstPrimitivePtr m_primitive;
		const std::vector<Imath::V3f> *m_positions;
		const std::vector<Imath::Quatf> *m_orientations;
		const std::vector<Imath::V3f> *m_scales;
		const std::vector<float> *m_uniformScales;

};

//////////////////////////////////////////////////////////////////////////
// Instancer
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( Instancer );

size_t Instancer::g_firstPlugIndex = 0;

static const IECore::InternedString idContextName( "instancer:id" );

Instancer::Instancer( const std::string &name )
	:	BranchCreator( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "name", Plug::In, "instances" ) );
	addChild( new ScenePlug( "instance" ) );
	addChild( new StringPlug( "position", Plug::In, "P" ) );
	addChild( new StringPlug( "orientation", Plug::In ) );
	addChild( new StringPlug( "scale", Plug::In ) );
	addChild( new ObjectPlug( "__engine", Plug::Out, NullObject::defaultNullObject() ) );
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

Gaffer::StringPlug *Instancer::positionPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *Instancer::positionPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *Instancer::orientationPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *Instancer::orientationPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::StringPlug *Instancer::scalePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::StringPlug *Instancer::scalePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

Gaffer::ObjectPlug *Instancer::enginePlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::ObjectPlug *Instancer::enginePlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 5 );
}

void Instancer::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	BranchCreator::affects( input, outputs );

	if(
		input == inPlug()->objectPlug() ||
		input == positionPlug() ||
		input == orientationPlug() ||
		input == scalePlug()
	)
	{
		outputs.push_back( enginePlug() );
	}

	if( input->parent<ScenePlug>() == instancePlug() )
	{
		outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );
	}

	if(
		input == namePlug() ||
		input == enginePlug()
	)
	{
		outputs.push_back( outPlug()->childNamesPlug() );
	}

	if( input == enginePlug() )
	{
		outputs.push_back( outPlug()->boundPlug() );
		outputs.push_back( outPlug()->transformPlug() );
	}
}

void Instancer::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	BranchCreator::hash( output, context, h );

	if( output == enginePlug() )
	{
		inPlug()->objectPlug()->hash( h );
		positionPlug()->hash( h );
		orientationPlug()->hash( h );
		scalePlug()->hash( h );
	}
}

void Instancer::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == enginePlug() )
	{
		static_cast<ObjectPlug *>( output )->setValue(
			new EngineData(
				inPlug()->objectPlug()->getValue(),
				positionPlug()->getValue(),
				orientationPlug()->getValue(),
				scalePlug()->getValue()
			)
		);
		return;
	}

	BranchCreator::compute( output, context );
}

struct Instancer::BoundHash
{

	BoundHash( const Instancer *instancer, const Instancer::EngineData *engine, const ScenePath &branchPath, const Context *c )
		:	m_instancer( instancer ), m_engine( engine ), m_branchPath( branchPath ), m_context( c ), m_hash()
	{
	}

	BoundHash( const BoundHash &rhs, split )
		:	m_instancer( rhs.m_instancer ), m_engine( rhs.m_engine ), m_branchPath( rhs.m_branchPath ), m_context( rhs.m_context ), m_hash()
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
			m_hash.append( m_engine->instanceTransform( i ) );
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
		const Instancer::EngineData *m_engine;
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

		ConstEngineDataPtr e = engine( parentPath, context );
		if( e->numInstances() )
		{
			ScenePath branchChildPath( branchPath );
			if( branchChildPath.size() == 0 )
			{
				branchChildPath.push_back( namePlug()->getValue() );
			}

			BoundHash hasher( this, e.get(), branchChildPath, context );
			task_group_context taskGroupContext( task_group_context::isolated );
			parallel_deterministic_reduce(
				blocked_range<size_t>( 0, e->numInstances(), 100 ),
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

	BoundUnion( const Instancer *instancer, const Instancer::EngineData *engine, const ScenePath &branchPath, const Context *c )
		:	m_instancer( instancer ), m_engine( engine ), m_branchPath( branchPath ), m_context( c ), m_union()
	{
	}

	BoundUnion( const BoundUnion &rhs, split )
		:	m_instancer( rhs.m_instancer ), m_engine( rhs.m_engine ), m_branchPath( rhs.m_branchPath ), m_context( rhs.m_context ), m_union()
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
			branchChildBound = transform( branchChildBound, m_engine->instanceTransform( i ) );
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
		const Instancer::EngineData *m_engine;
		const ScenePath &m_branchPath;
		const Context *m_context;
		Box3f m_union;

};

Imath::Box3f Instancer::computeBranchBound( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	if( branchPath.size() <= 1 )
	{
		// "/" or "/name"
		Box3f result;
		ConstEngineDataPtr e = engine( parentPath, context );
		if( e->numInstances() )
		{
			ScenePath branchChildPath( branchPath );
			if( branchChildPath.size() == 0 )
			{
				branchChildPath.push_back( namePlug()->getValue() );
			}

			BoundUnion unioner( this, e.get(), branchChildPath, context );
			task_group_context taskGroupContext( task_group_context::isolated );
			parallel_reduce(
				blocked_range<size_t>( 0, e->numInstances() ),
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
		engineHash( parentPath, context, h );
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
		const int index = instanceIndex( branchPath );
		ConstEngineDataPtr e = engine( parentPath, context );
		return e->instanceTransform( index );
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
		engineHash( parentPath, context, h );
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
		ConstEngineDataPtr e = engine( parentPath, context );
		const size_t s = e->numInstances();
		if( !s )
		{
			return outPlug()->childNamesPlug()->defaultValue();
		}

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

Instancer::ConstEngineDataPtr Instancer::engine( const ScenePath &parentPath, const Gaffer::Context *context ) const
{
	ScenePlug::PathScope scope( context, parentPath );
	return boost::static_pointer_cast<const EngineData>( enginePlug()->getValue() );
}

void Instancer::engineHash( const ScenePath &parentPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ScenePlug::PathScope scope( context, parentPath );
	enginePlug()->hash( h );
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

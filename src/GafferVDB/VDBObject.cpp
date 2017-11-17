//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, John Haddon. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#include <algorithm>

#include "boost/iostreams/categories.hpp"
#include "boost/iostreams/stream.hpp"

#include "openvdb/openvdb.h"
#include "openvdb/io/Stream.h"

#include "IECore/MessageHandler.h"
#include "IECore/Exception.h"
#include "IECore/MurmurHash.h"
#include "IECore/SimpleTypedData.h"

#include "GafferVDB/VDBObject.h"

using namespace IECore;
using namespace GafferVDB;

namespace
{

//! Calculate the worldspace bounds - 0.5 padding required to include the full volume and not the bound of the voxel centres.
template<typename T>
Imath::Box<Imath::Vec3<T> > worldBound( const openvdb::GridBase* grid, float padding = 0.50f )
{
	openvdb::Vec3i min = grid->metaValue<openvdb::Vec3i>( grid->META_FILE_BBOX_MIN );
	openvdb::Vec3i max = grid->metaValue<openvdb::Vec3i>( grid->META_FILE_BBOX_MAX );

	openvdb::Vec3d offset = openvdb::Vec3d( padding );
	openvdb::BBoxd indexBounds = openvdb::BBoxd( min - offset, max + offset );
	openvdb::BBoxd worldBounds = grid->transform().indexToWorld( indexBounds );
	openvdb::Vec3d minBB = worldBounds.min();
	openvdb::Vec3d maxBB = worldBounds.max();

	return Imath::Box<Imath::Vec3<T> >( Imath::Vec3<T>( minBB[0], minBB[1], minBB[2] ), Imath::Vec3<T>( maxBB[0], maxBB[1], maxBB[2] ) );
}


//! allow hashing via a io stream interface.
struct MurmurHashSink
{
	typedef char char_type;
	typedef boost::iostreams::sink_tag category;

	MurmurHashSink(MurmurHash &hash)
	: hash(hash)
	{
	}

	std::streamsize write( const char *s, std::streamsize n )
	{
		hash.append( s, n );
		return n;
	}

	MurmurHash &hash;
};

}

IE_CORE_DEFINEOBJECTTYPEDESCRIPTION( VDBObject );

const unsigned int VDBObject::m_ioVersion = 0;

VDBObject::VDBObject()
{
}

VDBObject::VDBObject(const std::string& filename)
: m_filename( filename )
{
	openvdb::initialize(); // safe to call multiple times but has a performance hit of a mutex.

	// note it seems fine for this file object to go out of scope
	// and grids are still able to pull in additional grid data
	openvdb::io::File file( filename );
	file.open(); //lazy loading of grid data is default enabling OPENVDB_DISABLE_DELAYED_LOAD will load the grids up front

	openvdb::GridPtrVecPtr grids = file.getGrids();

	if ( !grids )
	{
		throw IECore::Exception( "VDBObject::VDBObject - no grids " );
	}

	for (auto grid : *grids)
	{
		m_grids[grid->getName()] = HashedGrid ( grid, true ) ;
	}
}

VDBObject::~VDBObject()
{
}

openvdb::GridBase::ConstPtr VDBObject::findGrid(const std::string& name) const
{
	auto it = m_grids.find(name);
	if ( it != m_grids.end() )
	{
		return it->second.grid();
	}

	return openvdb::GridBase::Ptr();
}

openvdb::GridBase::Ptr VDBObject::findGrid(const std::string& name)
{
	auto it = m_grids.find( name );
	if ( it != m_grids.end() )
	{
		it->second.markedAsEdited();
		return it->second.grid();
	}

	return openvdb::GridBase::Ptr();
}

std::vector<std::string> VDBObject::gridNames() const
{
	std::vector<std::string> outputGridNames;
	for( const auto &it : m_grids )
	{
		outputGridNames.push_back( it.first );
	}
	return outputGridNames;
}

void VDBObject::insertGrid( openvdb::GridBase::Ptr grid )
{
	m_grids[grid->getName()] = HashedGrid( grid, false );
}

void VDBObject::removeGrid(const std::string& name)
{
	auto it = m_grids.find( name );

	if ( it != m_grids.end() )
	{
		m_grids.erase( it );
	}
}

Imath::Box3f VDBObject::bound() const
{
	Imath::Box3f combinedBounds;

	for( const auto &it : m_grids )
	{
		Imath::Box3f gridBounds = worldBound<float>( it.second.grid().get() );

		combinedBounds.extendBy( gridBounds );
	}

	return combinedBounds;
}

void VDBObject::render( IECore::Renderer *renderer ) const
{
}

IECore::CompoundObjectPtr VDBObject::metadata( const std::string &name )
{
	openvdb::GridBase::Ptr grid = findGrid( name );

	if( !grid )
	{
		return IECore::CompoundObjectPtr();
	}

	grid->addStatsMetadata();

	CompoundObjectPtr metadata = new CompoundObject();

	for (auto metaIt = grid->beginMeta(); metaIt != grid->endMeta(); ++metaIt)
	{
		openvdb::Metadata::Ptr ptr = metaIt->second;

		if (metaIt->second->typeName() == "string")
		{
			openvdb::TypedMetadata<openvdb::Name>::ConstPtr typedPtr = openvdb::DynamicPtrCast<openvdb::TypedMetadata<openvdb::Name> >(ptr);

			if (typedPtr)
			{
				StringDataPtr stringData = new StringData();
				stringData->writable() = typedPtr->value();
				metadata->members()[metaIt->first] = stringData;
			}
		}
		else if (metaIt->second->typeName() == "int64")
		{
			openvdb::TypedMetadata<openvdb::Int64>::ConstPtr typedPtr = openvdb::DynamicPtrCast<openvdb::TypedMetadata<openvdb::Int64> >(ptr);
			if (typedPtr)
			{
				Int64DataPtr intData = new Int64Data();
				intData->writable() = typedPtr->value();
				metadata->members()[metaIt->first] = intData;
			}
		}
		else if (metaIt->second->typeName() == "bool")
		{
			openvdb::TypedMetadata<bool>::ConstPtr typedPtr = openvdb::DynamicPtrCast<openvdb::TypedMetadata<bool> > (ptr);
			if (typedPtr)
			{
				BoolDataPtr data = new BoolData();
				data->writable() = typedPtr->value();
				metadata->members()[metaIt->first] = data;
			}

		}
		else if (metaIt->second->typeName() == "vec3i")
		{
			openvdb::TypedMetadata<openvdb::math::Vec3i>::ConstPtr typedPtr = openvdb::DynamicPtrCast<openvdb::TypedMetadata<openvdb::math::Vec3i> >(ptr);
			if (typedPtr)
			{
				V3iDataPtr data = new V3iData();
				data->writable() = Imath::V3i( typedPtr->value().x(), typedPtr->value().y(), typedPtr->value().z() );
				metadata->members()[metaIt->first] = data;
			}
		}
		else
		{
			IECore::msg( IECore::MessageHandler::Warning, "VDBObject::metadata", boost::format("'%1%' has unsupported metadata type: '%2%'") % metaIt->second->typeName() % metaIt->first);
		}
	}
	return metadata;
}


bool VDBObject::isEqualTo( const IECore::Object *other ) const
{
	if( !IECore::VisibleRenderable::isNotEqualTo( other ) )
	{
		return false;
	}

	const VDBObject *vdbObject = runTimeCast<const VDBObject>( other );

	if ( !vdbObject )
	{
		return false;
	}

	if (m_grids.size() != vdbObject->m_grids.size())
	{
		return false;
	}

	for (const auto& it : m_grids)
	{
		const auto itOther = vdbObject->m_grids.find( it.first );
		if ( itOther == vdbObject->m_grids.end() )
		{
			return false;
		}

		if (itOther->second.hash() != it.second.hash())
		{
			return false;
		}
	}

	return true;
}

void VDBObject::hash( IECore::MurmurHash &h ) const
{
	IECore::VisibleRenderable::hash( h );

	for( const auto& it : m_grids )
	{
		h.append( it.second.hash() );
	}
}

void VDBObject::copyFrom( const IECore::Object *other, IECore::Object::CopyContext *context  )
{
	IECore::VisibleRenderable::copyFrom( other, context );

	const VDBObject *vdbObject = runTimeCast<const VDBObject>( other );

	if ( !vdbObject )
	{
		return;
	}

	m_grids = vdbObject->m_grids;
	m_filename = vdbObject->m_filename;
}

void VDBObject::save( IECore::Object::SaveContext *context ) const
{
	IECore::VisibleRenderable::save( context );
	throw IECore::NotImplementedException( "VDBObject::save" );
}

void VDBObject::load( IECore::Object::LoadContextPtr context )
{
	IECore::VisibleRenderable::load( context );
	throw IECore::NotImplementedException( "VDBObject::load" );
}

void VDBObject::memoryUsage( IECore::Object::MemoryAccumulator &acc) const
{
	IECore::VisibleRenderable::memoryUsage( acc );

	for( const auto it : m_grids )
	{
		acc.accumulate( it.second.grid().get(), it.second.grid()->memUsage() );
	}
}

bool VDBObject::unmodifiedFromFile() const
{
	for( const auto it : m_grids )
	{
		if( !it.second.unmodifiedFromFile() )
		{
			return false;
		}
	}

	return true;
}

openvdb::GridBase::Ptr VDBObject::HashedGrid::grid() const
{
	return m_grid;
}

bool VDBObject::HashedGrid::unmodifiedFromFile() const
{
	return m_unmodifiedFromFile;
}

IECore::MurmurHash VDBObject::HashedGrid::hash() const
{
	if( !m_hashValid )
	{
		MurmurHashSink sink( m_hash );
		boost::iostreams::stream<MurmurHashSink> hashStream( sink );

		m_grid->writeTopology( hashStream );
		m_grid->writeBuffers( hashStream );
		m_grid->writeTransform( hashStream );

		m_hashValid = true;
	}

	return m_hash;
}

void VDBObject::HashedGrid::markedAsEdited()
{
	m_unmodifiedFromFile = false;

	if( m_grid.use_count() > 1 )
	{
		m_grid = m_grid->deepCopyGrid();
		m_hash = IECore::MurmurHash();
		m_hashValid = false;
	}
}
//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015 John Haddon. All rights reserved.
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

#include "boost/python.hpp"

#include "Gaffer/TypedObjectPlug.h"
#include "Gaffer/Private/IECorePreview/LRUCache.h"

#include "IECoreVDB/VDBObject.h"

#include "IECorePython/ScopedGILRelease.h"

#include "IECore/MurmurHash.h"
#include "IECore/SimpleTypedData.h"

#include "openvdb/tools/Count.h"

using namespace std;
using namespace boost::python;
using namespace IECore;
using namespace IECoreVDB;
using namespace Gaffer;

namespace
{

template<typename T>
DataPtr dataFromVDB( T value )
{
	return new TypedData<T>( value );
}

template<typename T>
DataPtr dataFromVDB( const openvdb::math::Vec3<T> &value )
{
	using ImathType = Imath::Vec3<T>;
	return new GeometricTypedData<ImathType>(
		ImathType( value.x(), value.y(), value.z() )
	);
}

openvdb::GridBase::ConstPtr grid( const ObjectPlug &objectPlug, const std::string &gridName )
{
	ConstVDBObjectPtr vdbObject = runTimeCast<const VDBObject>( objectPlug.getValue() );
	return vdbObject ? vdbObject->findGrid( gridName ) : nullptr;
}

StringDataPtr gridValueType( const ObjectPlug &objectPlug, const std::string &gridName )
{
	IECorePython::ScopedGILRelease gilRelease;
	openvdb::GridBase::ConstPtr g = grid( objectPlug, gridName );
	return g ? new StringData( g->valueType() ) : nullptr;
}

StringVectorDataPtr gridMetadataNames( const ObjectPlug &objectPlug, const std::string &gridName )
{
	IECorePython::ScopedGILRelease gilRelease;
	StringVectorDataPtr result = new StringVectorData;
	if( openvdb::GridBase::ConstPtr g = grid( objectPlug, gridName ) )
	{
		for( auto it = g->beginMeta(); it != g->endMeta(); ++it )
		{
			result->writable().push_back( it->first );
		}
	}
	return result;
}

DataPtr gridMetadata( const ObjectPlug &objectPlug, const std::string &gridName, const std::string &metadataName )
{
	IECorePython::ScopedGILRelease gilRelease;
	if( openvdb::GridBase::ConstPtr g = grid( objectPlug, gridName ) )
	{
		openvdb::Metadata::ConstPtr m = (*g)[metadataName];
		if( !m )
		{
			return nullptr;
		}

		const std::string typeName = m->typeName();

		if( typeName == openvdb::StringMetadata::staticTypeName() )
		{
			return new StringData( static_cast<const openvdb::StringMetadata *>( m.get() )->value() );
		}
		else if( typeName == openvdb::Int64Metadata::staticTypeName() )
		{
			return new Int64Data( static_cast<const openvdb::Int64Metadata *>( m.get() )->value() );
		}
		else if( typeName == openvdb::Int32Metadata::staticTypeName() )
		{
			return new IntData( static_cast<const openvdb::Int32Metadata *>( m.get() )->value() );
		}
		else if( typeName == openvdb::FloatMetadata::staticTypeName() )
		{
			return new FloatData( static_cast<const openvdb::FloatMetadata *>( m.get() )->value() );
		}
		else if( typeName == openvdb::DoubleMetadata::staticTypeName() )
		{
			return new DoubleData( static_cast<const openvdb::DoubleMetadata *>( m.get() )->value() );
		}
		else if( typeName == openvdb::BoolMetadata::staticTypeName() )
		{
			return new BoolData( static_cast<const openvdb::BoolMetadata *>( m.get() )->value() );
		}
		else if( typeName == openvdb::Vec3IMetadata::staticTypeName() )
		{
			const openvdb::Vec3i &v = static_cast<const openvdb::Vec3IMetadata *>( m.get() )->value();
			return new V3iData( Imath::V3i( v.x(), v.y(), v.z() ) );
		}
		else
		{
			return new StringData( fmt::format( "Unknown type \"{}\"", typeName ) );
		}
	}
	return nullptr;
}

struct GridPropertyCacheGetterKey
{

	GridPropertyCacheGetterKey( const ObjectPlug *objectPlug, const std::string &gridName )
		:	objectPlug( objectPlug ), gridName( gridName )
	{
		hash = objectPlug->hash();
		hash.append( gridName );
	}

	operator const IECore::MurmurHash &() const
	{
		return hash;
	}

	IECore::MurmurHash hash;
	const ObjectPlug *objectPlug;
	const string gridName;

};

struct GridPropertyCache : public IECorePreview::LRUCache<MurmurHash, ConstDataPtr, IECorePreview::LRUCachePolicy::Parallel, GridPropertyCacheGetterKey>
{

	using PropertyGetter = std::function<ConstDataPtr ( const openvdb::GridBase *grid )>;

	GridPropertyCache( PropertyGetter propertyGetter )
		:	IECorePreview::LRUCache<MurmurHash, ConstDataPtr, IECorePreview::LRUCachePolicy::Parallel, GridPropertyCacheGetterKey>(
				[propertyGetter] ( const GridPropertyCacheGetterKey &key, size_t &cost, const IECore::Canceller *canceller ) -> ConstDataPtr {
					cost = 1;
					if( openvdb::GridBase::ConstPtr g = grid( *key.objectPlug, key.gridName ) )
					{
						// The OpenVDB function called by our PropertyGetters typically
						// use TBB tasks. Isolate them so they don't go stealing unrelated
						// tasks that could lead to deadlock.
						return tbb::this_task_arena::isolate(
							[&] () {
								return propertyGetter( g.get() );
							}
						);
					}
					return nullptr;
				},
				/* maxCost = */ 1000 // Properties are small but expensive to compute - might as well cache a bunch of them.
			)
	{
	}

};

DataPtr gridActiveVoxels( const ObjectPlug &objectPlug, const std::string &gridName )
{
	IECorePython::ScopedGILRelease gilRelease;
	static GridPropertyCache g_cache(
		[] ( const openvdb::GridBase *grid ) {
			return new Int64Data( grid->activeVoxelCount() );
		}
	);

	return boost::const_pointer_cast<Data>( g_cache.get( { &objectPlug, gridName } ) );
}

DataPtr gridVoxelBound( const ObjectPlug &objectPlug, const std::string &gridName )
{
	IECorePython::ScopedGILRelease gilRelease;
	static GridPropertyCache g_cache(
		[] ( const openvdb::GridBase *grid ) {
			const auto box = grid->evalActiveVoxelBoundingBox();
			return new Box3iData(
				Imath::Box3i(
					Imath::V3i( box.min().x(), box.min().y(), box.min().z() ),
					Imath::V3i( box.max().x(), box.max().y(), box.max().z() )
				)
			);
		}
	);

	return boost::const_pointer_cast<Data>( g_cache.get( { &objectPlug, gridName } ) );
}

DataPtr gridMemoryUsage( const ObjectPlug &objectPlug, const std::string &gridName )
{
	IECorePython::ScopedGILRelease gilRelease;
	static GridPropertyCache g_cache(
		[] ( const openvdb::GridBase *grid ) {
			return new UInt64Data( grid->memUsage() );
		}
	);

	return boost::const_pointer_cast<Data>( g_cache.get( { &objectPlug, gridName } ) );
}

DataPtr gridMinMaxValue( const ObjectPlug &objectPlug, const std::string &gridName )
{
	IECorePython::ScopedGILRelease gilRelease;
	static GridPropertyCache g_cache(

		[] ( const openvdb::GridBase *grid ) {

			CompoundDataPtr result;

			using SupportedGridTypes = openvdb::NumericGridTypes::Append<openvdb::Vec3GridTypes>;

			grid->apply<SupportedGridTypes>(

				[&result]( auto &grid ) {

					auto minMax = openvdb::tools::minMax( grid.tree() );

					result = new CompoundData;
					result->writable()["min"] = dataFromVDB( minMax.min() );
					result->writable()["max"] = dataFromVDB( minMax.max() );

				}

			);

			return result;
		}

	);

	return boost::const_pointer_cast<Data>( g_cache.get( { &objectPlug, gridName } ) );
}

} // namespace

BOOST_PYTHON_MODULE( _GafferVDBUI )
{

	def( "_gridValueType", &gridValueType, ( boost::python::arg( "objectPlug" ), boost::python::arg( "gridName" ) ) );
	def( "_gridActiveVoxels", &gridActiveVoxels, ( boost::python::arg( "objectPlug" ), boost::python::arg( "gridName" ) ) );
	def( "_gridVoxelBound", &gridVoxelBound, ( boost::python::arg( "objectPlug" ), boost::python::arg( "gridName" ) ) );
	def( "_gridMemoryUsage", &gridMemoryUsage, ( boost::python::arg( "objectPlug" ), boost::python::arg( "gridName" ) ) );
	def( "_gridMinMaxValue", &gridMinMaxValue, ( boost::python::arg( "objectPlug" ), boost::python::arg( "gridName" ) ) );
	def( "_gridMetadataNames", &gridMetadataNames, ( boost::python::arg( "objectPlug" ), boost::python::arg( "gridName" ) ) );
	def( "_gridMetadata", &gridMetadata, ( boost::python::arg( "objectPlug" ), boost::python::arg( "gridName" ), boost::python::arg( "metadataName" ) ) );

}

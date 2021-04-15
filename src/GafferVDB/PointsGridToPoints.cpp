//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine. All rights reserved.
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
//      * Neither the name of Image Engine nor the names of
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

#include "GafferVDB/PointsGridToPoints.h"

#include "IECoreVDB/VDBObject.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/PointsPrimitive.h"

#include "openvdb/openvdb.h"
#include "openvdb/points/AttributeSet.h"
#include "openvdb/points/PointConversion.h"
#include "openvdb/points/PointCount.h"

#include <cstdint>

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreVDB;
using namespace Gaffer;
using namespace GafferVDB;

namespace
{

template<typename DestType, typename SourceType>
void convert(DestType& dest, const SourceType& src )
{
	dest = src;
};

template<>
void convert(Imath::V2i& dest, const openvdb::Vec2i& src)
{
	dest = Imath::V2i(src[0], src[1]);
}

template<>
void convert(Imath::V2f& dest, const openvdb::Vec2s& src)
{
	dest = Imath::V2f(src[0], src[1]);
}

template<>
void convert(Imath::V2d& dest, const openvdb::Vec2d& src)
{
	dest = Imath::V2d(src[0], src[1]);
}

template<>
void convert(Imath::V3i& dest, const openvdb::Vec3U8& src )
{
	dest = Imath::V3i(src[0], src[1], src[2]);
}

template<>
void convert(Imath::V3i& dest, const openvdb::Vec3U16& src )
{
	dest = Imath::V3i(src[0], src[1], src[2]);
}

template<>
void convert(Imath::V3i& dest, const openvdb::Vec3i& src)
{
	dest = Imath::V3i(src[0], src[1], src[2]);
}

template<>
void convert(Imath::V3f& dest, const openvdb::Vec3s& src)
{
	dest = Imath::V3f(src[0], src[1], src[2]);
}

template<>
void convert(Imath::V3d& dest, const openvdb::Vec3d& src)
{
	dest = Imath::V3d(src[0], src[1], src[2]);
}

template<>
void convert(Imath::M44f& dest, const openvdb::Mat4s & src)
{
	for( int i = 0; i < 4; ++i )
	{
		for( int j = 0; j < 4; ++j )
		{
			dest[i][j] = src[i][j];
		}
	}
}

template<>
void convert(Imath::M44d& dest, const openvdb::Mat4d & src)
{
	for( int i = 0; i < 4; ++i )
	{
		for( int j = 0; j < 4; ++j )
		{
			dest[i][j] = src[i][j];
		}
	}
}

template<>
void convert(Imath::Quatf& dest, const openvdb::math::Quats& src)
{
	dest = Imath::Quatf( src[3], src[0], src[1], src[2]);
}

template<>
void convert(Imath::Quatd& dest, const openvdb::math::Quatd& src)
{
	dest = Imath::Quatd( src[3], src[0], src[1], src[2]);
}

typedef openvdb::points::PointDataGrid::TreeType::LeafCIter LeafIter;

template<typename CortexType, typename VDBType, template <typename P> class StorageType = IECore::TypedData>
void appendData(IECore::Data *destArray, const openvdb::points::AttributeArray& array, LeafIter leafIter)
{
	auto cortexData = IECore::runTimeCast<StorageType<std::vector<CortexType> > > ( destArray );
	auto &writable = cortexData->writable();

	openvdb::points::AttributeHandle<VDBType> attributeHandle( array );

	for( auto indexIter = leafIter->beginIndexOn(); indexIter; ++indexIter )
	{
		CortexType d;
		convert(d, attributeHandle.get( *indexIter ));
		writable.push_back( d );
	}
};

template<typename CortexType, template <typename P> class StorageType = IECore::TypedData>
IECore::DataPtr createArray( size_t size )
{
	auto p = new StorageType<std::vector<CortexType> >();
	auto &writable = p->writable();
	writable.reserve( size );
	return p;
};

struct Functions
{
	typedef std::function<IECore::DataPtr(size_t size)> CreateFn;
	typedef std::function<
		void (
			IECore::Data *,
			const openvdb::points::AttributeArray&,
			LeafIter
		)
	> AppendFn;

	Functions( CreateFn create , AppendFn append ) : m_create(create), m_append(append) {}

	CreateFn m_create;
	AppendFn m_append;
};

const std::map<std::string, Functions >  converters =
{
	// scalar numeric types
	{
		openvdb::typeNameAsString<half>(),
		Functions(
			[](size_t size) -> IECore::DataPtr { return createArray<half>(size); },
			[](IECore::Data *destArray, const openvdb::points::AttributeArray& array, LeafIter leafIter)  { appendData<half, half>( destArray, array, leafIter ); }
		)
	},
	{
		openvdb::typeNameAsString<float>(),
		Functions(
			[](size_t size) -> IECore::DataPtr { return createArray<float>(size); },
			[](IECore::Data *destArray, const openvdb::points::AttributeArray& array, LeafIter leafIter)  { appendData<float, float>( destArray, array, leafIter ); }
		)
	},
	{
		openvdb::typeNameAsString<double>(),
		Functions(
			[](size_t size) -> IECore::DataPtr { return createArray<double>(size); },
			[](IECore::Data *destArray, const openvdb::points::AttributeArray& array, LeafIter leafIter)  { appendData<double, double>( destArray, array, leafIter ); }
		)
	},
	{
		openvdb::typeNameAsString<uint8_t>(),
		Functions(
			[](size_t size) -> IECore::DataPtr { return createArray<uint8_t>(size); },
			[](IECore::Data *destArray, const openvdb::points::AttributeArray& array, LeafIter leafIter)  { appendData<uint8_t, uint8_t>( destArray, array, leafIter ); }
		)
	},
	{
		openvdb::typeNameAsString<uint16_t>(),
		Functions(
			[](size_t size) -> IECore::DataPtr { return createArray<uint16_t>(size); },
			[](IECore::Data *destArray, const openvdb::points::AttributeArray& array, LeafIter leafIter)  { appendData<uint16_t, uint16_t>( destArray, array, leafIter ); }
		)
	},
	{
		openvdb::typeNameAsString<uint32_t>(),
		Functions(
			[](size_t size) -> IECore::DataPtr { return createArray<uint32_t>(size); },
			[](IECore::Data *destArray, const openvdb::points::AttributeArray& array, LeafIter leafIter)  { appendData<uint32_t, uint32_t>( destArray, array, leafIter ); }
		)
	},
	// todo check this function
	{
		openvdb::typeNameAsString<uint8_t>(),
		Functions(
			[](size_t size) -> IECore::DataPtr { return createArray<uint8_t>(size); },
			[](IECore::Data *destArray, const openvdb::points::AttributeArray& array, LeafIter leafIter)  { appendData<uint8_t, int8_t>( destArray, array, leafIter ); }
		)
	},
	{
		openvdb::typeNameAsString<int16_t>(),
		Functions(
			[](size_t size) -> IECore::DataPtr { return createArray<int16_t>(size); },
			[](IECore::Data *destArray, const openvdb::points::AttributeArray& array, LeafIter leafIter)  { appendData<int16_t, int16_t>( destArray, array, leafIter ); }
		)
	},
	{
		openvdb::typeNameAsString<int32_t>(),
		Functions(
			[](size_t size) -> IECore::DataPtr { return createArray<int32_t>(size); },
			[](IECore::Data *destArray, const openvdb::points::AttributeArray& array, LeafIter leafIter)  { appendData<int32_t, int32_t>( destArray, array, leafIter ); }
		)
	},

	// Vec2 int, single, double
	{
		openvdb::typeNameAsString<openvdb::Vec2i>(),
		Functions(
			[](size_t size) -> IECore::DataPtr { return createArray<Imath::V2i, IECore::GeometricTypedData>(size); },
			[](IECore::Data *destArray, const openvdb::points::AttributeArray& array, LeafIter leafIter)  { appendData<Imath::V2i, openvdb::Vec2i, IECore::GeometricTypedData>( destArray, array, leafIter ); }
		)
	},
	{
		openvdb::typeNameAsString<openvdb::Vec2s>(),
		Functions(
			[](size_t size) -> IECore::DataPtr { return createArray<Imath::V2f, IECore::GeometricTypedData>(size); },
			[](IECore::Data *destArray, const openvdb::points::AttributeArray& array, LeafIter leafIter)  { appendData<Imath::V2f, openvdb::Vec2s, IECore::GeometricTypedData>( destArray, array, leafIter ); }
		)
	},
	{
		openvdb::typeNameAsString<openvdb::Vec2d>(),
		Functions(
			[](size_t size) -> IECore::DataPtr { return createArray<Imath::V2d, IECore::GeometricTypedData>(size); },
			[](IECore::Data *destArray, const openvdb::points::AttributeArray& array, LeafIter leafIter)  { appendData<Imath::V2d, openvdb::Vec2d, IECore::GeometricTypedData>( destArray, array, leafIter ); }
		)
	},
	// Vec3 u8, 16, int, single, double
	{
		openvdb::typeNameAsString<openvdb::Vec3U8>(),
		Functions(
			[](size_t size) -> IECore::DataPtr { return createArray<Imath::V3i, IECore::GeometricTypedData>(size); },
			[](IECore::Data *destArray, const openvdb::points::AttributeArray& array, LeafIter leafIter)  { appendData<Imath::V3i, openvdb::Vec3U8, IECore::GeometricTypedData>( destArray, array, leafIter ); }
		)
	},
	{
		openvdb::typeNameAsString<openvdb::Vec3U16>(),
		Functions(
			[](size_t size) -> IECore::DataPtr { return createArray<Imath::V3i, IECore::GeometricTypedData>(size); },
			[](IECore::Data *destArray, const openvdb::points::AttributeArray& array, LeafIter leafIter)  { appendData<Imath::V3i, openvdb::Vec3U16, IECore::GeometricTypedData>( destArray, array, leafIter ); }
		)
	},
	{
		openvdb::typeNameAsString<openvdb::Vec3i>(),
		Functions(
			[](size_t size) -> IECore::DataPtr { return createArray<Imath::V3i, IECore::GeometricTypedData>(size); },
			[](IECore::Data *destArray, const openvdb::points::AttributeArray& array, LeafIter leafIter)  { appendData<Imath::V3i, openvdb::Vec3i, IECore::GeometricTypedData>( destArray, array, leafIter ); }
		)
	},
	{
		openvdb::typeNameAsString<openvdb::Vec3s>(),
		Functions(
			[](size_t size) -> IECore::DataPtr { return createArray<Imath::V3f, IECore::GeometricTypedData>(size); },
			[](IECore::Data *destArray, const openvdb::points::AttributeArray& array, LeafIter leafIter)  { appendData<Imath::V3f, openvdb::Vec3s, IECore::GeometricTypedData>( destArray, array, leafIter ); }
		)
	},
	{
		openvdb::typeNameAsString<openvdb::Vec3d>(),
		Functions(
			[](size_t size) -> IECore::DataPtr { return createArray<Imath::V3d, IECore::GeometricTypedData>(size); },
			[](IECore::Data *destArray, const openvdb::points::AttributeArray& array, LeafIter leafIter)  { appendData<Imath::V3d, openvdb::Vec3d, IECore::GeometricTypedData>( destArray, array, leafIter ); }
		)
	},
	{
		openvdb::typeNameAsString<std::string>(),
		Functions(
			[](size_t size) -> IECore::DataPtr { return createArray<std::string>(size); },
			[](IECore::Data *destArray, const openvdb::points::AttributeArray& array, LeafIter leafIter)  { appendData<std::string, std::string>( destArray, array, leafIter ); }
		)
	},
	// matrix conversion - single & double
	{
		openvdb::typeNameAsString<openvdb::Mat4s>(),
		Functions(
			[](size_t size) -> IECore::DataPtr { return createArray<Imath::M44f>(size); },
			[](IECore::Data *destArray, const openvdb::points::AttributeArray& array, LeafIter leafIter)  { appendData<Imath::M44f, openvdb::Mat4s>( destArray, array, leafIter ); }
		)
	},
	{
		openvdb::typeNameAsString<openvdb::Mat4d>(),
		Functions(
			[](size_t size) -> IECore::DataPtr { return createArray<Imath::M44d>(size); },
			[](IECore::Data *destArray, const openvdb::points::AttributeArray& array, LeafIter leafIter)  { appendData<Imath::M44d, openvdb::Mat4d>( destArray, array, leafIter ); }
		)
	},

	// quaternions - single & double
	{
		openvdb::typeNameAsString<openvdb::math::Quats>(),
		Functions(
			[](size_t size) -> IECore::DataPtr { return createArray<Imath::Quatf>(size); },
			[](IECore::Data *destArray, const openvdb::points::AttributeArray& array, LeafIter leafIter)  { appendData<Imath::Quatf, openvdb::math::Quats>( destArray, array, leafIter ); }
		)
	},
	{
		openvdb::typeNameAsString<openvdb::math::Quatd>(),
		Functions(
			[](size_t size) -> IECore::DataPtr { return createArray<Imath::Quatd>(size); },
			[](IECore::Data *destArray, const openvdb::points::AttributeArray& array, LeafIter leafIter)  { appendData<Imath::Quatd, openvdb::math::Quatd>( destArray, array, leafIter ); }
		)
	},
};

void appendPrimitiveVariableData( IECoreScene::PrimitiveVariableMap &variableMap,
	const std::string &name,
	const std::string &type,
	LeafIter leafIter,
	const openvdb::points::AttributeArray &arrayData,
	uint64_t count)
{

	auto itConverter = converters.find( type );
	if ( itConverter == converters.end() )
	{
		return;
	}

	IECoreScene::PrimitiveVariable primVar;

	auto primVarIt = variableMap.find( name );
	if( primVarIt == variableMap.end() )
	{
		primVar = IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, itConverter->second.m_create( count ) );
		variableMap[name] = primVar;
	}
	else
	{
		primVar = primVarIt->second;
	}

	itConverter->second.m_append( primVar.data.get(), arrayData, leafIter);
}

IECoreScene::PointsPrimitivePtr createPointsPrimitive( openvdb::GridBase::ConstPtr baseGrid, std::function<bool( const std::string & )> primitiveVariableFilter )
{
	openvdb::points::PointDataGrid::ConstPtr pointsGrid = openvdb::GridBase::constGrid<openvdb::points::PointDataGrid>( baseGrid );
	if( !pointsGrid )
	{
		return nullptr;
	}

	openvdb::Index64 count = openvdb::points::pointCount( pointsGrid->tree() );

	IECore::V3fVectorDataPtr pointData = new IECore::V3fVectorData();
	auto &points = pointData->writable();
	points.reserve( count );

	IECoreScene::PrimitiveVariableMap primVars;

	for( auto leafIter = pointsGrid->tree().cbeginLeaf(); leafIter; ++leafIter )
	{
		const openvdb::points::AttributeArray &array = leafIter->constAttributeArray( "P" );
		openvdb::points::AttributeHandle<openvdb::Vec3f> positionHandle( array );

		const openvdb::points::AttributeSet &attributeSet = leafIter->attributeSet();
		const openvdb::points::AttributeSet::Descriptor &descriptor = attributeSet.descriptor();

		for (const auto &it : descriptor.map() )
		{
			size_t index = it.second;
			const std::string &attributeName = it.first;
			if ( !primitiveVariableFilter( attributeName ) )
			{
				continue;
			}
			const openvdb::points::AttributeArray *attributeArray = attributeSet.get( index );
			appendPrimitiveVariableData( primVars, attributeName, descriptor.type( index ).first, leafIter, *attributeArray, count );
		}

		for( auto indexIter = leafIter->beginIndexOn(); indexIter; ++indexIter )
		{
			openvdb::Vec3f voxelPosition = positionHandle.get( *indexIter );
			const openvdb::Vec3d xyz = indexIter.getCoord().asVec3d();
			openvdb::Vec3f worldPosition = pointsGrid->transform().indexToWorld( voxelPosition + xyz );
			points.emplace_back( worldPosition[0], worldPosition[1], worldPosition[2] );
		}
	}

	IECoreScene::PointsPrimitivePtr newPoints = new IECoreScene::PointsPrimitive( pointData );

	for ( auto it : primVars )
	{
		newPoints->variables[it.first] = it.second;
	}

	return newPoints;
}

} //namespace

GAFFER_NODE_DEFINE_TYPE( PointsGridToPoints );

size_t PointsGridToPoints::g_firstPlugIndex = 0;

PointsGridToPoints::PointsGridToPoints( const std::string &name ) : SceneElementProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "grid", Plug::In, "points" ) );

	// 'names' & 'invertNames' match PrimitiveVariableProcessor
	addChild( new StringPlug( "names" ) );
	addChild( new BoolPlug( "invertNames" ) );
}

PointsGridToPoints::~PointsGridToPoints()
{
}

Gaffer::StringPlug *PointsGridToPoints::gridPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *PointsGridToPoints::gridPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *PointsGridToPoints::namesPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *PointsGridToPoints::namesPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1);
}

Gaffer::BoolPlug *PointsGridToPoints::invertNamesPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::BoolPlug *PointsGridToPoints::invertNamesPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

void PointsGridToPoints::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );

	if( input == gridPlug() || input == namesPlug() || input == invertNamesPlug() )
	{
		outputs.push_back( outPlug()->objectPlug() );
	}
}

bool PointsGridToPoints::processesObject() const
{
	return true;
}

void PointsGridToPoints::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	SceneElementProcessor::hashProcessedObject( path, context, h );

	gridPlug()->hash( h );
	namesPlug()->hash( h );
	invertNamesPlug()->hash ( h );
}

IECore::ConstObjectPtr PointsGridToPoints::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const
{
	const VDBObject *vdbObject = runTimeCast<const VDBObject>( inputObject.get() );
	if( !vdbObject )
	{
		return inputObject;
	}

	openvdb::GridBase::ConstPtr grid = vdbObject->findGrid( gridPlug()->getValue() );

	if ( !grid )
	{
		return inputObject;
	}

	std::string names = namesPlug()->getValue();
	bool invert = invertNamesPlug()->getValue();
	auto primitiveVariableFilter = [names, invert](const std::string& primitiveVariableName) -> bool
	{
		if (primitiveVariableName == "P")
		{
			return false;
		}
		return StringAlgo::matchMultiple( primitiveVariableName, names ) != invert;
	};

	IECoreScene::PointsPrimitivePtr points =  createPointsPrimitive( grid, primitiveVariableFilter );

	if ( !points )
	{
		return inputObject;
	}

	return points;
}

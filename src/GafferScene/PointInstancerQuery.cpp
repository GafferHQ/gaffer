//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//       *Redistributions of source code must retain the above
//        copyright notice, this list of conditions and the following
//        disclaimer.
//
//       *Redistributions in binary form must reproduce the above
//        copyright notice, this list of conditions and the following
//        disclaimer in the documentation and/or other materials provided with
//        the distribution.
//
//       *Neither the name of John Haddon nor the names of
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

#include "GafferScene/PointInstancerQuery.h"

#include "GafferScene/Private/PointInstancerAlgo.h"

#include "IECore/DataAlgo.h"
#include "IECore/NullObject.h"

using namespace std;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

struct InstanceAttribute
{

	template<typename T>
	DataPtr operator() ( const GeometricTypedData<vector<T>> *data, const PrimitiveVariable &primitiveVariable, size_t pointIndex ) const
	{
		using IndexedView = PrimitiveVariable::IndexedView<T>;
		IndexedView indexedView( primitiveVariable );

		using DataType = GeometricTypedData<T>;
		typename DataType::Ptr result = new DataType( indexedView[pointIndex] );
		result->setInterpretation( data->getInterpretation() );
		return result;
	}

	template<typename T>
	DataPtr operator() ( const TypedData<vector<T>> *data, const PrimitiveVariable &primitiveVariable, size_t pointIndex ) const
	{
		using IndexedView = PrimitiveVariable::IndexedView<T>;
		IndexedView indexedView( primitiveVariable );

		using DataType = TypedData<T>;
		return new DataType( indexedView[pointIndex] );
	}

	DataPtr operator() ( const Data *data, const PrimitiveVariable &primitiveVariable, size_t pointIndex ) const
	{
		return nullptr;
	}

};

IECore::CompoundObjectPtr instanceAttributes( const IECoreScene::PointInstancer *instancer, size_t pointIndex )
{
	IECore::CompoundObjectPtr result = new IECore::CompoundObject;

	for( const auto &[name, primitiveVariable] : instancer->instanceAttributes() )
	{
		if( !instancer->isPrimitiveVariableValid( primitiveVariable ) )
		{
			// Avoid potential out-of-bounds reads if variable is wrong size.
			continue;
		}
		InstanceAttribute a;
		auto d = IECore::dispatch( primitiveVariable.data.get(), a, primitiveVariable, pointIndex );
		if( d )
		{
			result->members()[name] = d;
		}
	}

	return result;
}

} // namespace

struct PointInstancerQuery::IDMapData : public IECore::Data
{
	// Maps from ID to index;
	using IDMap = std::unordered_map<int64_t, size_t>;
	std::optional<IDMap> map;
	// Holds the indices that are invisible.
	std::unordered_set<size_t> invisibleIndices;
};

size_t PointInstancerQuery::g_firstPlugIndex = 0;

GAFFER_NODE_DEFINE_TYPE( PointInstancerQuery );

PointInstancerQuery::PointInstancerQuery( const std::string &name )
	:	Gaffer::ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "scene" ) );
	addChild( new Gaffer::StringPlug( "location" ) );
	/// \todo If we had an Int64Plug, we would probably use it here.
	addChild( new Gaffer::IntPlug( "id", Plug::In, 0, 0 ) );

	addChild( new Gaffer::BoolPlug( "exists", Gaffer::Plug::Out ) );
	addChild( new Gaffer::StringPlug( "prototype", Gaffer::Plug::Out ) );
	addChild( new Gaffer::M44fPlug( "transform", Gaffer::Plug::Out ) );
	addChild( new Gaffer::BoolPlug( "visible", Gaffer::Plug::Out ) );
	addChild( new Gaffer::CompoundObjectPlug( "attributes", Gaffer::Plug::Out ) );

	addChild( new Gaffer::ObjectPlug( "__idMap", Gaffer::Plug::Out, IECore::NullObject::defaultNullObject() ) );
}

PointInstancerQuery::~PointInstancerQuery()
{
}

ScenePlug *PointInstancerQuery::scenePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const ScenePlug *PointInstancerQuery::scenePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *PointInstancerQuery::locationPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *PointInstancerQuery::locationPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::IntPlug *PointInstancerQuery::idPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::IntPlug *PointInstancerQuery::idPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

Gaffer::BoolPlug *PointInstancerQuery::existsPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::BoolPlug *PointInstancerQuery::existsPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

Gaffer::StringPlug *PointInstancerQuery::prototypePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::StringPlug *PointInstancerQuery::prototypePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

Gaffer::M44fPlug *PointInstancerQuery::transformPlug()
{
	return getChild<M44fPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::M44fPlug *PointInstancerQuery::transformPlug() const
{
	return getChild<M44fPlug>( g_firstPlugIndex + 5 );
}

Gaffer::BoolPlug *PointInstancerQuery::visiblePlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::BoolPlug *PointInstancerQuery::visiblePlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 6 );
}

Gaffer::CompoundObjectPlug *PointInstancerQuery::attributesPlug()
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 7 );
}

const Gaffer::CompoundObjectPlug *PointInstancerQuery::attributesPlug() const
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 7 );
}

Gaffer::ObjectPlug *PointInstancerQuery::idMapPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 8 );
}

const Gaffer::ObjectPlug *PointInstancerQuery::idMapPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 8 );
}

void PointInstancerQuery::affects( const Gaffer::Plug *const input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if( affectsQuerySource( input ) )
	{
		outputs.push_back( existsPlug() );
		outputs.push_back( prototypePlug() );
		outputs.push_back( transformPlug() );
		outputs.push_back( visiblePlug() );
		outputs.push_back( attributesPlug() );
	}

	if( input == scenePlug()->objectPlug() )
	{
		outputs.push_back( idMapPlug() );
	}
}

void PointInstancerQuery::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if(
		output == existsPlug() ||
		output == prototypePlug() ||
		output == transformPlug() ||
		output == visiblePlug() ||
		output == attributesPlug()
	)
	{
		ComputeNode::hash( output, context, h );
		hashQuerySource( context, h );
		if( output == prototypePlug() )
		{
			// `hashQuerySource()` uses the location but doesn't include it in the hash,
			// allowing us to share most results across identical PointInstancers at different
			// locations. However, we use the location when converting prototypes to absolute paths,
			// so we need to include it in the hash for this one output.
			locationPlug()->hash( h );
		}
	}
	else if( output == idMapPlug() )
	{
		ComputeNode::hash( output, context, h );
		scenePlug()->objectPlug()->hash( h );
	}
	else
	{
		ComputeNode::hash( output, context, h );
	}
}

void PointInstancerQuery::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if(
		output == existsPlug() ||
		output == prototypePlug() ||
		output == transformPlug() ||
		output == visiblePlug() ||
		output == attributesPlug()
	)
	{
		auto [pointInstancer, pointIndex, idMapData] = querySource( context );
		if( output == existsPlug() )
		{
			static_cast<BoolPlug *>( output )->setValue( pointInstancer && pointIndex >= 0 );
		}
		else if( output == prototypePlug() )
		{
			string prototype;
			if( pointInstancer && pointIndex >= 0 )
			{
				auto prototypeIndices = pointInstancer->getPrototypeIndex();
				auto prototypes = pointInstancer->getPrototypes();
				if( prototypeIndices && prototypes && (size_t)pointIndex < prototypeIndices.size())
				{
					const int prototypeIndex = prototypeIndices[pointIndex];
					if( prototypeIndex >= 0 && (size_t)prototypeIndex < prototypes.size() )
					{
						prototype = prototypes[prototypeIndex];
						if( prototype.size() )
						{
							prototype = ScenePlug::pathToString(
								Private::PointInstancerAlgo::fullPrototypePath(
									prototype,
									ScenePlug::stringToPath( locationPlug()->getValue() )
								)
							);
						}
					}
				}
			}
			static_cast<StringPlug *>( output )->setValue( prototype );
		}
		else if( output == transformPlug() )
		{
			Imath::M44f transform;
			if( pointInstancer && pointIndex >= 0 )
			{
				IECoreScene::PointInstancer::TransformQuery transformQuery( *pointInstancer );
				transform = transformQuery.transform( pointIndex );
			}
			static_cast<M44fPlug *>( output )->setValue( transform );
		}
		else if( output == visiblePlug() )
		{
			bool visible = false;
			if( pointInstancer && pointIndex >= 0 )
			{
				visible = !idMapData->invisibleIndices.count( pointIndex );
			}
			static_cast<BoolPlug *>( output )->setValue( visible );
		}
		else if( output == attributesPlug() )
		{
			ConstCompoundObjectPtr attributes = attributesPlug()->defaultValue();
			if( pointInstancer && pointIndex >= 0 )
			{
				attributes = instanceAttributes( pointInstancer.get(), pointIndex );
			}
			static_cast<CompoundObjectPlug *>( output )->setValue( attributes );
		}
	}
	else if( output == idMapPlug() )
	{
		IDMapDataPtr mapData = new IDMapData;
		auto pointInstancer = IECore::runTimeCast<const IECoreScene::PointInstancer>( scenePlug()->objectPlug()->getValue() );
		if( pointInstancer )
		{
			if( auto ids = pointInstancer->getID() )
			{
				auto &map = mapData->map.emplace();
				for( size_t i = 0; i < ids.size(); ++i )
				{
					map[ids[i]] = i;
				}
			}

			if( auto invisibleIDs = pointInstancer->getInvisibleIDs() )
			{
				for( const auto id : invisibleIDs )
				{
					if( mapData->map )
					{
						auto it = mapData->map->find( id );
						if( it != mapData->map->end() )
						{
							mapData->invisibleIndices.insert( it->second );
						}
					}
					else
					{
						mapData->invisibleIndices.insert( id );
					}
				}
			}
		}
		static_cast<ObjectPlug *>( output )->setValue( mapData );
	}
	else
	{
		ComputeNode::compute( output, context );
	}
}

bool PointInstancerQuery::affectsQuerySource( const Gaffer::Plug *input ) const
{
	return
		input == locationPlug() ||
		input == scenePlug()->existsPlug() ||
		input == scenePlug()->objectPlug() ||
		input == idPlug()
	;
}

void PointInstancerQuery::hashQuerySource( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const string location = locationPlug()->getValue();
	if( location.empty() )
	{
		return;
	}

	const auto locationPath = ScenePlug::stringToPath( location );
	ScenePlug::PathScope scope( context, &locationPath );
	if( !scenePlug()->existsPlug()->getValue() )
	{
		return;
	}

	scenePlug()->objectPlug()->hash( h );
	idMapPlug()->hash( h );
	idPlug()->hash( h );
}

PointInstancerQuery::QuerySource PointInstancerQuery::querySource( const Gaffer::Context *context ) const
{
	const string location = locationPlug()->getValue();
	if( location.empty() )
	{
		return { nullptr, -1, nullptr };
	}

	const auto locationPath = ScenePlug::stringToPath( location );
	ScenePlug::PathScope scope( context, &locationPath );
	if( !scenePlug()->existsPlug()->getValue() )
	{
		return { nullptr, -1, nullptr };
	}

	auto pointInstancer = IECore::runTimeCast<const IECoreScene::PointInstancer>( scenePlug()->objectPlug()->getValue() );
	if( !pointInstancer )
	{
		return { nullptr, -1, nullptr };
	}

	auto idMapData = IECore::runTimeCast<const IDMapData>( idMapPlug()->getValue() );
	const int64_t id = idPlug()->getValue();
	int64_t pointIndex = -1;
	if( !idMapData->map )
	{
		if( (size_t)id < pointInstancer->getNumPoints() )
		{
			pointIndex = id;
		}
	}
	else
	{
		auto it = idMapData->map->find( id );
		if( it != idMapData->map->end() )
		{
			pointIndex = it->second;
		}
	}
	return { pointInstancer, pointIndex, idMapData };
}

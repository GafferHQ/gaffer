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

#include "GafferScene/Capsule.h"
#include "GafferScene/Orientation.h"
#include "GafferScene/SceneAlgo.h"

#include "GafferScene/Private/ChildNamesMap.h"
#include "GafferScene/Private/RendererAlgo.h"
#include "GafferScene/Private/IECoreScenePreview/Renderer.h"

#include "Gaffer/Context.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/Private/IECorePreview/LRUCache.h"

#include "IECoreScene/Primitive.h"

#include "IECore/DataAlgo.h"
#include "IECore/MessageHandler.h"
#include "IECore/ObjectVector.h"
#include "IECore/NullObject.h"
#include "IECore/VectorTypedData.h"

#include "boost/lexical_cast.hpp"
#include "boost/unordered_set.hpp"

#include "tbb/blocked_range.h"
#include "tbb/parallel_for.h"
#include "tbb/parallel_reduce.h"
#include "tbb/spin_mutex.h"

#include "fmt/format.h"

#include <functional>
#include <unordered_map>

using namespace std;
using namespace std::placeholders;
using namespace tbb;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

const PrimitiveVariable *findVertexVariable( const IECoreScene::Primitive* primitive, const InternedString &name )
{
	PrimitiveVariableMap::const_iterator it = primitive->variables.find( name );
	if( it == primitive->variables.end() )
	{
		return nullptr;
	}

	if(
		it->second.interpolation == IECoreScene::PrimitiveVariable::Vertex ||
		(
			it->second.interpolation == IECoreScene::PrimitiveVariable::Varying &&
			primitive->variableSize( PrimitiveVariable::Vertex ) == primitive->variableSize( PrimitiveVariable::Varying )
		)
	)
	{
		return &it->second;
	}

	return nullptr;

}

// We need to able to quantize all our basic numeric values, so we have a set of templates for this, with
// a special exception if you try to use a non-zero quantize on a type that can't be quantize ( ie. a string ).
//
// We quantize by forcing a value to the closest value that is a multiple of quantize.  For vector types,
// this is done independently for each axis.
class QuantizeException {};

template <class T>
inline T quantize( const T &v, float q )
{
	if( q != 0.0f )
	{
		throw QuantizeException();
	}
	return v;
}

template <>
inline float quantize( const float &v, float q )
{
	if( q == 0.0f )
	{
		return v;
	}
	// \todo : Higher performance round
	float r = q * round( v / q );

	// Letting negative zeros slip through is confusing because they hash to different values
	if( r == 0 )
	{
		r = 0;
	}
	return r;
}

template <>
inline int quantize( const int &v, float q )
{
	if( q == 0.0f )
	{
		return v;
	}
	int intQuantize = round( q );
	if( intQuantize == 0 )
	{
		return v;
	}
	int halfQuantize = intQuantize / 2;
	return intQuantize * ( ( v + halfQuantize ) / intQuantize );
}

template <class T>
inline Vec2<T> quantize( const Vec2<T> &v, float q )
{
	return Vec2<T>( quantize( v[0], q ), quantize( v[1], q ) );
}

template <class T>
inline Vec3<T> quantize( const Vec3<T> &v, float q )
{
	return Vec3<T>( quantize( v[0], q ), quantize( v[1], q ), quantize( v[2], q ) );
}

template <>
inline Color3f quantize( const Color3f &v, float q )
{
	return Color3f( quantize( v[0], q ), quantize( v[1], q ), quantize( v[2], q ) );
}

template <>
inline Color4f quantize( const Color4f &v, float q )
{
	return Color4f( quantize( v[0], q ), quantize( v[1], q ), quantize( v[2], q ), quantize( v[3], q ) );
}

// An internal struct for storing everything we need to know about a context modification we're making
// when accessing the prototypes scene
struct PrototypeContextVariable
{
	InternedString name;               // Name of context variable
	const PrimitiveVariable *primVar;  // Primitive variable that drives it
	float quantize;                    // The interval we quantize to
	bool offsetMode;                   // Special mode for adding to existing variable instead of replacing
	bool seedMode;                     // Special mode for seed context which is driven from the id
	int numSeeds;                      // When in seedMode, the number of distinct seeds to output
	int seedScramble;                  // A random seed that affects how seeds are generated
};


// A functor for use with IECore::dispatch that sets a variable in a context, based on a PrototypeContextVariable
// struct
struct AccessPrototypeContextVariable
{
	template< class T>
	void operator()( const TypedData<vector<T>> *data, const PrototypeContextVariable &v, size_t index, Context::EditableScope &scope )
	{
		T raw = PrimitiveVariable::IndexedView<T>( *v.primVar )[index];
		T value = quantize( raw, v.quantize );
		scope.setAllocated( v.name, value );
	}

	void operator()( const TypedData<vector<float>> *data, const PrototypeContextVariable &v, size_t index, Context::EditableScope &scope )
	{
		float raw = PrimitiveVariable::IndexedView<float>( *v.primVar )[index];
		float value = quantize( raw, v.quantize );

		if( v.offsetMode )
		{
			scope.setAllocated( v.name, value + scope.context()->get<float>( v.name ) );
		}
		else
		{
			scope.setAllocated( v.name, value );
		}
	}

	void operator()( const TypedData<vector<int>> *data, const PrototypeContextVariable &v, size_t index, Context::EditableScope &scope )
	{
		int raw = PrimitiveVariable::IndexedView<int>( *v.primVar )[index];
		int value = quantize( raw, v.quantize );

		if( v.offsetMode )
		{
			scope.setAllocated( v.name, float(value) + scope.context()->get<float>( v.name ) );
		}
		else
		{
			scope.setAllocated( v.name, value );
		}
	}

	void operator()( const Data *data, const PrototypeContextVariable &v, size_t index, Context::EditableScope &scope )
	{
		throw IECore::Exception( "Context variable prim vars must contain vector data" );
	}
};

// A functor for use with IECore::dispatch that adds to a hash, based on a PrototypeContextVariable
// struct.  This is only used to count the number of unique hashes, so we can take some shortcuts, for
// example, we ignore the offsetMode, because adding the offsets to a different global time doesn't change
// the number of unique offsets.  We also ignore the name of the context variable, since we always process
// the same PrototypeContextVariables in the same order
struct UniqueHashPrototypeContextVariable
{
	template< class T>
	void operator()( const TypedData<vector<T>> *data, const PrototypeContextVariable &v, size_t index, MurmurHash &contextHash )

	{
		T raw = PrimitiveVariable::IndexedView<T>( *v.primVar )[index];
		T value = quantize( raw, v.quantize );
		contextHash.append( value );
	}

	void operator()( const Data *data, const PrototypeContextVariable &v, int index, MurmurHash &contextHash )
	{
		throw IECore::Exception( "Context variable prim vars must contain vector data" );
	}
};

InternedString g_prototypeRootName( "root" );
ConstInternedStringVectorDataPtr g_emptyNames = new InternedStringVectorData();

struct IdData
{
	IdData() :
		intElements( nullptr ), int64Elements( nullptr )
	{
	}

	void initialize( const Primitive *primitive, const std::string &name )
	{
		if( const IntVectorData *intData = primitive->variableData<IntVectorData>( name ) )
		{
			intElements = &intData->readable();
		}
		else if( const Int64VectorData *int64Data = primitive->variableData<Int64VectorData>( name ) )
		{
			int64Elements = &int64Data->readable();
		}

	}

	size_t size() const
	{
		if( intElements )
		{
			return intElements->size();
		}
		else if( int64Elements )
		{
			return int64Elements->size();
		}
		else
		{
			return 0;
		}
	}

	int64_t element( size_t i ) const
	{
		if( intElements )
		{
			return (*intElements)[i];
		}
		else
		{
			return (*int64Elements)[i];
		}
	}

	const std::vector<int> *intElements;
	const std::vector<int64_t> *int64Elements;

};

// We create a seed integer that corresponds to the id by hashing the id and then modulo'ing to
// numSeeds, to create seeds in the range 0 .. numSeeds-1 that persistently correspond to the ids,
// with a grouping pattern that can be changed with seedScramble
int seedForPoint( size_t index, const IdData &idData, int numSeeds, int seedScramble )
{
	int64_t id = index;
	if( idData.size() )
	{
		id = idData.element( index );
	}

	// numSeeds is set to 0 when we're just passing through the id
	if( numSeeds != 0 )
	{
		// The method used for random generation of seeds is actually rather important.
		// We need a random access RNG which allows evaluating any input id independently,
		// and should not create lattice artifacts if interpreted as a spacial attribute
		// such as size.  This is actually a somewhat demanding set of criteria - many
		// easy to seed RNGs with a small state space could create lattice artifacts.
		//
		// Using MurmurHash doesn't seem conceptually perfect, but it uses code we already
		// have around, should perform fairly well ( might help if the constructor was inlined ),
		// and I've tested for lattice artifacts by generating 200 000 points with Y set to
		// seedId, and X set to point index.  These points looked good, with even distribution
		// and no latticing, so this is probably a reasonable approach to stick with

		IECore::MurmurHash seedHash;
		seedHash.append( seedScramble );

		if( id <= INT32_MAX && id >= INT_MIN )
		{
			// This branch shouldn't be needed, we'd like to just treat ids as 64 bit now ...
			// but if we just took the branch below, that would changing the seeding of existing
			// scenes.
			seedHash.append( (int)id );
		}
		else
		{
			seedHash.append( id );
		}

		id = int( ( double( seedHash.h1() ) / double( UINT64_MAX ) ) * double( numSeeds ) );
		id = id % numSeeds;  // For the rare case h1 / max == 1.0, make sure we stay in range
	}
	return id;
}

}

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
			ConstPrimitivePtr primitive,
			PrototypeMode mode,
			const std::string &prototypeIndexName,
			const std::string &rootsVariable,
			const StringVectorData *rootsList,
			const ScenePlug *prototypes,
			const std::string &idName,
			bool omitDuplicateIds,
			const std::string &position,
			const std::string &orientation,
			const std::string &scale,
			const std::string &inactiveIds,
			const std::string &attributes,
			const std::string &attributePrefix,
			const std::vector< PrototypeContextVariable > &prototypeContextVariables
		)
			:	m_primitive( primitive ),
				m_numPrototypes( 0 ),
				m_numValidPrototypes( 0 ),
				m_prototypeIndices( nullptr ),
				m_positions( nullptr ),
				m_orientations( nullptr ),
				m_scales( nullptr ),
				m_uniformScales( nullptr ),
				m_prototypeContextVariables( prototypeContextVariables )
		{
			if( !m_primitive )
			{
				return;
			}

			initPrototypes( mode, prototypeIndexName, rootsVariable, rootsList, prototypes );

			m_ids.initialize( m_primitive.get(), idName );
			if( m_ids.size() && m_ids.size() != numPoints() )
			{
				throw IECore::Exception( fmt::format( "Id primitive variable \"{}\" has incorrect size", idName ) );
			}

			if( const V3fVectorData *p = m_primitive->variableData<V3fVectorData>( position ) )
			{
				m_positions = &p->readable();
				if( m_positions->size() != numPoints() )
				{
					throw IECore::Exception( fmt::format( "Position primitive variable \"{}\" has incorrect size", position ) );
				}
			}

			if( const QuatfVectorData *o = m_primitive->variableData<QuatfVectorData>( orientation ) )
			{
				m_orientations = &o->readable();
				if( m_orientations->size() != numPoints() )
				{
					throw IECore::Exception( fmt::format( "Orientation primitive variable \"{}\" has incorrect size", orientation ) );
				}
			}

			if( const V3fVectorData *s = m_primitive->variableData<V3fVectorData>( scale ) )
			{
				m_scales = &s->readable();
				if( m_scales->size() != numPoints() )
				{
					throw IECore::Exception( fmt::format( "Scale primitive variable \"{}\" has incorrect size", scale ) );
				}
			}
			else if( const FloatVectorData *s = m_primitive->variableData<FloatVectorData>( scale ) )
			{
				m_uniformScales = &s->readable();
				if( m_uniformScales->size() != numPoints() )
				{
					throw IECore::Exception( fmt::format( "Uniform scale primitive variable \"{}\" has incorrect size", scale ) );
				}
			}

			if( m_ids.size() )
			{
				for( size_t i = 0, e = numPoints(); i < e; ++i )
				{
					int64_t id = m_ids.element(i);
					auto ins = m_idsToPointIndices.try_emplace( id, i );
					if( !ins.second )
					{
						// We have multiple indices trying to use this id.
						if( !omitDuplicateIds )
						{
							throw IECore::Exception( fmt::format( "Instance id \"{}\" is duplicated at index {} and {}. This probably indicates invalid source data, if you want to hack around it, you can set \"omitDuplicateIds\".", id, m_idsToPointIndices[id], i ) );
						}

						if( !m_indicesInactive.size() )
						{
							m_indicesInactive.resize( numPoints(), false );
						}

						// If we're omitting duplicate ids, then we need to omit both the current index, and
						// the index that first tried to use this id.
						m_indicesInactive[ i ] = true;
						m_indicesInactive[ ins.first->second ] = true;
					}
				}
			}

			std::vector<std::string> inactiveIdVarNames;
			IECore::StringAlgo::tokenize( inactiveIds, ' ', inactiveIdVarNames );
			for( std::string &inactiveIdVarName : inactiveIdVarNames )
			{
				if( m_primitive->variables.find( inactiveIdVarName ) == m_primitive->variables.end() )
				{
					continue;
				}

				const PrimitiveVariable *vertexInactiveVar = findVertexVariable( m_primitive.get(), inactiveIdVarName );
				if( vertexInactiveVar )
				{
					if( IECore::size( vertexInactiveVar->data.get() ) != numPoints() )
					{
						throw IECore::Exception( fmt::format( "Inactive primitive variable \"{}\" has incorrect size", inactiveIdVarName ) );
					}

					if( const auto *vertexInactiveData = IECore::runTimeCast<BoolVectorData>( vertexInactiveVar->data.get() ) )
					{
						const std::vector<bool> &vertexInactive = vertexInactiveData->readable();

						if( !m_indicesInactive.size() )
						{
							// If we don't already have an inactive array set up, we can just directly copy the data
							// from a vertex primitive variable. Technically, we might not even need to do this copy,
							// if there aren't any other inactive vars we're merging with, we could just have a
							// separate way of storing a const pointer for this case, but given that this data is
							// 32X smaller than any of our other per-vertex data anyway, it's probably fine to pay
							// the cost of copying it in exchange for slightly simpler code.
							m_indicesInactive = vertexInactive;
						}
						else
						{
							for( size_t i = 0; i < vertexInactive.size(); i++ )
							{
								if( vertexInactive[i] )
								{
									m_indicesInactive[ i ] = true;
								}
							}
						}
					}
					else if( const auto *vertexInactiveIntData = IECore::runTimeCast<IntVectorData>( vertexInactiveVar->data.get() ) )
					{
						const std::vector<int> &vertexInactiveInt = vertexInactiveIntData->readable();

						if( !m_indicesInactive.size() )
						{
							m_indicesInactive.resize( numPoints(), false );
						}

						for( size_t i = 0; i < vertexInactiveInt.size(); i++ )
						{
							if( vertexInactiveInt[i] )
							{
								m_indicesInactive[ i ] = true;
							}
						}
					}

					continue;
				}

				IdData idData;
				idData.initialize( m_primitive.get(), inactiveIdVarName );

				size_t idSize = idData.size();
				if( !idSize )
				{
					continue;
				}

				if( !m_indicesInactive.size() )
				{
					m_indicesInactive.resize( numPoints(), false );
				}

				if( m_idsToPointIndices.size() )
				{
					for( size_t i = 0; i < idSize; i++ )
					{
						auto it = m_idsToPointIndices.find( idData.element(i) );
						if( it == m_idsToPointIndices.end() )
						{
							// I wish I could throw here ... it would be a really helpful clue to get an error
							// if you've accidentally chosen a bad id. But ids might be changing over time, so
							// we probably need to allow someone to deactivate an id even if it doesn't exist
							// on all frames.
							continue;
						}
						m_indicesInactive[ it->second ] = true;
					}
				}
				else
				{
					for( size_t i = 0; i < idSize; i++ )
					{
						int64_t id = idData.element(i);
						if( id < 0 || id >= (int64_t)m_indicesInactive.size() )
						{
							continue;
						}
						m_indicesInactive[ id ] = true;
					}
				}
			}

			initAttributes( attributes, attributePrefix );

			for( const auto &v : m_prototypeContextVariables )
			{
				// We need to check if the primVars driving the context are the right size.
				// There's not an easy way to do this on PrimitiveVariable without knowing the type,
				// but we can check that it is valid for the primitive, and that the primitive size for that
				// variable is correct
				if( v.primVar && !(
					m_primitive->isPrimitiveVariableValid( *v.primVar ) &&
					m_primitive->variableSize( v.primVar->interpolation ) == numPoints()
				) )
				{
					throw IECore::Exception( fmt::format( "Context primitive variable for \"{}\" is not a correctly sized Vertex primitive variable", v.name.string() ) );
				}
			}
		}

		size_t numPoints() const
		{
			return m_primitive ? m_primitive->variableSize( PrimitiveVariable::Vertex ) : 0;
		}

		int64_t instanceId( size_t pointIndex ) const
		{
			return m_ids.size() ? m_ids.element( pointIndex ) : pointIndex;
		}

		size_t pointIndex( int64_t i ) const
		{
			if( !m_ids.size() )
			{
				if( i >= (int64_t)numPoints() || i < 0 )
				{
					throw IECore::Exception( fmt::format( "Instance id \"{}\" is invalid, instancer produces only {} children. Topology may have changed during shutter.", i, numPoints() ) );
				}
				return i;
			}

			IdsToPointIndices::const_iterator it = m_idsToPointIndices.find( i );
			if( it == m_idsToPointIndices.end() )
			{
				throw IECore::Exception( fmt::format( "Instance id \"{}\" is invalid. Topology may have changed during shutter.", i ) );
			}

			return it->second;
		}

		size_t pointIndex( const InternedString &name ) const
		{
			return pointIndex( boost::lexical_cast<size_t>( name ) );
		}

		size_t numValidPrototypes() const
		{
			return m_numValidPrototypes;
		}

		int prototypeIndex( size_t pointIndex ) const
		{
			if( m_numPrototypes == 0 )
			{
				return -1;
			}

			if( m_indicesInactive.size() )
			{
				// If this point is tagged as inactive ( could be due to a user specified inactiveIds,
				// or due to an id collision when omitDuplicateIds is set ), then we return -1 for
				// the prototype, which means to omit this point.
				if( m_indicesInactive[pointIndex] )
				{
					return -1;
				}
			}

			if( m_prototypeIndices )
			{
				return m_prototypeIndexRemap[ (*m_prototypeIndices)[pointIndex] % m_numPrototypes ];
			}
			else
			{
				return m_prototypeIndexRemap[ 0 ];
			}
		}

		// Return a pointer since this is for internal use only, and it helps communicate that we
		// are responsible for holding the storage for this scene path when it gets put in the context
		const ScenePlug::ScenePath *prototypeRoot( const InternedString &name ) const
		{
			return &( m_roots[m_names->input( name ).index]->readable() );
		}

		const ScenePlug::ScenePath *prototypeRoot( int prototypeId ) const
		{
			return &( m_roots[prototypeId]->readable() );
		}

		const InternedStringVectorData *prototypeNames() const
		{
			return m_names ? m_names->outputChildNames() : g_emptyNames.get();
		}

		M44f instanceTransform( size_t pointIndex ) const
		{
			M44f result;
			if( m_positions )
			{
				result.translate( (*m_positions)[pointIndex] );
			}
			if( m_orientations )
			{
				// Using Orientation::normalizedIfNeeded avoids modifying quaternions that are already
				// normalized. It's better for consistency to not be pointlessly changing the values
				// slightly at the limits of floating point precision, when they're already as close to
				// normalized as they can get, and this saves 4% runtime on InstancerTest.testBoundPerformance.
				result = Orientation::normalizedIfNeeded((*m_orientations)[pointIndex]).toMatrix44() * result;
			}
			if( m_scales )
			{
				result.scale( (*m_scales)[pointIndex] );
			}
			if( m_uniformScales )
			{
				result.scale( V3f( (*m_uniformScales)[pointIndex] ) );
			}
			return result;
		}

		size_t numInstanceAttributes() const
		{
			return m_attributeCreators.size();
		}

		void instanceAttributesHash( size_t pointIndex, MurmurHash &h ) const
		{
			h.append( m_attributesHash );
			h.append( (uint64_t)pointIndex );
		}

		void instanceAttributes( size_t pointIndex, CompoundObject &result ) const
		{
			CompoundObject::ObjectMap &writableResult = result.members();
			for( const auto &attributeCreator : m_attributeCreators )
			{
				writableResult[attributeCreator.first] = attributeCreator.second( pointIndex );
			}
		}

		using PrototypeHashes = std::map<InternedString, boost::unordered_set<IECore::MurmurHash>>;

		// In order to compute the number of variations, we compute a unique hash for every context we use
		// for evaluating prototypes.  So that we can track which sources are responsible for variations,
		// we return a map of hash sets, with a set of hashes for each variable name in
		// m_prototypeContextVariables, plus an extra entry for "" for the combined result of all variation
		// sources
		std::unique_ptr<PrototypeHashes> uniquePrototypeHashes() const
		{
			std::vector< boost::unordered_set< IECore::MurmurHash > > variableHashAccumulate( m_prototypeContextVariables.size() );
			boost::unordered_set< IECore::MurmurHash > totalHashAccumulate;

			size_t n = numPoints();
			for( size_t i = 0; i < n; i++ )
			{
				int protoIndex = prototypeIndex( i );
				if( protoIndex == -1 )
				{
					continue;
				}

				IECore::MurmurHash totalHash;
				const InternedStringVectorData &rootPath = *m_roots[ protoIndex ];

				// Note that we are rehashing the root path for every point, even though they are heavily
				// reused.  This seems suboptimal, but is simpler, and the more complex version doesn't
				// appear to make any performance difference in practice
				totalHash.append( &(rootPath.readable())[0], rootPath.readable().size() );
				for( unsigned int j = 0; j < m_prototypeContextVariables.size(); j++ )
				{
					IECore::MurmurHash r; // TODO - if we're using this in inner loops, the constructor should probably be inlined?
					hashPrototypeContextVariable( i, m_prototypeContextVariables[j], r );
					variableHashAccumulate[j].insert( r );
					totalHash.append( r );
				}
				totalHashAccumulate.insert( totalHash );
			}

			auto result = std::make_unique<PrototypeHashes>();
			for( unsigned int j = 0; j < m_prototypeContextVariables.size(); j++ )
			{
				(*result)[ m_prototypeContextVariables[j].name ] = variableHashAccumulate[j];
			}
			(*result)[ "" ] = totalHashAccumulate;

			return result;
		}

		bool hasContextVariables() const
		{
			return m_prototypeContextVariables.size() != 0;
		}

		// Set the context variables in the context for this point index, based on the m_prototypeContextVariables
		// set up for this EngineData
		void setPrototypeContextVariables( size_t pointIndex, Context::EditableScope &scope ) const
		{
			for( unsigned int i = 0; i < m_prototypeContextVariables.size(); i++ )
			{
				const PrototypeContextVariable &v = m_prototypeContextVariables[i];

				if( v.seedMode )
				{
					scope.setAllocated( v.name, seedForPoint( pointIndex, m_ids, v.numSeeds, v.seedScramble ) );
					continue;
				}

				if( !v.primVar )
				{
					continue;
				}

				try
				{
					IECore::dispatch( v.primVar->data.get(), AccessPrototypeContextVariable(), v, pointIndex, scope );
				}
				catch( QuantizeException & )
				{
					throw IECore::Exception( fmt::format( "Context variable \"{}\" : cannot quantize variable of type {}", v.name.string(), v.primVar->data->typeName() ) );
				}
			}
		}

	protected :

		// Needs to match setPrototypeContextVariables above, except that it operates on one
		// PrototypeContextVariable at a time instead of iterating through them
		void hashPrototypeContextVariable( size_t pointIndex, const PrototypeContextVariable &v, IECore::MurmurHash &result ) const
		{
			if( v.seedMode )
			{
				result.append( seedForPoint( pointIndex, m_ids, v.numSeeds, v.seedScramble ) );
				return;
			}

			if( !v.primVar )
			{
				return;
			}

			try
			{
				IECore::dispatch( v.primVar->data.get(), UniqueHashPrototypeContextVariable(), v, pointIndex, result );
			}
			catch( QuantizeException & )
			{
				throw IECore::Exception( fmt::format( "Context variable \"{}\" : cannot quantize variable of type {}", v.name.string(), v.primVar->data->typeName() ) );
			}
		}

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

		using AttributeCreator = std::function<DataPtr ( size_t )>;

		struct MakeAttributeCreator
		{

			template<typename T>
			AttributeCreator operator()( const TypedData<vector<T>> *data )
			{
				return std::bind( &createAttribute<T>, data->readable(), std::placeholders::_1 );
			}

			template<typename T>
			AttributeCreator operator()( const GeometricTypedData<vector<T>> *data )
			{
				return std::bind( &createGeometricAttribute<T>, data->readable(), data->getInterpretation(), std::placeholders::_1 );
			}

			AttributeCreator operator()( const Data *data )
			{
				throw IECore::InvalidArgumentException( "Expected VectorTypedData" );
			}

			private :

				template<typename T>
				static DataPtr createAttribute( const vector<T> &values, size_t index )
				{
					return new TypedData<T>( values[index] );
				}

				template<typename T>
				static DataPtr createGeometricAttribute( const vector<T> &values, GeometricData::Interpretation interpretation, size_t index )
				{
					return new GeometricTypedData<T>( values[index], interpretation );
				}

		};

		void initAttributes( const std::string &attributes, const std::string &attributePrefix )
		{
			m_attributesHash.append( attributePrefix );

			for( auto &primVar : m_primitive->variables )
			{
				if( !(
					primVar.second.interpolation == PrimitiveVariable::Vertex ||
					(
						primVar.second.interpolation == PrimitiveVariable::Varying &&
						m_primitive->variableSize( PrimitiveVariable::Vertex ) == m_primitive->variableSize( PrimitiveVariable::Varying )
					)
				) )
				{
					continue;
				}
				if( !StringAlgo::matchMultiple( primVar.first, attributes ) )
				{
					continue;
				}
				DataPtr d = primVar.second.expandedData();
				AttributeCreator attributeCreator = dispatch( d.get(), MakeAttributeCreator() );
				m_attributeCreators[attributePrefix + primVar.first] = attributeCreator;
				m_attributesHash.append( primVar.first );
				d->hash( m_attributesHash );
			}
		}

		void initPrototypes( PrototypeMode mode, const std::string &prototypeIndex, const std::string &rootsVariable, const StringVectorData *rootsList, const ScenePlug *prototypes )
		{
			const std::vector<std::string> *rootStrings = nullptr;
			std::vector<std::string> rootStringsAlloc;

			switch( mode )
			{
				case PrototypeMode::IndexedRootsList :
				{
					if( const auto *prototypeIndices = m_primitive->variableData<IntVectorData>( prototypeIndex ) )
					{
						m_prototypeIndices = &prototypeIndices->readable();
						if( m_prototypeIndices->size() != numPoints() )
						{
							throw IECore::Exception( fmt::format( "prototypeIndex primitive variable \"{}\" has incorrect size", prototypeIndex ) );
						}
					}

					rootStrings = &rootsList->readable();

					break;
				}
				case PrototypeMode::IndexedRootsVariable :
				{
					if( const auto *prototypeIndices = m_primitive->variableData<IntVectorData>( prototypeIndex ) )
					{
						m_prototypeIndices = &prototypeIndices->readable();
						if( m_prototypeIndices->size() != numPoints() )
						{
							throw IECore::Exception( fmt::format( "prototypeIndex primitive variable \"{}\" has incorrect size", prototypeIndex ) );
						}
					}

					const auto *roots = m_primitive->variableData<StringVectorData>( rootsVariable, PrimitiveVariable::Constant );
					if( !roots )
					{
						std::string message = fmt::format( "prototypeRoots primitive variable \"{}\" must be Constant StringVectorData when using IndexedRootsVariable mode", rootsVariable );
						if( m_primitive->variables.find( rootsVariable ) == m_primitive->variables.end() )
						{
							message += ", but it does not exist";
						}
						throw IECore::Exception( message );
					}

					rootStrings = &roots->readable();
					if( rootStrings->empty() )
					{
						throw IECore::Exception( fmt::format( "prototypeRoots primitive variable \"{}\" must specify at least one root location", rootsVariable ) );
					}

					break;
				}
				case PrototypeMode::RootPerVertex :
				{
					auto view = m_primitive->variableIndexedView<StringVectorData>( rootsVariable, PrimitiveVariable::Vertex );
					if( !view && m_primitive->variableSize( PrimitiveVariable::Vertex ) == m_primitive->variableSize( PrimitiveVariable::Varying ))
					{
						view = m_primitive->variableIndexedView<StringVectorData>( rootsVariable, PrimitiveVariable::Varying );
					}

					if( !view )
					{
						std::string message = fmt::format( "prototypeRoots primitive variable \"{}\" must be Vertex StringVectorData when using RootPerVertex mode", rootsVariable );
						if( m_primitive->variables.find( rootsVariable ) == m_primitive->variables.end() )
						{
							message += ", but it does not exist";
						}
						throw IECore::Exception( message );
					}

					m_prototypeIndices = view->indices();
					rootStrings = &view->data();

					if( !m_prototypeIndices )
					{
						std::unordered_map<std::string, int> duplicateRootMap;

						m_prototypeIndicesAlloc.reserve( rootStrings->size() );
						for( const std::string &i : *rootStrings )
						{
							auto insertResult = duplicateRootMap.try_emplace( i, rootStringsAlloc.size() );
							if( insertResult.second )
							{
								m_prototypeIndicesAlloc.push_back( rootStringsAlloc.size() );
								rootStringsAlloc.push_back( i );
							}
							else
							{
								m_prototypeIndicesAlloc.push_back( insertResult.first->second );
							}
						}
						rootStrings = &rootStringsAlloc;
						m_prototypeIndices = &m_prototypeIndicesAlloc;
					}
					break;
				}
			}

			std::vector<ConstInternedStringVectorDataPtr> inputNames;
			inputNames.reserve( rootStrings->size() );
			m_roots.reserve( rootStrings->size() );
			m_prototypeIndexRemap.reserve( rootStrings->size() );

			size_t i = 0;
			ScenePlug::ScenePath path;
			for( const auto &root : *rootStrings )
			{
				ScenePlug::stringToPath( root, path );
				if( !prototypes->exists( path ) )
				{
					throw IECore::Exception( fmt::format( "Prototype root \"{}\" does not exist in the `prototypes` scene", root ) );
				}

				if( path.empty() )
				{
					if( root == "/" )
					{
						inputNames.emplace_back( new InternedStringVectorData( { g_prototypeRootName } ) );
						m_roots.emplace_back( new InternedStringVectorData( path ) );
						m_prototypeIndexRemap.emplace_back( i++ );
					}
					else
					{
						m_prototypeIndexRemap.emplace_back( -1 );
					}
				}
				else
				{
					inputNames.emplace_back( new InternedStringVectorData( { path.back() } ) );
					m_roots.emplace_back( new InternedStringVectorData( path ) );
					m_prototypeIndexRemap.emplace_back( i++ );
				}
			}

			m_names = new Private::ChildNamesMap( inputNames );

			const std::vector< InternedString > outputChildNames = m_names->outputChildNames()->readable();
			m_numPrototypes = m_prototypeIndexRemap.size();
			m_numValidPrototypes = outputChildNames.size();

		}

		IECoreScene::ConstPrimitivePtr m_primitive;
		size_t m_numPrototypes;
		size_t m_numValidPrototypes;
		Private::ChildNamesMapPtr m_names;
		std::vector<ConstInternedStringVectorDataPtr> m_roots;
		std::vector<int> m_prototypeIndexRemap;
		std::vector<int> m_prototypeIndicesAlloc;
		const std::vector<int> *m_prototypeIndices;
		IdData m_ids;
		const std::vector<Imath::V3f> *m_positions;
		const std::vector<Imath::Quatf> *m_orientations;
		const std::vector<Imath::V3f> *m_scales;
		const std::vector<float> *m_uniformScales;

		using IdsToPointIndices = std::unordered_map <int64_t, size_t>;
		IdsToPointIndices m_idsToPointIndices;

		boost::container::flat_map<InternedString, AttributeCreator> m_attributeCreators;
		MurmurHash m_attributesHash;

		const std::vector< PrototypeContextVariable > m_prototypeContextVariables;

		std::vector<bool> m_indicesInactive;

		friend Instancer::EngineSplitPrototypesData;
};

// If we aren't encapsulating, we need to split the prototypes into groups, requiring us to do extra work
class Instancer::EngineSplitPrototypesData : public Data
{

	public :

		EngineSplitPrototypesData(
			ConstEngineDataPtr engineData
		)
			:	m_engineData( engineData )
		{

			if( !m_engineData->m_numValidPrototypes )
			{
				// We don't need to build m_pointIndicesForPrototype if we're not outputting any prototypes.
				return;
			}

			int constantPrototypeIndex = -1;
			if( !m_engineData->m_prototypeIndices )
			{
				constantPrototypeIndex = m_engineData->m_prototypeIndexRemap[ 0 ];
				if( constantPrototypeIndex == -1 )
				{
					// If we have no indices to specify other prototypes, and the first prototype is
					// invalid, we're not going to output anything, and can early exit
					return;
				}
			}

			// We need a list of which point indices belong to each prototype
			std::vector< std::vector<size_t> > pointIndicesForPrototypeIndex( m_engineData->m_numPrototypes );
			// Pre allocate if there's just one prototype, since we know the length will just be every point
			if( constantPrototypeIndex != -1 )
			{
				pointIndicesForPrototypeIndex[ constantPrototypeIndex ].reserve( m_engineData->numPoints() );
			}

			if( constantPrototypeIndex != -1 && !m_engineData->m_indicesInactive.size() )
			{
				// If there's a single prototype, and no indices are being omitted because they are duplicates,
				// then the list of point indices for the prototype is just an identity map of all integers
				// from 0 .. N - 1.
				//
				// It's pretty wasteful to store this, but it avoids special cases throughout this code to skip
				// using pointIndicesForPrototypeIndex when it isn't needed
				for( size_t i = 0, e = m_engineData->numPoints(); i < e; ++i )
				{
					pointIndicesForPrototypeIndex[ constantPrototypeIndex ].push_back( i );
				}
			}
			else
			{
				// The assignment of point indices to prototypes is non-trivial, so we actually have to do
				// a bit of work
				for( size_t i = 0, e = m_engineData->numPoints(); i < e; ++i )
				{
					// Add this point index to the list for its prototype
					int protoIndex = m_engineData->prototypeIndex( i );

					if( protoIndex != -1 )
					{
						pointIndicesForPrototypeIndex[ protoIndex ].push_back( i );
					}
				}
			}

			// We've populated instancerPrototypeIndex with a list of point indices for each prototype index.
			// When we need this, however, we need it indexed by name, so we move the vectors we've just built
			// to m_pointIndicesForPrototype which is indexed by name.
			const std::vector< InternedString > &outputChildNames = m_engineData->m_names->outputChildNames()->readable();
			for( unsigned int i = 0; i < m_engineData->m_numPrototypes; i++ )
			{
				int prototypeIndex = m_engineData->m_prototypeIndexRemap[ i ];
				if( prototypeIndex == -1 )
				{
					continue;
				}

				m_pointIndicesForPrototype.emplace( IECore::InternedString( outputChildNames[prototypeIndex] ), std::move( pointIndicesForPrototypeIndex[prototypeIndex] ) );
			}
		}

		const EngineData *engine() const
		{
			return m_engineData.get();
		}

		const std::vector<size_t> & pointIndicesForPrototype( const IECore::InternedString &prototypeName ) const
		{
			return m_pointIndicesForPrototype.at( prototypeName );
		}


	protected :

		ConstEngineDataPtr m_engineData;
		std::unordered_map< InternedString, std::vector<size_t> > m_pointIndicesForPrototype;
};


//////////////////////////////////////////////////////////////////////////
// InstancerCapsule
//////////////////////////////////////////////////////////////////////////

// We can achieve better performance using a special capsule that understands EngineData instead of
// using a generic Capsule that only understands generic ScenePlugs
class Instancer::InstancerCapsule : public Capsule
{

	public :

		InstancerCapsule()
			: m_instancer( nullptr )
		{
		}

		InstancerCapsule(
			const Instancer *instancer,
			const ScenePlug::ScenePath &root,
			const Gaffer::Context &context,
			const IECore::MurmurHash &hash,
			const Imath::Box3f &bound
		)
			: Capsule( instancer->capsuleScenePlug(), root, context, hash, bound ),
				m_instancer( instancer )
		{
		}

		~InstancerCapsule() override
		{
		}

		IE_CORE_DECLAREEXTENSIONOBJECT( InstancerCapsule, GafferScene::InstancerCapsuleTypeId, GafferScene::Capsule );

		// Defined at the bottom of this file, where it makes more sense
		void render( IECoreScenePreview::Renderer *renderer ) const override;

	private :

		const Instancer *m_instancer;
};

IE_CORE_DEFINEOBJECTTYPEDESCRIPTION( Instancer::InstancerCapsule );

bool Instancer::InstancerCapsule::isEqualTo( const IECore::Object *other ) const
{
	return Capsule::isEqualTo( other );
}

void Instancer::InstancerCapsule::hash( IECore::MurmurHash &h ) const
{
	Capsule::hash( h );
}

void Instancer::InstancerCapsule::copyFrom( const IECore::Object *other, IECore::Object::CopyContext *context )
{
	Capsule::copyFrom( other, context );

	const InstancerCapsule *instancerCapsule = static_cast<const InstancerCapsule *>( other );

	m_instancer = instancerCapsule->m_instancer;
}

void Instancer::InstancerCapsule::save( IECore::Object::SaveContext *context ) const
{
	// Parent class just takes care of printing warning about not being supported
	Capsule::save( context );
}

void Instancer::InstancerCapsule::load( IECore::Object::LoadContextPtr context )
{
	// Parent class just takes care of printing warning about not being supported
	Capsule::load( context );
}

void Instancer::InstancerCapsule::memoryUsage( IECore::Object::MemoryAccumulator &accumulator ) const
{
	Capsule::memoryUsage( accumulator );

	// The size of the base class is already included, so no need to duplicate that
	accumulator.accumulate( sizeof( InstancerCapsule ) - sizeof( Capsule ) );

}

// Implementation of InstancerCapsule::render()
// is defined at the bottom of this file, where it makes more sense


//////////////////////////////////////////////////////////////////////////
// Instancer
//////////////////////////////////////////////////////////////////////////

GAFFER_PLUG_DEFINE_TYPE( Instancer::ContextVariablePlug );

Instancer::ContextVariablePlug::ContextVariablePlug( const std::string &name, Direction direction, bool defaultEnable, unsigned flags )
	: ValuePlug( name, direction, flags )
{
	addChild( new BoolPlug( "enabled", direction, defaultEnable ) );
	addChild( new StringPlug( "name", direction, "" ) );
	addChild( new FloatPlug( "quantize", direction, 0.1, 0 ) );
}

Instancer::ContextVariablePlug::~ContextVariablePlug()
{
}

bool Instancer::ContextVariablePlug::acceptsChild( const GraphComponent *potentialChild ) const
{
	return children().size() < 3;
}

Gaffer::PlugPtr Instancer::ContextVariablePlug::createCounterpart( const std::string &name, Direction direction ) const
{
	return new Instancer::ContextVariablePlug( name, direction, enabledPlug()->defaultValue(), getFlags() );
}

Gaffer::BoolPlug *Instancer::ContextVariablePlug::enabledPlug()
{
	return getChild<BoolPlug>( 0 );
}

const Gaffer::BoolPlug *Instancer::ContextVariablePlug::enabledPlug() const
{
	return getChild<BoolPlug>( 0 );
}

Gaffer::StringPlug *Instancer::ContextVariablePlug::namePlug()
{
	return getChild<StringPlug>( 1 );
}

const Gaffer::StringPlug *Instancer::ContextVariablePlug::namePlug() const
{
	return getChild<StringPlug>( 1 );
}

Gaffer::FloatPlug *Instancer::ContextVariablePlug::quantizePlug()
{
	return getChild<FloatPlug>( 2 );
}

const Gaffer::FloatPlug *Instancer::ContextVariablePlug::quantizePlug() const
{
	return getChild<FloatPlug>( 2 );
}

GAFFER_NODE_DEFINE_TYPE( Instancer );

size_t Instancer::g_firstPlugIndex = 0;

Instancer::Instancer( const std::string &name )
	:	BranchCreator( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "name", Plug::In, "instances" ) );
	addChild( new ScenePlug( "prototypes" ) );
	addChild( new IntPlug( "prototypeMode", Plug::In, (int)PrototypeMode::IndexedRootsList, /* min */ (int)PrototypeMode::IndexedRootsList, /* max */ (int)PrototypeMode::RootPerVertex ) );
	addChild( new StringPlug( "prototypeIndex", Plug::In, "instanceIndex" ) );
	addChild( new StringPlug( "prototypeRoots", Plug::In, "prototypeRoots" ) );
	addChild( new StringVectorDataPlug( "prototypeRootsList", Plug::In, new StringVectorData ) );
	addChild( new StringPlug( "id", Plug::In, "instanceId" ) );
	addChild( new BoolPlug( "omitDuplicateIds", Plug::In, true ) );
	addChild( new StringPlug( "position", Plug::In, "P" ) );
	addChild( new StringPlug( "orientation", Plug::In ) );
	addChild( new StringPlug( "scale", Plug::In ) );
	addChild( new StringPlug( "inactiveIds", Plug::In, "" ) );
	addChild( new StringPlug( "attributes", Plug::In ) );
	addChild( new StringPlug( "attributePrefix", Plug::In ) );
	addChild( new BoolPlug( "encapsulate", Plug::In ) );
	addChild( new BoolPlug( "seedEnabled", Plug::In ) );
	addChild( new StringPlug( "seedVariable", Plug::In, "seed" ) );
	addChild( new IntPlug( "seeds", Plug::In, 10, 1 ) );
	addChild( new IntPlug( "seedPermutation", Plug::In ) );
	addChild( new BoolPlug( "rawSeed", Plug::In ) );
	addChild( new ValuePlug( "contextVariables", Plug::In ) );
	addChild( new ContextVariablePlug( "timeOffset", Plug::In, false, Plug::Flags::Default ) );
	addChild( new AtomicCompoundDataPlug( "variations", Plug::Out, new CompoundData() ) );
	addChild( new ObjectPlug( "__engine", Plug::Out, NullObject::defaultNullObject() ) );
	addChild( new ObjectPlug( "__engineSplitPrototypes", Plug::Out, NullObject::defaultNullObject() ) );
	addChild( new ScenePlug( "__capsuleScene", Plug::Out ) );
	addChild( new PathMatcherDataPlug( "__setCollaborate", Plug::Out, new IECore::PathMatcherData() ) );

	// Hide `destination` plug until we resolve issues surrounding `processesRootObject()`.
	// See `BranchCreator::computeObject()`.
	destinationPlug()->setName( "__destination" );

	capsuleScenePlug()->boundPlug()->setInput( outPlug()->boundPlug() );
	capsuleScenePlug()->transformPlug()->setInput( outPlug()->transformPlug() );
	capsuleScenePlug()->attributesPlug()->setInput( outPlug()->attributesPlug() );
	capsuleScenePlug()->setNamesPlug()->setInput( outPlug()->setNamesPlug() );
	capsuleScenePlug()->globalsPlug()->setInput( outPlug()->globalsPlug() );

	prototypesPlug()->setFlags( Plug::AcceptsDependencyCycles, true );
	for( Gaffer::Plug::RecursiveIterator it( prototypesPlug() ); !it.done(); ++it )
	{
		(*it)->setFlags( Plug::AcceptsDependencyCycles, true );
	}
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

ScenePlug *Instancer::prototypesPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex + 1 );
}

const ScenePlug *Instancer::prototypesPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex + 1 );
}

Gaffer::IntPlug *Instancer::prototypeModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::IntPlug *Instancer::prototypeModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *Instancer::prototypeIndexPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *Instancer::prototypeIndexPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::StringPlug *Instancer::prototypeRootsPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::StringPlug *Instancer::prototypeRootsPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

Gaffer::StringVectorDataPlug *Instancer::prototypeRootsListPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::StringVectorDataPlug *Instancer::prototypeRootsListPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 5 );
}

Gaffer::StringPlug *Instancer::idPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::StringPlug *Instancer::idPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 6 );
}

Gaffer::BoolPlug *Instancer::omitDuplicateIdsPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 7 );
}

const Gaffer::BoolPlug *Instancer::omitDuplicateIdsPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 7 );
}

Gaffer::StringPlug *Instancer::positionPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 8 );
}

const Gaffer::StringPlug *Instancer::positionPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 8 );
}

Gaffer::StringPlug *Instancer::orientationPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 9 );
}

const Gaffer::StringPlug *Instancer::orientationPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 9 );
}

Gaffer::StringPlug *Instancer::scalePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 10 );
}

const Gaffer::StringPlug *Instancer::scalePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 10 );
}

Gaffer::StringPlug *Instancer::inactiveIdsPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 11 );
}

const Gaffer::StringPlug *Instancer::inactiveIdsPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 11 );
}

Gaffer::StringPlug *Instancer::attributesPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 12 );
}

const Gaffer::StringPlug *Instancer::attributesPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 12 );
}

Gaffer::StringPlug *Instancer::attributePrefixPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 13 );
}

const Gaffer::StringPlug *Instancer::attributePrefixPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 13 );
}

Gaffer::BoolPlug *Instancer::encapsulatePlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 14 );
}

const Gaffer::BoolPlug *Instancer::encapsulatePlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 14 );
}

Gaffer::BoolPlug *Instancer::seedEnabledPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 15 );
}

const Gaffer::BoolPlug *Instancer::seedEnabledPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 15 );
}

Gaffer::StringPlug *Instancer::seedVariablePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 16 );
}

const Gaffer::StringPlug *Instancer::seedVariablePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 16 );
}

Gaffer::IntPlug *Instancer::seedsPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 17 );
}

const Gaffer::IntPlug *Instancer::seedsPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 17 );
}

Gaffer::IntPlug *Instancer::seedPermutationPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 18 );
}

const Gaffer::IntPlug *Instancer::seedPermutationPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 18 );
}

Gaffer::BoolPlug *Instancer::rawSeedPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 19 );
}

const Gaffer::BoolPlug *Instancer::rawSeedPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 19 );
}

Gaffer::ValuePlug *Instancer::contextVariablesPlug()
{
	return getChild<ValuePlug>( g_firstPlugIndex + 20 );
}

const Gaffer::ValuePlug *Instancer::contextVariablesPlug() const
{
	return getChild<ValuePlug>( g_firstPlugIndex + 20 );
}

GafferScene::Instancer::ContextVariablePlug *Instancer::timeOffsetPlug()
{
	return getChild<ContextVariablePlug>( g_firstPlugIndex + 21 );
}

const GafferScene::Instancer::ContextVariablePlug *Instancer::timeOffsetPlug() const
{
	return getChild<ContextVariablePlug>( g_firstPlugIndex + 21 );
}

Gaffer::AtomicCompoundDataPlug *Instancer::variationsPlug()
{
	return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex + 22 );
}

const Gaffer::AtomicCompoundDataPlug *Instancer::variationsPlug() const
{
	return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex + 22 );
}

Gaffer::ObjectPlug *Instancer::enginePlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 23 );
}

const Gaffer::ObjectPlug *Instancer::enginePlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 23 );
}

Gaffer::ObjectPlug *Instancer::engineSplitPrototypesPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 24 );
}

const Gaffer::ObjectPlug *Instancer::engineSplitPrototypesPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 24 );
}

GafferScene::ScenePlug *Instancer::capsuleScenePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex + 25 );
}

const GafferScene::ScenePlug *Instancer::capsuleScenePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex + 25 );
}

Gaffer::PathMatcherDataPlug *Instancer::setCollaboratePlug()
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 26 );
}

const Gaffer::PathMatcherDataPlug *Instancer::setCollaboratePlug() const
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 26 );
}

void Instancer::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	BranchCreator::affects( input, outputs );

	if(
		input == inPlug()->objectPlug() ||
		input == prototypeModePlug() ||
		input == prototypeIndexPlug() ||
		input == prototypeRootsPlug() ||
		input == prototypeRootsListPlug() ||
		input == prototypesPlug()->childNamesPlug() ||
		input == prototypesPlug()->existsPlug() ||
		input == idPlug() ||
		input == omitDuplicateIdsPlug() ||
		input == positionPlug() ||
		input == orientationPlug() ||
		input == scalePlug() ||
		input == inactiveIdsPlug() ||
		input == attributesPlug() ||
		input == attributePrefixPlug() ||
		input == seedEnabledPlug() ||
		input == seedVariablePlug() ||
		input == seedsPlug() ||
		input == seedPermutationPlug() ||
		input == rawSeedPlug() ||
		timeOffsetPlug()->isAncestorOf( input ) ||
		contextVariablesPlug()->isAncestorOf( input )
	)
	{
		outputs.push_back( enginePlug() );
	}

	if(
		input == enginePlug()
	)
	{
		outputs.push_back( engineSplitPrototypesPlug() );
	}

	// For the affects of our output plug, we can mostly rely on BranchCreator's mechanism driven
	// by affectsBranchObject etc., but for these 3 plugs, we have an overridden hash/compute
	// which in addition to everything that BranchCreator handles, are also affected by
	// encapsulatePlug()
	if( input == encapsulatePlug() )
	{
		outputs.push_back( outPlug()->objectPlug() );
		outputs.push_back( outPlug()->childNamesPlug() );
		outputs.push_back( outPlug()->setPlug() );
	}

	if(
		input->parent() == prototypesPlug() &&
		input != prototypesPlug()->globalsPlug() &&
		!encapsulatePlug()->isSetToDefault()
	)
	{
		outputs.push_back( outPlug()->objectPlug() );
	}

	// The capsule scene depends on all the same things as the regular output scene ( aside from not
	// being affected by the encapsulate plug, which always must be true when it's evaluated anyway ),
	// so we can leverage the logic in BranchCreator to drive it
	if( input == outPlug()->objectPlug() )
	{
		outputs.push_back( capsuleScenePlug()->objectPlug() );
	}
	if( input == outPlug()->childNamesPlug() )
	{
		outputs.push_back( capsuleScenePlug()->childNamesPlug() );
	}
	if( input == outPlug()->setPlug() )
	{
		outputs.push_back( capsuleScenePlug()->setPlug() );
	}

	if(
		input == enginePlug() ||
		input == filterPlug() ||
		input == inPlug()->childNamesPlug()
	)
	{
		outputs.push_back( variationsPlug() );
	}

	if(
		input == engineSplitPrototypesPlug() ||
		input == prototypesPlug()->setPlug() ||
		input == namePlug()
	)
	{
		outputs.push_back( setCollaboratePlug() );
	}
}

void Instancer::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	BranchCreator::hash( output, context, h );

	if( output == enginePlug() )
	{
		inPlug()->objectPlug()->hash( h );

		prototypeModePlug()->hash( h );
		prototypeIndexPlug()->hash( h );
		prototypeRootsPlug()->hash( h );
		prototypeRootsListPlug()->hash( h );
		h.append( prototypesPlug()->childNamesHash( ScenePath() ) );

		idPlug()->hash( h );
		omitDuplicateIdsPlug()->hash( h );
		positionPlug()->hash( h );
		orientationPlug()->hash( h );
		scalePlug()->hash( h );
		inactiveIdsPlug()->hash( h );
		attributesPlug()->hash( h );
		attributePrefixPlug()->hash( h );
		encapsulatePlug()->hash( h );

		seedEnabledPlug()->hash( h );
		seedVariablePlug()->hash( h );
		seedsPlug()->hash( h );
		seedPermutationPlug()->hash( h );
		rawSeedPlug()->hash( h );

		for( ContextVariablePlug::Iterator it( contextVariablesPlug() ); !it.done(); ++it )
		{
			const ContextVariablePlug *plug = it->get();
			if( plug->enabledPlug()->getValue() )
			{
				plug->namePlug()->hash( h );
				plug->quantizePlug()->hash( h );
			}
		}

		if( timeOffsetPlug()->enabledPlug()->getValue() )
		{
			timeOffsetPlug()->namePlug()->hash( h );
			timeOffsetPlug()->quantizePlug()->hash( h );
		}
	}
	else if( output == engineSplitPrototypesPlug() )
	{
		enginePlug()->hash( h );
	}
	else if( output == variationsPlug() )
	{
		// The sum of the variations across different engines depends on all the engines, but
		// not their order.  We can create a cheap order-independent hash by summing the hashes
		// all of the engines
		std::atomic<uint64_t> h1Accum( 0 ), h2Accum( 0 );
		auto functor =[this, &h1Accum, &h2Accum]( const GafferScene::ScenePlug *scene, const GafferScene::ScenePlug::ScenePath &path )
		{
			IECore::MurmurHash h = enginePlug()->hash();
			h1Accum += h.h1();
			h2Accum += h.h2();
			return true;
		};
		GafferScene::SceneAlgo::filteredParallelTraverse( inPlug(), filterPlug(), functor );
		h.append( IECore::MurmurHash( h1Accum, h2Accum ) );
	}
	else if( output == setCollaboratePlug() )
	{
		const ScenePath &sourcePath = context->get<ScenePath>( ScenePlug::scenePathContextName );

		ConstEngineSplitPrototypesDataPtr esp = this->engineSplitPrototypes( sourcePath, context );
		const EngineData *engine = esp->engine();

		if( !engine->hasContextVariables() )
		{
			// We use a slightly approximate version of hasContextVariables in hashBranchSet, to
			// avoid computing engine before necessary.  If it turns out that all the context variables
			// requested were actually invalid, then we can use the same fast approximate hash used in
			// hashBranchSet.
			//
			// This is a little bit weird, because in this scenario, this plug will never be computed :
			// computeBranchSet checks the accurate hasContextVariables before evaluating setCollaboratePlug.
			// But hashBranchSet is evaluating us, so we have to give a hash that will work for it.
			//
			// We could always hash this stuff in hashBranchSet, but we would lose out a benefit of a more
			// accurate hash when we do actually have context variables:  the slower hash won't change
			// if point locations change, unlike the engineHash which includes all changes
			engineHash( sourcePath, context, h );
			Context::EditableScope scope( context );
			scope.remove( ScenePlug::scenePathContextName );
			prototypesPlug()->setPlug()->hash( h );
			namePlug()->hash( h );
			return;
		}

		tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );

		for( const auto &prototypeName : engine->prototypeNames()->readable() )
		{
			const std::vector<size_t> &pointIndicesForPrototype = esp->pointIndicesForPrototype( prototypeName );

			std::atomic<uint64_t> h1Accum( 0 ), h2Accum( 0 );
			const ThreadState &threadState = ThreadState::current();
			tbb::parallel_for( tbb::blocked_range<size_t>( 0, pointIndicesForPrototype.size() ), [&]( const tbb::blocked_range<size_t> &r )
				{
					Context::EditableScope scope( threadState );
					// As part of the setCollaborate plug machinery, we put the sourcePath in the context.
					// Need to remove it before evaluating the prototype sets
					scope.remove( ScenePlug::scenePathContextName );
					for( size_t i = r.begin(); i != r.end(); ++i )
					{
						const size_t pointIndex = pointIndicesForPrototype[i];
						int64_t instanceId = engine->instanceId( pointIndex );
						engine->setPrototypeContextVariables( pointIndex, scope );
						IECore::MurmurHash instanceH;
						instanceH.append( instanceId );
						prototypesPlug()->setPlug()->hash( instanceH );
						h1Accum += instanceH.h1();
						h2Accum += instanceH.h2();
					}
				},
				taskGroupContext
			);

			const ScenePlug::ScenePath *prototypeRoot = engine->prototypeRoot( prototypeName );
			h.append( prototypeName );
			h.append( &(*prototypeRoot)[0], prototypeRoot->size() );
			h.append( IECore::MurmurHash( h1Accum, h2Accum ) );
		}
	}
}

void Instancer::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	// EnginePlug is evaluated in a context in which scene:path holds the parent path for a
	// branch.
	if( output == enginePlug() )
	{
		PrototypeMode mode = (PrototypeMode)prototypeModePlug()->getValue();
		ConstStringVectorDataPtr prototypeRootsList = prototypeRootsListPlug()->getValue();
		if( mode == PrototypeMode::IndexedRootsList && prototypeRootsList->readable().empty() )
		{
			const auto childNames = prototypesPlug()->childNames( ScenePath() );
			prototypeRootsList = new StringVectorData(
				std::vector<string>(
					childNames->readable().begin(),
					childNames->readable().end()
				)
			);
		}

		ConstPrimitivePtr primitive = runTimeCast<const Primitive>( inPlug()->objectPlug()->getValue() );

		// Prepare the list of all context variables that affect the prototype scope, in an internal
		// struct that makes it easier to use them later
		std::vector< PrototypeContextVariable > prototypeContextVariables;

		// Put together a list of everything that affect the contexts this engine will evaluate prototypes
		// in
		if( primitive )
		{
			bool timeOffsetEnabled = timeOffsetPlug()->enabledPlug()->getValue();
			std::string seedContextName = "";
			if( seedEnabledPlug()->getValue() )
			{
				seedContextName = seedVariablePlug()->getValue();
			}

			for( ContextVariablePlug::Iterator it( contextVariablesPlug() ); !it.done(); ++it )
			{
				const ContextVariablePlug *plug = it->get();

				InternedString name = plug->namePlug()->getValue();
				if( !plug->enabledPlug()->getValue() || name == "" )
				{
					continue;
				}

				if( name.string() == seedContextName )
				{
					throw IECore::Exception( "Cannot manually specify \"" + name.string() + "\" which is driven by seedVariable." );
				}
				else if( name.string() == "frame" && timeOffsetEnabled )
				{
					throw IECore::Exception( "Cannot manually specify \"frame\" when time offset is enabled." );
				}

				float quantize = plug->quantizePlug()->getValue();

				// We hold onto m_primitive for the lifetime of EngineData, so it's safe to keep raw pointers
				// to the primvars
				const PrimitiveVariable *primVar = findVertexVariable( primitive.get(), name );

				// If primVar is null, it will be silently ignored
				//
				// \todo : We usually don't want to error on a missing primVar when there's an
				// obvious fallback ( like just not setting the corresponding context variable ).
				// But should we at least warn about this somehow?
				//
				// We do still insert it into prototypeContextVariables though - this ensures that
				// all EngineData for this instancer has the same set of variables, which makes it
				// easier when we compare all the engines to count unique prototypes

				prototypeContextVariables.push_back( { name, primVar, quantize, false, false, 0, 0 } );
			}

			if( seedContextName != "" )
			{
				int seeds = rawSeedPlug()->getValue() ? 0 : seedsPlug()->getValue();
				int seedScramble = seedPermutationPlug()->getValue();

				// We set seedMode to true here, which means rather than reading a given primvar, this context
				// variable will be driven by whatever is driving id.
				prototypeContextVariables.push_back( { seedContextName, nullptr, 0, false, true, seeds, seedScramble } );
			}

			if( timeOffsetEnabled )
			{
				const PrimitiveVariable *timeOffsetPrimVar = findVertexVariable( primitive.get(), timeOffsetPlug()->namePlug()->getValue() );
				if( timeOffsetPrimVar &&
					timeOffsetPrimVar->data->typeId() != FloatVectorDataTypeId &&
					timeOffsetPrimVar->data->typeId() != IntVectorDataTypeId
				)
				{
					// \todo : Are we really OK with silently ignoring primvars of the wrong type?
					// This feels very confusing to users, but matches other behaviour in Instancer
					timeOffsetPrimVar = nullptr;
				}

				float quantize = IECore::runTimeCast< const FloatPlug >( timeOffsetPlug()->quantizePlug() )->getValue();
				prototypeContextVariables.push_back( { "frame", timeOffsetPrimVar, quantize, true, false, 0, 0 } );
			}
		}

		static_cast<ObjectPlug *>( output )->setValue(
			new EngineData(
				primitive,
				mode,
				prototypeIndexPlug()->getValue(),
				prototypeRootsPlug()->getValue(),
				prototypeRootsList.get(),
				prototypesPlug(),
				idPlug()->getValue(),
				omitDuplicateIdsPlug()->getValue(),
				positionPlug()->getValue(),
				orientationPlug()->getValue(),
				scalePlug()->getValue(),
				inactiveIdsPlug()->getValue(),
				attributesPlug()->getValue(),
				attributePrefixPlug()->getValue(),
				prototypeContextVariables
			)
		);
		return;
	}
	else if( output == engineSplitPrototypesPlug() )
	{
		static_cast<ObjectPlug *>( output )->setValue(
			new EngineSplitPrototypesData(
				boost::static_pointer_cast<const EngineData>( enginePlug()->getValue() )
			)
		);
		return;
	}
	else if( output == variationsPlug() )
	{
		// Compute the number of variations by accumulating massive lists of unique hashes from all EngineDatas
		// and then counting the total number of uniques
		tbb::spin_mutex locationMutex;
		std::vector< std::unique_ptr< EngineData::PrototypeHashes > > perLocationHashes;

		auto functor =[this, &locationMutex, &perLocationHashes]( const GafferScene::ScenePlug *scene, const GafferScene::ScenePlug::ScenePath &path )
		{
			ConstEngineDataPtr engine = boost::static_pointer_cast<const EngineData>( enginePlug()->getValue() );
			std::unique_ptr< EngineData::PrototypeHashes > locationHashes = engine->uniquePrototypeHashes();

			tbb::spin_mutex::scoped_lock lock( locationMutex );
			perLocationHashes.push_back( std::move( locationHashes ) );
			return true;
		};

		GafferScene::SceneAlgo::filteredParallelTraverse( inPlug(), filterPlug(), functor );

		CompoundDataPtr result = new CompoundData;

		std::vector< InternedString > outputNames;
		if( perLocationHashes.size() == 0 )
		{
			// There is always an entry for the empty string, which contains the total variations
			// for all context variables combined
			result->writable()[""] = new IntData( 0 );
		}
		else
		{
			// \todo - we should technically be returning Int64Data in this compound, in case someone
			// uses rawSeed mode with more than 2^32 points. But this would be a compatibility break,
			// so I'm not changing it now.

			if( perLocationHashes.size() == 1 )
			{
				// We only have one location, so we can just output the sizes of the hash sets
				// we got
				for( const auto &var : *perLocationHashes[0] )
				{
					result->writable()[var.first] = new IntData( var.second.size() );
				}
			}
			else
			{
				// For multiple locations, we need to merge the hash sets into a single giant set,
				// and then check its size.  This seems very expensive, but we only do this when
				// users are using the Context Variation tab, and need a display of how many
				// variations they are creating.  This plug isn't evaluated at render time.
				EngineData::PrototypeHashes combine( *perLocationHashes[0] );
				for( unsigned int i = 1; i < perLocationHashes.size(); i++ )
				{
					for( auto &var : *perLocationHashes[i] )
					{
						combine[ var.first ].merge( var.second );
					}
				}
				for( const auto &var : combine )
				{
					result->writable()[var.first] = new IntData( var.second.size() );
				}
			}
		}

		static_cast<AtomicCompoundDataPlug *>( output )->setValue( result );
		return;
	}
	else if( output == setCollaboratePlug() )
	{
		const ScenePath &sourcePath = context->get<ScenePath>( ScenePlug::scenePathContextName );

		ConstEngineSplitPrototypesDataPtr esp = this->engineSplitPrototypes( sourcePath, context );
		const EngineData* engine = esp->engine();

		PathMatcherDataPtr outputSetData = new PathMatcherData;
		PathMatcher &outputSet = outputSetData->writable();

		vector<InternedString> branchPath( { namePlug()->getValue() } );

		tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );

		for( const auto &prototypeName : engine->prototypeNames()->readable() )
		{
			branchPath.resize( 2 );
			branchPath.back() = prototypeName;
			const ScenePlug::ScenePath *prototypeRoot = engine->prototypeRoot( prototypeName );

			const std::vector<size_t> &pointIndicesForPrototype = esp->pointIndicesForPrototype( prototypeName );

			tbb::spin_mutex instanceMutex;
			branchPath.emplace_back( InternedString() );
			const ThreadState &threadState = ThreadState::current();
			tbb::parallel_for( tbb::blocked_range<size_t>( 0, pointIndicesForPrototype.size() ), [&]( const tbb::blocked_range<size_t> &r )
				{
					Context::EditableScope scope( threadState );
					// As part of the setCollaborate plug machinery, we put the sourcePath in the context.
					// Need to remove it before evaluating the prototype sets
					scope.remove( ScenePlug::scenePathContextName );

					for( size_t i = r.begin(); i != r.end(); ++i )
					{
						const size_t pointIndex = pointIndicesForPrototype[i];
						int64_t instanceId = engine->instanceId( pointIndex );
						engine->setPrototypeContextVariables( pointIndex, scope );
						ConstPathMatcherDataPtr instanceSet = prototypesPlug()->setPlug()->getValue();
						PathMatcher pointInstanceSet = instanceSet->readable().subTree( *prototypeRoot );

						tbb::spin_mutex::scoped_lock lock( instanceMutex );
						branchPath.back() = instanceId;
						outputSet.addPaths( pointInstanceSet, branchPath );
					}
				},
				taskGroupContext
			);
		}

		static_cast<PathMatcherDataPlug *>( output )->setValue( outputSetData );
		return;
	}

	BranchCreator::compute( output, context );
}

Gaffer::ValuePlug::CachePolicy Instancer::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == variationsPlug() )
	{
		return ValuePlug::CachePolicy::TaskCollaboration;
	}
	else if( output == setCollaboratePlug() )
	{
		return ValuePlug::CachePolicy::TaskCollaboration;
	}
	return BranchCreator::computeCachePolicy( output );
}

Gaffer::ValuePlug::CachePolicy Instancer::hashCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == variationsPlug() )
	{
		return ValuePlug::CachePolicy::TaskCollaboration;
	}
	else if( output == setCollaboratePlug() )
	{
		return ValuePlug::CachePolicy::TaskCollaboration;
	}
	return BranchCreator::hashCachePolicy( output );
}

bool Instancer::affectsBranchBound( const Gaffer::Plug *input ) const
{
	return
		input == engineSplitPrototypesPlug() ||
		input == namePlug() ||
		input == prototypesPlug()->boundPlug() ||
		input == prototypesPlug()->transformPlug() ||
		input == outPlug()->childBoundsPlug()
	;
}

void Instancer::hashBranchBound( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() < 2 )
	{
		// "/" or "/instances"
		ScenePath path = sourcePath;
		path.insert( path.end(), branchPath.begin(), branchPath.end() );
		if( branchPath.size() == 0 )
		{
			path.push_back( namePlug()->getValue() );
		}
		h = outPlug()->childBoundsHash( path );
	}
	else if( branchPath.size() == 2 )
	{
		// "/instances/<prototypeName>"
		BranchCreator::hashBranchBound( sourcePath, branchPath, context, h );

		engineHash( sourcePath, context, h );
		h.append( branchPath.back() );

		{
			PrototypeScope scope( enginePlug(), context, &sourcePath, &branchPath );

			prototypesPlug()->transformPlug()->hash( h );
			prototypesPlug()->boundPlug()->hash( h );
		}
	}
	else
	{
		// "/instances/<prototypeName>/<id>/..."
		PrototypeScope scope( enginePlug(), context, &sourcePath, &branchPath );
		h = prototypesPlug()->boundPlug()->hash();
	}
}

Imath::Box3f Instancer::computeBranchBound( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	if( branchPath.size() < 2 )
	{
		// "/" or "/instances"
		ScenePath path = sourcePath;
		path.insert( path.end(), branchPath.begin(), branchPath.end() );
		if( branchPath.size() == 0 )
		{
			path.push_back( namePlug()->getValue() );
		}
		return outPlug()->childBounds( path );
	}
	else if( branchPath.size() == 2 )
	{
		// "/instances/<prototypeName>"
		//
		// We need to return the union of all the transformed children, but
		// because we have direct access to the engine, we can implement this
		// more efficiently than `ScenePlug::childBounds()`.

		ConstEngineSplitPrototypesDataPtr esp = engineSplitPrototypes( sourcePath, context );
		const EngineData *e = esp->engine();

		M44f childTransform;
		Box3f childBound;
		{
			PrototypeScope scope( esp->engine(), context, &sourcePath, &branchPath );
			childTransform = prototypesPlug()->transformPlug()->getValue();
			childBound = prototypesPlug()->boundPlug()->getValue();
		}

		const std::vector<size_t> &pointIndicesForPrototype = esp->pointIndicesForPrototype( branchPath.back() );

		// TODO - might be worth using a looser approximation - expand point cloud bound by largest diagonal of
		// prototype bound x largest scale. Especially since this isn't fully accurate anyway: we are getting a
		// single bound for the prototype with no context variables set, which may have nothing to do with actual
		// prototype we get once the context variables are set.
		task_group_context taskGroupContext( task_group_context::isolated );
		return parallel_reduce(
			tbb::blocked_range<size_t>( 0, pointIndicesForPrototype.size() ),
			Box3f(),
			[ pointIndicesForPrototype, &e, &childBound, &childTransform ] ( const tbb::blocked_range<size_t> &r, Box3f u ) {
				for( size_t i = r.begin(); i != r.end(); ++i )
				{
					const size_t pointIndex = pointIndicesForPrototype[i];
					const M44f m = childTransform * e->instanceTransform( pointIndex );
					const Box3f b = transform( childBound, m );
					u.extendBy( b );
				}
				return u;
			},
			// Union
			[] ( const Box3f &b0, const Box3f &b1 ) {
				Box3f u( b0 );
				u.extendBy( b1 );
				return u;
			},
			tbb::auto_partitioner(),
			// Prevents outer tasks silently cancelling our tasks
			taskGroupContext
		);
	}
	else
	{
		// "/instances/<prototypeName>/<id>/..."
		PrototypeScope scope( enginePlug(), context, &sourcePath, &branchPath );
		return prototypesPlug()->boundPlug()->getValue();
	}
}

bool Instancer::affectsBranchTransform( const Gaffer::Plug *input ) const
{
	return
		input == enginePlug() ||
		input == prototypesPlug()->transformPlug()
	;
}

void Instancer::hashBranchTransform( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() <= 2 )
	{
		// "/" or "/instances" or "/instances/<prototypeName>"
		BranchCreator::hashBranchTransform( sourcePath, branchPath, context, h );
	}
	else if( branchPath.size() == 3 )
	{
		// "/instances/<prototypeName>/<id>"
		BranchCreator::hashBranchTransform( sourcePath, branchPath, context, h );
		{
			PrototypeScope scope( enginePlug(), context, &sourcePath, &branchPath );
			prototypesPlug()->transformPlug()->hash( h );
		}
		engineHash( sourcePath, context, h );
		h.append( branchPath[2] );
	}
	else
	{
		// "/instances/<prototypeName>/<id>/..."
		PrototypeScope scope( enginePlug(), context, &sourcePath, &branchPath );
		h = prototypesPlug()->transformPlug()->hash();
	}
}

Imath::M44f Instancer::computeBranchTransform( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	if( branchPath.size() <= 2 )
	{
		// "/" or "/instances" or "/instances/<prototypeName>"
		return M44f();
	}
	else if( branchPath.size() == 3 )
	{
		// "/instances/<prototypeName>/<id>"
		M44f result;
		ConstEngineDataPtr e = engine( sourcePath, context );
		{
			PrototypeScope scope( e.get(), context, &sourcePath, &branchPath );
			result = prototypesPlug()->transformPlug()->getValue();
		}
		const size_t pointIndex = e->pointIndex( branchPath[2] );
		result = result * e->instanceTransform( pointIndex );
		return result;
	}
	else
	{
		// "/instances/<prototypeName>/<id>/..."
		PrototypeScope scope( enginePlug(), context, &sourcePath, &branchPath );
		return prototypesPlug()->transformPlug()->getValue();
	}
}

bool Instancer::affectsBranchAttributes( const Gaffer::Plug *input ) const
{
	return
		input == prototypesPlug()->attributesPlug() ||
		input == enginePlug()
	;
}

void Instancer::hashBranchAttributes( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() <= 2 )
	{
		// "/" or "/instances" or "/instances/<prototypeName>"
		h = outPlug()->attributesPlug()->defaultValue()->Object::hash();
	}
	else if( branchPath.size() == 3 )
	{
		// "/instances/<prototypeName>/<id>"
		BranchCreator::hashBranchAttributes( sourcePath, branchPath, context, h );
		ConstEngineDataPtr e = engine( sourcePath, context );
		if( e->numInstanceAttributes() )
		{
			e->instanceAttributesHash( e->pointIndex( branchPath[2] ), h );
		}
		PrototypeScope scope( e.get(), context, &sourcePath, &branchPath );
		prototypesPlug()->attributesPlug()->hash( h );
	}
	else
	{
		// "/instances/<prototypeName>/<id>/...
		PrototypeScope scope( enginePlug(), context, &sourcePath, &branchPath );
		h = prototypesPlug()->attributesPlug()->hash();
	}
}

IECore::ConstCompoundObjectPtr Instancer::computeBranchAttributes( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	if( branchPath.size() <= 2 )
	{
		// "/" or "/instances" or "/instances/<prototypeName>"
		return outPlug()->attributesPlug()->defaultValue();
	}
	else if( branchPath.size() == 3 )
	{
		// "/instances/<prototypeName>/<id>"
		ConstEngineDataPtr e = engine( sourcePath, context );
		PrototypeScope scope( e.get(), context, &sourcePath, &branchPath );
		ConstCompoundObjectPtr prototypeAttrs = prototypesPlug()->attributesPlug()->getValue();
		if( e->numInstanceAttributes() )
		{
			CompoundObjectPtr result = new CompoundObject;
			result->members() = prototypeAttrs->members();

			e->instanceAttributes( e->pointIndex( branchPath[2] ), *result );
			return result;
		}
		else
		{
			return prototypeAttrs;
		}
	}
	else
	{
		// "/instances/<prototypeName>/<id>/...
		PrototypeScope scope( enginePlug(), context, &sourcePath, &branchPath );
		return prototypesPlug()->attributesPlug()->getValue();
	}
}

bool Instancer::processesRootObject() const
{
	return true;
}

bool Instancer::affectsBranchObject( const Gaffer::Plug *input ) const
{
	return
		input == prototypesPlug()->objectPlug() ||
		input == enginePlug()
	;
}

void Instancer::hashBranchObject( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() <= 2 )
	{
		// "/" or "/instances" or "/instances/<prototypeName>"
		h = outPlug()->objectPlug()->defaultValue()->Object::hash();
	}
	else
	{
		// "/instances/<prototypeName>/<id>/...
		PrototypeScope scope( enginePlug(), context, &sourcePath, &branchPath );
		h = prototypesPlug()->objectPlug()->hash();
	}
}

IECore::ConstObjectPtr Instancer::computeBranchObject( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	if( branchPath.size() <= 2 )
	{
		// "/" or "/instances" or "/instances/<prototypeName>"
		return outPlug()->objectPlug()->defaultValue();
	}
	else
	{
		// "/instances/<prototypeName>/<id>/...
		PrototypeScope scope( enginePlug(), context, &sourcePath, &branchPath );
		return prototypesPlug()->objectPlug()->getValue();
	}
}

void Instancer::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( parent != capsuleScenePlug() && encapsulatePlug()->getValue() )
	{
		// Handling this special case here means an extra call to sourceAndBranchPaths
		// when we're encapsulating and we're not inside a branch - this is a small
		// unnecessary cost, but by falling back to just using BranchCreator hashObject
		// when branchPath.size() != 2, we are able to just use all the logic from
		// BranchCreator, without exposing any new API surface
		ScenePath sourcePath, branchPath;
		parentAndBranchPaths( path, sourcePath, branchPath );
		if( branchPath.size() == 1 )
		{
			BranchCreator::hashBranchObject( sourcePath, branchPath, context, h );
			h.append( reinterpret_cast<uint64_t>( this ) );
			/// We need to include anything that will affect how the capsule will expand.
			for( const auto &prototypePlug : ValuePlug::Range( *prototypesPlug() ) )
			{
				if( prototypePlug != prototypesPlug()->globalsPlug() )
				{
					h.append( prototypePlug->dirtyCount() );
				}
			}
			engineHash( sourcePath, context, h );
			h.append( context->hash() );
			outPlug()->boundPlug()->hash( h );
			return;
		}
	}

	BranchCreator::hashObject( path, context, parent, h );
}

IECore::ConstObjectPtr Instancer::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( parent != capsuleScenePlug() && encapsulatePlug()->getValue() )
	{
		ScenePath sourcePath, branchPath;
		parentAndBranchPaths( path, sourcePath, branchPath );
		if( branchPath.size() == 1 )
		{
			return new InstancerCapsule(
				this,
				context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName ) ,
				*context,
				outPlug()->objectPlug()->hash(),
				outPlug()->boundPlug()->getValue()
			);
		}
	}

	return BranchCreator::computeObject( path, context, parent );
}


bool Instancer::affectsBranchChildNames( const Gaffer::Plug *input ) const
{
	return
		input == namePlug() ||
		input == engineSplitPrototypesPlug()
	;
}

void Instancer::hashBranchChildNames( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() == 0 )
	{
		// "/"
		BranchCreator::hashBranchChildNames( sourcePath, branchPath, context, h );
		namePlug()->hash( h );
	}
	else if( branchPath.size() == 1 )
	{
		// "/instances"
		BranchCreator::hashBranchChildNames( sourcePath, branchPath, context, h );
		engineHash( sourcePath, context, h );
	}
	else if( branchPath.size() == 2 )
	{
		// "/instances/<prototypeName>"
		BranchCreator::hashBranchChildNames( sourcePath, branchPath, context, h );
		engineSplitPrototypesHash( sourcePath, context, h );
		h.append( branchPath.back() );
	}
	else
	{
		// "/instances/<prototypeName>/<id>/..."
		PrototypeScope scope( enginePlug(), context, &sourcePath, &branchPath );
		h = prototypesPlug()->childNamesPlug()->hash();
	}
}

IECore::ConstInternedStringVectorDataPtr Instancer::computeBranchChildNames( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
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
		// "/instances"
		return engine( sourcePath, context )->prototypeNames();
	}
	else if( branchPath.size() == 2 )
	{
		// "/instances/<prototypeName>"

		ConstEngineSplitPrototypesDataPtr esp = engineSplitPrototypes( sourcePath, context );

		const std::vector<size_t> &pointIndicesForPrototype = esp->pointIndicesForPrototype( branchPath.back() );

		// The children of the prototypeName are all the instances which use this prototype,
		// which we can query from the engine - however the names we output under use
		// the ids, not the point indices, and must be sorted. So we need to allocate a
		// temp buffer of integer ids, before converting to strings.

		std::vector<int64_t> ids;
		ids.reserve( pointIndicesForPrototype.size() );

		const EngineData *engineData = esp->engine();
		for( size_t q : pointIndicesForPrototype )
		{
			ids.push_back( engineData->instanceId( q ) );
		}

		// Sort ids before converting to string ( they have already been uniquified but not sorted by
		// the EngineData which uses a hash table )
		std::sort( ids.begin(), ids.end() );

		InternedStringVectorDataPtr childNamesData = new InternedStringVectorData;
		std::vector<InternedString> &childNames = childNamesData->writable();
		childNames.reserve( ids.size() );
		for( int64_t id : ids )
		{
			childNames.emplace_back( id );
		}

		return childNamesData;
	}
	else
	{
		// "/instances/<prototypeName>/<id>/..."
		PrototypeScope scope( enginePlug(), context, &sourcePath, &branchPath );
		return prototypesPlug()->childNamesPlug()->getValue();
	}
}

void Instancer::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( parent != capsuleScenePlug() && encapsulatePlug()->getValue() )
	{
		ScenePath sourcePath, branchPath;
		parentAndBranchPaths( path, sourcePath, branchPath );
		if( branchPath.size() == 1 )
		{
			h = outPlug()->childNamesPlug()->defaultValue()->Object::hash();
			return;
		}
	}

	BranchCreator::hashChildNames( path, context, parent, h );
}

IECore::ConstInternedStringVectorDataPtr Instancer::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( parent != capsuleScenePlug() && encapsulatePlug()->getValue() )
	{
		ScenePath sourcePath, branchPath;
		parentAndBranchPaths( path, sourcePath, branchPath );
		if( branchPath.size() == 1 )
		{
			return outPlug()->childNamesPlug()->defaultValue();
		}
	}

	return BranchCreator::computeChildNames( path, context, parent );
}

bool Instancer::affectsBranchSetNames( const Gaffer::Plug *input ) const
{
	return input == prototypesPlug()->setNamesPlug();
}

void Instancer::hashBranchSetNames( const ScenePath &sourcePath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	assert( sourcePath.size() == 0 ); // Expectation driven by `constantBranchSetNames() == true`

	if( prototypesPlug()->getInput() == outPlug() )
	{
		h = inPlug()->setNamesPlug()->hash();
		return;
	}

	h = prototypesPlug()->setNamesPlug()->hash();
}

IECore::ConstInternedStringVectorDataPtr Instancer::computeBranchSetNames( const ScenePath &sourcePath, const Gaffer::Context *context ) const
{
	assert( sourcePath.size() == 0 ); // Expectation driven by `constantBranchSetNames() == true`

	if( prototypesPlug()->getInput() == outPlug() )
	{
		return inPlug()->setNamesPlug()->getValue();
	}

	return prototypesPlug()->setNamesPlug()->getValue();
}

bool Instancer::affectsBranchSet( const Gaffer::Plug *input ) const
{
	return
		input == enginePlug() ||
		input == prototypesPlug()->setPlug() ||
		input == namePlug() ||
		input == setCollaboratePlug()
	;
}

void Instancer::hashBranchSet( const ScenePath &sourcePath, const IECore::InternedString &setName, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	BranchCreator::hashBranchSet( sourcePath, setName, context, h );

	// If we have context variables, we need to do a much more expensive evaluation of the prototype set
	// plug in every instance context.  We allow task collaboration on this expensive evaluation by redirecting
	// to an internal plug when we have context variables.  We could request hasContextVariables off the engine,
	// but we don't need to evaluate the engine here, so instead we make a conservative hasContextVariables
	// based on whether the source plugs have been touched
	bool hasContextVariables =
		( !timeOffsetPlug()->enabledPlug()->isSetToDefault() && !timeOffsetPlug()->namePlug()->isSetToDefault() ) ||
		!seedEnabledPlug()->isSetToDefault();

	for( ContextVariablePlug::Iterator it( contextVariablesPlug() ); !it.done() && !hasContextVariables; ++it )
	{
		const ContextVariablePlug *plug = it->get();

		hasContextVariables |=
			( plug->enabledPlug()->getInput() || plug->enabledPlug()->getValue() ) &&
			!plug->namePlug()->isSetToDefault();
	}

	if( hasContextVariables )
	{
		Context::EditableScope scope( context );
		scope.set( ScenePlug::scenePathContextName, &sourcePath );
		setCollaboratePlug()->hash( h );
	}
	else
	{
		engineHash( sourcePath, context, h );
		prototypesPlug()->setPlug()->hash( h );
		namePlug()->hash( h );
	}
}

IECore::ConstPathMatcherDataPtr Instancer::computeBranchSet( const ScenePath &sourcePath, const IECore::InternedString &setName, const Gaffer::Context *context ) const
{
	ConstEngineDataPtr engine = this->engine( sourcePath, context );

	if( engine->hasContextVariables() )
	{
		// When doing the much expensive work required when we have context variables, we try to share the
		// work between multiple threads using an internal PathMatcher plug with a TaskCollaborate policy.
		// The setCollaborate plug does all the heavy work.  It is evaluated with the sourcePath in the
		// context's scenePath, and it returns a PathMatcher for the set contents of one branch.
		Context::EditableScope scope( context );
		scope.set( ScenePlug::scenePathContextName, &sourcePath );
		return setCollaboratePlug()->getValue();
	}

	ConstPathMatcherDataPtr inputSet = prototypesPlug()->setPlug()->getValue();

	PathMatcherDataPtr outputSetData = new PathMatcherData;
	PathMatcher &outputSet = outputSetData->writable();

	vector<InternedString> branchPath( { namePlug()->getValue(), InternedString(), InternedString() } );

	vector<InternedString> outputPrototypePath( sourcePath.size() + 2 );
	outputPrototypePath = sourcePath;
	outputPrototypePath.push_back( namePlug()->getValue() );
	outputPrototypePath.push_back( InternedString() );

	for( const auto &prototypeName : engine->prototypeNames()->readable() )
	{
		PathMatcher instanceSet = inputSet->readable().subTree( *engine->prototypeRoot( prototypeName ) );
		branchPath[1] = prototypeName;

		outputPrototypePath.back() = prototypeName;

		ConstInternedStringVectorDataPtr childNamesData = capsuleScenePlug()->childNames( outputPrototypePath );

		for( const auto &childName : childNamesData->readable() )
		{
			branchPath[2] = childName;
			outputSet.addPaths( instanceSet, branchPath );
		}
	}

	return outputSetData;
}

void Instancer::hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( parent != capsuleScenePlug() && encapsulatePlug()->getValue() )
	{
		h = inPlug()->setPlug()->hash();
		return;
	}

	BranchCreator::hashSet( setName, context, parent, h );
}

IECore::ConstPathMatcherDataPtr Instancer::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( parent != capsuleScenePlug() && encapsulatePlug()->getValue() )
	{
		return inPlug()->setPlug()->getValue();
	}

	return BranchCreator::computeSet( setName, context, parent );
}

Instancer::ConstEngineDataPtr Instancer::engine( const ScenePath &sourcePath, const Gaffer::Context *context ) const
{
	ScenePlug::PathScope scope( context, &sourcePath );
	return boost::static_pointer_cast<const EngineData>( enginePlug()->getValue() );
}

void Instancer::engineHash( const ScenePath &sourcePath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ScenePlug::PathScope scope( context, &sourcePath );
	enginePlug()->hash( h );
}

Instancer::ConstEngineSplitPrototypesDataPtr Instancer::engineSplitPrototypes( const ScenePath &sourcePath, const Gaffer::Context *context ) const
{
	ScenePlug::PathScope scope( context, &sourcePath );
	return boost::static_pointer_cast<const EngineSplitPrototypesData>( engineSplitPrototypesPlug()->getValue() );
}

void Instancer::engineSplitPrototypesHash( const ScenePath &sourcePath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ScenePlug::PathScope scope( context, &sourcePath );
	engineSplitPrototypesPlug()->hash( h );
}

const std::type_info &Instancer::instancerCapsuleTypeInfo()
{
	return typeid( InstancerCapsule );
}

Instancer::PrototypeScope::PrototypeScope( const Gaffer::ObjectPlug *enginePlug, const Gaffer::Context *context, const ScenePath *sourcePath, const ScenePath *branchPath )
	:	Gaffer::Context::EditableScope( context )
{
	set( ScenePlug::scenePathContextName, sourcePath );

	// Must hold a smart pointer to engine so it can't be freed during the lifespan of this scope
	m_engine = boost::static_pointer_cast<const EngineData>( enginePlug->getValue() );

	setPrototype( m_engine.get(), branchPath );
}

Instancer::PrototypeScope::PrototypeScope( const EngineData *engine, const Gaffer::Context *context, const ScenePath *sourcePath, const ScenePath *branchPath )
	:	Gaffer::Context::EditableScope( context )
{
	setPrototype( engine, branchPath );
}

void Instancer::PrototypeScope::setPrototype( const EngineData *engine, const ScenePath *branchPath )
{
	assert( branchPath->size() >= 2 );

	const ScenePlug::ScenePath *prototypeRoot = engine->prototypeRoot( (*branchPath)[1] );

	if( branchPath->size() >= 3 && engine->hasContextVariables() )
	{
		const size_t pointIndex = engine->pointIndex( (*branchPath)[2] );
		engine->setPrototypeContextVariables( pointIndex, *this );
	}

	if( branchPath->size() > 3 )
	{
		m_prototypePath = *prototypeRoot;
		m_prototypePath.reserve( prototypeRoot->size() + branchPath->size() - 3 );
		m_prototypePath.insert( m_prototypePath.end(), branchPath->begin() + 3, branchPath->end() );
		set( ScenePlug::scenePathContextName, &m_prototypePath );
	}
	else
	{
		set( ScenePlug::scenePathContextName, prototypeRoot );
	}
}

namespace
{

// It shouldn't be necessary for this to be refcounted - but LRUCache is set up to make it impossible
// to get a pointer to the internal storage, since things could be evicted. We are disabling evictions,
// but we're still stuck with needing a shared pointer of some sort.
struct Prototype : public IECore::RefCounted
{
	Prototype(
		const ScenePlug *prototypesPlug, const ScenePlug::ScenePath *prototypeRoot,
		const std::vector<float> &sampleTimes, const IECore::MurmurHash &hash,
		const GafferScene::Private::RendererAlgo::RenderOptions &renderOptions,
		const Context *prototypeContext,
		IECoreScenePreview::Renderer *renderer,
		bool prepareRendererAttributes
	)
	{
		const float onFrameTime = prototypeContext->getFrame();

		Context::EditableScope scope( prototypeContext );

		scope.set( ScenePlug::scenePathContextName, prototypeRoot );

		m_attributes = prototypesPlug->attributesPlug()->getValue();
		if( prepareRendererAttributes )
		{
			m_rendererAttributes = renderer->attributes( m_attributes.get() );
		}

		for( unsigned int i = 0; i < sampleTimes.size(); i++ )
		{
			scope.setFrame( sampleTimes[i] );
			m_transforms.push_back( prototypesPlug->transformPlug()->getValue() );
		}

		IECore::MurmurHash h = hash;
		h.append( prototypeContext->hash() );
		h.append( *prototypeRoot );

		// We find the capsules using the engine at shutter open, but the time used to construct the capsules
		// must be the on-frame time, since the capsules will add their own shutter
		scope.setFrame( onFrameTime );

		if( prototypesPlug->childNamesPlug()->getValue()->readable().size() == 0 )
		{
			if( !renderOptions.purposeIncluded( m_attributes.get() ) )
			{
				// This prototype is not included. Leave m_object empty, which means this prototype will be skipped.
				return;
			}

			GafferScene::Private::RendererAlgo::deformationMotionTimes( renderOptions, m_attributes.get(), m_objectSampleTimes );
			GafferScene::Private::RendererAlgo::objectSamples( prototypesPlug->objectPlug(), m_objectSampleTimes, m_object );

			m_objectPointers.reserve( m_object.size() );
			for( ConstObjectPtr &i : m_object )
			{
				m_objectPointers.push_back( i.get() );
			}
		}
		else
		{
			// \todo - are there situations where this will be slow, and the renderer doesn't use it?
			const Box3f bound = prototypesPlug->boundPlug()->getValue();

			CapsulePtr newCapsule = new Capsule(
				prototypesPlug,
				*prototypeRoot,
				*prototypeContext,
				h,
				bound
			);

			// Pass through our render options to the sub-capsules
			newCapsule->setRenderOptions( renderOptions );
			m_object.push_back( std::move( newCapsule ) );
		}
	}

	std::vector<ConstObjectPtr> m_object;

	// Rather awkwardly, we need to store the objects as raw pointers as well, because Renderer::object
	// requires a vector of pointers for the animated case.
	std::vector<const Object *> m_objectPointers;
	std::vector<float> m_objectSampleTimes;
	ConstCompoundObjectPtr m_attributes;
	IECoreScenePreview::Renderer::AttributesInterfacePtr m_rendererAttributes;
	std::vector<M44f> m_transforms;
};

typedef boost::intrusive_ptr< const Prototype > ConstPrototypePtr;

struct PrototypeCacheGetterKey
{

	PrototypeCacheGetterKey( int prototypeId, const Context *context )
		: prototypeId( prototypeId ), context( context )
	{
	}

	operator IECore::MurmurHash () const
	{
		IECore::MurmurHash result = context->hash();
		result.append( prototypeId );
		return result;
	}

	const int prototypeId;
	const Context *context;
};

} // namespace

void Instancer::InstancerCapsule::render( IECoreScenePreview::Renderer *renderer ) const
{
	if( !renderer )
	{
		throw IECore::Exception( "Null renderer passed to InstancerCapsule" );
	}
	throwIfNoScene();

	// ============================================================================
	// Prepare context for scene evaluation
	// ============================================================================

	const float onFrameTime = context()->getFrame();
	const Context::Scope scope( context() );

	const ScenePlug::ScenePath enginePath( root().begin(), root().begin() + root().size() - 1 );

	const GafferScene::Private::RendererAlgo::RenderOptions renderOpts = renderOptions();

	// This is a bit of a weird convention for using a const variable with an initialization that doesn't
	// fit in one line ... not sure how I feel about it. In this case, it's crucial that sampleTimes is
	// const, because it is used from multiple threads simultaneously.
	const vector<float> sampleTimes = [this, &enginePath, &renderOpts]()
	{
		vector<float> result;
		const ConstCompoundObjectPtr sceneAttributes = m_instancer->inPlug()->fullAttributes( enginePath );
		GafferScene::Private::RendererAlgo::transformMotionTimes( renderOpts, sceneAttributes.get(), result );

		if( result.size() == 0 )
		{
			result.push_back( context()->getFrame() );
		}

		return result;
	}();

	// ============================================================================
	// Get the Engines
	// ============================================================================

	std::vector< ConstEngineDataPtr > engines( sampleTimes.size() );
	{
		Context::EditableScope frameScope( context() );
		for( unsigned int i = 0; i < sampleTimes.size(); i++ )
		{
			frameScope.setFrame( sampleTimes[i] );
			engines[i] = m_instancer->engine( enginePath, frameScope.context() );
		}
	}

	// ============================================================================
	// Set up a vector of all the prototypes
	// Or, if the prototypes depend on context, so there is no fixed prototype for
	// each prototype index, set up cache that will be used to find each
	// prototype
	// ============================================================================
	const ScenePlug *prototypesPlug = m_instancer->prototypesPlug();

	const IECore::MurmurHash outerCapsuleHash = Object::hash();

	const bool hasAttributes = engines[0]->numInstanceAttributes() > 0;

	task_group_context taskGroupContext( task_group_context::isolated );
	const ThreadState &threadState = ThreadState::current();

	// fixedPrototypes is used when the prototypes don't depend on context
	std::vector<ConstPrototypePtr> fixedPrototypes;
	if( !engines[0]->hasContextVariables() )
	{
		fixedPrototypes.resize( engines[0]->numValidPrototypes() );

		const ThreadState &threadState = ThreadState::current();
		tbb::parallel_for( tbb::blocked_range<size_t>( 0, fixedPrototypes.size() ),
			[&]( const tbb::blocked_range<size_t> &r )
			{
				Context::EditableScope threadScope( threadState );

				for( size_t i = r.begin(); i != r.end(); ++i )
				{
					fixedPrototypes[i] = new Prototype(
						prototypesPlug, engines[0]->prototypeRoot( i ), sampleTimes, outerCapsuleHash, renderOpts,
						threadScope.context(), renderer,
						// If we don't have instance attributes, we can prepare renderer attributes ahead of time
						!hasAttributes
					);

				}
			},
			taskGroupContext
		);

	}

	const Context *defaultContext = context();

	// If fixedPrototypes is not set, we will put prototypes in this cache whenever we first encounter
	// a prototype using a given context.
	IECorePreview::LRUCache<IECore::MurmurHash, ConstPrototypePtr, IECorePreview::LRUCachePolicy::Parallel, PrototypeCacheGetterKey> prototypeCache(
		[
			&prototypesPlug, &sampleTimes, &outerCapsuleHash, &renderOpts,
			&renderer, &hasAttributes, &engines, &defaultContext
		]
		( const PrototypeCacheGetterKey &key, size_t &cost, const IECore::Canceller *canceller ) -> ConstPrototypePtr
		{
			cost = 1;
			return new Prototype(
				prototypesPlug, engines[0]->prototypeRoot( key.prototypeId ), sampleTimes, outerCapsuleHash, renderOpts,
				key.context ? key.context : defaultContext, renderer,
				// If we don't have instance attributes, we can prepare renderer attributes ahead of time
				!hasAttributes
			);
		},
		std::numeric_limits<size_t>::max() // Never evict, even if prototypes are all unique
	);

	// ============================================================================
	// Output the instances
	// ============================================================================

	// We've found problems with performance when running too many iterations in parallel, which appear
	// to be related with hitting AiNode too hard in parallel ( perhaps related to threads spread between
	// separate processors ). To partially solve this, we set the grain size so that we shouldn't use more
	// than 32 threads, which appears to help some in testing.
	size_t grainSize = std::max( (size_t)1, engines[0]->numPoints() / 32 );

	tbb::parallel_for( tbb::blocked_range<size_t>( 0, engines[0]->numPoints(), grainSize ),
		[&]( const tbb::blocked_range<size_t> &r )
		{
			Context::EditableScope prototypeScope( threadState );

			vector<M44f> pointTransforms( sampleTimes.size() );
			IECoreScenePreview::Renderer::AttributesInterfacePtr attribsStorage;

			// Storage for names, indexed by prototype id ( each instance of the same prototype
			// will reuse this storage )
			std::vector< std::string > names( engines[0]->numValidPrototypes() );
			std::vector< int > namePrefixLengths( engines[0]->numValidPrototypes() );

			for( size_t pointIndex = r.begin(); pointIndex != r.end(); ++pointIndex )
			{
				int protoIndex = engines[0]->prototypeIndex( pointIndex );
				if( protoIndex == -1 )
				{
					// Invalid prototype
					continue;
				}

				const Prototype *proto;
				if( fixedPrototypes.size() )
				{
					proto = fixedPrototypes[protoIndex].get();
				}
				else
				{
					// The prototype depends on the context, so we need to find the prototype context for
					// this instance.


					// We find the capsules using the engine at shutter open, but the time used to construct the capsules
					// must be the on-frame time, since the capsules will add their own shutter ( and we also handle
					// the shutter ourselves for transform matrices )
					//
					// For most context variables, we are overwriting them for each prototype anyway, so
					// we can reuse the context. But timeOffset is relative, so it's important that we reset the
					// time before we do setPrototypeContextVariables for the next element. ( Should this be more
					// general instead of assuming that frame is the only variable for which offsetMode may be set? )
					prototypeScope.setFrame( onFrameTime );

					engines[0]->setPrototypeContextVariables( pointIndex, prototypeScope );

					proto = prototypeCache.get( PrototypeCacheGetterKey( protoIndex, prototypeScope.context() ) ).get();
				}

				if( !proto->m_object.size() )
				{
					// No object to render. This could happen if the protype didn't meet the
					// RenderOptions::purposeIncluded test.
					continue;
				}

				IECoreScenePreview::Renderer::AttributesInterface *attribs;
				if( hasAttributes )
				{
					CompoundObjectPtr currentAttributes = new CompoundObject();

					// Since we're not going to modify any existing members (only add new ones),
					// and our result is only read in this function, and never written, we can
					// directly reference the input members in our result without copying. Be
					// careful not to modify them though!
					currentAttributes->members() = proto->m_attributes->members();

					engines[0]->instanceAttributes( pointIndex, *currentAttributes );
					attribsStorage = renderer->attributes( currentAttributes.get() );
					attribs = attribsStorage.get();
				}
				else
				{
					attribs = proto->m_rendererAttributes.get();
				}

				int64_t instanceId = engines[0]->instanceId( pointIndex );


				if( !namePrefixLengths[protoIndex] )
				{
					// If we haven't allocated a name for this prototype index, allocate it now,
					// including additional storage that will hold the digits for each instance id
					const std::string &protoName = engines[0]->prototypeNames()->readable()[ protoIndex ].string();
					names[protoIndex].reserve( protoName.size() + std::numeric_limits< int64_t >::digits10 + 1 );
					names[protoIndex] += protoName;
					names[protoIndex].append( 1, '/' );
					namePrefixLengths[protoIndex] = names[protoIndex].size();
				}

				// Create a name by concatenating the name of the prototype with digits of the current
				// instance id.
				// Including the prototype name is not necessary for uniqueness ( the instance ids are
				// already unique ), but doing this keeps the names more consistent with how things end
				// up being named when they use the non-encapsulated hierarchy.
				std::string &name = names[ protoIndex ];
				const int prefixLen = namePrefixLengths[ protoIndex ];
				name.resize( namePrefixLengths[protoIndex] + std::numeric_limits< int64_t >::digits10 + 1 );
				name.resize( std::to_chars( &name[prefixLen], &(*name.end()), instanceId ).ptr - &name[0] );

				IECoreScenePreview::Renderer::ObjectInterfacePtr objectInterface;
				if( proto->m_objectSampleTimes.size() )
				{
					objectInterface = renderer->object(
						name, proto->m_objectPointers, proto->m_objectSampleTimes, attribs
					);
				}
				else
				{
					objectInterface = renderer->object(
						name, proto->m_object[0].get(), attribs
					);
				}

				if( sampleTimes.size() == 1 )
				{
					objectInterface->transform( proto->m_transforms[0] * engines[0]->instanceTransform( pointIndex ) );
				}
				else
				{
					for( unsigned int i = 0; i < engines.size(); i++ )
					{
						int curPointIndex = i == 0 ? pointIndex : engines[i]->pointIndex( instanceId );
						pointTransforms[i] = proto->m_transforms[i] * engines[i]->instanceTransform( curPointIndex );
					}

					objectInterface->transform( pointTransforms, sampleTimes );
				}

			}
		},
		taskGroupContext
	);
}

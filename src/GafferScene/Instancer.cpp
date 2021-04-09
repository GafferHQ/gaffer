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
#include "GafferScene/SceneAlgo.h"

#include "GafferScene/Private/ChildNamesMap.h"

#include "Gaffer/Context.h"
#include "Gaffer/StringPlug.h"

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
	if( it == primitive->variables.end() || it->second.interpolation != IECoreScene::PrimitiveVariable::Vertex )
	{
		return nullptr;
	}
	return &it->second;
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
	void operator()( const TypedData<vector<T>> *data, const PrototypeContextVariable &v, int index, Context::EditableScope &scope )
	{
		T raw = PrimitiveVariable::IndexedView<T>( *v.primVar )[index];
		T value = quantize( raw, v.quantize );
		scope.set( v.name, value );
	}

	void operator()( const TypedData<vector<float>> *data, const PrototypeContextVariable &v, int index, Context::EditableScope &scope )
	{
		float raw = PrimitiveVariable::IndexedView<float>( *v.primVar )[index];
		float value = quantize( raw, v.quantize );

		if( v.offsetMode )
		{
			scope.set( v.name, value + scope.context()->get<float>( v.name ) );
		}
		else
		{
			scope.set( v.name, value );
		}
	}

	void operator()( const TypedData<vector<int>> *data, const PrototypeContextVariable &v, int index, Context::EditableScope &scope )
	{
		int raw = PrimitiveVariable::IndexedView<int>( *v.primVar )[index];
		int value = quantize( raw, v.quantize );

		if( v.offsetMode )
		{
			scope.set( v.name, float(value) + scope.context()->get<float>( v.name ) );
		}
		else
		{
			scope.set( v.name, value );
		}
	}

	void operator()( const Data *data, const PrototypeContextVariable &v, int index, Context::EditableScope &scope )
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
	void operator()( const TypedData<vector<T>> *data, const PrototypeContextVariable &v, int index, MurmurHash &contextHash )

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

// We create a seed integer that corresponds to the id by hashing the id and then modulo'ing to
// numSeeds, to create seeds in the range 0 .. numSeeds-1 that persistently correspond to the ids,
// with a grouping pattern that can be changed with seedScramble
int seedForPoint( int index, const PrimitiveVariable *primVar, int numSeeds, int seedScramble )
{
	int id = index;
	if( primVar )
	{
		// TODO - the exception this will throw on non-int primvars may not be very clear to users
		id = PrimitiveVariable::IndexedView<int>( *primVar )[index];
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
		seedHash.append( id );
		id = int( ( double( seedHash.h1() ) / double( UINT64_MAX ) ) * double( numSeeds ) );
		id = id % numSeeds;  // For the rare case h1 / max == 1.0, make sure we stay in range
	}
	return id;
}

InternedString g_prototypeRootName( "root" );
ConstInternedStringVectorDataPtr g_emptyNames = new InternedStringVectorData();

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
			const std::string &index,
			const std::string &rootsVariable,
			const StringVectorData *rootsList,
			const ScenePlug *prototypes,
			const std::string &id,
			const std::string &position,
			const std::string &orientation,
			const std::string &scale,
			const std::string &attributes,
			const std::string &attributePrefix,
			const std::vector< PrototypeContextVariable > &prototypeContextVariables
		)
			:	m_primitive( primitive ),
				m_numPrototypes( 0 ),
				m_numValidPrototypes( 0 ),
				m_indices( nullptr ),
				m_ids( nullptr ),
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

			initPrototypes( mode, index, rootsVariable, rootsList, prototypes );

			if( const IntVectorData *ids = m_primitive->variableData<IntVectorData>( id ) )
			{
				m_ids = &ids->readable();
				if( m_ids->size() != numPoints() )
				{
					throw IECore::Exception( boost::str( boost::format( "Id primitive variable \"%1%\" has incorrect size" ) % id ) );
				}
			}

			if( const V3fVectorData *p = m_primitive->variableData<V3fVectorData>( position ) )
			{
				m_positions = &p->readable();
				if( m_positions->size() != numPoints() )
				{
					throw IECore::Exception( boost::str( boost::format( "Position primitive variable \"%1%\" has incorrect size" ) % position ) );
				}
			}

			if( const QuatfVectorData *o = m_primitive->variableData<QuatfVectorData>( orientation ) )
			{
				m_orientations = &o->readable();
				if( m_orientations->size() != numPoints() )
				{
					throw IECore::Exception( boost::str( boost::format( "Orientation primitive variable \"%1%\" has incorrect size" ) % orientation ) );
				}
			}

			if( const V3fVectorData *s = m_primitive->variableData<V3fVectorData>( scale ) )
			{
				m_scales = &s->readable();
				if( m_scales->size() != numPoints() )
				{
					throw IECore::Exception( boost::str( boost::format( "Scale primitive variable \"%1%\" has incorrect size" ) % scale ) );
				}
			}
			else if( const FloatVectorData *s = m_primitive->variableData<FloatVectorData>( scale ) )
			{
				m_uniformScales = &s->readable();
				if( m_uniformScales->size() != numPoints() )
				{
					throw IECore::Exception( boost::str( boost::format( "Uniform scale primitive variable \"%1%\" has incorrect size" ) % scale ) );
				}
			}

			if( m_ids )
			{
				for( size_t i = 0; i<numPoints(); ++i )
				{
					// Iterate in reverse order so that in case of duplicates, the first one will override
					size_t reverseI = numPoints() - 1 - i;
					m_idsToPointIndices[(*m_ids)[reverseI]] = reverseI;
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
					throw IECore::Exception( boost::str( boost::format( "Context primitive variable for \"%1%\" is not a correctly sized Vertex primitive variable" ) % v.name.string() ) );
				}
			}
		}

		size_t numPoints() const
		{
			return m_primitive ? m_primitive->variableSize( PrimitiveVariable::Vertex ) : 0;
		}

		size_t instanceId( size_t pointIndex ) const
		{
			return m_ids ? (*m_ids)[pointIndex] : pointIndex;
		}

		size_t pointIndex( const InternedString &name ) const
		{
			const size_t i = boost::lexical_cast<size_t>( name );
			if( !m_ids )
			{
				return i;
			}

			IdsToPointIndices::const_iterator it = m_idsToPointIndices.find( i );
			if( it == m_idsToPointIndices.end() )
			{
				throw IECore::Exception( boost::str( boost::format( "Instance id \"%1%\" is invalid" ) % name ) );
			}

			return it->second;
		}

		size_t numValidPrototypes() const
		{
			return m_numValidPrototypes;
		}

		int prototypeIndex( size_t pointIndex ) const
		{
			if( m_numPrototypes )
			{
				return m_prototypeIndexRemap[ ( m_indices ? (*m_indices)[pointIndex] : 0 ) % m_numPrototypes ];
			}
			else
			{
				return -1;
			}
		}

		const ScenePlug::ScenePath &prototypeRoot( const InternedString &name ) const
		{
			return runTimeCast<const InternedStringVectorData>( m_roots[m_names->input( name ).index] )->readable();
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
				result = (*m_orientations)[pointIndex].toMatrix44() * result;
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

		CompoundObjectPtr instanceAttributes( size_t pointIndex ) const
		{
			CompoundObjectPtr result = new CompoundObject;
			CompoundObject::ObjectMap &writableResult = result->members();
			for( const auto &attributeCreator : m_attributeCreators )
			{
				writableResult[attributeCreator.first] = attributeCreator.second( pointIndex );
			}
			return result;
		}

		typedef std::map< InternedString, boost::unordered_set< IECore::MurmurHash > > PrototypeHashes;

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
			for( unsigned int i = 0; i < n; i++ )
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

			// \todo - should use make_unique once we standardize on C++14
			std::unique_ptr<PrototypeHashes> result( new PrototypeHashes() );
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

		// Set the context variables in the context for this index, based on the m_prototypeContextVariables
		// set up for this EngineData
		void setPrototypeContextVariables( int index, Context::EditableScope &scope ) const
		{
			for( unsigned int i = 0; i < m_prototypeContextVariables.size(); i++ )
			{
				const PrototypeContextVariable &v = m_prototypeContextVariables[i];

				if( v.seedMode )
				{
					scope.set( v.name, seedForPoint( index, v.primVar, v.numSeeds, v.seedScramble ) );
					continue;
				}

				if( !v.primVar )
				{
					continue;
				}

				try
				{
					IECore::dispatch( v.primVar->data.get(), AccessPrototypeContextVariable(), v, index, scope );
				}
				catch( QuantizeException &e )
				{
					throw IECore::Exception( boost::str( boost::format( "Context variable \"%1%\" : cannot quantize variable of type %2%" ) % index % v.primVar->data->typeName() ) );
				}
			}
		}

	protected :

		// Needs to match setPrototypeContextVariables above, except that it operates on one
		// PrototypeContextVariable at a time instead of iterating through them
		void hashPrototypeContextVariable( int index, const PrototypeContextVariable &v, IECore::MurmurHash &result ) const
		{
			if( v.seedMode )
			{
				result.append( seedForPoint( index, v.primVar, v.numSeeds, v.seedScramble ) );
				return;
			}

			if( !v.primVar )
			{
				return;
			}

			try
			{
				IECore::dispatch( v.primVar->data.get(), UniqueHashPrototypeContextVariable(), v, index, result );
			}
			catch( QuantizeException &e )
			{
				throw IECore::Exception( boost::str( boost::format( "Context variable \"%1%\" : cannot quantize variable of type %2%" ) % index % v.primVar->data->typeName() ) );
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

		typedef std::function<DataPtr ( size_t )> AttributeCreator;

		struct MakeAttributeCreator
		{

			template<typename T>
			AttributeCreator operator()( const TypedData<vector<T>> *data )
			{
				return std::bind( &createAttribute<T>, data->readable(), ::_1 );
			}

			template<typename T>
			AttributeCreator operator()( const GeometricTypedData<vector<T>> *data )
			{
				return std::bind( &createGeometricAttribute<T>, data->readable(), data->getInterpretation(), ::_1 );
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
				if( primVar.second.interpolation != PrimitiveVariable::Vertex )
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

		void initPrototypes( PrototypeMode mode, const std::string &index, const std::string &rootsVariable, const StringVectorData *rootsList, const ScenePlug *prototypes )
		{
			const std::vector<std::string> *rootStrings = nullptr;

			switch( mode )
			{
				case PrototypeMode::IndexedRootsList :
				{
					if( const auto *indices = m_primitive->variableData<IntVectorData>( index ) )
					{
						m_indices = &indices->readable();
						if( m_indices->size() != numPoints() )
						{
							throw IECore::Exception( boost::str( boost::format( "prototypeIndex primitive variable \"%1%\" has incorrect size" ) % index ) );
						}
					}

					rootStrings = &rootsList->readable();

					break;
				}
				case PrototypeMode::IndexedRootsVariable :
				{
					if( const auto *indices = m_primitive->variableData<IntVectorData>( index ) )
					{
						m_indices = &indices->readable();
						if( m_indices->size() != numPoints() )
						{
							throw IECore::Exception( boost::str( boost::format( "prototypeIndex primitive variable \"%1%\" has incorrect size" ) % index ) );
						}
					}

					const auto *roots = m_primitive->variableData<StringVectorData>( rootsVariable, PrimitiveVariable::Constant );
					if( !roots )
					{
						std::string message = boost::str( boost::format( "prototypeRoots primitive variable \"%1%\" must be Constant StringVectorData when using IndexedRootsVariable mode" ) % rootsVariable );
						if( m_primitive->variables.find( rootsVariable ) == m_primitive->variables.end() )
						{
							message += ", but it does not exist";
						}
						throw IECore::Exception( message );
					}

					rootStrings = &roots->readable();
					if( rootStrings->empty() )
					{
						throw IECore::Exception( boost::str( boost::format( "prototypeRoots primitive variable \"%1%\" must specify at least one root location" ) % rootsVariable ) );
					}

					break;
				}
				case PrototypeMode::RootPerVertex :
				{
					const auto view = m_primitive->variableIndexedView<StringVectorData>( rootsVariable, PrimitiveVariable::Vertex );
					if( !view )
					{
						std::string message = boost::str( boost::format( "prototypeRoots primitive variable \"%1%\" must be Vertex StringVectorData when using RootPerVertex mode" ) % rootsVariable );
						if( m_primitive->variables.find( rootsVariable ) == m_primitive->variables.end() )
						{
							message += ", but it does not exist";
						}
						throw IECore::Exception( message );
					}

					m_indices = view->indices();
					rootStrings = &view->data();
					if( rootStrings->empty() )
					{
						throw IECore::Exception( boost::str( boost::format( "prototypeRoots primitive variable \"%1%\" must specify at least one root location" ) % rootsVariable ) );
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
					throw IECore::Exception( boost::str( boost::format( "Prototype root \"%1%\" does not exist in the `prototypes` scene" ) % root ) );
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
			m_numPrototypes = m_prototypeIndexRemap.size();
			m_numValidPrototypes = m_names->outputChildNames()->readable().size();
		}

		IECoreScene::ConstPrimitivePtr m_primitive;
		size_t m_numPrototypes;
		size_t m_numValidPrototypes;
		Private::ChildNamesMapPtr m_names;
		std::vector<ConstInternedStringVectorDataPtr> m_roots;
		std::vector<int> m_prototypeIndexRemap;
		const std::vector<int> *m_indices;
		const std::vector<int> *m_ids;
		const std::vector<Imath::V3f> *m_positions;
		const std::vector<Imath::Quatf> *m_orientations;
		const std::vector<Imath::V3f> *m_scales;
		const std::vector<float> *m_uniformScales;

		typedef std::unordered_map <int, size_t> IdsToPointIndices;
		IdsToPointIndices m_idsToPointIndices;

		boost::container::flat_map<InternedString, AttributeCreator> m_attributeCreators;
		MurmurHash m_attributesHash;

		const std::vector< PrototypeContextVariable > m_prototypeContextVariables;
};

//////////////////////////////////////////////////////////////////////////
// Instancer
//////////////////////////////////////////////////////////////////////////

GAFFER_PLUG_DEFINE_TYPE( Instancer::ContextVariablePlug );

Instancer::ContextVariablePlug::ContextVariablePlug( const std::string &name, Direction direction, bool defaultEnable, unsigned flags )
	:   ValuePlug( name, direction, flags )
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
	addChild( new StringPlug( "position", Plug::In, "P" ) );
	addChild( new StringPlug( "orientation", Plug::In ) );
	addChild( new StringPlug( "scale", Plug::In ) );
	addChild( new StringPlug( "attributes", Plug::In ) );
	addChild( new StringPlug( "attributePrefix", Plug::In ) );
	addChild( new BoolPlug( "encapsulateInstanceGroups", Plug::In ) );
	addChild( new BoolPlug( "seedEnabled", Plug::In ) );
	addChild( new StringPlug( "seedVariable", Plug::In, "seed" ) );
	addChild( new IntPlug( "seeds", Plug::In, 10, 1 ) );
	addChild( new IntPlug( "seedPermutation", Plug::In ) );
	addChild( new BoolPlug( "rawSeed", Plug::In ) );
	addChild( new ValuePlug( "contextVariables", Plug::In ) );
	addChild( new ContextVariablePlug( "timeOffset", Plug::In, false, Plug::Flags::Default ) );
	addChild( new AtomicCompoundDataPlug( "variations", Plug::Out, new CompoundData() ) );
	addChild( new ObjectPlug( "__engine", Plug::Out, NullObject::defaultNullObject() ) );
	addChild( new AtomicCompoundDataPlug( "__prototypeChildNames", Plug::Out, new CompoundData ) );
	addChild( new ScenePlug( "__capsuleScene", Plug::Out ) );
	addChild( new PathMatcherDataPlug( "__setCollaborate", Plug::Out, new IECore::PathMatcherData() ) );

	capsuleScenePlug()->boundPlug()->setInput( outPlug()->boundPlug() );
	capsuleScenePlug()->transformPlug()->setInput( outPlug()->transformPlug() );
	capsuleScenePlug()->attributesPlug()->setInput( outPlug()->attributesPlug() );
	capsuleScenePlug()->setNamesPlug()->setInput( outPlug()->setNamesPlug() );
	capsuleScenePlug()->globalsPlug()->setInput( outPlug()->globalsPlug() );
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

Gaffer::StringPlug *Instancer::positionPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 7 );
}

const Gaffer::StringPlug *Instancer::positionPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 7 );
}

Gaffer::StringPlug *Instancer::orientationPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 8 );
}

const Gaffer::StringPlug *Instancer::orientationPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 8 );
}

Gaffer::StringPlug *Instancer::scalePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 9 );
}

const Gaffer::StringPlug *Instancer::scalePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 9 );
}

Gaffer::StringPlug *Instancer::attributesPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 10 );
}

const Gaffer::StringPlug *Instancer::attributesPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 10 );
}

Gaffer::StringPlug *Instancer::attributePrefixPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 11 );
}

const Gaffer::StringPlug *Instancer::attributePrefixPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 11 );
}

Gaffer::BoolPlug *Instancer::encapsulateInstanceGroupsPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 12 );
}

const Gaffer::BoolPlug *Instancer::encapsulateInstanceGroupsPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 12 );
}

Gaffer::BoolPlug *Instancer::seedEnabledPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 13 );
}

const Gaffer::BoolPlug *Instancer::seedEnabledPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 13 );
}

Gaffer::StringPlug *Instancer::seedVariablePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 14 );
}

const Gaffer::StringPlug *Instancer::seedVariablePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 14 );
}

Gaffer::IntPlug *Instancer::seedsPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 15 );
}

const Gaffer::IntPlug *Instancer::seedsPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 15 );
}

Gaffer::IntPlug *Instancer::seedPermutationPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 16 );
}

const Gaffer::IntPlug *Instancer::seedPermutationPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 16 );
}

Gaffer::BoolPlug *Instancer::rawSeedPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 17 );
}

const Gaffer::BoolPlug *Instancer::rawSeedPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 17 );
}

Gaffer::ValuePlug *Instancer::contextVariablesPlug()
{
	return getChild<ValuePlug>( g_firstPlugIndex + 18 );
}

const Gaffer::ValuePlug *Instancer::contextVariablesPlug() const
{
	return getChild<ValuePlug>( g_firstPlugIndex + 18 );
}

GafferScene::Instancer::ContextVariablePlug *Instancer::timeOffsetPlug()
{
	return getChild<ContextVariablePlug>( g_firstPlugIndex + 19 );
}

const GafferScene::Instancer::ContextVariablePlug *Instancer::timeOffsetPlug() const
{
	return getChild<ContextVariablePlug>( g_firstPlugIndex + 19 );
}

Gaffer::AtomicCompoundDataPlug *Instancer::variationsPlug()
{
	return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex + 20 );
}

const Gaffer::AtomicCompoundDataPlug *Instancer::variationsPlug() const
{
	return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex + 20 );
}

Gaffer::ObjectPlug *Instancer::enginePlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 21 );
}

const Gaffer::ObjectPlug *Instancer::enginePlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 21 );
}

Gaffer::AtomicCompoundDataPlug *Instancer::prototypeChildNamesPlug()
{
	return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex + 22 );
}

const Gaffer::AtomicCompoundDataPlug *Instancer::prototypeChildNamesPlug() const
{
	return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex + 22 );
}

GafferScene::ScenePlug *Instancer::capsuleScenePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex + 23 );
}

const GafferScene::ScenePlug *Instancer::capsuleScenePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex + 23 );
}

Gaffer::PathMatcherDataPlug *Instancer::setCollaboratePlug()
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 24 );
}

const Gaffer::PathMatcherDataPlug *Instancer::setCollaboratePlug() const
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 24 );
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
		input == positionPlug() ||
		input == orientationPlug() ||
		input == scalePlug() ||
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

	if( input == enginePlug() )
	{
		outputs.push_back( prototypeChildNamesPlug() );
	}

	// For the affects of our output plug, we can mostly rely on BranchCreator's mechanism driven
	// by affectsBranchObject etc., but for these 3 plugs, we have an overridden hash/compute
	// which in addition to everything that BranchCreator handles, are also affected by
	// encapsulateInstanceGroupsPlug()
	if( input == encapsulateInstanceGroupsPlug() )
	{
		outputs.push_back( outPlug()->objectPlug() );
		outputs.push_back( outPlug()->childNamesPlug() );
		outputs.push_back( outPlug()->setPlug() );
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
		input == enginePlug() ||
		input == prototypesPlug()->setPlug() ||
		input == prototypeChildNamesPlug() ||
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
		positionPlug()->hash( h );
		orientationPlug()->hash( h );
		scalePlug()->hash( h );
		attributesPlug()->hash( h );
		attributePrefixPlug()->hash( h );

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
	else if( output == prototypeChildNamesPlug() )
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
		const ScenePath &parentPath = context->get<ScenePath>( ScenePlug::scenePathContextName );

		ConstEngineDataPtr engine = this->engine( parentPath, context );
		if( !engine->hasContextVariables() )
		{
			// We use a slightly approximate version of hasContextVariables in hashBranchSet, to
			// avoid computing engine before necessary.  If it turns out that all the context variables
			// requested were actually invalid, then we can use the same fast approximate hash used in
			// hashBranchSet.
			//
			// This is a little bit weird, because in this scenario, this plug will never be evaluated:
			// computeBranchSet checks the accurate hasContextVariables before evaluating setCollaboratePlug.
			// But hashBranchSet is evaluating us, so we have to give a hash that will work for it.
			//
			// We could always hash this stuff in hashBranchSet, but we would lose out a benefit of a more
			// accurate hash when we do actually have context variables:  the slower hash won't change
			// if point locations change, unlike the engineHash which includes all changes
			engineHash( parentPath, context, h );
			prototypeChildNamesHash( parentPath, context, h );
			prototypesPlug()->setPlug()->hash( h );
			namePlug()->hash( h );
			return;
		}

		IECore::ConstCompoundDataPtr prototypeChildNames = this->prototypeChildNames( parentPath, context );

		tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );

		for( const auto &prototypeName : engine->prototypeNames()->readable() )
		{
			const vector<InternedString> &childNames = prototypeChildNames->member<InternedStringVectorData>( prototypeName )->readable();

			std::atomic<uint64_t> h1Accum( 0 ), h2Accum( 0 );
			const ThreadState &threadState = ThreadState::current();
			tbb::parallel_for( tbb::blocked_range<size_t>( 0, childNames.size() ), [&]( const tbb::blocked_range<size_t> &r )
				{
					Context::EditableScope scope( threadState );
					// As part of the setCollaborate plug machinery, we put the parentPath in the context.
					// Need to remove it before evaluating the prototype sets
					scope.remove( ScenePlug::scenePathContextName );
					for( size_t i = r.begin(); i != r.end(); ++i )
					{
						const size_t pointIndex = engine->pointIndex( childNames[i] );
						engine->setPrototypeContextVariables( pointIndex, scope );
						IECore::MurmurHash instanceH;
						instanceH.append( childNames[i] );
						prototypesPlug()->setPlug()->hash( instanceH );
						h1Accum += instanceH.h1();
						h2Accum += instanceH.h2();
					}
				},
				taskGroupContext
			);

			const ScenePlug::ScenePath &prototypeRoot = engine->prototypeRoot( prototypeName );
			h.append( prototypeName );
			h.append( &prototypeRoot[0], prototypeRoot.size() );
			h.append( IECore::MurmurHash( h1Accum, h2Accum ) );
		}
	}
}

void Instancer::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	// Both the enginePlug and prototypeChildNamesPlug are evaluated
	// in a context in which scene:path holds the parent path for a
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
				const PrimitiveVariable *idPrimVar = findVertexVariable( primitive.get(), idPlug()->getValue() );
				if( idPrimVar && idPrimVar->data->typeId() != IntVectorDataTypeId )
				{
					idPrimVar = nullptr;
				}

				int seeds = rawSeedPlug()->getValue() ? 0 : seedsPlug()->getValue();
				int seedScramble = seedPermutationPlug()->getValue();
				prototypeContextVariables.push_back( { seedContextName, idPrimVar, 0, false, true, seeds, seedScramble } );
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
				positionPlug()->getValue(),
				orientationPlug()->getValue(),
				scalePlug()->getValue(),
				attributesPlug()->getValue(),
				attributePrefixPlug()->getValue(),
				prototypeContextVariables
			)
		);
		return;
	}
	else if( output == prototypeChildNamesPlug() )
	{
		// Here we compute and cache the child names for all of
		// the /instances/<prototypeName> locations at once. We
		// could instead compute them one at a time in
		// computeBranchChildNames() but that would require N
		// passes over the input points, where N is the number
		// of prototypes.
		ConstEngineDataPtr engine = boost::static_pointer_cast<const EngineData>( enginePlug()->getValue() );
		const auto &prototypeNames = engine->prototypeNames()->readable();

		vector<vector<size_t>> indexedPrototypeChildIds;

		size_t numPrototypes = engine->numValidPrototypes();
		if( numPrototypes )
		{
			indexedPrototypeChildIds.resize( numPrototypes );
			for( size_t i = 0, e = engine->numPoints(); i < e; ++i )
			{
				int prototypeIndex = engine->prototypeIndex( i );
				if( prototypeIndex != -1 )
				{
					indexedPrototypeChildIds[prototypeIndex].push_back( engine->instanceId( i ) );
				}
			}
		}

		CompoundDataPtr result = new CompoundData;
		for( size_t i = 0; i < numPrototypes; ++i )
		{
			// Sort and uniquify ids before converting to string
			std::sort( indexedPrototypeChildIds[i].begin(), indexedPrototypeChildIds[i].end() );
			auto last = std::unique( indexedPrototypeChildIds[i].begin(), indexedPrototypeChildIds[i].end() );
			indexedPrototypeChildIds[i].erase( last, indexedPrototypeChildIds[i].end() );

			InternedStringVectorDataPtr prototypeChildNames = new InternedStringVectorData;
			for( size_t id : indexedPrototypeChildIds[i] )
			{
				prototypeChildNames->writable().emplace_back( id );
			}
			result->writable()[prototypeNames[i]] = prototypeChildNames;
		}

		static_cast<AtomicCompoundDataPlug *>( output )->setValue( result );
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

		std::vector< int > numUnique;
		std::vector< InternedString > outputNames;
		if( perLocationHashes.size() == 0 )
		{
			// There is always an entry for the empty string, which contains the total variations
			// for all context variables combined
			result->writable()[""] = new IntData( 0 );
		}
		else
		{
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
		const ScenePath &parentPath = context->get<ScenePath>( ScenePlug::scenePathContextName );

		ConstEngineDataPtr engine = this->engine( parentPath, context );

		IECore::ConstCompoundDataPtr prototypeChildNames = this->prototypeChildNames( parentPath, context );

		PathMatcherDataPtr outputSetData = new PathMatcherData;
		PathMatcher &outputSet = outputSetData->writable();

		vector<InternedString> branchPath( { namePlug()->getValue() } );

		tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );

		for( const auto &prototypeName : engine->prototypeNames()->readable() )
		{
			branchPath.resize( 2 );
			branchPath.back() = prototypeName;
			const ScenePlug::ScenePath &prototypeRoot = engine->prototypeRoot( prototypeName );

			const vector<InternedString> &childNames = prototypeChildNames->member<InternedStringVectorData>( prototypeName )->readable();

			tbb::spin_mutex instanceMutex;
			branchPath.emplace_back( InternedString() );
			const ThreadState &threadState = ThreadState::current();
			tbb::parallel_for( tbb::blocked_range<size_t>( 0, childNames.size() ), [&]( const tbb::blocked_range<size_t> &r )
				{
					Context::EditableScope scope( threadState );
					// As part of the setCollaborate plug machinery, we put the parentPath in the context.
					// Need to remove it before evaluating the prototype sets
					scope.remove( ScenePlug::scenePathContextName );

					for( size_t i = r.begin(); i != r.end(); ++i )
					{
						const size_t pointIndex = engine->pointIndex( childNames[i] );
						engine->setPrototypeContextVariables( pointIndex, scope );
						ConstPathMatcherDataPtr instanceSet = prototypesPlug()->setPlug()->getValue();
						PathMatcher pointInstanceSet = instanceSet->readable().subTree( prototypeRoot );

						tbb::spin_mutex::scoped_lock lock( instanceMutex );
						branchPath.back() = childNames[i];
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
		input == enginePlug() ||
		input == namePlug() ||
		input == prototypesPlug()->boundPlug() ||
		input == prototypesPlug()->transformPlug() ||
		input == prototypeChildNamesPlug() ||
		input == outPlug()->childBoundsPlug()
	;
}

void Instancer::hashBranchBound( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() < 2 )
	{
		// "/" or "/instances"
		ScenePath path = parentPath;
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
		BranchCreator::hashBranchBound( parentPath, branchPath, context, h );

		engineHash( parentPath, context, h );
		prototypeChildNamesHash( parentPath, context, h );
		h.append( branchPath.back() );

		{
			PrototypeScope scope( enginePlug(), context, parentPath, branchPath );
			prototypesPlug()->transformPlug()->hash( h );
			prototypesPlug()->boundPlug()->hash( h );
		}
	}
	else
	{
		// "/instances/<prototypeName>/<id>/..."
		PrototypeScope scope( enginePlug(), context, parentPath, branchPath );
		h = prototypesPlug()->boundPlug()->hash();
	}
}

Imath::Box3f Instancer::computeBranchBound( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	if( branchPath.size() < 2 )
	{
		// "/" or "/instances"
		ScenePath path = parentPath;
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

		ConstEngineDataPtr e = engine( parentPath, context );
		ConstCompoundDataPtr ic = prototypeChildNames( parentPath, context );
		const vector<InternedString> &childNames = ic->member<InternedStringVectorData>( branchPath.back() )->readable();

		M44f childTransform;
		Box3f childBound;
		{
			PrototypeScope scope( enginePlug(), context, parentPath, branchPath );
			childTransform = prototypesPlug()->transformPlug()->getValue();
			childBound = prototypesPlug()->boundPlug()->getValue();
		}

		typedef vector<InternedString>::const_iterator Iterator;
		typedef blocked_range<Iterator> Range;

		task_group_context taskGroupContext( task_group_context::isolated );
		return parallel_reduce(
			Range( childNames.begin(), childNames.end() ),
			Box3f(),
			[ &e, &childBound, &childTransform ] ( const Range &r, Box3f u ) {
				for( Iterator i = r.begin(); i != r.end(); ++i )
				{
					const size_t pointIndex = e->pointIndex( *i );
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
		PrototypeScope scope( enginePlug(), context, parentPath, branchPath );
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

void Instancer::hashBranchTransform( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() <= 2 )
	{
		// "/" or "/instances" or "/instances/<prototypeName>"
		BranchCreator::hashBranchTransform( parentPath, branchPath, context, h );
	}
	else if( branchPath.size() == 3 )
	{
		// "/instances/<prototypeName>/<id>"
		BranchCreator::hashBranchTransform( parentPath, branchPath, context, h );
		{
			PrototypeScope scope( enginePlug(), context, parentPath, branchPath );
			prototypesPlug()->transformPlug()->hash( h );
		}
		engineHash( parentPath, context, h );
		h.append( branchPath[2] );
	}
	else
	{
		// "/instances/<prototypeName>/<id>/..."
		PrototypeScope scope( enginePlug(), context, parentPath, branchPath );
		h = prototypesPlug()->transformPlug()->hash();
	}
}

Imath::M44f Instancer::computeBranchTransform( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
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
		{
			PrototypeScope scope( enginePlug(), context, parentPath, branchPath );
			result = prototypesPlug()->transformPlug()->getValue();
		}
		ConstEngineDataPtr e = engine( parentPath, context );
		const size_t pointIndex = e->pointIndex( branchPath[2] );
		result = result * e->instanceTransform( pointIndex );
		return result;
	}
	else
	{
		// "/instances/<prototypeName>/<id>/..."
		PrototypeScope scope( enginePlug(), context, parentPath, branchPath );
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

void Instancer::hashBranchAttributes( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() <= 1 )
	{
		// "/" or "/instances"
		h = outPlug()->attributesPlug()->defaultValue()->Object::hash();
	}
	else if( branchPath.size() == 2 )
	{
		// "/instances/<prototypeName>"
		PrototypeScope scope( enginePlug(), context, parentPath, branchPath );
		h = prototypesPlug()->attributesPlug()->hash();
	}
	else if( branchPath.size() == 3 )
	{
		// "/instances/<prototypeName>/<id>"
		BranchCreator::hashBranchAttributes( parentPath, branchPath, context, h );
		{
			ConstEngineDataPtr e = engine( parentPath, context );
			if( e->numInstanceAttributes() )
			{
				e->instanceAttributesHash( e->pointIndex( branchPath[2] ), h );
			}
		}
	}
	else
	{
		// "/instances/<prototypeName>/<id>/...
		PrototypeScope scope( enginePlug(), context, parentPath, branchPath );
		h = prototypesPlug()->attributesPlug()->hash();
	}
}

IECore::ConstCompoundObjectPtr Instancer::computeBranchAttributes( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	if( branchPath.size() <= 1 )
	{
		// "/" or "/instances"
		return outPlug()->attributesPlug()->defaultValue();
	}
	else if( branchPath.size() == 2 )
	{
		// "/instances/<prototypeName>"
		PrototypeScope scope( enginePlug(), context, parentPath, branchPath );
		return prototypesPlug()->attributesPlug()->getValue();
	}
	else if( branchPath.size() == 3 )
	{
		// "/instances/<prototypeName>/<id>"
		ConstEngineDataPtr e = engine( parentPath, context );
		if( e->numInstanceAttributes() )
		{
			return e->instanceAttributes( e->pointIndex( branchPath[2] ) );
		}
		else
		{
			return outPlug()->attributesPlug()->defaultValue();
		}
	}
	else
	{
		// "/instances/<prototypeName>/<id>/...
		PrototypeScope scope( enginePlug(), context, parentPath, branchPath );
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

void Instancer::hashBranchObject( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() <= 2 )
	{
		// "/" or "/instances" or "/instances/<prototypeName>"
		h = outPlug()->objectPlug()->defaultValue()->Object::hash();
	}
	else
	{
		// "/instances/<prototypeName>/<id>/...
		PrototypeScope scope( enginePlug(), context, parentPath, branchPath );
		h = prototypesPlug()->objectPlug()->hash();
	}
}

IECore::ConstObjectPtr Instancer::computeBranchObject( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	if( branchPath.size() <= 2 )
	{
		// "/" or "/instances" or "/instances/<prototypeName>"
		return outPlug()->objectPlug()->defaultValue();
	}
	else
	{
		// "/instances/<prototypeName>/<id>/...
		PrototypeScope scope( enginePlug(), context, parentPath, branchPath );
		return prototypesPlug()->objectPlug()->getValue();
	}
}

void Instancer::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( parent != capsuleScenePlug() && encapsulateInstanceGroupsPlug()->getValue() )
	{
		// Handling this special case here means an extra call to parentAndBranchPaths
		// when we're encapsulating and we're not inside a branch - this is a small
		// unnecessary cost, but by falling back to just using BranchCreator hashObject
		// when branchPath.size() != 2, we are able to just use all the logic from
		// BranchCreator, without exposing any new API surface
		ScenePath parentPath, branchPath;
		parentAndBranchPaths( path, parentPath, branchPath );
		if( branchPath.size() == 2 )
		{
			BranchCreator::hashBranchObject( parentPath, branchPath, context, h );
			h.append( reinterpret_cast<uint64_t>( this ) );
			/// We need to include anything that will affect how the capsule will expand.
			/// \todo Once we fix motion blur behaviour so that Capsules don't
			/// depend on the source scene's shutter settings, we should be able to omit
			/// the `dirtyCount` for `prototypesPlug()->globalsPlug()`, by summing the
			/// count for its siblings instead.
			h.append( prototypesPlug()->dirtyCount() );
			engineHash( parentPath, context, h );
			h.append( context->hash() );
			outPlug()->boundPlug()->hash( h );
			return;
		}
	}

	BranchCreator::hashObject( path, context, parent, h );
}

IECore::ConstObjectPtr Instancer::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( parent != capsuleScenePlug() && encapsulateInstanceGroupsPlug()->getValue() )
	{
		ScenePath parentPath, branchPath;
		parentAndBranchPaths( path, parentPath, branchPath );
		if( branchPath.size() == 2 )
		{
			return new Capsule(
				capsuleScenePlug(),
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
		input == prototypeChildNamesPlug() ||
		input == enginePlug()
	;
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
		// "/instances"
		BranchCreator::hashBranchChildNames( parentPath, branchPath, context, h );
		engineHash( parentPath, context, h );
	}
	else if( branchPath.size() == 2 )
	{
		// "/instances/<prototypeName>"
		BranchCreator::hashBranchChildNames( parentPath, branchPath, context, h );
		prototypeChildNamesHash( parentPath, context, h );
		h.append( branchPath.back() );
	}
	else
	{
		// "/instances/<prototypeName>/<id>/..."
		PrototypeScope scope( enginePlug(), context, parentPath, branchPath );
		h = prototypesPlug()->childNamesPlug()->hash();
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
		// "/instances"
		return engine( parentPath, context )->prototypeNames();
	}
	else if( branchPath.size() == 2 )
	{
		// "/instances/<prototypeName>"
		IECore::ConstCompoundDataPtr ic = prototypeChildNames( parentPath, context );
		return ic->member<InternedStringVectorData>( branchPath.back() );
	}
	else
	{
		// "/instances/<prototypeName>/<id>/..."
		PrototypeScope scope( enginePlug(), context, parentPath, branchPath );
		return prototypesPlug()->childNamesPlug()->getValue();
	}
}

void Instancer::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( parent != capsuleScenePlug() && encapsulateInstanceGroupsPlug()->getValue() )
	{
		ScenePath parentPath, branchPath;
		parentAndBranchPaths( path, parentPath, branchPath );
		if( branchPath.size() == 2 )
		{
			h = outPlug()->childNamesPlug()->defaultValue()->Object::hash();
			return;
		}
	}

	BranchCreator::hashChildNames( path, context, parent, h );
}

IECore::ConstInternedStringVectorDataPtr Instancer::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( parent != capsuleScenePlug() && encapsulateInstanceGroupsPlug()->getValue() )
	{
		ScenePath parentPath, branchPath;
		parentAndBranchPaths( path, parentPath, branchPath );
		if( branchPath.size() == 2 )
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

void Instancer::hashBranchSetNames( const ScenePath &parentPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	assert( parentPath.size() == 0 ); // Expectation driven by `constantBranchSetNames() == true`
	h = prototypesPlug()->setNamesPlug()->hash();
}

IECore::ConstInternedStringVectorDataPtr Instancer::computeBranchSetNames( const ScenePath &parentPath, const Gaffer::Context *context ) const
{
	assert( parentPath.size() == 0 ); // Expectation driven by `constantBranchSetNames() == true`
	return prototypesPlug()->setNamesPlug()->getValue();
}

bool Instancer::affectsBranchSet( const Gaffer::Plug *input ) const
{
	return
		input == enginePlug() ||
		input == prototypesPlug()->setPlug() ||
		input == prototypeChildNamesPlug() ||
		input == namePlug() ||
		input == setCollaboratePlug()
	;
}

void Instancer::hashBranchSet( const ScenePath &parentPath, const IECore::InternedString &setName, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	BranchCreator::hashBranchSet( parentPath, setName, context, h );

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
		scope.set( ScenePlug::scenePathContextName, parentPath );
		setCollaboratePlug()->hash( h );
	}
	else
	{
		engineHash( parentPath, context, h );
		prototypeChildNamesHash( parentPath, context, h );
		prototypesPlug()->setPlug()->hash( h );
		namePlug()->hash( h );
	}
}

IECore::ConstPathMatcherDataPtr Instancer::computeBranchSet( const ScenePath &parentPath, const IECore::InternedString &setName, const Gaffer::Context *context ) const
{
	ConstEngineDataPtr engine = this->engine( parentPath, context );

	if( engine->hasContextVariables() )
	{
		// When doing the much expensive work required when we have context variables, we try to share the
		// work between multiple threads using an internal PathMatcher plug with a TaskCollaborate policy.
		// The setCollaborate plug does all the heavy work.  It is evaluated with the parentPath in the
		// context's scenePath, and it returns a PathMatcher for the set contents of one branch.
		Context::EditableScope scope( context );
		scope.set( ScenePlug::scenePathContextName, parentPath );
		return setCollaboratePlug()->getValue();
	}

	IECore::ConstCompoundDataPtr prototypeChildNames = this->prototypeChildNames( parentPath, context );
	ConstPathMatcherDataPtr inputSet = prototypesPlug()->setPlug()->getValue();

	PathMatcherDataPtr outputSetData = new PathMatcherData;
	PathMatcher &outputSet = outputSetData->writable();

	vector<InternedString> branchPath( { namePlug()->getValue() } );

	for( const auto &prototypeName : engine->prototypeNames()->readable() )
	{
		branchPath.resize( 2 );
		branchPath.back() = prototypeName;

		PathMatcher instanceSet = inputSet->readable().subTree( engine->prototypeRoot( prototypeName ) );

		const vector<InternedString> &childNames = prototypeChildNames->member<InternedStringVectorData>( prototypeName )->readable();

		branchPath.emplace_back( InternedString() );
		for( const auto &childName : childNames )
		{
			branchPath.back() = childName;
			outputSet.addPaths( instanceSet, branchPath );
		}
	}

	return outputSetData;
}

void Instancer::hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( parent != capsuleScenePlug() && encapsulateInstanceGroupsPlug()->getValue() )
	{
		h = inPlug()->setPlug()->hash();
		return;
	}

	BranchCreator::hashSet( setName, context, parent, h );
}

IECore::ConstPathMatcherDataPtr Instancer::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( parent != capsuleScenePlug() && encapsulateInstanceGroupsPlug()->getValue() )
	{
		return inPlug()->setPlug()->getValue();
	}

	return BranchCreator::computeSet( setName, context, parent );
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

IECore::ConstCompoundDataPtr Instancer::prototypeChildNames( const ScenePath &parentPath, const Gaffer::Context *context ) const
{
	ScenePlug::PathScope scope( context, parentPath );
	return prototypeChildNamesPlug()->getValue();
}

void Instancer::prototypeChildNamesHash( const ScenePath &parentPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ScenePlug::PathScope scope( context, parentPath );
	prototypeChildNamesPlug()->hash( h );
}

Instancer::PrototypeScope::PrototypeScope( const Gaffer::ObjectPlug *enginePlug, const Gaffer::Context *context, const ScenePath &parentPath, const ScenePath &branchPath )
	:	Gaffer::Context::EditableScope( context )
{
	assert( branchPath.size() >= 2 );

	set( ScenePlug::scenePathContextName, parentPath );
	ConstEngineDataPtr engine = boost::static_pointer_cast<const EngineData>( enginePlug->getValue() );
	const ScenePlug::ScenePath &prototypeRoot = engine->prototypeRoot( branchPath[1] );

	if( branchPath.size() >= 3 && engine->hasContextVariables() )
	{
		const size_t pointIndex = engine->pointIndex( branchPath[2] );
		engine->setPrototypeContextVariables( pointIndex, *this );
	}

	if( branchPath.size() > 3 )
	{
		ScenePlug::ScenePath prototypePath( prototypeRoot );
		prototypePath.reserve( prototypeRoot.size() + branchPath.size() - 3 );
		prototypePath.insert( prototypePath.end(), branchPath.begin() + 3, branchPath.end() );
		set( ScenePlug::scenePathContextName, prototypePath );
	}
	else
	{
		set( ScenePlug::scenePathContextName, prototypeRoot );
	}
}

//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/Private/IECoreScenePreview/MeshAlgo.h"

#include "IECoreScene/PrimitiveVariable.h"
#include "IECoreScene/MeshPrimitive.h"

#include "IECore/DataAlgo.h"
#include "IECore/TypeTraits.h"

#include <opensubdiv/bfr/refinerSurfaceFactory.h>
#include <opensubdiv/bfr/surface.h>
#include <opensubdiv/bfr/tessellation.h>
#include <opensubdiv/far/topologyDescriptor.h>

#include <unordered_map>
#include <numeric>

#include "fmt/format.h"

#include "tbb/parallel_for.h"

using namespace IECoreScene;
using namespace IECore;
using namespace IECoreScenePreview;

namespace OSDF = OpenSubdiv::Far;
namespace OSDB = OpenSubdiv::Bfr;

namespace {

template<class F, typename... Args>
typename std::invoke_result_t<F, Data *, Args&&...> dispatchVectorData( const IECore::Data *data, F &&functor, Args&&... args )
{
	IECore::dispatch( data,
		[&]( const auto *typedData )
		{
			using DataType = typename std::remove_cv_t< std::remove_pointer_t< decltype( typedData ) > >;
			if constexpr ( TypeTraits::IsVectorTypedData<DataType>::value )
			{
				return functor( typedData, std::forward<Args>( args )... );
			}

			throw IECore::Exception( "Invalid primitive variable type, this message should never be seen because we earlier check isPrimitiveVariableValid" );
		}
	);
}

// is_specialization_of pasted from C++ standards proposal WG21 P2098R0

template< class T, template<class...> class Primary >
struct is_specialization_of : std::false_type{};

template< template<class...> class Primary, class... Args >
struct is_specialization_of< Primary<Args...>, Primary> : std::true_type{};

template< class T , template<class...> class Primary >
inline constexpr bool is_specialization_of_v = is_specialization_of<T, Primary>::value;


// Declare a bunch of machinery for converting from Gaffer types to arrays of floats and back.
// This is pretty verbose when in practice toFloats for most types could probably be implemented
// in most current compilers by just casting the address of src as a float pointer. But doing it
// this way avoids undefined behaviour, and gives reasonable results for corner cases like doubles
// or ints.

template< class T >
constexpr int numFloatsForType()
{
	if constexpr( std::is_arithmetic_v< T > ) return 1;
	else if constexpr( std::is_same_v< T, Imath::half > ) return 1;
	else if constexpr( is_specialization_of_v< T, Imath::Vec2 > ) return 2;
	else if constexpr( is_specialization_of_v< T, Imath::Vec3 > ) return 3;
	else if constexpr( is_specialization_of_v< T, Imath::Color3 > ) return 3;
	else if constexpr( is_specialization_of_v< T, Imath::Color4 > ) return 4;
	else if constexpr( is_specialization_of_v< T, Imath::Quat > ) return 4;
	else if constexpr( is_specialization_of_v< T, Imath::Box > ) return 2 * numFloatsForType< decltype(T::min) >();
	else if constexpr( is_specialization_of_v< T, Imath::Matrix33 > ) return 9;
	else if constexpr( is_specialization_of_v< T, Imath::Matrix44 > ) return 16;
	else if constexpr( std::is_same_v< T, std::string > || std::is_same_v< T, IECore::InternedString > )
	{
		// Trying to interpolate strings is weird enough that I guess I'm OK with just returning
		// empty strings - the user can probably figure out that this means that tessellating varying strings
		// is not supported? Even though we don't store anything for strings, we return 1 to avoid confusing
		// the compiler with a zero-length buffer.
		return 1;
	}
}

template< class T >
void toFloats( const T& src, float *v )
{
	if constexpr( std::is_arithmetic_v< T > )
	{
		v[0] = src;
	}
	else if constexpr( std::is_same_v< T, Imath::half > )
	{
		v[0] = src;
	}
	else if constexpr( is_specialization_of_v< T, Imath::Vec2 > )
	{
		v[0] = src.x;
		v[1] = src.y;
	}
	else if constexpr( is_specialization_of_v< T, Imath::Vec3 > )
	{
		v[0] = src.x;
		v[1] = src.y;
		v[2] = src.z;
	}
	else if constexpr( is_specialization_of_v< T, Imath::Color3 > )
	{
		v[0] = src.x;
		v[1] = src.y;
		v[2] = src.z;
	}
	else if constexpr( is_specialization_of_v< T, Imath::Color4 > )
	{
		v[0] = src.r;
		v[1] = src.g;
		v[2] = src.b;
		v[3] = src.a;
	}
	else if constexpr( is_specialization_of_v< T, Imath::Quat > )
	{
		v[0] = src.r;
		v[1] = src.v.x;
		v[2] = src.v.y;
		v[3] = src.v.z;
	}
	else if constexpr( is_specialization_of_v< T, Imath::Box > )
	{
		using VT = decltype(T::min);
		toFloats<VT>( src.min, v );
		toFloats<VT>( src.max, v + numFloatsForType<VT>() );
	}
	else if constexpr( is_specialization_of_v< T, Imath::Matrix33 > )
	{
		v[0] = src[0][0];
		v[1] = src[0][1];
		v[2] = src[0][2];
		v[3] = src[1][0];
		v[4] = src[1][1];
		v[5] = src[1][2];
		v[6] = src[2][0];
		v[7] = src[2][1];
		v[8] = src[2][2];
	}
	else if constexpr( is_specialization_of_v< T, Imath::Matrix44 > )
	{
		v[0]  = src[0][0];
		v[1]  = src[0][1];
		v[2]  = src[0][2];
		v[3]  = src[0][3];
		v[4]  = src[1][0];
		v[5]  = src[1][1];
		v[6]  = src[1][2];
		v[7]  = src[1][3];
		v[8]  = src[2][0];
		v[9]  = src[2][1];
		v[10] = src[2][2];
		v[11] = src[2][3];
		v[12] = src[3][0];
		v[13] = src[3][1];
		v[14] = src[3][2];
		v[15] = src[3][3];
	}
	else if constexpr( std::is_same_v< T, std::string > || std::is_same_v< T, IECore::InternedString > )
	{
		// Ignore strings
	}
}

template< class T >
T fromFloats( float *v )
{
	// Special case for integers to get more accuracy by rounding.
	if constexpr( std::is_integral_v< T > ) return T( std::round( *v ) );
	else if constexpr( std::is_arithmetic_v< T > ) return T( *v );
	else if constexpr( std::is_same_v< T, Imath::half > ) return T( *v );
	else if constexpr( is_specialization_of_v< T, Imath::Vec2 > ) return T( v[0], v[1] );
	else if constexpr( is_specialization_of_v< T, Imath::Vec3 > ) return T( v[0], v[1], v[2] );
	else if constexpr( is_specialization_of_v< T, Imath::Color3 > ) return T( v[0], v[1], v[2] );
	else if constexpr( is_specialization_of_v< T, Imath::Color4 > ) return T( v[0], v[1], v[2], v[3] );
	else if constexpr( is_specialization_of_v< T, Imath::Quat > ) return T( v[0], v[1], v[2], v[3] );
	else if constexpr( is_specialization_of_v< T, Imath::Box > )
	{
		using VT = decltype(T::min);
		return T( fromFloats<VT>( v ), fromFloats<VT>( v + numFloatsForType<VT>() ) );
	}
	else if constexpr( is_specialization_of_v< T, Imath::Matrix33 > )
	{
		return T( v[0], v[1], v[2], v[3], v[4], v[5], v[6], v[7], v[8] );
	}
	else if constexpr( is_specialization_of_v< T, Imath::Matrix44 > )
	{
		return T( v[0], v[1], v[2], v[3], v[4], v[5], v[6], v[7], v[8], v[9], v[10], v[11], v[12], v[13], v[14], v[15] );
	}
	else if constexpr( std::is_same_v< T, std::string > || std::is_same_v< T, IECore::InternedString > )
	{
		return T();
	}
}

// Translate topology, crease, and corner data from an IECore::MeshPrimitive into the opensubdiv format.
void setTopologyCreasesAndCorners( OSDF::TopologyDescriptor &desc, const IECoreScene::MeshPrimitive &inputMesh, std::vector<int> &expandedIds, std::vector<float> &expandedSharpnesses )
{
	desc.numVertices = inputMesh.variableSize( PrimitiveVariable::Vertex );
	desc.numFaces = inputMesh.variableSize( PrimitiveVariable::Uniform );
	desc.numVertsPerFace = inputMesh.verticesPerFace()->readable().data();
	desc.vertIndicesPerFace = inputMesh.vertexIds()->readable().data();

	const IECore::IntVectorData *cornerIdsData = inputMesh.cornerIds();
	const std::vector<int> &cornerIds = cornerIdsData->readable();

	const IECore::FloatVectorData *cornerSharpnessesData = inputMesh.cornerSharpnesses();
	const std::vector<float> &cornerSharpnesses = cornerSharpnessesData->readable();

	if( !cornerIds.empty() && !cornerSharpnesses.empty() )
	{
		desc.numCorners = cornerIds.size();
		desc.cornerVertexIndices = cornerIds.data();
		desc.cornerWeights = cornerSharpnesses.data();
	}

	const IECore::IntVectorData *creaseLengthsData = inputMesh.creaseLengths();
	const std::vector<int> creaseLengths = creaseLengthsData->readable();

	if( !creaseLengths.empty() )
	{
		const IECore::FloatVectorData *creaseSharpnessesData = inputMesh.creaseSharpnesses();
		const std::vector<float> creaseSharpnesses = creaseSharpnessesData->readable();

		const IECore::IntVectorData *creaseIdsData = inputMesh.creaseIds();
		const std::vector<int> creaseIds = creaseIdsData->readable();

		// Cortex stores crease edges in a compact way where multiple edges can
		// be part of a crease. OpenSubdiv expects us to provide vertex pairs,
		// though, so we need to assemble those from the more compact
		// representation.

		size_t requiredSize = std::accumulate( creaseLengths.begin(), creaseLengths.end(), 0 ) - creaseLengths.size();
		expandedIds.reserve( requiredSize * 2 );
		expandedSharpnesses.reserve( requiredSize );

		int offset = 0;
		int numCreases = 0;
		for( size_t i = 0; i < creaseLengths.size(); ++i )
		{
			int length = creaseLengths[i];

			for( int j = 1; j < length; ++j, ++numCreases )
			{
				expandedIds.push_back( creaseIds[offset + j - 1] );
				expandedIds.push_back( creaseIds[offset + j] );

				expandedSharpnesses.push_back( creaseSharpnesses[i] );
			}

			offset += length;
		}

		desc.numCreases = numCreases;
		desc.creaseVertexIndexPairs = expandedIds.data();
		desc.creaseWeights = expandedSharpnesses.data();
	}
}

// Store a pair of a vertex index and a facevarying index
// This is used to deduplicated any facevarying indices that belong to different vertices.
struct FaceVaryingMatch
{
	FaceVaryingMatch( int vi, int fvi ) :
		vertexIndex( vi ), faceVaryingIndex( fvi )
	{
	}

	bool operator==( const FaceVaryingMatch &other ) const
	{
		return vertexIndex == other.vertexIndex && faceVaryingIndex == other.faceVaryingIndex;
	}

	int vertexIndex;
	int faceVaryingIndex;
};

// Hash function for above
struct FaceVaryingMatchHash
{
	std::size_t operator()( const FaceVaryingMatch& k ) const
	{
		std::size_t seed = k.vertexIndex;
		seed += ((size_t)k.faceVaryingIndex) << 32;
		return seed;
	}
};

// A PrimvarSetup stores the data for a primvar we need to interpolate. In particular, during construction it
// takes care of making sure faceVarying indices are correct, and it has storage for the outputs, which
// is allocated when allocateOutputs is called after the first multithreaded pass where we collect the sizes
// of everything.

struct PrimvarSetup
{
	PrimvarSetup(
		const std::string &name, const PrimitiveVariable &var,
		const std::vector<int> *vertexIds = nullptr
	)
		: m_name( name ), m_var( var ), m_outIndicesWritable( nullptr )
	{
		if( var.interpolation == PrimitiveVariable::FaceVarying )
		{
			// Handle faceVarying primvars without indices
			if( !var.indices )
			{
				// We're missing out on some optimization here on meshes with multiple unindexed faceVarying
				// primvars. We could allocate these indices just once, and perhaps more importantly, we could
				// use a single faceVarying channel in OpenSubdiv whenever two facevarying primvars have the
				// same indices. But in practice, faceVaryings are usually going to be UVs, and UVs usually do
				// have shared vertices, and when there are multiple UVs, it's usually because the vertex
				// splitting is different. So to keep the code simple, we just leverage the same override
				// indices data structure we use when splitting facevertices that are reused between different
				// vertices.
				m_overrideFaceVaryingIndices.reserve( vertexIds->size() );
				for( unsigned int i = 0; i < vertexIds->size(); i++ )
				{
					m_overrideFaceVaryingIndices.push_back( i );
				}
				return;
			}

			// If we have indices, then we need to double check that they aren't being shared between unrelated
			// vertices. This could happen, for example, if you nicely UV a tire, then make 2 copies of it,
			// merge them into the same mesh, and weld matching UVs. By default, this would result in
			// something effectively non-manifold - instead of 4 faces meeting at each UV, 8 faces meet
			// at each UV. Neither our code or OpenSubdiv like this very much. We assume in this case that
			// the desired result is to make a copy of the UV for each independent vertex in space that uses it.
			const int numBaseElements = IECore::size( var.data.get() );
			std::vector< int > firstVertexForFaceVarying( numBaseElements, -1 );
			std::unordered_map< FaceVaryingMatch, int, FaceVaryingMatchHash > faceVaryingMatches;

			const std::vector<int> &fvIndices = var.indices->readable();

			bool overriding = false;
			for( unsigned int i = 0; i < vertexIds->size(); i++ )
			{
				int faceVaryingIndex = fvIndices[i];

				// We start by looking up in a vector mapping faceVarying indices to their vertex.
				// In the common case where faceVarying indices are not shared between vertices, each faceVertex
				// will get a single vertex, and we will never have to put anything in the more expensive
				// faceVaryingMatches map.

				if( firstVertexForFaceVarying[ faceVaryingIndex ] == -1 )
				{
					firstVertexForFaceVarying[ faceVaryingIndex ] = (*vertexIds)[i];
				}
				else if( firstVertexForFaceVarying[ faceVaryingIndex ] != (*vertexIds)[i] )
				{
					// We've found a faceVertex that is used with 2 different vertices. We're going to need
					// to populate the override indices

					if( !overriding )
					{
						// If we haven't allocated the override indices yet, start by filling in all the indices
						// we've already processed ( which didn't have any conflicts )
						m_overrideFaceVaryingIndices.reserve( vertexIds->size() );
						m_overrideFaceVaryingIndices.insert( m_overrideFaceVaryingIndices.begin(), &fvIndices[0], &fvIndices[ i ] );
						overriding = true;
					}

					// Indices greater than then original number of base elements are used to indicate that the
					// index has been duplicated to avoid bad sharing. These higher indices will have
					// numBaseElements subtracted, and then be indexed into m_deduplicatedReindex in order to get
					// the actual index.
					//
					// We try the emplace - if we've already seen a version of this faceVarying index for this
					// vertex, then we'll get that instead.
					auto [ it, success ] = faceVaryingMatches.emplace( FaceVaryingMatch( (*vertexIds)[i], fvIndices[i] ), (int)( numBaseElements + m_deduplicatedReindex.size() ) );
					if( success )
					{
						m_deduplicatedReindex.push_back( faceVaryingIndex );
					}

					faceVaryingIndex = it->second;
				}

				if( overriding )
				{
					m_overrideFaceVaryingIndices.push_back( faceVaryingIndex );
				}
			}
		}
	}

	void allocateOutputs( int outputSize, int outputIndexSize )
	{
		// NOTE : This would logically be an excellent place for using a vector type that doesn't force
		// initialization for outData and outIndicesData - we need to allocate all the memory so that
		// different threads can indepedently fill it.
		//
		// I haven't gone and done the podVectorResizeUninitialized trick here because I was unable to
		// demonstrate any measurable performance improvement ( there's maybe something in the 0.3% range,
		// but that could be noise ). So probably not worth making things more complicated at the moment,
		// but it would be nice to have a better vector type.

		// Uniform primitive variables are quite different - they never need to be interpolated, so we can
		// just reuse the input data, and only need to write new indices.
		if( m_var.interpolation != PrimitiveVariable::Uniform )
		{
			dispatchVectorData(
				m_var.data.get(),
				[&]( const auto *typedData ) -> void
				{
					using DataType = typename std::decay_t< decltype( *typedData ) >;
					typename DataType::Ptr outData = new DataType();
					outData->writable().resize( outputSize );
					m_outWritable = &( outData->writable() );
					m_outData = outData;
				}
			);

			IECore::setGeometricInterpretation( m_outData.get(), IECore::getGeometricInterpretation( m_var.data.get() ) );
		}

		if( outputIndexSize > 0 )
		{
			m_outIndicesData = new IntVectorData();
			m_outIndicesData->writable().resize( outputIndexSize );
			m_outIndicesWritable = m_outIndicesData->writable().data();
		}
	}

	std::string m_name;
	const PrimitiveVariable &m_var;

	std::vector<int> m_overrideFaceVaryingIndices;
	std::vector<int> m_deduplicatedReindex;

	IECore::DataPtr m_outData;
	void* m_outWritable;
	IECore::IntVectorDataPtr m_outIndicesData;
	int* m_outIndicesWritable;
};

// Create PrimvarSetup's for the variables we need to interpolate
void setupVariables(
	const MeshPrimitive &mesh, bool calculateNormals,
	PrimvarSetup &posPrimvarSetup,
	std::vector< PrimvarSetup > &vertexPrimvarSetups,
	std::vector< PrimvarSetup > &uniformPrimvarSetups,
	std::vector< PrimvarSetup > &faceVaryingPrimvarSetups,
	const IECore::Canceller *canceller
)
{
	const std::vector<int> &vertexIds = mesh.vertexIds()->readable();

	for( PrimitiveVariableMap::const_iterator it = mesh.variables.begin(); it != mesh.variables.end(); ++it )
	{
		Canceller::check( canceller );
		if( it->first == "P" || ( calculateNormals && it->first == "N" ) )
		{
			// Don't set up variables that are handled by special cases
			continue;
		}

		if( !mesh.isPrimitiveVariableValid( it->second) )
		{
			throw Exception( "Cannot tessellate invalid primvar: \"" + it->first + "\"" );
		}

		if( it->second.interpolation == PrimitiveVariable::Constant )
		{
			// No need to do any setup, we just copy them across at the end.
		}
		else if( it->second.interpolation == PrimitiveVariable::FaceVarying )
		{
			faceVaryingPrimvarSetups.push_back( PrimvarSetup( it->first, it->second, &vertexIds ) );
		}
		else if( it->second.interpolation == PrimitiveVariable::Vertex )
		{
			vertexPrimvarSetups.push_back( PrimvarSetup( it->first, it->second ) );
		}
		else if( it->second.interpolation == PrimitiveVariable::Uniform )
		{
			uniformPrimvarSetups.push_back( PrimvarSetup( it->first, it->second ) );
		}
	}
}

// Convert a vector of counts into a vector of offsets
int intVectorAccumulate( std::vector<int> &v )
{
	int accum = 0;
	for( int &o : v )
	{
		int prevAccum = accum;
		accum += o;
		o = prevAccum;
	}
	return accum;
}


// Define a thread-safe SurfaceFactory using tbb mutexes
struct MutexReadGuard
{
	MutexReadGuard( tbb::spin_rw_mutex &m )
		: m_guard( m, false )
	{
	}

	tbb::spin_rw_mutex::scoped_lock m_guard;
};

struct MutexWriteGuard
{
	MutexWriteGuard( tbb::spin_rw_mutex &m )
		: m_guard( m, true )
	{
	}

	tbb::spin_rw_mutex::scoped_lock m_guard;
};

typedef OSDB::SurfaceFactoryCacheThreaded< tbb::spin_rw_mutex, MutexReadGuard, MutexWriteGuard > SurfaceFactoryCache;
typedef OSDB::RefinerSurfaceFactory< SurfaceFactoryCache > SurfaceFactory;


// In order to output a watertight mesh, we need to share output vertices and edges where the input vertices
// and edges are shared. To do this, we assign each edge and vertex one of the faces it touches as its owner.

// Store which face owns a vertex, and the offset into the tessellated vertices for that face where the
// output vertex corresponding to this input vertex is found.
struct VertexOwner
{
	int face;
	int offset;
};

// Store which face owns an edge, and the offset into the tessellated vertices for that face where the
// list of output vertices corresponding to this edge are found.
struct EdgeOwner
{
	int face;
	int offset;

	// Stores whether the face that generates the output vertices for this edge has a lower vertex index
	// first for this edge ( this tells us when we need to flip the order of the vertices along the edge
	// when we're using them in an adjacent face ).
	bool direction;
};

// Store all the topological information needed to allocate and correctly connect up a primvar. This
// is gathered on the first parallel pass, then used to allocate the outputs, and then used during the
// final paralllel pass to put the output data in the right places.
//
// All vertex primvars share the same topology, but each FaceVarying primvar needs its own.
struct PrimvarTopology
{
	PrimvarTopology( const OSDF::TopologyLevel &meshTopology, int faceVaryingChannel = -1 ) :
		m_mesh( meshTopology ), m_faceVaryingChannel( faceVaryingChannel )
	{
		m_facePointOffsets.resize( m_mesh.GetNumFaces() );
		m_vertexOwners.resize(
			faceVaryingChannel == -1 ? m_mesh.GetNumVertices() : m_mesh.GetNumFVarValues( faceVaryingChannel ),
			{ -1, -1 }
		);
		m_edgeOwners.resize( m_mesh.GetNumEdges(), { -1, -1, false } );
	}

	inline void addFace( int faceIndex, const OSDB::Tessellation &tessPattern, const OSDF::ConstIndexArray &fVerts, const OSDF::ConstIndexArray &fEdges, int tessUniformRate )
	{
		OSDF::ConstIndexArray fvarValues;
		if( m_faceVaryingChannel != -1 )
		{
			fvarValues = m_mesh.GetFaceFVarValues( faceIndex, m_faceVaryingChannel );
		}

		int ownedBoundaryPoints = 0;
		for( int i = 0; i < fVerts.size(); ++i )
		{

			OSDF::Index vertIndex = fVerts[i];

			bool isVertexOwner = true;
			if( m_faceVaryingChannel == -1 || m_mesh.DoesVertexFVarTopologyMatch( vertIndex, m_faceVaryingChannel ) )
			{
				// For vertex primvar, or faceVarying primvars at verts where the faceVarying topology
				// matches vertex topology, the owner is whichever face touching this vertex has the lowest
				// index.
				for( OSDF::Index f : m_mesh.GetVertexFaces( vertIndex ) )
				{
					isVertexOwner &= f >= faceIndex;
				}
			}
			else
			{
				OSDF::ConstIndexArray adjFaces = m_mesh.GetVertexFaces( vertIndex );
				OSDF::ConstLocalIndexArray adjFaceLocalIndices = m_mesh.GetVertexFaceLocalIndices( vertIndex );

				// At a split vertex for a faceVarying primvar, we have to check the faceVarying indices of
				// adjacent faces at this vertex
				for( int j = 0; j < adjFaces.size(); j++ )
				{
					if( fvarValues[i] == m_mesh.GetFaceFVarValues( adjFaces[j], m_faceVaryingChannel )[ adjFaceLocalIndices[j] ] )
					{
						isVertexOwner &= adjFaces[j] >= faceIndex;
					}
				}
			}

			if( isVertexOwner )
			{
				// For faceVarying primitive variables, vertex ownership is stored per-faceVarying index
				// ( If there are two different faceVarying values at a Vertex, then we need two different faces
				// to be responsible for computing that vertex )
				int vertOwnerIndex = m_faceVaryingChannel == -1 ? vertIndex : fvarValues[i];

				// Even if this face is the owner of the vertex, we need to check that we haven't already added
				// it. This handles the non-manifold case where a face contains the same vertex multiple times.
				if( m_vertexOwners[vertOwnerIndex].face == -1 )
				{
					m_vertexOwners[vertOwnerIndex].face = faceIndex;
					m_vertexOwners[vertOwnerIndex].offset = ownedBoundaryPoints;
					ownedBoundaryPoints++;
				}
			}

			OSDF::Index edgeIndex = fEdges[i];
			int edgeRate = tessUniformRate;
			if( edgeRate > 1 )
			{
				int pointsPerEdge = edgeRate - 1;

				bool isEdgeOwner = true;
				if( m_faceVaryingChannel != -1 && !m_mesh.DoesEdgeFVarTopologyMatch( edgeIndex, m_faceVaryingChannel ) )
				{
					// If the edge is split by a facevarying primvar, we don't set an owner, which actually
					// means every face owns its own copy of the edge.
					isEdgeOwner = false;
					ownedBoundaryPoints += pointsPerEdge;
				}
				else
				{
					for( OSDF::Index f : m_mesh.GetEdgeFaces( edgeIndex ) )
					{
						isEdgeOwner &= f >= faceIndex;
					}
				}

				if( isEdgeOwner )
				{
					m_edgeOwners[edgeIndex].face = faceIndex;
					m_edgeOwners[edgeIndex].offset = ownedBoundaryPoints;
					m_edgeOwners[edgeIndex].direction = fVerts[ ( i + 1 ) % fVerts.size() ] > vertIndex;
					ownedBoundaryPoints += pointsPerEdge;
				}
			}
		}

		const int unownedBoundaryPoints = tessPattern.GetNumBoundaryCoords() - ownedBoundaryPoints;
		m_facePointOffsets[ faceIndex ] = tessPattern.GetNumCoords() - unownedBoundaryPoints;
	}

	// Must be called after all faces have had their points counted during the first parallel loop,
	// but before we use these offsets in the second parallel loop
	int accumulateFacePoints()
	{
		return intVectorAccumulate( m_facePointOffsets );
	}

	const OSDF::TopologyLevel &m_mesh;
	const int m_faceVaryingChannel;

	std::vector<int> m_facePointOffsets;
	std::vector<VertexOwner> m_vertexOwners;
	std::vector<EdgeOwner> m_edgeOwners;
};

// Call OpenSubdiv's Evaluate function, and store the result in one of our types
template < class T >
void evaluateSurface(
	const OSDB::Surface<float> &surface, const float *patchPointData, const float *uv,
	int outIndex, std::vector<T> &out, T *outNormals = nullptr
)
{
	constexpr int typeSize = numFloatsForType<T>();

	float buffer[typeSize];

	if( outNormals )
	{
		float du[typeSize];
		float dv[typeSize];

		surface.Evaluate( uv, patchPointData, typeSize, buffer, du, dv );

		// We know that we only pass outNormals for P, which is required to be V3f, so it's not a problem
		// that other types don't define cross or normalized
		if constexpr( std::is_same_v< T, Imath::V3f > )
		{
			outNormals[ outIndex ] = fromFloats<T>( du ).cross( fromFloats<T>( dv ) ).normalized();
		}
	}
	else
	{
		surface.Evaluate( uv, patchPointData, typeSize, buffer );
	}

	out[ outIndex ] = fromFloats<T>( buffer );
}

// Data that is only needed while tessellating a face, but can then be discarded. We don't want to reallocate
// it freshly for every face, so we instead store it once per thread.
struct TessellationTempBuffers
{
	OSDB::Surface<float> faceVaryingSurface;
	std::vector<int> patchPointIndices;
	std::vector<float> patchPoints;
	std::vector<int> boundaryIndices;
	std::vector<int> collapseIndices;
};


// Produce all the tessellated results for one primitive for one face.
//
// This code is adapted from OpenSubdiv::Bfr tutorial 2.2
// https://graphics.pixar.com/opensubdiv/docs/bfr_tutorial_2_2.html
//
// It has been fairly heavily modified to work with Gaffer's data
// structures, and also to handle non-manifold geo, and also to
// output triangles when OpenSubdiv emits a triangle, rather than
// degenerate quads.
template <class T>
void tessellateVariable(
	const OSDB::Surface<float> &surface, int faceIndex,
	const OSDF::ConstIndexArray &fVerts, const OSDF::ConstIndexArray &fEdges,
	int tessUniformRate, const OSDB::Tessellation &tessPattern, const std::vector< Imath::V2f > &coords,
	const PrimvarTopology &primvarTopology,
	TessellationTempBuffers &buffers,
	PrimvarSetup &setup,
	const IECore::Canceller *canceller,
	int outIndicesIndex, int *outVerticesPerFace = nullptr, T *outNormals = nullptr
)
{
	std::vector<T> &out = *(std::vector<T>*)(setup.m_outWritable);
	const int typeSize = numFloatsForType<T>();
	buffers.patchPointIndices.resize( surface.GetNumControlPoints() );
	buffers.patchPoints.resize( surface.GetNumPatchPoints() * typeSize );

	// Get the control points for the patches for this face.
	// We get the indices from OpenSubdiv, but then access the control points ourselves, so we
	// can take into account our indexing.

	surface.GetControlPointIndices( buffers.patchPointIndices.data() );
	if( setup.m_var.interpolation != PrimitiveVariable::FaceVarying )
	{
		PrimitiveVariable::IndexedView<T> indexedView( setup.m_var );

		// Use the IndexedView to get correct value for the control points whether or not they are indexed.
		for( unsigned int i = 0; i < buffers.patchPointIndices.size(); i++ )
		{
			toFloats<T>( indexedView[ buffers.patchPointIndices[i] ], &buffers.patchPoints[i * typeSize] );
		}
	}
	else
	{
		// For FaceVarying primitive variables, any indices are handled by OSD's topology, so we need
		// to not apply the indices here.
		const std::vector< T > &d =
			IECore::runTimeCast< const IECore::TypedData<std::vector<T> > >( setup.m_var.data.get() )->readable();

		if( !setup.m_deduplicatedReindex.size() )
		{
			for( unsigned int i = 0; i < buffers.patchPointIndices.size(); i++ )
			{
				toFloats<T>( d[ buffers.patchPointIndices[i] ], &buffers.patchPoints[i * typeSize] );
			}
		}
		else
		{
			// Though if we have a special reindex to handle deduplication, we do need to apply that
			int numBaseElements = d.size();
			for( unsigned int i = 0; i < buffers.patchPointIndices.size(); i++ )
			{
				int index = buffers.patchPointIndices[i];
				if( index >= numBaseElements )
				{
					index = setup.m_deduplicatedReindex[ index - numBaseElements ];
				}

				toFloats<T>( d[ index ], &buffers.patchPoints[i * typeSize] );
			}
		}
	}


	// Some of the patch points come from the control points, the remainder are derived from those by
	// this function.
	surface.ComputePatchPoints( buffers.patchPoints.data(), typeSize );

	// All the tricky parts of the tessellation are about the boundaries.
	//
	// OpenSubdiv gives the boundary coords first in the `coords` list.
	// We traverse the boundary first, either outputting the correct
	// tessellated values, or identifying that the value is owned by
	// another face, and outputting the right index to point to the
	// owner.

	const int numOutCoords = tessPattern.GetNumCoords();
	const int numBoundaryCoords = tessPattern.GetNumBoundaryCoords();
	const int numInteriorCoords = numOutCoords - numBoundaryCoords;

	const Imath::V2f *tessBoundaryCoords = &coords[0];
	const Imath::V2f *tessInteriorCoords = &coords[numBoundaryCoords];

	if( setup.m_outIndicesWritable )
	{
		buffers.boundaryIndices.resize(numBoundaryCoords);
	}


	OSDF::ConstIndexArray fvarValues;
	if( primvarTopology.m_faceVaryingChannel != -1 )
	{
		fvarValues = primvarTopology.m_mesh.GetFaceFVarValues( faceIndex, primvarTopology.m_faceVaryingChannel );
	}

	// Walk around the face, inspecting each vertex and outgoing edge,
	int boundaryIndex = 0;
	int outOffset = primvarTopology.m_facePointOffsets[faceIndex];
	for( int i = 0; i < fVerts.size(); ++i )
	{
		Canceller::check( canceller );
		// First handle a vertex

		// For faceVarying primitive variables, vertex ownership is stored per-faceVarying index
		int vertOwnerIndex = primvarTopology.m_faceVaryingChannel == -1 ? fVerts[i] : fvarValues[i];

		const VertexOwner &vOwner = primvarTopology.m_vertexOwners[ vertOwnerIndex ];
		if( vOwner.face == faceIndex && vOwner.offset == outOffset - primvarTopology.m_facePointOffsets[faceIndex] )
		{
			// We are the owner - evaluate the primvar at this corner
			evaluateSurface<T>(
				surface, buffers.patchPoints.data(), (float*)&tessBoundaryCoords[ boundaryIndex ],
				outOffset++, out, outNormals
			);
		}

		if( setup.m_outIndicesWritable )
		{
			// Output vertex index to the list of boundary indices.
			buffers.boundaryIndices[boundaryIndex] = primvarTopology.m_facePointOffsets[ vOwner.face ] + vOwner.offset;
		}

		boundaryIndex++;

		OSDF::Index edgeIndex = fEdges[i];
		int edgeRate = tessUniformRate;

		// Now handle an edge

		if( edgeRate > 1 )
		{
			int pointsPerEdge = edgeRate - 1;

			const EdgeOwner &eOwner = primvarTopology.m_edgeOwners[ edgeIndex ];

			// When the owning face is left at -1, that means the edge is split, and each adjacent face
			// owns its own copy
			if( eOwner.face == -1 || eOwner.face == faceIndex )
			{
				// We are the owner, evaluate the primvar at each point on this edge
				for (int j = 0; j < pointsPerEdge; ++j )
				{
					evaluateSurface<T>(
						surface, buffers.patchPoints.data(), (float*)&tessBoundaryCoords[ boundaryIndex + j ],
						outOffset++, out, outNormals
					);
				}
			}

			if( setup.m_outIndicesWritable )
			{
				int edgeStart;
				bool directionMatches;

				if( eOwner.face == -1 || eOwner.face == faceIndex )
				{
					// We are the owner, just write out the indices for the points we just wrote
					edgeStart = outOffset - pointsPerEdge;
					directionMatches = true;
				}
				else
				{
					// Another face owns this edge - grab the index offsets from the owner.
					edgeStart = primvarTopology.m_facePointOffsets[ eOwner.face ] + eOwner.offset;

					// Check if we're traversing the edge in the same direction as the owner.
					// In a manifold mesh, this is always false, since each edge is joined to 2 faces, which
					// traverse it clockwise on different sides. But it doesn't cost much to get it right in
					// the non-manifold case.
					directionMatches = eOwner.direction == ( fVerts[ ( i + 1 ) % fVerts.size() ] > fVerts[i] );
				}

				if( directionMatches )
				{
					// Add the points to the boundary - this is the same whether we just wrote them, or
					// whether this is a weird non-manifold join to an existing edge.
					for (int j = 0; j < pointsPerEdge; ++j)
					{
						buffers.boundaryIndices[ boundaryIndex + j ] = edgeStart + j;
					}
				}
				else
				{
					// Assign shared points to boundary in reverse order:
					for (int j = 0; j < pointsPerEdge; ++j)
					{
						buffers.boundaryIndices[ boundaryIndex + j ] = edgeStart + pointsPerEdge - 1 - j;
					}
				}
			}

			boundaryIndex += pointsPerEdge;
		}
	}

	// Evaluate any interior points unique to this face -- appending
	// them to those shared points computed above for the boundary.
	// This is easy, because interior points are never shared.
	if( numInteriorCoords )
	{
		for (int i = 0; i < numInteriorCoords; ++i)
		{
			Canceller::check( canceller );
			evaluateSurface<T>(
				surface, buffers.patchPoints.data(), (float*)&tessInteriorCoords[ i ],
				outOffset++, out, outNormals
			);
		}
	}

	if( setup.m_outIndicesWritable )
	{
		// Write out the vertex indices for the faces coming from all our tessellated facets.

		// If we are writing out quad facets, but the face is irregular, and the tessellation rate is odd,
		// then OpenSubDiv will write out some quad facets that are actually triangles, labelled with one vert
		// set to -1. In order to output accurate topology, we need to collapse this list, removing -1s, and
		// adjusting the vertex counts of corresponding faces.
		const bool needsCollapse = tessPattern.GetFacetSize() == 4 && fVerts.size() != 4 && ( tessUniformRate & 1 );

		int *outIndices;
		if( needsCollapse )
		{
			// If we need to collapse vertex ids, then we have to put the vertex ids in a temporary buffer
			// instead of writing straight to the final buffer.
			buffers.collapseIndices.resize( tessPattern.GetNumFacets() * 4 );
			outIndices = buffers.collapseIndices.data();
		}
		else
		{
			outIndices = &setup.m_outIndicesWritable[outIndicesIndex];
		}


		int tessInteriorOffset = outOffset - numOutCoords;
		tessPattern.GetFacets( outIndices );


		// GetFacets generates coordinate indices used by the facets are local
		// to the face (i.e. they range from [0..N-1], where N is the
		// number of coordinates in the pattern) and so need to be offset
		// to refer to global vertex indices.
		//
		// Whereas the edge gets overwritten with the boundary indices we've
		// computed, which are already global. TransformFacetCoordIndices does
		// both.

		// TransformFacetCoordIndices seems to incorrectly not be labelled as const, so we cheat
		// with a const_cast
		const_cast< OSDB::Tessellation* >( &tessPattern )->TransformFacetCoordIndices(
			outIndices, buffers.boundaryIndices.data(), tessInteriorOffset
		);

		if( needsCollapse )
		{
			// If some of our quads are actually tris, we need to scan through looking for indices of -1,
			// and not copying those to the actual output. Whenever we find a -1, we decrease the
			// verticesPerFace count for the corresponding face, so that we output actual triangles,
			// instead of degenerate quads.
			for( unsigned int i = 0; i < buffers.collapseIndices.size(); i++ )
			{
				if( buffers.collapseIndices[i] != -1 )
				{
					setup.m_outIndicesWritable[outIndicesIndex++] = buffers.collapseIndices[i];
				}
				else
				{
					// Update the verticesPerFace count to handle that we've removed a vert, and this face is
					// no longer a quad.
					if( outVerticesPerFace )
					{
						outVerticesPerFace[ i / 4 ]--;
					}
				}
			}
		}
	}
}

// Output tessellations for all primvar setups for one face
void tessellateVariables(
	const SurfaceFactory &meshSurfaceFactory, const OSDB::Tessellation &tessPattern,
	int faceIndex, OSDF::ConstIndexArray fVerts, OSDF::ConstIndexArray fEdges,
	int tessUniformRate, const std::vector<Imath::V2f> &tessCoords,
	std::vector<int> &outVerticesPerFace, int faceFacetOffset, int faceFacetVertexOffset,
	const PrimvarTopology &vertexTopology, const OSDB::Surface<float> &vertexSurface,
	PrimvarSetup &posPrimvarSetup, std::vector<Imath::V3f> &outNormals,
	std::vector< PrimvarSetup > &vertexPrimvarSetups, std::vector< PrimvarSetup > &uniformPrimvarSetups,
	const std::vector< PrimvarTopology > &faceVaryingTopologies, std::vector< PrimvarSetup > &faceVaryingPrimvarSetups,
	TessellationTempBuffers &buffers,
	const IECore::Canceller *canceller
)
{
	const int numFacets = tessPattern.GetNumFacets();

	tessellateVariable<Imath::V3f>(
		vertexSurface, faceIndex, fVerts, fEdges, tessUniformRate, tessPattern, tessCoords,
		vertexTopology,
		buffers,
		posPrimvarSetup, canceller, faceFacetVertexOffset,
		&outVerticesPerFace[faceFacetOffset], outNormals.size() ? outNormals.data() : nullptr
	);

	for( PrimvarSetup &setup : vertexPrimvarSetups )
	{
		dispatchVectorData(
			setup.m_var.data.get(),
			[&]( const auto *typedData ) -> void
			{
				using ElementType = typename std::remove_pointer_t< decltype( typedData ) >::ValueType::value_type;

				tessellateVariable<ElementType>(
					vertexSurface, faceIndex, fVerts, fEdges, tessUniformRate, tessPattern, tessCoords,
					vertexTopology,
					buffers,
					setup, canceller, faceFacetVertexOffset
				);
			}
		);
	}

	for( PrimvarSetup &setup : uniformPrimvarSetups )
	{
		int uniformIndex = setup.m_var.indices ? setup.m_var.indices->readable()[faceIndex] : faceIndex;
		for( int i = 0; i < numFacets; i++ )
		{
			setup.m_outIndicesWritable[ faceFacetOffset + i ] = uniformIndex;
		}
	}

	for( unsigned int i = 0; i < faceVaryingPrimvarSetups.size(); i++ )
	{
		if( !meshSurfaceFactory.InitFaceVaryingSurface( faceIndex, &buffers.faceVaryingSurface, i ) )
		{
			continue;
		}

		dispatchVectorData(
			faceVaryingPrimvarSetups[i].m_var.data.get(),
			[&]( const auto *typedData ) -> void
			{
				using ElementType = typename std::remove_pointer_t< decltype( typedData ) >::ValueType::value_type;
				tessellateVariable<ElementType>(
					buffers.faceVaryingSurface, faceIndex, fVerts, fEdges, tessUniformRate, tessPattern, tessCoords,
					faceVaryingTopologies[i],
					buffers,
					faceVaryingPrimvarSetups[i], canceller, faceFacetVertexOffset
				);
			}
		);
	}
}

// When OpenSubdiv outputs quads, it sometimes actually makes a triangle by setting one of the 4 vertex indices
// of a quad to -1. We can currently predict exactly when this happens using these heuristics.
//
// Once we support adaptive subdivision, this logic gets a lot more complicated, and OpenSubdiv doesn't offer
// a way to query it without getting the full list of facet vertex indices - we'll probably need to either
// get the facet vertex indices an extra time during the first pass ( or get them and store them for later reuse ),
// and manually count how many -1s are in the list.
int numDegenerateQuadsInTessellation( int tessFacetSize, int nVerts, int tessUniformRate )
{
	if( tessFacetSize != 4 )
	{
		// If we're outputting triangles, then OSD never omits vertices
		return 0;
	}
	else if( nVerts == 4 || !( tessUniformRate & 1 ) )
	{
		// If the input face is a quad, or the tessellation rate is uniform and even, then OSD always outputs quads
		return 0;
	}
	else if( nVerts == 3 )
	{
		// One triangle in the center of the odd tessellation of a tri
		return 1;
	}
	else
	{
		// For other odd tessellations, we get one center cap which is triangulated.
		return nVerts;
	}
}

} // namespace

MeshPrimitivePtr MeshAlgo::tessellateMesh(
	const MeshPrimitive &inputMesh, int divisions,
	bool calculateNormals, IECore::InternedString scheme,
	const IECore::Canceller *canceller
)
{
	if( !inputMesh.verticesPerFace()->readable().size() )
	{
		return inputMesh.copy();
	}

	const int tessUniformRate = divisions + 1;

	if( !scheme.string().size() )
	{
		scheme = inputMesh.interpolation();
	}

	OpenSubdiv::Sdc::SchemeType osScheme = OpenSubdiv::Sdc::SCHEME_CATMARK;
	// \todo - use scheme name definitions from IECoreScene::MeshPrimitive once we update Cortex
	//
	// We use bilinear if the scheme is set to bilinear, or if there is no scheme specified ( which
	// is how USD represent simple polygons. Note that for historical reasons, having no scheme is
	// stored as "linear" instead of "none".
	if( scheme == "bilinear" || scheme == "linear" )
	{
		osScheme = OpenSubdiv::Sdc::SCHEME_BILINEAR;
	}
	else if( scheme == "catmullClark" )
	{
		osScheme = OpenSubdiv::Sdc::SCHEME_CATMARK;
	}
	else if( scheme == "loop" )
	{
		osScheme = OpenSubdiv::Sdc::SCHEME_LOOP;
	}
	else
	{
		throw Exception( "Unknown subdivision scheme: " + scheme.string() );
	}

	if( osScheme == OpenSubdiv::Sdc::SCHEME_LOOP && inputMesh.maxVerticesPerFace() > 3 )
	{
		throw Exception( "Loop subdivision can only be applied to triangle meshes ");
	}

	// Create PrimvarSetups for all the primvars we need to interpolate

	if( !inputMesh.variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex ) )
	{
		throw IECore::Exception( "Mesh must have V3f P primvar." );
	}
	if( !inputMesh.isPrimitiveVariableValid( inputMesh.variables.at( "P" ) ) )
	{
		throw IECore::Exception( "P primvar is invalid." );
	}
	PrimvarSetup posPrimvarSetup( "P", inputMesh.variables.at( "P" ) );

	std::vector< PrimvarSetup > vertexPrimvarSetups;
	std::vector< PrimvarSetup > uniformPrimvarSetups;
	std::vector< PrimvarSetup > faceVaryingPrimvarSetups;
	setupVariables(
		inputMesh, calculateNormals,
		posPrimvarSetup, vertexPrimvarSetups, uniformPrimvarSetups, faceVaryingPrimvarSetups, canceller
	);


	// These subdiv options hold all the tricky boundary settings
	OpenSubdiv::Sdc::Options options;
	options.SetVtxBoundaryInterpolation(OpenSubdiv::Sdc::Options::VTX_BOUNDARY_EDGE_AND_CORNER);

	// Choosing a reasonable default here is actually tricky - the options are pretty confusing, and
	// don't match between different packages ( and it seems like often artists may not actually be
	// getting exactly what they expect ).
	// FVAR_LINEAR_BOUNDARIES, which forces all boundaries to be linear, would seem to make sense, but
	// is actually a terrible option - it turns some concave corners inside-out, and is 30% slower.
	// FVAR_LINEAR_CORNERS_ONLY could be a good option - it would match Arnold's default.
	// But we've chosen FVAR_LINEAR_CORNERS_PLUS1 to match USD ( Which unfortunately isn't supported
	// by Arnold, but is hopefully close enough to what artists expect ).
	options.SetFVarLinearInterpolation( OpenSubdiv::Sdc::Options::FVAR_LINEAR_CORNERS_PLUS1 );

	// The TopologyDescriptor is how we pass all our mesh topology to OpenSubdiv

	typedef OSDF::TopologyDescriptor Descriptor;
	Descriptor desc;

	std::vector<int> creaseIdsBuffer;
	std::vector<float> creaseSharpnessesBuffer;
	setTopologyCreasesAndCorners( desc, inputMesh, creaseIdsBuffer, creaseSharpnessesBuffer );

	std::vector<Descriptor::FVarChannel> channels( faceVaryingPrimvarSetups.size() );
	desc.numFVarChannels = faceVaryingPrimvarSetups.size();

	for( unsigned int i = 0; i < faceVaryingPrimvarSetups.size(); i++ )
	{
		PrimvarSetup &s = faceVaryingPrimvarSetups[i];

		// If we are deduplicating the indices, we are creating new indices past the end of the data,
		// which point into m_deduplicatedReindex instead, so we need to include that when we tell
		// OpenSubdiv how many indices there are.
		channels[i].numValues = IECore::size( s.m_var.data.get() ) + s.m_deduplicatedReindex.size();

		if( s.m_overrideFaceVaryingIndices.size() )
		{
			channels[i].valueIndices = s.m_overrideFaceVaryingIndices.data();
		}
		else
		{
			channels[i].valueIndices = s.m_var.indices->readable().data();
		}
	}
	desc.fvarChannels = channels.data();

	// Instantiate a FarTopologyRefiner from the descriptor
	Canceller::check( canceller );
	std::unique_ptr<OSDF::TopologyRefiner> refiner( OSDF::TopologyRefinerFactory<Descriptor>::Create(desc, OSDF::TopologyRefinerFactory<Descriptor>::Options(osScheme, options)) );

	SurfaceFactory::Options surfaceOptions;

	Canceller::check( canceller );
	SurfaceFactory meshSurfaceFactory( *refiner, surfaceOptions);

	OSDB::Tessellation::Options tessOptions;
	// We use quads except for Loop subdivision which uses tris.
	const int tessFacetSize = osScheme != OpenSubdiv::Sdc::SCHEME_LOOP ? 4 : 3;
	tessOptions.SetFacetSize( tessFacetSize );
	tessOptions.PreserveQuads( tessFacetSize == 4);

	// baseLevel gives us our original mesh back, but with all the adjacency information computed that OpenSubdiv
	// requires. Since OpenSubdiv needs the adjacency information anyway, we might as well use that when we're
	// figuring out shared vertices.
	OSDF::TopologyLevel const & baseLevel = refiner->GetLevel(0);

	// If we were doing adaptive tessellation, here would be the place to prepare a list of tessellation rates
	// per edge that would be referenced below in place of tessUniformRate, to ensure consistency.

	const int numFaces = baseLevel.GetNumFaces();

	Canceller::check( canceller );
	std::vector<int> faceFacetVertexOffsets( numFaces );
	Canceller::check( canceller );
	std::vector<int> faceFacetOffsets( numFaces );

	Canceller::check( canceller );
	PrimvarTopology vertexTopology( baseLevel );

	// Each FaceVarying primvar needs its own topology - we put them in a vector with matching indices.
	std::vector< PrimvarTopology > faceVaryingTopologies;
	faceVaryingTopologies.reserve( faceVaryingPrimvarSetups.size() );
	for( unsigned int i = 0; i < faceVaryingPrimvarSetups.size(); i++ )
	{
		Canceller::check( canceller );
		faceVaryingTopologies.emplace_back( baseLevel, i );
	}

	tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );

	// For our first parallel_for, we're just sorting out the topology and counts for everything, so we can
	// allocate our outputs, and set up the correct offsets to store everything at.
	//
	// The main that doesn't parallelize well here is that InitVertexSurface does some potentially quite
	// expensive work when it first encounters a type of irregular face ... this is then cached for reuse,
	// but if two threads try to access the same type of irregular face, they will both compute it. This can
	// result in quite a bit of repeated work in extreme cases - for example, a lat-long sphere has a row of
	// extremely irregular faces at both poles, all with matching structure. It is very likely that every
	// thread used will find one of those faces at the same time ( since the work for a regular face is
	// trivially in comparison, every thread will rip through until it finds an irregular face ), so that
	// one kind of irregular structure can be computed many times. The solution would be if we could do a
	// pass where we collect the keys for each type of irregular face in the mesh, and then did a parrallel
	// loop over those keys. OpenSubdiv is not set up to let us do that though, and this is much less of
	// an issue on reasonable quad meshes than it is on spheres.
	tbb::parallel_for(
		tbb::blocked_range<int>( 0, numFaces ),
		[&]( tbb::blocked_range<int> &range )
		{
			OSDB::Surface<float> faceSurface;

			for( int faceIndex = range.begin(); faceIndex != range.end(); ++faceIndex )
			{
				Canceller::check( canceller );
				// Initialize the Surface for this face -- if valid (skipping
				// holes and boundary faces in some rare cases):
				if( !meshSurfaceFactory.InitVertexSurface( faceIndex, &faceSurface ) )
				{
					continue;
				}

				OSDF::ConstIndexArray fVerts = baseLevel.GetFaceVertices(faceIndex);
				OSDF::ConstIndexArray fEdges = baseLevel.GetFaceEdges(faceIndex);

				OSDB::Tessellation tessPattern(
					faceSurface.GetParameterization(), tessUniformRate, tessOptions
				);

				faceFacetOffsets[ faceIndex ] = tessPattern.GetNumFacets();
				faceFacetVertexOffsets[ faceIndex ] =
					tessPattern.GetNumFacets() * tessFacetSize -
					numDegenerateQuadsInTessellation( tessFacetSize, fVerts.size(), tessUniformRate );

				vertexTopology.addFace( faceIndex, tessPattern, fVerts, fEdges, tessUniformRate );

				for( PrimvarTopology &t : faceVaryingTopologies )
				{
					t.addFace( faceIndex, tessPattern, fVerts, fEdges, tessUniformRate );
				}
			}
		},
		tbb::static_partitioner(),
		taskGroupContext
	);

	// All off our offset arrays are initially filled with counts, which we must accumulate in order to convert
	// them to offsets. This is one of the main pieces that we're not multithreading - in theory, we could
	// allocate each primvar on a separate thread. But in practice, summing some integers doesn't seem to
	// be much of a bottleneck compared to the actual OpenSubdiv work.

	const int numOutPoints = vertexTopology.accumulateFacePoints();
	const int numOutFacets = intVectorAccumulate( faceFacetOffsets );
	const int numOutVertexIds = intVectorAccumulate( faceFacetVertexOffsets );

	Canceller::check( canceller );
	posPrimvarSetup.allocateOutputs( numOutPoints, numOutVertexIds );
	for( PrimvarSetup &setup : vertexPrimvarSetups )
	{
		Canceller::check( canceller );
		setup.allocateOutputs( numOutPoints, 0 );
	}

	for( PrimvarSetup &setup : uniformPrimvarSetups )
	{
		Canceller::check( canceller );
		setup.allocateOutputs( 0, numOutFacets );
	}

	for( unsigned int i = 0; i < faceVaryingPrimvarSetups.size(); i++ )
	{
		Canceller::check( canceller );
		const int numOutFaceVarying = faceVaryingTopologies[i].accumulateFacePoints();
		faceVaryingPrimvarSetups[i].allocateOutputs( numOutFaceVarying, numOutVertexIds );
	}

	// \todo : We currently assume that normals are per-vertex - this makes things much easier, they can just
	// be generated alongside P which always per-vertex. But this fails to account for infinitely sharp
	// creases - we could do more accurate representation of infinitely sharp creases without over-tessellating
	// if we output facing-varying normals and split vertices based on IsEdgeInfSharp.
	V3fVectorDataPtr outNormalsData = new V3fVectorData();
	outNormalsData->setInterpretation( GeometricData::Normal );
	std::vector<Imath::V3f> &outNormals = outNormalsData->writable();
	if( calculateNormals )
	{
		Canceller::check( canceller );
		// See comment in allocateOutputs() about vector initialization
		outNormals.resize( numOutPoints );
	}

	Canceller::check( canceller );
	IntVectorDataPtr outVerticesPerFaceData = new IntVectorData();
	std::vector<int> &outVerticesPerFace = outVerticesPerFaceData->writable();
	outVerticesPerFace.resize( numOutFacets, tessFacetSize );

	// Now we can do a second parallel loop where we do all the real work - we tessellate all the primitive
	// variables into their correct spot in the allocated outputs, using the topology information computed
	// in the first loop to know when we're reusing data from shared vertices or edges.
	tbb::parallel_for(
		tbb::blocked_range<int>( 0, numFaces ),
		[&]( tbb::blocked_range<int> &range )
		{
			OSDB::Surface<float> vertexSurface;
			std::vector<Imath::V2f> tessCoords;

			TessellationTempBuffers tessellationTempBuffers;

			for( int faceIndex = range.begin(); faceIndex != range.end(); ++faceIndex )
			{
				Canceller::check( canceller );

				// Initialize the Surface for this face -- if valid (skipping
				// holes and boundary faces in some rare cases):
				if( !meshSurfaceFactory.InitVertexSurface( faceIndex, &vertexSurface ) )
				{
					continue;
				}

				//
				// Declare a simple uniform Tessellation for the Parameterization
				// of this face and identify coordinates of the points to evaluate:
				//
				OSDB::Tessellation tessPattern( vertexSurface.GetParameterization(), tessUniformRate, tessOptions );

				tessCoords.resize( tessPattern.GetNumCoords() );
				tessPattern.GetCoords( (float*)tessCoords.data() );

				tessellateVariables(
					meshSurfaceFactory, tessPattern,
					faceIndex, baseLevel.GetFaceVertices( faceIndex ), baseLevel.GetFaceEdges( faceIndex ),
					tessUniformRate, tessCoords,
					outVerticesPerFace, faceFacetOffsets[faceIndex], faceFacetVertexOffsets[faceIndex],
					vertexTopology, vertexSurface, posPrimvarSetup, outNormals,
					vertexPrimvarSetups, uniformPrimvarSetups,
					faceVaryingTopologies, faceVaryingPrimvarSetups,
					tessellationTempBuffers, canceller
				);

			}
		},
		tbb::auto_partitioner(),
		taskGroupContext
	);

	MeshPrimitivePtr result = new MeshPrimitive( outVerticesPerFaceData, posPrimvarSetup.m_outIndicesData, "linear", IECore::runTimeCast<IECore::V3fVectorData>( posPrimvarSetup.m_outData.get() ) );

	if( calculateNormals )
	{
		result->variables["N"] = PrimitiveVariable( PrimitiveVariable::Vertex, outNormalsData );
	}

	for( PrimvarSetup &setup : vertexPrimvarSetups )
	{
		result->variables[setup.m_name] = PrimitiveVariable( PrimitiveVariable::Vertex, setup.m_outData );
	}

	for( PrimvarSetup &setup : uniformPrimvarSetups )
	{
		result->variables[setup.m_name] = PrimitiveVariable( PrimitiveVariable::Uniform, setup.m_var.data, setup.m_outIndicesData );
	}

	for( PrimvarSetup &setup : faceVaryingPrimvarSetups )
	{
		result->variables[setup.m_name] = PrimitiveVariable( PrimitiveVariable::FaceVarying, setup.m_outData, setup.m_outIndicesData );
	}

	// We didn't need to make setups to hold interpolated data for constant primvars, we just copy them
	// across directly.
	for( const auto &it : inputMesh.variables )
	{
		if( it.second.interpolation == PrimitiveVariable::Constant )
		{
			result->variables[it.first] = PrimitiveVariable( PrimitiveVariable::Constant, const_cast<Data*>( it.second.data.get() ) );
		}
	}

	return result;
}

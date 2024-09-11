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

#include "GafferScene/Private/IECoreScenePreview/PrimitiveAlgo.h"

#include "IECoreScene/PrimitiveVariable.h"
#include "IECoreScene/MeshPrimitive.h"
#include "IECoreScene/CurvesPrimitive.h"
#include "IECoreScene/PointsPrimitive.h"

#include "IECore/DataAlgo.h"
#include "IECore/TypeTraits.h"

#include <unordered_map>
#include <numeric>

#include "fmt/format.h"

#include "tbb/parallel_for.h"

using namespace IECoreScene;
using namespace IECore;
using namespace IECoreScenePreview;


namespace {

// Copied from Context.inl because it isn't public
template<typename T>
struct DataTraits
{
	using DataType = IECore::TypedData<T>;
};

template<typename T>
struct DataTraits<Imath::Vec2<T> >
{
	using DataType = IECore::GeometricTypedData<Imath::Vec2<T>>;
};

template<typename T>
struct DataTraits<Imath::Vec3<T> >
{
	using DataType = IECore::GeometricTypedData<Imath::Vec3<T>>;
};

template<typename T>
struct DataTraits<std::vector<Imath::Vec2<T> > >
{
	using DataType = IECore::GeometricTypedData<std::vector<Imath::Vec2<T>>>;
};

template<typename T>
struct DataTraits<std::vector<Imath::Vec3<T> > >
{
	using DataType = IECore::GeometricTypedData<std::vector<Imath::Vec3<T>>>;
};


// Return if we have TypedData holder for a vector of T
template< typename T>
constexpr bool supportsVectorTypedData()
{
	// This should probably be a whitelist, not a blacklist. But also it should be defined somewhere
	// central, not here.
	return !(
		std::is_same_v< T, IECore::TransformationMatrixd > ||
		std::is_same_v< T, IECore::TransformationMatrixf > ||
		std::is_same_v< T, IECore::Splineff > ||
		std::is_same_v< T, IECore::SplinefColor3f > ||
		std::is_same_v< T, IECore::SplinefColor4f > ||
		std::is_same_v< T, IECore::Splinedd > ||
		std::is_same_v< T, IECore::PathMatcher > ||
		std::is_same_v< T, boost::posix_time::ptime>
	);
}

Imath::M44f normalTransform( const Imath::M44f &m )
{
	Imath::M44f result = m.inverse();
	result.transpose();
	return result;
}

// \todo : Perhaps belongs in DataAlgo with IECore::size? ( Also, stuff like DataAlgo::size should be
// refactored to use `if constexpr` )
void dataResize( Data *data, size_t size )
{
	IECore::dispatch( data,
		[size] ( auto *typedData ) {
			using DataType = std::remove_pointer_t< decltype( typedData ) >;
			if constexpr( TypeTraits::IsVectorTypedData< DataType >::value )
			{
				// Ideally, we wouldn't initialize anything here, and we would only zero out the memory
				// if needed. ( ie. while we're in the final multithreaded loop of mergePrimitives, and find
				// that one primvar has no data for this primvar, then we could zero out just that segment ...
				// that would be a potentially significant performance win ).
				//
				// However, we currently can't suppress zero-initialization for most types, so it's most
				// consistent if for now we just force everything to to zero-initialize, rather than taking
				// advantage of the extra performance for the types where we could.
				//
				// So we've got a hardcoded list here of imath types where the default constructor doesn't
				// initialize. Note that if there is any type covered by dispatch which doesn't initialize,
				// and isn't listed in this hardcoded list, you will get weird, uninitialized behaviour.
				if constexpr(
					std::is_same_v< DataType, V2iVectorData > || std::is_same_v< DataType, V3iVectorData > ||
					std::is_same_v< DataType, V2fVectorData > || std::is_same_v< DataType, V3fVectorData > ||
					std::is_same_v< DataType, V2dVectorData > || std::is_same_v< DataType, V3dVectorData > ||
					std::is_same_v< DataType, Color3fVectorData > || std::is_same_v< DataType, Color4fVectorData >
				)
				{
					using SingleElementType = typename DataType::ValueType::value_type;
					typedData->writable().resize( size, SingleElementType( 0 ) );
				}
				else
				{
					typedData->writable().resize( size );
				}
			}
			else if( size != 1 )
			{
				throw IECore::Exception( fmt::format(
					"Can't resize, not a vector data type: {}", typedData->typeName()
				) );
			}
		}
	);
}

inline void transformPrimVarValue(
	const Imath::V3f *source, Imath::V3f *dest, int numElements,
	const Imath::M44f &matrix, const Imath::M44f &normalMatrix, GeometricData::Interpretation interpretation
)
{
	if( interpretation == GeometricData::Point )
	{
		for( int i = 0; i < numElements; i++ )
		{
			*(dest++) = *(source++) * matrix;
		}
	}
	else if( interpretation == GeometricData::Vector )
	{
		for( int i = 0; i < numElements; i++ )
		{
			matrix.multDirMatrix( *(source++), *(dest++) );
		}
	}
	else if( interpretation == GeometricData::Normal )
	{
		for( int i = 0; i < numElements; i++ )
		{
			normalMatrix.multDirMatrix( *(source++), *(dest++) );
		}
	}
	else
	{
		for( int i = 0; i < numElements; i++ )
		{
			*(dest++) = *(source++);
		}
	}

}


inline void copyElements( const Data *sourceData, size_t sourceIndex, Data *destData, size_t destIndex, size_t num, const Imath::M44f &matrix, const Imath::M44f &normalMatrix )
{
	IECore::dispatch( destData,
		[&] ( auto *typedDestData ) {
			using DataType = std::remove_pointer_t< decltype( typedDestData ) >;
			if constexpr( TypeTraits::IsVectorTypedData< DataType >::value )
			{
				auto &typedDest = typedDestData->writable();
				auto *typedSourceData = IECore::runTimeCast< const DataType >( sourceData );
				if( !typedSourceData )
				{
					// Failed to cast to destination type ... maybe this is a Constant variable being promoted,
					// and the Data stores a single element instead of a vector?

					using SingleElementDataType = typename DataTraits< typename DataType::ValueType::value_type >::DataType;

					auto *singleElementTypedSourceData = IECore::runTimeCast< const SingleElementDataType >( sourceData );
					if( singleElementTypedSourceData )
					{
						assert( num == 1 );
						if constexpr( std::is_same_v< SingleElementDataType, V3fData > )
						{
							// Fairly weird corner case, but technically Constant primvars could need transforming too
							GeometricData::Interpretation interp = singleElementTypedSourceData->getInterpretation();
							transformPrimVarValue(
								&singleElementTypedSourceData->readable(), &typedDest[ destIndex ], 1,
								matrix, normalMatrix, interp
							);
						}
						else
						{
							typedDest[ destIndex ] = singleElementTypedSourceData->readable();
						}
						return;
					}
					else
					{
						throw IECore::Exception( fmt::format(
							"Can't copy element of type {} to destination of type: {}",
							sourceData->typeName(), destData->typeName()
						) );
					}
				}
				const auto &typedSource = typedSourceData->readable();

				assert( typedSource.size() >= sourceIndex + num );
				assert( typedDest.size() >= destIndex + num );

				if constexpr( std::is_same_v< DataType, V3fVectorData > )
				{
					GeometricData::Interpretation interp = typedSourceData->getInterpretation();
					transformPrimVarValue(
						&typedSource[ sourceIndex ], &typedDest[ destIndex ], num, matrix, normalMatrix, interp
					);
				}
				else
				{
					for( size_t i = 0; i < num; i++ )
					{
						typedDest[ destIndex + i ] = typedSource[ sourceIndex + i ];
					}
				}
			}
			else
			{
				throw IECore::Exception( fmt::format(
					"Can't copy elements, not a vector data type: {}", typedDestData->typeName()
				) );
			}
		}
	);
}

IECore::TypeId vectorDataTypeFromDataType( const Data *data )
{
	return IECore::dispatch( data,
		[] ( auto *typedData ) {
			using DataType = std::remove_pointer_t< decltype( typedData ) >;
			if constexpr( TypeTraits::HasValueType< DataType >::value )
			{
				using ValueType = typename DataType::ValueType;
				if constexpr(
					!TypeTraits::IsVectorTypedData< DataType >::value &&
					supportsVectorTypedData<ValueType>()
				)
				{
					return DataTraits< std::vector<ValueType> >::DataType::staticTypeId();
				}
			}
			return IECore::InvalidTypeId;
		}
	);
}

bool interpolationMatches(
	IECoreScene::TypeId primType, PrimitiveVariable::Interpolation a, PrimitiveVariable::Interpolation b
)
{
	if( a == b )
	{
		return true;
	}

	if( primType == IECoreScene::MeshPrimitiveTypeId )
	{
		auto isVertex = []( PrimitiveVariable::Interpolation x) {
			return x == PrimitiveVariable::Vertex || x == PrimitiveVariable::Varying;
		};
		return isVertex( a ) && isVertex( b );
	}
	else if( primType == IECoreScene::CurvesPrimitiveTypeId )
	{
		auto isVarying = []( PrimitiveVariable::Interpolation x) {
			return x == PrimitiveVariable::Varying || x == PrimitiveVariable::FaceVarying;
		};
		return isVarying( a ) && isVarying( b );
	}
	else
	{
		assert( primType == IECoreScene::PointsPrimitiveTypeId );
		auto isVertex = []( PrimitiveVariable::Interpolation x) {
			return x == PrimitiveVariable::Vertex || x == PrimitiveVariable::Varying || x == PrimitiveVariable::FaceVarying;
		};
		return isVertex( a ) && isVertex( b );
	}
}

// Set up indices on the destination matching the source indices ( includes handling converting interpolations ).
// Note that this only handles interpolations used by mergePrimitives ( ie. only promotion to more specific
// interpolations, like Vertex -> FaceVarying, but it can't do averaging ).
void copyIndices(
	const std::vector<int> *sourceIndices, int *destIndices,
	IECoreScene::TypeId primTypeId,
	PrimitiveVariable::Interpolation sourceInterp, PrimitiveVariable::Interpolation destInterp,
	size_t numIndices, size_t dataStart,
	const Primitive *sourcePrim
)
{
	// Helper function that translates from an index in the source data to an index in the destination
	// data, based on the data offset, and the source indices ( if present )
	auto translateIndex = [sourceIndices, dataStart]( int j ){
		return sourceIndices ? dataStart + (*sourceIndices)[j] : dataStart + j;
	};

	if( interpolationMatches( primTypeId, sourceInterp, destInterp ) )
	{
		// If the interpolation hasn't changed, we don't need to anything special, just translate
		// each index.
		for( size_t j = 0; j < numIndices; j++ )
		{
			*(destIndices++) = translateIndex( j );
		}
	}
	else if( sourceInterp == PrimitiveVariable::Constant )
	{
		// Constant variables aren't stored as vectors, so they can't have been indexed to start,
		// just set all the output indices to the one element of output data.
		for( size_t j = 0; j < numIndices; j++ )
		{
			*(destIndices++) = dataStart;
		}
	}
	else if( sourceInterp == PrimitiveVariable::Uniform )
	{
		if( primTypeId == IECoreScene::MeshPrimitiveTypeId )
		{
			// On a mesh, if you combine a Uniform with anything it doesn't match, then it gets
			// promoted to FaceVarying.
			assert( destInterp == PrimitiveVariable::FaceVarying );

			const MeshPrimitive *sourceMesh = static_cast< const MeshPrimitive* >( sourcePrim );
			const std::vector<int> &sourceVerticesPerFace = sourceMesh->verticesPerFace()->readable();

			int sourceI = 0;
			for( int numVerts : sourceVerticesPerFace )
			{
				for( int k = 0; k < numVerts; k++ )
				{
					*(destIndices++) = translateIndex( sourceI );
				}
				sourceI++;
			}
		}
		else if( primTypeId == IECoreScene::CurvesPrimitiveTypeId )
		{
			const CurvesPrimitive *sourceCurves = static_cast< const CurvesPrimitive* >( sourcePrim );

			if( destInterp == PrimitiveVariable::Vertex )
			{
				const std::vector<int> &sourceVerticesPerCurve = sourceCurves->verticesPerCurve()->readable();
				int sourceI = 0;
				for( int numVerts : sourceVerticesPerCurve )
				{
					for( int k = 0; k < numVerts; k++ )
					{
						*(destIndices++) = translateIndex( sourceI );
					}
					sourceI++;
				}
			}
			else
			{
				assert( destInterp == PrimitiveVariable::Varying );
				int sourceI = 0;
				size_t sourceNumCurves = sourceCurves->numCurves();
				for( size_t i = 0; i < sourceNumCurves; i++ )
				{
					int numVarying = sourceCurves->variableSize( PrimitiveVariable::Varying, i );
					for( int k = 0; k < numVarying; k++ )
					{
						*(destIndices++) = translateIndex( sourceI );
					}
					sourceI++;
				}
			}
		}
		else
		{
			int constantIndex = translateIndex( 0 );
			for( size_t j = 0; j < numIndices; j++ )
			{
				*(destIndices++) = constantIndex;
			}
		}
	}
	else
	{
		// The only time we convert to a non-matching interpolation from something that isn't uniform,
		// is when promototing Vertex primvars on meshes.
		assert( destInterp == PrimitiveVariable::FaceVarying );
		assert( primTypeId == IECoreScene::MeshPrimitiveTypeId );
		assert( sourceInterp == PrimitiveVariable::Vertex || sourceInterp == PrimitiveVariable::Varying );

		const MeshPrimitive *sourceMesh = static_cast< const MeshPrimitive* >( sourcePrim );
		const std::vector<int> &sourceVertexIds = sourceMesh->vertexIds()->readable();

		for( size_t j = 0; j < numIndices; j++ )
		{
			*(destIndices++) = translateIndex( sourceVertexIds[ j ] );
		}
	}
}


class MergePrimitivesMeshResult
{
public:
	using PrimitiveType = IECoreScene::MeshPrimitive;

	// Initialize, and allocate storage for the topology
	MergePrimitivesMeshResult(
		const std::vector< std::pair< const IECoreScene::Primitive*, Imath::M44f > > &primitives,
		const std::vector< int > &totalInterpolation
	)
	{

		result = new IECoreScene::MeshPrimitive();

		// Need to hold onto this until we pass it to the result in finalize
		m_numVertices = totalInterpolation[ PrimitiveVariable::Vertex ];

		setMeshGlobals( result.get(), primitives );

		m_resultVerticesPerFaceData = new IntVectorData;
		m_resultVertexIdsData = new IntVectorData;

		m_resultVerticesPerFaceData->writable().resize( totalInterpolation[ PrimitiveVariable::Uniform ] );
		m_resultVertexIdsData->writable().resize( totalInterpolation[ PrimitiveVariable::FaceVarying ] );

		int totalAccumCorners = 0;
		int totalAccumCreases = 0;
		int totalAccumCreaseIds = 0;

		m_countCorners.reserve( primitives.size() );
		m_countCreases.reserve( primitives.size() );
		m_countCreaseIds.reserve( primitives.size() );
		m_accumCorners.reserve( primitives.size() );
		m_accumCreases.reserve( primitives.size() );
		m_accumCreaseIds.reserve( primitives.size() );

		for( const auto & [prim, matrix] : primitives )
		{
			const MeshPrimitive *mesh = static_cast< const MeshPrimitive * >( prim );

			m_countCorners.push_back( mesh->cornerIds()->readable().size() );
			m_accumCorners.push_back( totalAccumCorners );
			totalAccumCorners += m_countCorners.back();

			m_countCreases.push_back( mesh->creaseLengths()->readable().size() );
			m_accumCreases.push_back( totalAccumCreases );
			totalAccumCreases += m_countCreases.back();

			m_countCreaseIds.push_back( mesh->creaseIds()->readable().size() );
			m_accumCreaseIds.push_back( totalAccumCreaseIds );
			totalAccumCreaseIds += m_countCreaseIds.back();
		}

		if( totalAccumCorners )
		{
			m_resultCornerIdsData = new IntVectorData;
			m_resultCornerIdsData->writable().resize( totalAccumCorners );
			m_resultCornerSharpnessesData = new FloatVectorData;
			m_resultCornerSharpnessesData->writable().resize( totalAccumCorners );
		}

		if( totalAccumCreases )
		{
			m_resultCreaseLengthsData = new IntVectorData;
			m_resultCreaseLengthsData->writable().resize( totalAccumCreases );
			m_resultCreaseSharpnessesData = new FloatVectorData;
			m_resultCreaseSharpnessesData->writable().resize( totalAccumCreases );
			m_resultCreaseIdsData = new IntVectorData;
			m_resultCreaseIdsData->writable().resize( totalAccumCreaseIds );
		}
	}

	// This must be called once for each source primitive
	void copyFromSource(
		const MeshPrimitive *mesh, int i,
		std::vector<std::vector<int> > &countInterpolation, std::vector< std::vector<int> > &accumInterpolation,
		const IECore::Canceller *canceller
	)
	{
		int startUniform = accumInterpolation[ PrimitiveVariable::Uniform ][i];
		int numUniform = countInterpolation[ PrimitiveVariable::Uniform ][i];
		int startVertex = accumInterpolation[ PrimitiveVariable::Vertex ][i];
		int startFaceVarying = accumInterpolation[ PrimitiveVariable::FaceVarying ][i];
		int numFaceVarying = countInterpolation[ PrimitiveVariable::FaceVarying ][i];

		const int *sourceVerticesPerFace = &mesh->verticesPerFace()->readable()[0];
		int *resultVerticesPerFace = &m_resultVerticesPerFaceData->writable()[ startUniform ];
		Canceller::check( canceller );
		for( int j = 0; j < numUniform; j++ )
		{
			*(resultVerticesPerFace++) = *(sourceVerticesPerFace++);
		}

		const int* sourceVertexIds = &mesh->vertexIds()->readable()[0];
		int *resultVertexIds = &m_resultVertexIdsData->writable()[startFaceVarying];
		Canceller::check( canceller );
		for( int j = 0; j < numFaceVarying; j++ )
		{
			*(resultVertexIds++) = *(sourceVertexIds++) + startVertex;
		}

		if( m_resultCornerIdsData )
		{
			const int *sourceCornerIds = &mesh->cornerIds()->readable()[0];
			const float *sourceCornerSharpnesses = &mesh->cornerSharpnesses()->readable()[0];
			int *resultCornerIds = &m_resultCornerIdsData->writable()[ m_accumCorners[i] ];
			float *resultCornerSharpnesses = &m_resultCornerSharpnessesData->writable()[ m_accumCorners[i] ];
			Canceller::check( canceller );
			for( int j = 0; j < m_countCorners[i]; j++ )
			{
				*(resultCornerIds++) = *(sourceCornerIds++) + startVertex;
				*(resultCornerSharpnesses++) = *(sourceCornerSharpnesses++);
			}
		}

		if( m_resultCreaseLengthsData )
		{
			const int *sourceCreaseLengths = &mesh->creaseLengths()->readable()[0];
			const float *sourceCreaseSharpnesses = &mesh->creaseSharpnesses()->readable()[0];
			int *resultCreaseLengths = &m_resultCreaseLengthsData->writable()[m_accumCreases[i]];
			float *resultCreaseSharpnesses = &m_resultCreaseSharpnessesData->writable()[m_accumCreases[i]];
			Canceller::check( canceller );
			for( int j = 0; j < m_countCreases[i]; j++ )
			{
				*(resultCreaseLengths++) = *(sourceCreaseLengths++);
				*(resultCreaseSharpnesses++) = *(sourceCreaseSharpnesses++);
			}

			const int *sourceCreaseIds = &mesh->creaseIds()->readable()[0];
			int *resultCreaseIds = &m_resultCreaseIdsData->writable()[m_accumCreaseIds[i]];
			Canceller::check( canceller );
			for( int j = 0; j < m_countCreaseIds[i]; j++ )
			{
				*(resultCreaseIds++) = *(sourceCreaseIds++) + startVertex;
			}
		}
	}

	// This must be called after all calls to copyFromSource
	void finalize()
	{

		result->setTopologyUnchecked( m_resultVerticesPerFaceData, m_resultVertexIdsData, m_numVertices, result->interpolation() );

		if( m_resultCornerIdsData )
		{
			result->setCorners( m_resultCornerIdsData.get(), m_resultCornerSharpnessesData.get() );
		}

		if( m_resultCreaseLengthsData )
		{
			result->setCreases(
				m_resultCreaseLengthsData.get(), m_resultCreaseIdsData.get(), m_resultCreaseSharpnessesData.get()
			);
		}
	}



	// Return an interpolation adequate to store data of either input interpolation
	static PrimitiveVariable::Interpolation mergeInterpolations(
		PrimitiveVariable::Interpolation a, PrimitiveVariable::Interpolation b, const IECore::InternedString &msgName
	)
	{
		PrimitiveVariable::Interpolation result;

		// In general, more specific Interpolations have a higher enum value, so we want to take
		// whichever interpolation is higher. This doesn't always work, so afterwards we have several
		// special cases to clean things up.
		result = std::max( a, b );

		if(
			result >= PrimitiveVariable::Vertex &&
			( a == PrimitiveVariable::Uniform || b == PrimitiveVariable::Uniform )
		)
		{
			// On meshes, if you mix Uniform and Vertex, we need to use FaceVarying to represent both
			result = PrimitiveVariable::FaceVarying;
		}

		// When merging interpolations, if the interpolation has synonymous names, we always choose the canonical one
		if( interpolationMatches( MeshPrimitiveTypeId, result, PrimitiveVariable::Vertex ) )
		{
			result = PrimitiveVariable::Vertex;
		}

		return result;
	}

	IECoreScene::MeshPrimitivePtr result;

private:

	static void setMeshGlobals(
		MeshPrimitive *result,
		const std::vector< std::pair< const IECoreScene::Primitive*, Imath::M44f > > &primitives
	)
	{
		const MeshPrimitive *firstMesh = static_cast< const MeshPrimitive * >( primitives[0].first );
		std::string meshInterpolation = firstMesh->interpolation();
		IECore::InternedString interpolateBound = firstMesh->getInterpolateBoundary();
		IECore::InternedString faceVaryingLI = firstMesh->getFaceVaryingLinearInterpolation();
		IECore::InternedString triangleSub = firstMesh->getTriangleSubdivisionRule();

		for( const auto & [prim, matrix] : primitives )
		{
			const MeshPrimitive *mesh = static_cast< const MeshPrimitive * >( prim );
			if(
				meshInterpolation != "" &&
				mesh->interpolation() != meshInterpolation
			)
			{
				msg( Msg::Warning, "mergePrimitives",
					fmt::format(
						"Ignoring mismatch between mesh interpolations {} and {} and defaulting to linear",
						meshInterpolation, mesh->interpolation()
					)
				);
				meshInterpolation = "";
			}

			if(
				interpolateBound != "" &&
				mesh->getInterpolateBoundary() != interpolateBound
			)
			{
				msg( Msg::Warning, "mergePrimitives",
					fmt::format(
						"Ignoring mismatch between mesh interpolate bound {} and {} and defaulting to edgeAndCorner",
						interpolateBound.string(), mesh->getInterpolateBoundary().string()
					)
				);
				interpolateBound = "";
			}

			if(
				faceVaryingLI != "" &&
				mesh->getFaceVaryingLinearInterpolation() != faceVaryingLI
			)
			{
				msg( Msg::Warning, "mergePrimitives",
					fmt::format(
						"Ignoring mismatch between mesh face varying linear interpolation {} and {} and defaulting to cornersPlus1",
						faceVaryingLI.string(), mesh->getFaceVaryingLinearInterpolation().string()
					)
				);
				faceVaryingLI = "";
			}

			if(
				triangleSub != "" &&
				mesh->getTriangleSubdivisionRule() != triangleSub
			)
			{
				msg( Msg::Warning, "mergePrimitives",
					fmt::format(
						"Ignoring mismatch between mesh triangle subdivision rule {} and {} and defaulting to catmullClark",
						triangleSub.string(), mesh->getTriangleSubdivisionRule().string()
					)
				);
				triangleSub = "";
			}
		}

		if( meshInterpolation == "" )
		{
			meshInterpolation = "linear";
		}
		result->setInterpolation( meshInterpolation );

		if( interpolateBound == "" )
		{
			interpolateBound = MeshPrimitive::interpolateBoundaryEdgeAndCorner;
		}
		result->setInterpolateBoundary( interpolateBound );

		if( faceVaryingLI == "" )
		{
			faceVaryingLI = MeshPrimitive::faceVaryingLinearInterpolationCornersPlus1;
		}
		result->setFaceVaryingLinearInterpolation( faceVaryingLI );

		if( triangleSub == "" )
		{
			triangleSub = MeshPrimitive::triangleSubdivisionRuleCatmullClark;
		}
		result->setTriangleSubdivisionRule( triangleSub );
	}

	IntVectorDataPtr m_resultVerticesPerFaceData;
	IntVectorDataPtr m_resultVertexIdsData;
	int m_numVertices;

	std::vector<int> m_countCorners;
	std::vector<int> m_countCreases;
	std::vector<int> m_countCreaseIds;
	std::vector<int> m_accumCorners;
	std::vector<int> m_accumCreases;
	std::vector<int> m_accumCreaseIds;

	IntVectorDataPtr m_resultCornerIdsData;
	FloatVectorDataPtr m_resultCornerSharpnessesData;
	IntVectorDataPtr m_resultCreaseLengthsData;
	IntVectorDataPtr m_resultCreaseIdsData;
	FloatVectorDataPtr m_resultCreaseSharpnessesData;
};


class MergePrimitivesCurvesResult
{
public:
	using PrimitiveType = IECoreScene::CurvesPrimitive;

	// Initialize, and allocate storage for the topology
	MergePrimitivesCurvesResult(
		const std::vector< std::pair< const IECoreScene::Primitive*, Imath::M44f > > &primitives,
		const std::vector< int > &totalInterpolation
	)
	{
		result = new IECoreScene::CurvesPrimitive();

		m_resultVerticesPerCurveData = new IntVectorData;
		m_resultVerticesPerCurveData->writable().resize( totalInterpolation[ PrimitiveVariable::Uniform ] );

		setCurvesGlobals( result.get(), primitives );
	}

	// This must be called once for each source primitive
	void copyFromSource(
		const CurvesPrimitive *curves, int i,
		std::vector<std::vector<int> > &countInterpolation, std::vector< std::vector<int> > &accumInterpolation,
		const IECore::Canceller *canceller
	)
	{
		int startUniform = accumInterpolation[ PrimitiveVariable::Uniform ][i];
		int numUniform = countInterpolation[ PrimitiveVariable::Uniform ][i];

		int *resultVerticesPerCurve = &m_resultVerticesPerCurveData->writable()[ startUniform ];
		const int *sourceVerticesPerCurve = &curves->verticesPerCurve()->readable()[0];
		Canceller::check( canceller );
		for( int j = 0; j < numUniform; j++ )
		{
			*(resultVerticesPerCurve++) = *(sourceVerticesPerCurve++);
		}
	}

	// This must be called after all calls to copyFromSource
	void finalize()
	{
		result->setTopology( m_resultVerticesPerCurveData, result->basis(), result->periodic() );
	}

	// Return an interpolation adequate to store data of either input interpolation
	static PrimitiveVariable::Interpolation mergeInterpolations(
		PrimitiveVariable::Interpolation a, PrimitiveVariable::Interpolation b, const IECore::InternedString &msgName
	)
	{
		PrimitiveVariable::Interpolation result;

		// In general, more specific Interpolations have a higher enum value, so we want to take
		// whichever interpolation is higher. This doesn't always work, so afterwards we have
		// special cases to clean things up.
		result = std::max( a, b );

		if(
			result >= PrimitiveVariable::Varying &&
			( a == PrimitiveVariable::Vertex || b == PrimitiveVariable::Vertex )
		)
		{
			// Mixing Vertex/Varying on curves requires a lossy resample that would make things more complex.
			msg( Msg::Warning, "mergePrimitives",
				fmt::format(
					"Discarding variable \"{}\" - Cannot mix Vertex and Varying curve variables.",
					std::string( msgName )
				)
			);
			result = PrimitiveVariable::Invalid;
		}

		// When merging interpolations, if the interpolation has synonymous names, we always choose the canonical one
		if( interpolationMatches( CurvesPrimitiveTypeId, result, PrimitiveVariable::Varying ) )
		{
			result = PrimitiveVariable::Varying;
		}

		return result;
	}

	IECoreScene::CurvesPrimitivePtr result;

private:

	static void setCurvesGlobals(
		CurvesPrimitive *result,
		const std::vector< std::pair< const IECoreScene::Primitive*, Imath::M44f > > &primitives
	)
	{
		const CurvesPrimitive *firstCurves = static_cast< const CurvesPrimitive * >( primitives[0].first );
		CubicBasisf basis = firstCurves->basis();
		bool periodic = firstCurves->periodic();

		static const CubicBasisf invalidBasis( Imath::M44f( 0.0f ), 0 );

		for( const auto & [prim, matrix] : primitives )
		{
			const CurvesPrimitive *curves = static_cast< const CurvesPrimitive * >( prim );
			if( curves->periodic() != periodic )
			{
				throw IECore::Exception( "Cannot merge periodic and non-periodic curves" );
			}

			if(
				basis != invalidBasis &&
				curves->basis() != basis
			)
			{
				msg( Msg::Warning, "mergePrimitives",
					"Ignoring mismatch in curve basis and defaulting to linear"
				);
				basis = invalidBasis;
			}
		}

		if( basis == invalidBasis )
		{
			basis = CubicBasisf::linear();
		}

		result->setTopology( result->verticesPerCurve(), basis, periodic );
	}

	IntVectorDataPtr m_resultVerticesPerCurveData;
};

class MergePrimitivesPointsResult
{
public:
	using PrimitiveType = IECoreScene::PointsPrimitive;

	MergePrimitivesPointsResult(
		const std::vector< std::pair< const IECoreScene::Primitive*, Imath::M44f > > &primitives,
		const std::vector< int > &totalInterpolation
	)
	{
		result = new IECoreScene::PointsPrimitive( totalInterpolation[ PrimitiveVariable::Vertex ] );
	}

	void copyFromSource(
		const PointsPrimitive *curves, int i,
		std::vector<std::vector<int> > &countInterpolation, std::vector< std::vector<int> > &accumInterpolation,
		const IECore::Canceller *canceller
	)
	{
		// Points don't have any topology to copy
	}

	void finalize()
	{
	}

	// Return an interpolation adequate to store data of either input interpolation
	static PrimitiveVariable::Interpolation mergeInterpolations(
		PrimitiveVariable::Interpolation a, PrimitiveVariable::Interpolation b, const IECore::InternedString &msgName
	)
	{
		// On points, everything is output as Vertex
		return PrimitiveVariable::Vertex;
	}

	IECoreScene::PointsPrimitivePtr result;
};

template<class ResultStruct>
IECoreScene::PrimitivePtr mergePrimitivesInternal(
	const std::vector< std::pair< const IECoreScene::Primitive*, Imath::M44f > > &primitives,
	const IECore::Canceller *canceller
)
{
	IECoreScene::TypeId resultTypeId = (IECoreScene::TypeId)ResultStruct::PrimitiveType::staticTypeId();

	// Data we need to store for each primvar we output
	struct PrimVarInfo
	{
		PrimVarInfo( PrimitiveVariable::Interpolation interpol, IECore::TypeId t, GeometricData::Interpretation interpretation, int numPrimitives )
			: interpolation( interpol ),
			typeId( t ), interpretation( interpretation ), interpretationInvalid( false ), indexed( false ),
			numData( numPrimitives, 0 )
		{
		}

		// Interpolation is set to Invalid if a primitive variable is being ignored.
		PrimitiveVariable::Interpolation interpolation;

		// Need to track typeId so we can make sure everything matches
		IECore::TypeId typeId;

		GeometricData::Interpretation interpretation;
		bool interpretationInvalid;

		// The only case where we don't index the output is if all the input interpolations match, and none
		// of the inputs are indexed - hopefully this is the common case though.
		bool indexed;

		// We need to collect the data size before we can allocate the output primvars
		std::vector<unsigned int> numData;
		std::vector<unsigned int> accumDataSizes;
	};

	std::unordered_map< IECore::InternedString, PrimVarInfo > varInfos;

	for( const auto & [prim, matrix] : primitives )
	{
		if( !prim )
		{
			throw IECore::Exception( "Cannot merge null Primitive" );
		}

		// We already have a primitive, so the types must match
		if( !IECore::runTimeCast< const typename ResultStruct::PrimitiveType >( prim ) )
		{
			throw IECore::Exception( fmt::format(
				"Primitive type mismatch: Cannot merge {} with {}",
				prim->typeName(), ResultStruct::PrimitiveType::staticTypeName()
			) );
		}
	}

	//
	// Before we can even start counting the sizes of things, we need to gather information about what
	// kinds of primitives and primvars we're dealing with.
	//

	for( const auto & [prim, matrix] : primitives )
	{
		// Process all the primvars for this primitive, adding new entries to the varInfo list, or
		// checking that existing entries match correctly
		for( const auto &[name, var] : prim->variables )
		{
			GeometricData::Interpretation interpretation = IECore::getGeometricInterpretation( var.data.get() );

			IECore::TypeId varTypeId = var.data->typeId();

			if( var.interpolation == PrimitiveVariable::Constant )
			{
				varTypeId = vectorDataTypeFromDataType( var.data.get() );
			}

			PrimVarInfo &varInfo = varInfos.try_emplace( name, var.interpolation, varTypeId, interpretation, primitives.size() ).first->second;

			if( varInfo.interpolation == PrimitiveVariable::Invalid )
			{
				continue;
			}

			if( varTypeId == IECore::InvalidTypeId )
			{
				msg( Msg::Warning, "mergePrimitives",
					fmt::format(
						"Discarding variable \"{}\" - Cannot promote Constant primitive variable of type \"{}\".",
						std::string( name ), var.data->typeName()
					)
				);
				varInfo.interpolation = PrimitiveVariable::Invalid;
				continue;
			}

			if( varInfo.typeId != varTypeId )
			{
				msg( Msg::Warning, "mergePrimitives",
					fmt::format(
						"Discarding variable \"{}\" - types don't match: \"{}\" and \"{}\"",
						name,
						IECore::RunTimeTyped::typeNameFromTypeId( varInfo.typeId ),
						IECore::RunTimeTyped::typeNameFromTypeId( var.data->typeId() )
					)
				);
				varInfo.interpolation = PrimitiveVariable::Invalid;
				continue;
			}

			if( !varInfo.interpretationInvalid )
			{
				if( interpretation != varInfo.interpretation )
				{
					varInfo.interpretation = GeometricData::Interpretation::None;
					varInfo.interpretationInvalid = true;
					msg( Msg::Warning, "mergePrimitives",
						fmt::format(
							"Interpretation mismatch for primitive variable \"{}\", defaulting to \"None\"", name
						)
					);
				}
			}

			varInfo.interpolation = ResultStruct::mergeInterpolations( varInfo.interpolation, var.interpolation, name );
		}
	}

	//
	// Now loop over variables collecting the information we'll need to allocate them.
	//

	for( auto &[name, varInfo] : varInfos )
	{
		if( varInfo.interpolation == PrimitiveVariable::Invalid )
		{
			continue;
		}

		// If we've processed all primitives, and this var is still just a Constant, promote it to at least
		// Uniform, so we can represent different values from different primitives.
		if( varInfo.interpolation == PrimitiveVariable::Constant )
		{
			varInfo.interpolation = PrimitiveVariable::Uniform;
		}


		// We also need to count the amount of data for this primvar contributed by each primitive.

		bool incomplete = false;
		for( unsigned int i = 0; i < primitives.size(); i++ )
		{

			auto it = primitives[i].first->variables.find( name );

			if( it == primitives[i].first->variables.end() )
			{
				// This primitive doesn't have this primvar, we'll just write one data element
				// that will be left uninitialized.
				// Note : It's probably arguable what is most correct here ... is it unexpected that a var that
				// usually isn't indexed would become indexed because one prim is missing it? But there is an
				// efficiency gain in not storing the zero value repeatedly ( in any case where the data type is
				// more than 4 bytes ). I've currently gone with indexing it because it feels simplest to
				// implement - we need to make this work for the indexed case, so it's easy to just always use
				// the indexed case.
				varInfo.numData[i] = 1;
				varInfo.indexed = true;
				incomplete = true;
				continue;
			}

			varInfo.numData[i] = IECore::size( it->second.data.get() );

			// Only if everything is simple and matches can we skip outputting indices ( though this
			// is hopefully the most common case )
			if( it->second.indices || !interpolationMatches( resultTypeId, it->second.interpolation, varInfo.interpolation ) )
			{
				varInfo.indexed = true;
			}
		}

		if( incomplete )
		{
			if( name == "N" )
			{
				// Using default initialized normals is particularly likely to produce confusion, so we have a special
				// warning for this case.
				msg( Msg::Warning, "mergePrimitives",
					"Primitive variable N missing on some input primitives, defaulting to zero length normals."
				);
			}
		}
	}

	//
	// Prepare count and offset lists for every interpolation type ( simpler than doing an extra query over
	// all variables to collect which interpolations are used ).
	//

	// There isn't a MaxInterpolation enum, but we don't expect this list to change, and can double check
	// the current maximum
	const int numInterpolations = 6;
	assert( PrimitiveVariable::Constant < numInterpolations );
	assert( PrimitiveVariable::Uniform < numInterpolations );
	assert( PrimitiveVariable::Vertex < numInterpolations );
	assert( PrimitiveVariable::Varying < numInterpolations );
	assert( PrimitiveVariable::FaceVarying < numInterpolations );

	std::vector< std::vector<int> > countInterpolation( numInterpolations );
	std::vector< int > totalInterpolation( numInterpolations );
	std::vector< std::vector<int> > accumInterpolation( numInterpolations );

	for( int interpolation = 0; interpolation < numInterpolations; interpolation++ )
	{
		int accum = 0;
		countInterpolation[interpolation].reserve( primitives.size() );
		accumInterpolation[interpolation].reserve( primitives.size() );
		for( unsigned int i = 0; i < primitives.size(); i++ )
		{
			countInterpolation[interpolation].push_back( primitives[i].first->variableSize( ((PrimitiveVariable::Interpolation)interpolation) ) );
			accumInterpolation[interpolation][i] = accum;
			accum += countInterpolation[interpolation].back();
		}
		totalInterpolation[interpolation] = accum;
	}

	//
	// Allocate the result, together with any topology information needed
	//

	ResultStruct result( primitives, totalInterpolation );

	//
	// Allocate storage for the primitives variables
	//

	for( auto &[name, varInfo] : varInfos )
	{
		if( varInfo.interpolation == PrimitiveVariable::Invalid )
		{
			continue;
		}

		varInfo.accumDataSizes.reserve( varInfo.numData.size() );
		size_t accumDataSize = 0;
		for( unsigned int i : varInfo.numData )
		{
			varInfo.accumDataSizes.push_back( accumDataSize );
			accumDataSize += i;
		}

		PrimitiveVariable &p = result.result->variables.emplace(name, PrimitiveVariable() ).first->second;

		p.data = IECore::runTimeCast<Data>( IECore::Object::create( varInfo.typeId ) );

		IECore::setGeometricInterpretation( p.data.get(), varInfo.interpretation );
		p.interpolation = varInfo.interpolation;
		Canceller::check( canceller );
		dataResize( p.data.get(), accumDataSize );

		if( varInfo.indexed )
		{
			p.indices = new IntVectorData();
			Canceller::check( canceller );
			p.indices->writable().resize( totalInterpolation[ varInfo.interpolation ] );
		}
	}

	//
	// Now a big parallel loop where we do the majority of actual work - copying all the primvar and topology
	// data to the destination.
	//

	// In theory, we would a finer-grained threading of this, so we could optimize the case where a small
	// number of extremely large primitives are combined. However, with the current level of multithreading,
	// it's already hard to produce cases where this loop is a significant contributor to runtime cost. The
	// more significant issue is that when allocating *VectorData, we currently don't have a way to skip
	// the zero-initialize, so much of the cost is currently in that ( which is hard to parallelize, and
	// also is completely unnecessary ). There's probably not much point threading this further until we fix
	// that.

	tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );

	tbb::parallel_for(
		tbb::blocked_range<size_t>( 0, primitives.size() ),
		[&]( tbb::blocked_range<size_t> &range )
		{
			for( size_t i = range.begin(); i != range.end(); i++ )
			{
				const Primitive &sourcePrim = *primitives[i].first;

				const Imath::M44f &matrix = primitives[i].second;
				const Imath::M44f normalMatrix = normalTransform( matrix );

				// Copy the data ( and indices ) for each prim var for this primitive into
				// the destination primvar.
				for( auto &[name, varInfo] : varInfos )
				{
					if( varInfo.interpolation == PrimitiveVariable::Invalid )
					{
						continue;
					}

					PrimitiveVariable &destVar = result.result->variables.find( name )->second;

					const size_t numIndices = countInterpolation[ varInfo.interpolation ][i];
					const size_t startIndex = accumInterpolation[ varInfo.interpolation ][i];
					const size_t dataStart = varInfo.accumDataSizes[i];


					auto it = sourcePrim.variables.find( name );
					if( it == sourcePrim.variables.end() || it->second.interpolation == PrimitiveVariable::Invalid )
					{
						// No matching data found in this primitive for this primvar

						// We don't currently have a way to suppress zero-initialization of the data, so
						// we don't need to initialize that here

						Canceller::check( canceller );

						// We always leave one data element for primitives that don't have the relevant
						// primvar, so just write out all indices pointing to that element.
						int *destIndices = &destVar.indices->writable()[ startIndex ];
						for( size_t j = 0; j < numIndices; j++ )
						{
							*(destIndices++) = dataStart;
						}
					}
					else
					{
						const PrimitiveVariable &sourceVar = it->second;

						Canceller::check( canceller );
						copyElements( sourceVar.data.get(), 0, destVar.data.get(), dataStart, varInfo.numData[i], matrix, normalMatrix );

						if( varInfo.indexed )
						{
							Canceller::check( canceller );
							int *destIndices = &destVar.indices->writable()[ startIndex ];

							copyIndices(
								sourceVar.indices ? &sourceVar.indices->readable() : nullptr, destIndices,
								resultTypeId, sourceVar.interpolation, varInfo.interpolation,
								numIndices, dataStart,
								&sourcePrim
							);
						}
					}
				}

				// Copy the topology information for this primitive into the result topology information,
				// using a type specific function

				result.copyFromSource(
					static_cast< const typename ResultStruct::PrimitiveType * >( primitives[i].first ), i,
					countInterpolation, accumInterpolation, canceller
				);
			}
		},
		tbb::auto_partitioner(),
		taskGroupContext
	);

	// Set topology and other primitive type specific globals
	result.finalize();

	return result.result;
}

// Why isn't this a static in RunTimeTyped?
bool isInstanceOf( IECore::TypeId type, IECore::TypeId baseType )
{
	return type == baseType || RunTimeTyped::inheritsFrom( type, baseType );
}

} // namespace


void PrimitiveAlgo::transformPrimitive(
	IECoreScene::Primitive &primitive, Imath::M44f matrix,
	const IECore::Canceller *canceller
)
{
	if( matrix == Imath::M44f() )
	{
		// Early out for identity matrix
		return;
	}

	Imath::M44f normalMatrix = normalTransform( matrix );

	tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );

	for( const auto &[name, var] : primitive.variables )
	{
		Canceller::check( canceller );
		V3fVectorData *vecVar = IECore::runTimeCast<V3fVectorData>( var.data.get() );
		V3fData *vecConstVar = IECore::runTimeCast<V3fData>( var.data.get() );
		if( !vecVar && !vecConstVar )
		{
			continue;
		}

		GeometricData::Interpretation interp = vecVar ? vecVar->getInterpretation() : vecConstVar->getInterpretation();
		if( !(
			interp == GeometricData::Interpretation::Point ||
			interp == GeometricData::Interpretation::Vector ||
			interp == GeometricData::Interpretation::Normal
		) )
		{
			continue;
		}

		if( vecVar )
		{
			std::vector< Imath::V3f >& writable = vecVar->writable();

			for( size_t i = 0; i < writable.size(); i++ )
			{
				Canceller::check( canceller );
				transformPrimVarValue(
					&writable[i], &writable[i], 1,
					matrix, normalMatrix, interp
				);
			};
		}
		else
		{
			// Fairly weird corner case, but technically Constant primvars could need transforming too
			transformPrimVarValue( &vecConstVar->writable(), &vecConstVar->writable(), 1, matrix, normalMatrix, interp );
		}
	}
}

IECoreScene::PrimitivePtr PrimitiveAlgo::mergePrimitives(
	const std::vector< std::pair< const IECoreScene::Primitive*, Imath::M44f > > &primitives,
	const IECore::Canceller *canceller
)
{
	if( !primitives.size() )
	{
		throw IECore::Exception( "mergePrimitives requires at least one primitive" );
	}

	if( !primitives[0].first )
	{
		throw IECore::Exception( "Cannot merge null Primitive" );
	}

	IECore::TypeId resultTypeId = primitives[0].first->typeId();
	if( isInstanceOf( resultTypeId, (IECore::TypeId)IECoreScene::MeshPrimitiveTypeId ) )
	{
		return mergePrimitivesInternal<MergePrimitivesMeshResult>( primitives, canceller );
	}
	else if( isInstanceOf( resultTypeId, (IECore::TypeId)IECoreScene::CurvesPrimitiveTypeId ) )
	{
		return mergePrimitivesInternal<MergePrimitivesCurvesResult>( primitives, canceller );
	}
	else if( isInstanceOf( resultTypeId, (IECore::TypeId)IECoreScene::PointsPrimitiveTypeId ) )
	{
		return mergePrimitivesInternal<MergePrimitivesPointsResult>( primitives, canceller );
	}
	else
	{
		throw IECore::Exception( fmt::format(
			"Unsupported Primitive type for merging: {}", primitives[0].first->typeId()
		) );
	}
}

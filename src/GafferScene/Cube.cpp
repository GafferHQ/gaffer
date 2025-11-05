//////////////////////////////////////////////////////////////////////////
//
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

#include "GafferScene/Cube.h"

#include "IECoreScene/MeshPrimitive.h"

using namespace Gaffer;
using namespace GafferScene;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;

namespace {

// addCorner, add[XYZ}Edge and add[XYZ]Face all output the vertex positions of a feature, and
// store the indices of the new vertices in the appropriate perFaceIndices.
// They all take an ID that specifies the location of the feature on the axes that aren't spanned.
// See below for more description of perFaceIndices.

void addCorner(
	const V3i &cornerID, const V3i &vertsPer,
	std::vector< V3f > &pos, std::vector< std::vector< int > > &perFaceIndices
)
{
	int vertIndex = pos.size();
	pos.push_back( V3f( cornerID ) );

	perFaceIndices[ 4 + !cornerID.x ][
		cornerID.y * ( vertsPer.y - 1 ) +
		cornerID.z * ( vertsPer.z - 1 ) * vertsPer.y
	] = vertIndex;
	perFaceIndices[ 2 + !cornerID.y ][
		cornerID.x * ( vertsPer.x - 1 ) +
		cornerID.z * ( vertsPer.z - 1 ) * vertsPer.x
	] = vertIndex;
	perFaceIndices[ 0 + !cornerID.z ][
		cornerID.x * ( vertsPer.x - 1 ) +
		cornerID.y * ( vertsPer.y - 1 ) * vertsPer.x
	] = vertIndex;
}

void addXEdge(
	const V2i &edgeID, const V3i &vertsPer,
	std::vector< V3f > &pos, std::vector< std::vector< int > > &perFaceIndices
)
{
	for( int i = 1; i < vertsPer.x - 1; i++ )
	{
		int vertIndex = pos.size();
		pos.push_back( V3f( i / float( vertsPer.x - 1 ), edgeID.x, edgeID.y ) );

		perFaceIndices[ 2 + !edgeID.x ][ i              + edgeID.y * ( vertsPer.z - 1 ) * vertsPer.x ] = vertIndex;
		perFaceIndices[ 0 + !edgeID.y ][ i              + edgeID.x * ( vertsPer.y - 1 ) * vertsPer.x ] = vertIndex;
	}
}

void addYEdge(
	const V2i &edgeID, const V3i &vertsPer,
	std::vector< V3f > &pos, std::vector< std::vector< int > > &perFaceIndices
)
{
	for( int i = 1; i < vertsPer.y - 1; i++ )
	{
		int vertIndex = pos.size();
		pos.push_back( V3f( edgeID.x, i / float( vertsPer.y - 1 ), edgeID.y ) );

		perFaceIndices[ 4 + !edgeID.x ][ i              + edgeID.y * ( vertsPer.z - 1 ) * vertsPer.y ] = vertIndex;
		perFaceIndices[ 0 + !edgeID.y ][ i * vertsPer.x + edgeID.x * ( vertsPer.x - 1 ) ] = vertIndex;
	}
}

void addZEdge(
	const V2i &edgeID, const V3i &vertsPer,
	std::vector< V3f > &pos, std::vector< std::vector< int > > &perFaceIndices
)
{
	for( int i = 1; i < vertsPer.z - 1; i++ )
	{
		int vertIndex = pos.size();
		pos.push_back( V3f( edgeID.x, edgeID.y, i / float( vertsPer.z - 1 ) ) );

		perFaceIndices[ 4 + !edgeID.x ][ i * vertsPer.y + edgeID.y * ( vertsPer.y - 1 ) ] = vertIndex;
		perFaceIndices[ 2 + !edgeID.y ][ i * vertsPer.x + edgeID.x * ( vertsPer.x - 1 ) ] = vertIndex;
	}
}

void addXFace(
	int faceID, const V3i &vertsPer,
	std::vector< V3f > &pos, std::vector< std::vector< int > > &perFaceIndices
)
{
	for( int j = 1; j < vertsPer.z - 1; j++ )
	{
		for( int i = 1; i < vertsPer.y - 1; i++ )
		{
			perFaceIndices[ 4 + !faceID ][ i + j * vertsPer.y ] = pos.size();
			pos.push_back( V3f( faceID, i / float( vertsPer.y - 1 ), j / float( vertsPer.z - 1 ) ) );
		}
	}
}

void addYFace(
	int faceID, const V3i &vertsPer,
	std::vector< V3f > &pos, std::vector< std::vector< int > > &perFaceIndices
)
{
	for( int j = 1; j < vertsPer.z - 1; j++ )
	{
		for( int i = 1; i < vertsPer.x - 1; i++ )
		{
			perFaceIndices[ 2 + !faceID ][ i + j * vertsPer.x ] = pos.size();
			pos.push_back( V3f( i / float( vertsPer.x - 1 ), faceID, j / float( vertsPer.z - 1 ) ) );
		}
	}
}

void addZFace(
	int faceID, const V3i &vertsPer,
	std::vector< V3f > &pos, std::vector< std::vector< int > > &perFaceIndices
)
{
	for( int j = 1; j < vertsPer.y - 1; j++ )
	{
		for( int i = 1; i < vertsPer.x - 1; i++ )
		{
			perFaceIndices[ 0 + !faceID ][ i + j * vertsPer.x ] = pos.size();
			pos.push_back( V3f( i / float( vertsPer.x - 1 ), j / float( vertsPer.y - 1 ), faceID ) );
		}
	}
}

// Use the indices we've stored for a cube face to output all the vertex ids for that face
void outputVertexIDsForFace(
	const V2i &size, const std::vector<int> &indices,
	bool flipOrder, int rotate,
	std::vector<int> &vertexIds
)
{
	for( int y = 0; y < size.y - 1; y++ )
	{
		for( int x = 0; x < size.x - 1; x++ )
		{
			for( int j = 0; j < 4; j++ )
			{
				// The order we pick the vertices for this sub face depends on both
				// flipOrder ( to get winding orders correct ), and rotate ( chosen
				// solely for backwards compatibility )
				int pick = ( ( flipOrder ? 3 - j : j ) + rotate ) % 4;

				if(      pick == 0 ) vertexIds.push_back( indices[y * size.x + x] );
				else if( pick == 1 ) vertexIds.push_back( indices[y * size.x + x + 1] );
				else if( pick == 2 ) vertexIds.push_back( indices[( y + 1 ) * size.x + x + 1] );
				else if( pick == 3 ) vertexIds.push_back( indices[( y + 1 ) * size.x + x] );
			}
		}
	}
}

// Output all uvs. Store some indices where faces start, which will be useful for writing UV indices.
void outputUVs( const V3i &vertsPer, std::vector<V2f>& uvs, int uvFaceIndices[5] )
{
	int uvSize = 2 * ( vertsPer.x * vertsPer.y + vertsPer.y * vertsPer.z + vertsPer.z * vertsPer.x ) - vertsPer.x * 3 - vertsPer.y * 2;
	uvs.reserve( uvSize );

	auto centralUVScanline = [&uvs, &vertsPer]( float v ){
		for( int i = 0; i < vertsPer[0]; i++ )
		{
			uvs.push_back( Imath::V2f( 0.375f + 0.25f * i / float( vertsPer[0] - 1 ), v ) );
		}
	};

	// Output the 4 faces that are in the central column
	uvFaceIndices[0] = uvs.size();
	for( int i = 0; i < vertsPer[1] - 1; i++ )
	{
		centralUVScanline( 0.25f * i / float( vertsPer[1] - 1 ) );
	}
	uvFaceIndices[1] = uvs.size();
	for( int i = 0; i < vertsPer[2] - 1; i++ )
	{
		centralUVScanline( 0.25f + 0.25f * i / float( vertsPer[2] - 1 ) );
	}
	uvFaceIndices[2] = uvs.size();
	for( int i = 0; i < vertsPer[1] - 1; i++ )
	{
		centralUVScanline( 0.5f + 0.25f * i / float( vertsPer[1] - 1 ) );
	}
	uvFaceIndices[3] = uvs.size();
	for( int i = 0; i < vertsPer[2]; i++ )
	{
		centralUVScanline( 0.75f + 0.25f * i / float( vertsPer[2] - 1 ) );
	}

	// Output the left and right "wings" of the UV map. Might make more sense if each face was
	// contiguous instead of interleaving the scanlines of these two, but this order is fixed
	// for backwards compatibility.
	uvFaceIndices[4] = uvs.size();
	for( int i = 0; i < vertsPer[1]; i++ )
	{
		float v = 0.25f * i / float( vertsPer[1] - 1 );
		for( int j = 0; j < vertsPer[2] - 1; j++ )
		{
			uvs.push_back( Imath::V2f( 0.125f + 0.25f * ( vertsPer[2] - 2 - j ) / float( vertsPer[2] - 1 ), v ) );
		}
		for( int j = 0; j < vertsPer[2] - 1; j++ )
		{
			uvs.push_back( Imath::V2f( 0.875f - 0.25f * j / float( vertsPer[2] - 1 ), v ) );
		}
	}

	assert( (int)uvs.size() == uvSize );
}

// Output some simple UV indices, where the UVs were generated contiguously.
void outputUVIndices( std::vector<int> &uvIndices, int faceIndex, int sizeU, int sizeV, bool flipV, int rotate )
{
	for( int rawV = 0; rawV < sizeV - 1; rawV++ )
	{
		int v = flipV ? sizeV - 2 - rawV : rawV;
		for( int u = 0; u < sizeU - 1; u++ )
		{
			for( int j = 0; j < 4; j++ )
			{
				int pick = ( j + rotate ) % 4;

				if(      pick == 0 ) uvIndices.push_back( faceIndex + v * sizeU + u );
				else if( pick == 1 ) uvIndices.push_back( faceIndex + v * sizeU + u + 1 );
				else if( pick == 2 ) uvIndices.push_back( faceIndex + ( v + 1 ) * sizeU + u + 1 );
				else if( pick == 3 ) uvIndices.push_back( faceIndex + ( v + 1 ) * sizeU + u );
			}
		}
	}
}

// The more complex case for UV indices is on the +X and -X faces, which use the
// left and right "wings" of the UV mapping, and need to splice together the left or right
// column to the central UVs
void outputSplicedUVIndices(
	std::vector<int> &uvIndices, const V3i &vertsPer,
	int faceIndex, int spliceColumn, int spliceSource, bool flipU
)
{
	auto faceVertex = [&uvIndices, faceIndex, spliceColumn, spliceSource, vertsPer]( int u, int v ){
		if( u == spliceColumn )
		{
			uvIndices.push_back( spliceSource + v * vertsPer.x );
		}
		else
		{
			uvIndices.push_back( faceIndex + v * 2 * ( vertsPer.z - 1 ) + u );
		}
	};

	for( int rawU = 0; rawU < vertsPer.z - 1; rawU++ )
	{
		int u = flipU ? vertsPer.z - 2 - rawU : rawU;
		for( int v = 0; v < vertsPer.y - 1; v++ )
		{
			faceVertex( u, v );
			faceVertex( u, v + 1 );
			faceVertex( u + 1, v + 1 );
			faceVertex( u + 1, v );
		}
	}
}

MeshPrimitivePtr createDividedBox( const Box3f &b, const Imath::V3f &divisions )
{
	// How many vertices we need on each axis
	V3i vertsPer = divisions + V3i(1);

	// perFaceIndices and faceSizes store intermediate data for each face
	// The 6 six faces are stored in this order:
	// +Z, -Z, +Y, -Y, +X, -X
	// ( I would have preferred the opposite, but this is consistent with the order
	// used in the normals that we need to be compatible with, and saves a reorder ).
	//
	// faceSizes stores the sizes of the two axes covered by each face.
	// perFaceIndices stores a vertex index for every vertex used by the face
	// ( storing this intermediate data avoids having a huge number of special cases
	// for different overlaps when scanning through every face-vertex outputting
	// vertex ids ).

	std::vector< Imath::V2i > faceSizes;
	faceSizes.push_back( Imath::V2i( vertsPer[0], vertsPer[1] ) );
	faceSizes.push_back( Imath::V2i( vertsPer[0], vertsPer[1] ) );
	faceSizes.push_back( Imath::V2i( vertsPer[0], vertsPer[2] ) );
	faceSizes.push_back( Imath::V2i( vertsPer[0], vertsPer[2] ) );
	faceSizes.push_back( Imath::V2i( vertsPer[1], vertsPer[2] ) );
	faceSizes.push_back( Imath::V2i( vertsPer[1], vertsPer[2] ) );

	std::vector< std::vector< int > > perFaceIndices;

	perFaceIndices.resize( 6 );
	size_t numFaces = 0;
	for( int i = 0; i < 6; i++ )
	{
		perFaceIndices[i].resize( faceSizes[i].x * faceSizes[i].y );
		numFaces += ( faceSizes[i].x - 1 ) * ( faceSizes[i].y - 1 );
	}

	int posSize =
		2 * ( vertsPer.x * vertsPer.y + vertsPer.y * vertsPer.z + vertsPer.z * vertsPer.x )
		- vertsPer.x * 4 - vertsPer.y * 4 - vertsPer.z * 4 + 8;
	std::vector< V3f > pos;
	pos.reserve( posSize );

	// The add* functions that add vertex positions to `pos` also put their indices in
	// perFaceIndices which is used to ensure we index them correctly, which means the
	// output will be a correct cube regardless of what order any of these calls are
	// made in. I've mostly tried to choose an order that makes as much sense as possible
	// ... except for the corners. I can't really see any justification for this
	// particular order, but we want to keep backwards compatibility, so we're just using
	// the same order as before.

	addCorner( V3i( 0, 0, 0 ), vertsPer, pos, perFaceIndices );
	addCorner( V3i( 1, 0, 0 ), vertsPer, pos, perFaceIndices );
	addCorner( V3i( 1, 1, 0 ), vertsPer, pos, perFaceIndices );
	addCorner( V3i( 0, 1, 0 ), vertsPer, pos, perFaceIndices );
	addCorner( V3i( 1, 0, 1 ), vertsPer, pos, perFaceIndices );
	addCorner( V3i( 1, 1, 1 ), vertsPer, pos, perFaceIndices );
	addCorner( V3i( 0, 0, 1 ), vertsPer, pos, perFaceIndices );
	addCorner( V3i( 0, 1, 1 ), vertsPer, pos, perFaceIndices );

	std::vector<V2i> corners = { V2i( 0, 0 ), V2i( 0, 1 ), V2i( 1, 0 ), V2i( 1, 1 ) };
	for( V2i q : corners )
	{
		addXEdge( q, vertsPer, pos, perFaceIndices );
	}

	for( V2i q : corners )
	{
		addYEdge( q, vertsPer, pos, perFaceIndices );
	}

	for( V2i q : corners )
	{
		addZEdge( q, vertsPer, pos, perFaceIndices );
	}

	addXFace( 0, vertsPer, pos, perFaceIndices );
	addXFace( 1, vertsPer, pos, perFaceIndices );

	addYFace( 0, vertsPer, pos, perFaceIndices );
	addYFace( 1, vertsPer, pos, perFaceIndices );

	addZFace( 0, vertsPer, pos, perFaceIndices );
	addZFace( 1, vertsPer, pos, perFaceIndices );

	assert( (int)pos.size() == posSize );

	// For simplicity, we generate the vertex positions as unit cube spanning [0,1] on all axes,
	// and only scale it to the requested size/location here.
	for( V3f &p : pos )
	{
		p = b.min + b.size() * p ;
	}

	std::vector<int> verticesPerFace( numFaces, 4 );

	std::vector<int> vertexIds;
	vertexIds.reserve( numFaces * 4 );

	// Output the vertex ids - we've already prepped the indices needed for each
	// cube face, so we just need to visit each of the 6 faces, and output 4 verts
	// for each sub face. The 3rd and 4th arguments are a flag to flip the order
	// ( needed to winding order correct ), and a offset to rotation ( needed only
	// for the sake of backwards compatibility ).
	// The order we output these faces in is also arbitrary, and chosen solely
	// for backwards compatibility.
	outputVertexIDsForFace( faceSizes[1], perFaceIndices[1], true, 0, vertexIds );
	outputVertexIDsForFace( faceSizes[4], perFaceIndices[4], false, 0, vertexIds );
	outputVertexIDsForFace( faceSizes[0], perFaceIndices[0], false, 1, vertexIds );
	outputVertexIDsForFace( faceSizes[5], perFaceIndices[5], true, 0, vertexIds );
	outputVertexIDsForFace( faceSizes[2], perFaceIndices[2], true, 2, vertexIds );
	outputVertexIDsForFace( faceSizes[3], perFaceIndices[3], false, 0, vertexIds );

	const std::string interpolation = "linear";
	MeshPrimitivePtr result = new MeshPrimitive(
		new IntVectorData( std::move( verticesPerFace ) ),
		new IntVectorData( std::move( vertexIds ) ),
		interpolation,
		new V3fVectorData( std::move( pos ) )
	);


	std::vector<Imath::V2f> uvs;
	int uvFaceIndices[5];
	// Output UVs
	outputUVs( vertsPer, uvs, uvFaceIndices );

	std::vector<int> uvIndices;
	uvIndices.reserve( vertexIds.size() );

	// Output UV indices. The order we visit faces in, and the flip and rotate parameters
	// must match the calls to outputVertexIDsForFace. In addition, for UVs, there are
	// two different kinds edge sharing:
	// * edge sharing that is inherent in using UVs from the central column which are
	//   generated contiguously ( uses outputUVIndices )
	// * edge sharing on the "wings" on the left and right, where one edge is shared
	//   with the central column ( uses outputSplicedUVIndices )
	outputUVIndices( uvIndices, uvFaceIndices[2], vertsPer[0], vertsPer[1], true, 0 );
	outputSplicedUVIndices( uvIndices, vertsPer,
		uvFaceIndices[4] + vertsPer[2] - 1, vertsPer[2] - 1, vertsPer[0] - 1, false
	);
	outputUVIndices( uvIndices, uvFaceIndices[0], vertsPer[0], vertsPer[1], false, 1 );
	outputSplicedUVIndices( uvIndices, vertsPer,
		uvFaceIndices[4] - 1, 0, 0, true
	);
	outputUVIndices( uvIndices, uvFaceIndices[1], vertsPer[0], vertsPer[2], true, 2 );
	outputUVIndices( uvIndices, uvFaceIndices[3], vertsPer[0], vertsPer[2], false, 0 );

	result->variables["uv"] = PrimitiveVariable(
		PrimitiveVariable::FaceVarying,
		new V2fVectorData( std::move( uvs ), GeometricData::UV ),
		new IntVectorData ( std::move( uvIndices ) )
	);

	// Normals are by far the simplest primvar to generate - we just output one value for each face,
	// and then output the appropriate number of repeated indices for each face.

	std::vector<Imath::V3f> normals {
		Imath::V3f( 0, 0, 1 ),
		Imath::V3f( 0, 0, -1 ),
		Imath::V3f( 0, 1, 0 ),
		Imath::V3f( 0, -1, 0 ),
		Imath::V3f( 1, 0, 0 ),
		Imath::V3f( -1, 0, 0 ),
	};

	std::vector<int> nIndices;

	nIndices.reserve( vertexIds.size() );

	for( int i : { 1, 4, 0, 5, 2, 3 } )
	{
		const int n = ( faceSizes[i].x - 1 ) * ( faceSizes[i].y - 1 ) * 4;
		for( int j = 0; j < n; j++ )
		{
			nIndices.push_back( i );
		}
	};

	result->variables["N"] = PrimitiveVariable(
		PrimitiveVariable::FaceVarying,
		new V3fVectorData( std::move( normals ), GeometricData::Normal ),
		new IntVectorData ( std::move( nIndices ) )
	);

	return result;
}

} // namespace

GAFFER_NODE_DEFINE_TYPE( Cube );

size_t Cube::g_firstPlugIndex = 0;

Cube::Cube( const std::string &name )
	:	ObjectSource( name, "cube" )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new V3fPlug( "dimensions", Plug::In, V3f( 1.0f ), V3f( 0.0f ) ) );
	addChild( new V3iPlug( "divisions", Plug::In, V3i( 1 ), V3i( 1 ) ) );
}

Cube::~Cube()
{
}

Gaffer::V3fPlug *Cube::dimensionsPlug()
{
	return getChild<V3fPlug>( g_firstPlugIndex );
}

const Gaffer::V3fPlug *Cube::dimensionsPlug() const
{
	return getChild<V3fPlug>( g_firstPlugIndex );
}

Gaffer::V3iPlug *Cube::divisionsPlug()
{
	return getChild<V3iPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::V3iPlug *Cube::divisionsPlug() const
{
	return getChild<V3iPlug>( g_firstPlugIndex + 1 );
}

void Cube::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ObjectSource::affects( input, outputs );

	if(
		input->parent<V3fPlug>() == dimensionsPlug() ||
		input->parent<V3iPlug>() == divisionsPlug()
	)
	{
		outputs.push_back( sourcePlug() );
	}
}

void Cube::hashSource( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	dimensionsPlug()->hash( h );
	divisionsPlug()->hash( h );
}

IECore::ConstObjectPtr Cube::computeSource( const Context *context ) const
{
	V3f dimensions = dimensionsPlug()->getValue();
	V3i divisions = divisionsPlug()->getValue();

	return createDividedBox( Box3f( -dimensions / 2.0f, dimensions / 2.0f ), divisions );
}

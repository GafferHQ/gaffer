//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/MeshSegments.h"

#include "IECore/DataAlgo.h"

#include "IECoreScene/MeshAlgo.h"
#include "IECoreScene/MeshPrimitive.h"

using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

namespace {

// Output a segment value for each face which groups faces into groups which share the same index targets.
// The internal code for this function calls these index targets "vertices", since that is the easiest case
// to think about, but they could be something else with a face-varying index ( like UVs ) - this function
// just requires that the indices are clustered into contiguous "faces", where the size of each face is
// given by verticesPerFace, and that the number of things pointed to by the indices is numIndexed.
void segmentIndices( const std::vector<int> &verticesPerFace, const std::vector<int> &indices, int numIndexed, std::vector<int> &uniformSegments )
{
	// The core of this function is the segments vector, which has an element for each vertex.
	// Each vertex must store the index of a vertex with a lower index than itself inside the same
	// connected segment ( or itself if it is the lowest index in the segment ).
	std::vector<int> segments( numIndexed );

	// Before we add any faces, every vertex is in a separate segment, so it just points to itself.
	for( int i = 0; i < numIndexed; i++ )
	{
		segments[i] = i;
	}

	// We now update the segments by adding each face
	int vertexIdsIndex = 0;
	for( int f : verticesPerFace )
	{
		// Find the lowest vertex index for any segment this face connects
		int minVertex = numIndexed;
		for( int i = 0; i < f; i++ )
		{
			// For each vertex in the current face
			int v = indices[ vertexIdsIndex + i ];

			// Trace the references between vertices until we find a vertex that points to itself,
			// this is the lowest vertex index in this segment
			while( true )
			{
				int vNext = segments[v];
				if( vNext == v )
				{
					break;
				}
				v = vNext;
			}

			// Find the lowest vertex of any connected segment
			minVertex = std::min( minVertex, v );
		}

		// We now need to merge the segments by writing the lowest index found to all the segments we found.
		// The minimum to maintain validity is to write the new index to the final vertex in the chain for
		// each corner of the face.  In order to ensure a O( N ) runtime however, we need to make sure that
		// we overwrite every vertex we examined - this means that each link is only followed while considering
		// one face - the next time we get to it, we will be able to shortcut straight to the lowest vertex
		// in the segment.  This guarantees that we aren't repeatedly following the same link to cause
		// worse than linear runtime.
		//
		// This could be done by allocating a ( usually small ) vector to hold the vertices that we visit for
		// each face, however performance is very slightly better ( measured as a consistent 2 - 3% ) if we
		// just repeat the same traversal.  I'm guessing this is because we need to write to each of the
		// intermediate vertices anyway, so there isn't much caching cost in reading them as well, and it's
		// better for the cache to not introduce more memory locations ( always better to avoid unpredictable
		// allocations anyway ).
		for( int i = 0; i < f; i++ )
		{
			int v = indices[ vertexIdsIndex + i ];
			while( true )
			{
				int vNext = segments[v];
				segments[v] = minVertex;
				if( vNext == v )
				{
					break;
				}
				v = vNext;
			}
		}

		// Advance to next face
		vertexIdsIndex += f;
	}

	// We now have all faces considered, and have the property that every vertex points to a vertex less than
	// itself in the segment unless it is lowest in the segment.  This means we can now just process all
	// vertices, starting from the lowest.  If a vertex points to itself, it marks a new segment, otherwise
	// it can just take the segment index from the vertex it points to ( which is guaranteed to have already
	// been processed, since we process in order ).
	int numSegments = 0;
	for( int i = 0; i < numIndexed; i++ )
	{
		if( segments[i] == i )
		{
			numSegments++;
			segments[i] = numSegments - 1;
		}
		else
		{
			segments[i] = segments[ segments[i] ];
		}
	}

	uniformSegments.clear();
	uniformSegments.reserve( verticesPerFace.size() );

	// Convert from whatever "vertices" we are segmenting ( which may actually be UVs or anything else
	// that is indexed ) to uniform ( one value per face ).  We do this just by reading one vertex from
	// each face.
	vertexIdsIndex = 0;
	for( int f : verticesPerFace )
	{
		uniformSegments.push_back( segments[ indices[ vertexIdsIndex ] ] );
		vertexIdsIndex += f;
	}
}

} // namespace

size_t MeshSegments::g_firstPlugIndex = 0;

GAFFER_NODE_DEFINE_TYPE( MeshSegments );

MeshSegments::MeshSegments( const std::string &name )
	:	ObjectProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "connectivity", Plug::In, "P" ) );
	addChild( new StringPlug( "segment", Plug::In, "segment" ) );
}

MeshSegments::~MeshSegments()
{
}

Gaffer::StringPlug *MeshSegments::connectivityPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *MeshSegments::connectivityPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *MeshSegments::segmentPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *MeshSegments::segmentPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

bool MeshSegments::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return
		ObjectProcessor::affectsProcessedObject( input ) ||
		input == connectivityPlug() ||
		input == segmentPlug()
	;
}

void MeshSegments::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ObjectProcessor::hashProcessedObject( path, context, h );

	connectivityPlug()->hash( h );
	segmentPlug()->hash( h );
}

IECore::ConstObjectPtr MeshSegments::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	const std::string segmentPrimVar = segmentPlug()->getValue();
	const std::string connectivityPrimVar = connectivityPlug()->getValue();
	const MeshPrimitive *mesh = runTimeCast<const MeshPrimitive>( inputObject );
	if( !mesh || !segmentPrimVar.size() )
	{
		return inputObject;
	}

	const std::vector<int> &verticesPerFace = mesh->verticesPerFace()->readable();
	IntVectorDataPtr uniformSegmentsData;

	if( connectivityPrimVar == "" )
	{
		uniformSegmentsData = new IntVectorData();
		segmentIndices(
			verticesPerFace, mesh->vertexIds()->readable(),
			mesh->variableSize( PrimitiveVariable::Interpolation::Vertex ),
			uniformSegmentsData->writable()
		);
	}
	else
	{
		auto it = mesh->variables.find( connectivityPrimVar );
		if( it == mesh->variables.end() )
		{
			throw IECore::Exception( "No primitive variable named \"" + connectivityPrimVar + "\"" );
		}

		if( it->second.interpolation == PrimitiveVariable::Interpolation::Vertex || it->second.interpolation == PrimitiveVariable::Interpolation::Varying )
		{
			if( it->second.indices )
			{
				throw IECore::Exception( "Vertex primitive variable " + connectivityPrimVar + " has indices.  Indices are not supported on vertex primitive variables." );
			}
			uniformSegmentsData = new IntVectorData();
			segmentIndices(
				verticesPerFace, mesh->vertexIds()->readable(),
				mesh->variableSize( PrimitiveVariable::Interpolation::Vertex ),
				uniformSegmentsData->writable()
			);
		}
		else if( it->second.interpolation == PrimitiveVariable::Interpolation::FaceVarying )
		{
			if( !it->second.indices )
			{
				// \todo : suggest using PrimitiveVariableWeld, once this node exists." );
				throw IECore::Exception( "FaceVarying primitive variable " + connectivityPrimVar + " must be indexed in order to use as connectivity." );
			}
			uniformSegmentsData = new IntVectorData();
			segmentIndices(
				verticesPerFace, it->second.indices->readable(),
				IECore::size( it->second.data.get() ),
				uniformSegmentsData->writable()
			);
		}
		else if( it->second.interpolation == PrimitiveVariable::Interpolation::Uniform )
		{
			if( !it->second.indices )
			{
				throw IECore::Exception( "Uniform primitive variable " + connectivityPrimVar + " must be indexed in order to use as connectivity." );
			}
			uniformSegmentsData = it->second.indices;
		}
		else if( it->second.interpolation == PrimitiveVariable::Interpolation::Constant )
		{
			// Not very useful, but it is completely consistent that if you segment based on a constant primvar,
			// all faces must be in the same segment
			uniformSegmentsData = new IntVectorData();
			uniformSegmentsData->writable().resize( mesh->verticesPerFace()->readable().size(), 0 );
		}
		else
		{
			throw IECore::Exception( "Invalid interpolation for primitive variable \"" + connectivityPrimVar + "\".");
		}
	}

	MeshPrimitivePtr result = mesh->copy();
	result->variables[segmentPrimVar] = PrimitiveVariable( PrimitiveVariable::Uniform, uniformSegmentsData );
	return result;
}

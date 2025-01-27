//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Lucien Fostier. All rights reserved.
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

#include "GafferML/TensorToMesh.h"

#include "IECoreScene/MeshPrimitive.h"


using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferML;

GAFFER_NODE_DEFINE_TYPE( TensorToMesh );

size_t TensorToMesh::g_firstPlugIndex = 0;

TensorToMesh::TensorToMesh( const std::string &name )
	:	ObjectSource( name, "tensorMesh" )
{

	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new TensorPlug( "position" ) );
	addChild( new TensorPlug( "vertexIds" ) );

}

TensorToMesh::~TensorToMesh()
{
}

TensorPlug *TensorToMesh::positionTensorPlug()
{
	return getChild<TensorPlug>( g_firstPlugIndex );
}

const TensorPlug *TensorToMesh::positionTensorPlug() const
{
	return getChild<TensorPlug>( g_firstPlugIndex );
}

TensorPlug *TensorToMesh::vertexIdsTensorPlug()
{
	return getChild<TensorPlug>( g_firstPlugIndex + 1 );
}

const TensorPlug *TensorToMesh::vertexIdsTensorPlug() const
{
	return getChild<TensorPlug>( g_firstPlugIndex + 1 );
}

void TensorToMesh::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ObjectSource::affects( input, outputs );
	if ( input == positionTensorPlug() || input == vertexIdsTensorPlug() )
	{
		outputs.push_back(sourcePlug());
	}

}

void TensorToMesh::hashSource( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	positionTensorPlug()->hash( h );
	vertexIdsTensorPlug()->hash( h );
}

IECore::ConstObjectPtr TensorToMesh::computeSource( const Context *context ) const
{
	ConstTensorPtr positionTensorData = positionTensorPlug()->getValue();

	if( !positionTensorData->value() )
	{
		throw IECore::Exception( "Empty Position tensor" );
	}

	auto positionShape = positionTensorData->shape();
	if ( positionShape.size() != 3 )
	{
		throw IECore::Exception( "Invalid position tensor number of dimensions, should have 3 dimensions" );
	}

	if ( positionShape[2] % 3 != 0 )
	{
		throw IECore::Exception( "Invalid position dimensions, only 3d coordinates are supported" );
	}

	if ( positionTensorData->value().GetTensorTypeAndShapeInfo().GetElementType() != ONNX_TENSOR_ELEMENT_DATA_TYPE_FLOAT )
	{
		throw IECore::Exception( "Invalid data type input for position tensor, only float is currently supported" );
	}

	const size_t count = positionTensorData->value().GetTensorTypeAndShapeInfo().GetElementCount();

	const float *sourceData = positionTensorData->value().GetTensorData<float>();

	ConstTensorPtr vertexIdsTensorData = vertexIdsTensorPlug()->getValue();
	if( !vertexIdsTensorData->value() )
	{
		throw IECore::Exception( "Empty VertexIds tensor" );
	}

	if ( vertexIdsTensorData->value().GetTensorTypeAndShapeInfo().GetElementType() != ONNX_TENSOR_ELEMENT_DATA_TYPE_INT64 )
	{
		throw IECore::Exception( "Invalid data type input for vertexIds tensor, only int64 is currently supported" );
	}

	const int64_t *sourceVertexIdsData = vertexIdsTensorData->value().GetTensorData<int64_t>();

	// Copy out topology
	IntVectorDataPtr verticesPerFaceData = new IntVectorData;
	vector<int> &verticesPerFace = verticesPerFaceData->writable();

	IntVectorDataPtr vertexIdsData = new IntVectorData;
	vector<int> &vertexIds = vertexIdsData->writable();

	V3fVectorDataPtr pointsData = new V3fVectorData;
	vector<V3f> &points = pointsData->writable();

	for( size_t i = 0; i < count; i += 3 )
	{
		Imath::V3f v;
		for( size_t j = 0; j < 3; j++ )
		{
			v[j] = *( sourceData + ( i + j ) );
		}
		points.push_back( v );
	}

	int vertexPerFace = vertexIdsTensorData->value().GetTensorTypeAndShapeInfo().GetShape()[1];
	for( int i = 0; i < vertexIdsTensorData->value().GetTensorTypeAndShapeInfo().GetShape()[0]; i++ )
	{
		verticesPerFace.push_back(vertexPerFace);
		for ( int j = 0; j < vertexPerFace; j++ )
		{
			vertexIds.push_back( *( sourceVertexIdsData + i * vertexPerFace + j ) );
		}
	}

	return new MeshPrimitive( verticesPerFaceData, vertexIdsData, "linear", pointsData );
}

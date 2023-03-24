//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, John Haddon. All rights reserved.
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

#include "GafferScene/Wireframe.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/MeshPrimitive.h"
#include "IECoreScene/CurvesPrimitive.h"

#include "IECore/DataAlgo.h"

#include "boost/functional/hash.hpp"

#include "fmt/format.h"

#include <unordered_set>

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

struct MakeWireframe
{

	CurvesPrimitivePtr operator() ( const V2fVectorData *data, const MeshPrimitive *mesh, const string &name, const PrimitiveVariable &primitiveVariable )
	{
		return makeWireframe<V2fVectorData>( data, mesh, name, primitiveVariable );
	}

	CurvesPrimitivePtr operator() ( const V3fVectorData *data, const MeshPrimitive *mesh, const string &name, const PrimitiveVariable &primitiveVariable )
	{
		return makeWireframe<V3fVectorData>( data, mesh, name, primitiveVariable );
	}

	CurvesPrimitivePtr operator() ( const Data *data, const MeshPrimitive *mesh, const string &name, const PrimitiveVariable &primitiveVariable )
	{
		throw IECore::Exception(
			fmt::format( "PrimitiveVariable \"{}\" has unsupported type \"{}\"", name, data->typeName() )
		);
	}

	private :

		template<typename T>
		CurvesPrimitivePtr makeWireframe( const T *data, const MeshPrimitive *mesh, const string &name, const PrimitiveVariable &primitiveVariable )
		{
			using Vec = typename T::ValueType::value_type;
			using DataView = PrimitiveVariable::IndexedView<Vec>;

			DataView dataView;
			const vector<int> *vertexIds = nullptr;
			switch( primitiveVariable.interpolation )
			{
				case PrimitiveVariable::Vertex :
				case PrimitiveVariable::Varying :
					vertexIds = &mesh->vertexIds()->readable();
					dataView = DataView( primitiveVariable );
					break;
				case PrimitiveVariable::FaceVarying :
					vertexIds = primitiveVariable.indices ? &primitiveVariable.indices->readable() : nullptr;
					dataView = DataView( data->readable(), nullptr );
					break;
				default :
					throw IECore::Exception(
						fmt::format( "Primitive variable \"{}\" must have Vertex, Varying or FaceVarying interpolation", name )
					);
			}

			IECore::V3fVectorDataPtr pData = new V3fVectorData;
			pData->setInterpretation( GeometricData::Point );
			vector<V3f> &p = pData->writable();
			// We don't know upfront how many edges we will generate.
			// `mesh->variableSize( PrimitiveVariable::FaceVarying )` gives us
			// an upper bound, but edges can be shared by faces in which case
			// we only add the edge once. For a fully closed mesh without border
			// edges, we will only generate half of the edges from this upper bound.
			// (For non-manifold meshes we could generate even fewer, but we assume
			// we will not be given those).
			const size_t minExpectedEdges = mesh->variableSize( PrimitiveVariable::FaceVarying ) / 2;
			// Each edge we add will add 2 points to `p`.
			p.reserve( minExpectedEdges * 2 );

			using Edge = std::pair<int, int>;
			using EdgeSet = unordered_set<Edge, boost::hash<Edge>>;
			EdgeSet edgesVisited;
			edgesVisited.reserve( mesh->variableSize( PrimitiveVariable::FaceVarying ) );

			int vertexIdsIndex = 0;
			for( int numVertices : mesh->verticesPerFace()->readable() )
			{
				for( int i = 0; i < numVertices; ++i )
				{
					int index0 = vertexIdsIndex + i;
					int index1 = vertexIdsIndex + (i + 1) % numVertices;
					if( vertexIds )
					{
						index0 = (*vertexIds)[index0];
						index1 = (*vertexIds)[index1];
					}

					Edge edge( min( index0, index1 ), max( index0, index1 ) );
					if( edgesVisited.insert( edge ).second )
					{
						p.push_back( v3f( dataView[index0] ) );
						p.push_back( v3f( dataView[index1] ) );
					}
				}
				vertexIdsIndex += numVertices;
			}

			IECore::IntVectorDataPtr vertsPerCurveData = new IntVectorData;
			vertsPerCurveData->writable().resize( p.size() / 2, 2 );

			CurvesPrimitivePtr result = new CurvesPrimitive( vertsPerCurveData );
			result->variables["P"] = PrimitiveVariable( PrimitiveVariable::Vertex, pData );
			return result;
		}

		V3f v3f( const Imath::V3f &v )
		{
			return v;
		}

		V3f v3f( const Imath::V2f &v )
		{
			return V3f( v.x, v.y, 0.0f );
		}

};

/// \todo Perhaps this could go in IECoreScene::MeshAlgo
CurvesPrimitivePtr wireframe( const MeshPrimitive *mesh, const std::string &position )
{
	auto it = mesh->variables.find( position );
	if( it == mesh->variables.end() )
	{
		throw IECore::Exception( fmt::format( "MeshPrimitive has no primitive variable named \"{}\"", position ) );
	}

	CurvesPrimitivePtr result = dispatch( it->second.data.get(), MakeWireframe(), mesh, it->first, it->second );
	return result;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Wireframe
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( Wireframe );

size_t Wireframe::g_firstPlugIndex = 0;

Wireframe::Wireframe( const std::string &name )
	:	Deformer( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "position", Plug::In, "P" ) );
	addChild( new FloatPlug( "width", Plug::In, 1.0f, 0.0f ) );
}

Wireframe::~Wireframe()
{
}

Gaffer::StringPlug *Wireframe::positionPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *Wireframe::positionPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::FloatPlug *Wireframe::widthPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::FloatPlug *Wireframe::widthPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

bool Wireframe::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return Deformer::affectsProcessedObject( input ) ||
		input == positionPlug() ||
		input == widthPlug()
	;
}

void Wireframe::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Deformer::hashProcessedObject( path, context, h );
	positionPlug()->hash( h );
	widthPlug()->hash( h );
}

IECore::ConstObjectPtr Wireframe::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	const MeshPrimitive *mesh = runTimeCast<const MeshPrimitive>( inputObject );
	if( !mesh )
	{
		return inputObject;
	}

	CurvesPrimitivePtr result = wireframe( mesh, positionPlug()->getValue() );
	for( const auto &pv : mesh->variables )
	{
		if( pv.second.interpolation == PrimitiveVariable::Constant )
		{
			// OK to reference data directly, because result becomes const upon return.
			result->variables.insert( pv );
		}
	}
	result->variables["width"] = PrimitiveVariable( PrimitiveVariable::Constant, new FloatData( widthPlug()->getValue() ) );

	return result;
}

bool Wireframe::adjustBounds() const
{
	if( !Deformer::adjustBounds() )
	{
		return false;
	}

	return positionPlug()->getValue() != "P";
}

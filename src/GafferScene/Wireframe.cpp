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

	CurvesPrimitivePtr operator() ( const V2fVectorData *positions, const vector<int> &verticesPerFace, const vector<int> &vertexIds )
	{
		return makeWireframe( positions->baseReadable(), 2, verticesPerFace, vertexIds );
	}

	CurvesPrimitivePtr operator() ( const V3fVectorData *positions, const vector<int> &verticesPerFace, const vector<int> &vertexIds )
	{
		return makeWireframe( positions->baseReadable(), 3, verticesPerFace, vertexIds );
	}

	CurvesPrimitivePtr operator() ( const Data *positions, const vector<int> &verticesPerFace, const vector<int> &vertexIds )
	{
		throw IECore::Exception( boost::str(
			boost::format( "Position has unsupported type \"%1%\"" ) % positions->typeName()
		) );
	}

	private :

		V3f position( const float *positions, int dimensions, int index )
		{
			V3f result( 0.0f );
			for( int i = 0; i < dimensions; ++i )
			{
				result[i] = positions[index*dimensions+i];
			}
			return result;
		}

		CurvesPrimitivePtr makeWireframe( const float *positions, int dimensions, const vector<int> &verticesPerFace, const vector<int> &vertexIds )
		{
			IECore::V3fVectorDataPtr pData = new V3fVectorData;
			pData->setInterpretation( GeometricData::Point );
			vector<V3f> &p = pData->writable();

			using Edge = std::pair<int, int>;
			using EdgeSet = unordered_set<Edge, boost::hash<Edge>>;
			EdgeSet edgesVisited;

			int vertexIdsIndex = 0;
			for( int numVertices : verticesPerFace )
			{
				for( int i = 0; i < numVertices; ++i )
				{
					int index0 = vertexIds[vertexIdsIndex + i];
					int index1 = vertexIds[vertexIdsIndex + (i + 1) % numVertices];
					Edge edge( min( index0, index1 ), max( index0, index1 ) );
					if( edgesVisited.insert( edge ).second )
					{
						p.push_back( position( positions, dimensions, index0 ) );
						p.push_back( position( positions, dimensions, index1 ) );
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

};

/// \todo Perhaps this could go in IECoreScene::MeshAlgo
CurvesPrimitivePtr wireframe( const MeshPrimitive *mesh, const std::string &position )
{
	auto it = mesh->variables.find( position );
	if( it == mesh->variables.end() )
	{
		throw IECore::Exception( boost::str(
			boost::format( "MeshPrimitive has no primitive variable \"%1%\"" ) % position
		) );
	}

	const IntVectorData *indices = nullptr;
	switch( it->second.interpolation )
	{
		case PrimitiveVariable::Vertex :
			indices = mesh->vertexIds();
			if( it->second.indices )
			{
				throw IECore::Exception( "Vertex primitive variable with indices not supported" );
			}
			break;
		case PrimitiveVariable::FaceVarying :
			indices = it->second.indices.get();
			break;
		default :
			throw IECore::Exception( "Position must have Vertex or FaceVarying interpolation" );
	}

	CurvesPrimitivePtr result = dispatch( it->second.data.get(), MakeWireframe(), mesh->verticesPerFace()->readable(), indices->readable() );
	return result;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Wireframe
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( Wireframe );

size_t Wireframe::g_firstPlugIndex = 0;

Wireframe::Wireframe( const std::string &name )
	:	SceneElementProcessor( name, PathMatcher::NoMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "position", Plug::In, "P" ) );
	addChild( new FloatPlug( "width", Plug::In, 1.0f, 0.0f ) );

	// Fast pass-throughs for things we don't modify
	outPlug()->boundPlug()->setInput( inPlug()->boundPlug() );
	outPlug()->attributesPlug()->setInput( inPlug()->attributesPlug() );
	outPlug()->transformPlug()->setInput( inPlug()->transformPlug() );
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

void Wireframe::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );

	if(
		input == positionPlug() ||
		input == widthPlug()
	)
	{
		outputs.push_back( outPlug()->objectPlug() );
	}
}

bool Wireframe::processesObject() const
{
	return true;
}

void Wireframe::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	positionPlug()->hash( h );
	widthPlug()->hash( h );
}

IECore::ConstObjectPtr Wireframe::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const
{
	const MeshPrimitive *mesh = runTimeCast<const MeshPrimitive>( inputObject.get() );
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

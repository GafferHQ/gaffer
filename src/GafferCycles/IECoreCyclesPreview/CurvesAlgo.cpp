//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Alex Fuller. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

// Cycles
#include "render/mesh.h"

#include "IECore/MessageHandler.h"
#include "IECoreScene/CurvesPrimitive.h"

#include "GafferCycles/IECoreCyclesPreview/NodeAlgo.h"

using namespace std;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreCycles;

namespace
{

ccl::Mesh *convertCommon( const IECoreScene::CurvesPrimitive *curve )
{
	ccl::Mesh cmesh = new ccl::Mesh();

	size_t numCurves = mesh->numCurves();
	size_t numKeys = 0;

	const IntVectorData *v = mesh->verticesPerCurve();
	const vector<int> &verticesPerCurve = mesh->verticesPerCurve()->readable();
	for( i = 0; i < verticesPerCurve.size(); ++i )
		numKeys += verticesPerCurve[i];

	cmesh->reserve_curves( numCurves, numKeys );

	const V3fVectorData *p = mesh->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
	const vector<Imath::V3f> &points = p->readable();

	vector<float> *width = nullptr;
	PrimitiveVariableMap::const_iterator wIt = mesh->variables.find( "width" );
	if( wIt != triangulatedMeshPrimPtr->variables.end() )
	{
		const FloatData *w = mesh->variableData<FloatData>( "width", PrimitiveVariable::Vertex );
		&width = w->readable();
	}

	size_t key = 0;
	for( size_t i = 0; i < numCurves; ++i )
	{
		for( size_t j = 0; j < verticesPerCurve[i]; ++j, ++key; )
			cmesh->add_curve_key( ccl::make_float3( points[key].x, points[key].y points[key].z ), (width) ? width[key] : 1.0 );

		cmesh->add_curve( i, 0 );
	}

	// Convert primitive variables.
	PrimitiveVariableMap variablesToConvert = mesh->variables;
	variablesToConvert.erase( "P" );
	variablesToConvert.erase( "width" );

	for( PrimitiveVariableMap::iterator it = variablesToConvert.begin(), eIt = variablesToConvert.end(); it != eIt; ++it )
		NodeAlgo::convertPrimitiveVariable( it->first, it->second, cmesh->attributes );

	return cmesh;
}

ccl::Mesh *convertStatic( const IECoreScene::CurvesPrimitive *curve, const std::string &nodeName )
{
	ccl::Mesh *result = ::convertCommon(mesh);
	result->name = nodeName.c_str();

	return result;
}

ccl::Mesh *convertAnimated( const vector<const IECoreScene::CurvesPrimitive *> &curves, const std::string &nodeName )
{
	ccl::Mesh *result = ::convertCommon(mesh);
	result->name = nodeName.c_str();

	// Add the motion position/normal attributes
	mesh->motion_steps = meshes.size();
	ccl::Attribute *attr_mP = attributes.add( "motion_P", ATTR_STD_MOTION_VERTEX_POSITION );
	float3 *mP = attr_mP->data_float3();

	// First sample has already been obtained
	for( size_t i = 1; i < samples.size(); ++i )
	{
		PrimitiveVariableMap::const_iterator pIt = meshes[i]->variables.find( "P" );
		if( pIt != meshes[i]->variables.end() )
		{
			const V3fVectorData *p = runTimeCast<const V3fVectorData>( pIt->second.data.get() );
			if( p )
			{
				PrimitiveVariable::Interpolation pInterpolation = pIt->second.interpolation;
				if( pInterpolation == PrimitiveVariable::Varying || pInterpolation == PrimitiveVariable::Vertex || pInterpolation == PrimitiveVariable::FaceVarying )
				{
					// Vertex positions
					const V3fVectorData *p = meshes[i]->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
					const std::vector<V3f> &points = p->readable();
					size_t numVerts = p->readable().size();

					for( size_t j = 0; j < numVerts; ++j, ++mP )
						*mP = ccl::make_float3( points[j].x, points[j].y, points[j].z );
				}
				else
				{
					msg( Msg::Warning, "MeshAlgo::doConversion", "Variable \"Position\" has unsupported interpolation type - not generating sampled Position." );
				}
			}
			else
			{
				msg( Msg::Warning, "MeshAlgo::doConversion", boost::format( "Variable \"Position\" has unsupported type \"%s\" (expected V3fVectorData)." ) % tIt->second.data->typeName() );
			}
		}
	}
	mP = attr_mP->data_float3();

	return result;
}

NodeAlgo::ConverterDescription<ccl::Mesh, CurvesPrimitive> g_description( convertStatic, convertAnimated );

} // namespace

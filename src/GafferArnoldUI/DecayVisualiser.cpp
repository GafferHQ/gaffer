//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine. All rights reserved.
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

#include "GafferScene/Private/IECoreGLPreview/LightFilterVisualiser.h"

#include "IECoreGL/Group.h"
#include "IECoreGL/Primitive.h"
#include "IECoreGL/Renderable.h"
#include "IECoreGL/ShaderLoader.h"
#include "IECoreGL/ShaderStateComponent.h"
#include "IECoreGL/TextureLoader.h"
#include "IECoreGL/ToGLMeshConverter.h"

#include "IECoreScene/MeshPrimitive.h"

#include "IECore/CompoundObject.h"

using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreGL;
using namespace IECoreGLPreview;

namespace
{
typedef std::pair<float, V3f> Knot;
typedef std::vector<Knot> KnotVector;

const char *faceCameraVertexSource()
{
	return
		"#version 120\n"
		""
		"#if __VERSION__ <= 120\n"
		"#define in attribute\n"
		"#endif\n"
		""
		"in vec3 vertexP;"
		"void main()"
		"{"
			"vec3 aimedXAxis, aimedYAxis, aimedZAxis;"
			""
			"aimedXAxis = normalize( gl_ModelViewMatrixInverse * vec4( 0, 0, -1, 0 ) ).xyz;"
			"aimedYAxis = normalize( gl_ModelViewMatrixInverse * vec4( 0, 1, 0, 0 ) ).xyz;"
			"aimedZAxis = normalize( gl_ModelViewMatrixInverse * vec4( 1, 0, 0, 0 ) ).xyz;"
			""
			"vec3 pAimed = vertexP.x * aimedXAxis + vertexP.y * aimedYAxis + vertexP.z * aimedZAxis;"
			"vec4 pCam = gl_ModelViewMatrix * vec4( pAimed, 1 );"
			""
			"gl_Position = gl_ProjectionMatrix * pCam;"
		"}"
		;
}

const char *knotFragSource()
{
	return
		"uniform vec3 markerColor;"
		""
		"void main()"
		"{"
			"gl_FragColor = vec4(markerColor, 1);"
		"}"
		;
}

// \todo These should be consolidated with the function in BarndoorVisualiser into a templatized version
//       Where should that live?
float parameterOrDefault( const IECore::CompoundData *data, const char *key, const float def )
{
	ConstFloatDataPtr member = data->member<const FloatData>( key );
	if( member )
	{
		return member->readable();
	}
	return def;
}

bool parameterOrDefault( const IECore::CompoundData *data, const char *key, const bool def )
{
	ConstBoolDataPtr member = data->member<const BoolData>( key );
	if( member )
	{
		return member->readable();
	}
	return def;
}

void getKnotsToVisualize( const IECoreScene::ShaderNetwork *shaderNetwork, KnotVector &knots )
{
	const IECore::CompoundData *filterShaderParameters = shaderNetwork->outputShader()->parametersData();

	bool nearEnabled = parameterOrDefault( filterShaderParameters, "use_near_atten", false );
	bool farEnabled = parameterOrDefault( filterShaderParameters, "use_far_atten", false );

	if( nearEnabled )
	{
		float nearStart = parameterOrDefault( filterShaderParameters, "near_start", 0.0f );
		float nearEnd = parameterOrDefault( filterShaderParameters, "near_end", 0.0f );

		knots.push_back( Knot( nearStart, V3f( 0.0f ) ) );
		knots.push_back( Knot( nearEnd, V3f( 1.0f ) ) );
	}

	if( farEnabled )
	{
		float farStart = parameterOrDefault( filterShaderParameters, "far_start", 0.0f );
		float farEnd = parameterOrDefault( filterShaderParameters, "far_end", 0.0f );

		knots.push_back( Knot( farStart, V3f( 1.0f ) ) );
		knots.push_back( Knot( farEnd, V3f( 0.0f ) ) );
	}
}

void addKnot( IECoreGL::GroupPtr group, const Knot &knot )
{
	IECoreGL::GroupPtr markerGroup = new IECoreGL::Group();

	IntVectorDataPtr vertsPerPoly = new IntVectorData;
	std::vector<int> &vertsPerPolyVec = vertsPerPoly->writable();
	vertsPerPolyVec.push_back( 3 );

	IntVectorDataPtr vertIds = new IntVectorData;
	std::vector<int> &vertIdsVec = vertIds->writable();
	vertIdsVec.push_back( 0 );
	vertIdsVec.push_back( 1 );
	vertIdsVec.push_back( 2 );

	V3fVectorDataPtr p = new V3fVectorData;
	std::vector<V3f> &pVec = p->writable();
	pVec.push_back( V3f(  0, 0,  0  ) );
	pVec.push_back( V3f(  0, 1, -1  ) );
	pVec.push_back( V3f(  0, 1,  1  ) );

	IECoreScene::MeshPrimitivePtr mesh = new IECoreScene::MeshPrimitive( vertsPerPoly, vertIds, "linear", p );
	ToGLMeshConverterPtr meshConverter = new ToGLMeshConverter( mesh );
	markerGroup->addChild( IECore::runTimeCast<IECoreGL::Renderable>( meshConverter->convert() ) );

	Imath::M44f trans;
	trans.translate( V3f( 0, 0, -knot.first ) );
	trans.scale( V3f( 0.05 ) );
	markerGroup->setTransform( trans );

	IECore::CompoundObjectPtr shaderParameters = new CompoundObject;
	shaderParameters->members()["markerColor"] = new IECore::Color3fData( knot.second );

	markerGroup->getState()->add(
		new IECoreGL::Primitive::Selectable( false ) );
	markerGroup->getState()->add(
		new IECoreGL::ShaderStateComponent(
			ShaderLoader::defaultShaderLoader(),
			TextureLoader::defaultTextureLoader(),
			faceCameraVertexSource(),
			"",
			knotFragSource(), shaderParameters ) );

	group->addChild( markerGroup );
}

class DecayVisualiser final : public LightFilterVisualiser
{

	public :

		IE_CORE_DECLAREMEMBERPTR( DecayVisualiser )

		DecayVisualiser();
		~DecayVisualiser() override;

		Visualisations visualise( const IECore::InternedString &attributeName, const IECoreScene::ShaderNetwork *shaderNetwork, const IECoreScene::ShaderNetwork *lightShaderNetwork, const IECore::CompoundObject *attributes, IECoreGL::ConstStatePtr &state ) const override;

	protected :

		static LightFilterVisualiser::LightFilterVisualiserDescription<DecayVisualiser> g_visualiserDescription;

};

IE_CORE_DECLAREPTR( DecayVisualiser )

// register the new visualiser
LightFilterVisualiser::LightFilterVisualiserDescription<DecayVisualiser> DecayVisualiser::g_visualiserDescription( "ai:lightFilter", "light_decay" );

DecayVisualiser::DecayVisualiser()
{
}

DecayVisualiser::~DecayVisualiser()
{
}

Visualisations DecayVisualiser::visualise( const IECore::InternedString &attributeName, const IECoreScene::ShaderNetwork *shaderNetwork, const IECoreScene::ShaderNetwork *lightShaderNetwork, const IECore::CompoundObject *attributes, IECoreGL::ConstStatePtr &state ) const
{

	KnotVector knots;
	getKnotsToVisualize( shaderNetwork, knots );

	Visualisations v;

	if( knots.empty() )
	{
		return v;
	}

	IECoreGL::GroupPtr result = new IECoreGL::Group();

	for( KnotVector::size_type i = 0; i < knots.size(); ++i )
	{
		addKnot( result, knots[i] );
	}

	v[  VisualisationType::Geometry ] = result;
	return v;
}

} // namespace

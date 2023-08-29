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

#include "GafferSceneUI/StandardLightVisualiser.h"

#include "GafferScene/Private/IECoreGLPreview/LightFilterVisualiser.h"

#include "Gaffer/Metadata.h"

#include "IECoreGL/CurvesPrimitive.h"
#include "IECoreGL/Group.h"
#include "IECoreGL/Renderable.h"
#include "IECoreGL/ShaderLoader.h"
#include "IECoreGL/ShaderStateComponent.h"
#include "IECoreGL/TextureLoader.h"
#include "IECoreGL/ToGLMeshConverter.h"

#include "IECoreScene/MeshPrimitive.h"
#include "IECoreScene/Shader.h"

using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreGL;
using namespace IECoreGLPreview;
using namespace GafferSceneUI;

namespace
{

enum class BarndoorLocation { Top, Right, Left, Bottom };

float parameterOrDefault( const IECore::CompoundData *data, const char *key, const float def )
{
	ConstFloatDataPtr member = data->member<const FloatData>( key );
	if( member )
	{
		return member->readable();
	}
	return def;
}

const char *barndoorFragSource()
{
	return
		"void main()"
		"{"
		"if( mod( float( gl_FragCoord.x + gl_FragCoord.y ), 2.0) == 0.0 )"
			"{"
				"discard;"
			"}"
			"else"
			"{"
				"gl_FragColor = vec4(0, 0, 0, 1);"
			"}"
		"}"
		;
}

void addBarndoor( IECoreGL::GroupPtr result, BarndoorLocation location, float cornerLeft, float cornerRight )
{

	if( !( cornerLeft > 0 || cornerRight > 0 ) )
	{
		return;
	}

	cornerLeft = 1 - cornerLeft * 2.0;
	cornerRight = 1 - cornerRight * 2.0;

	IntVectorDataPtr vertsPerPoly = new IntVectorData;
	std::vector<int> &vertsPerPolyVec = vertsPerPoly->writable();
	vertsPerPolyVec.push_back( 4 );

	IntVectorDataPtr vertIds = new IntVectorData;
	std::vector<int> &vertIdsVec = vertIds->writable();
	vertIdsVec.push_back( 0 );
	vertIdsVec.push_back( 1 );
	vertIdsVec.push_back( 2 );
	vertIdsVec.push_back( 3 );

	V3fVectorDataPtr p = new V3fVectorData;
	std::vector<V3f> &pVec = p->writable();
	pVec.push_back( V3f( -1, 1, 0  ) );
	pVec.push_back( V3f( 1, 1, 0  ) );
	pVec.push_back( V3f( 1, cornerRight, 0  ) );
	pVec.push_back( V3f( -1, cornerLeft, 0  ) );

	IECoreScene::MeshPrimitivePtr mesh = new IECoreScene::MeshPrimitive( vertsPerPoly, vertIds, "linear", p );

	Imath::M44f trans;
	switch( location )
	{
	case BarndoorLocation::Top:
		break;
	case BarndoorLocation::Bottom:
		trans.rotate( V3f( 0, 0, M_PI ) );
		break;
	case BarndoorLocation::Left:
		trans.rotate( V3f( 0, 0, M_PI / 2.0 ) );
		break;
	case BarndoorLocation::Right:
		trans.rotate( V3f( 0, 0, M_PI / -2.0 ) );
		break;
	}

	ToGLMeshConverterPtr meshConverter = new ToGLMeshConverter( mesh );

	IECoreGL::GroupPtr barndoorGroup = new IECoreGL::Group();
	barndoorGroup->getState()->add( new IECoreGL::Primitive::Selectable( false ) );
	barndoorGroup->addChild( IECore::runTimeCast<IECoreGL::Renderable>( meshConverter->convert() ) );
	barndoorGroup->setTransform( trans );

	result->addChild( barndoorGroup );
}

class BarndoorVisualiser final : public LightFilterVisualiser
{

	public :

		IE_CORE_DECLAREMEMBERPTR( BarndoorVisualiser )

		BarndoorVisualiser();
		~BarndoorVisualiser() override;

		Visualisations visualise( const IECore::InternedString &attributeName, const IECoreScene::ShaderNetwork *shaderNetwork, const IECoreScene::ShaderNetwork *lightShaderNetwork, const IECore::CompoundObject *attributes, IECoreGL::ConstStatePtr &state ) const override;

	protected :

		static LightFilterVisualiser::LightFilterVisualiserDescription<BarndoorVisualiser> g_visualiserDescription;

};

IE_CORE_DECLAREPTR( BarndoorVisualiser )

// register the new visualiser
LightFilterVisualiser::LightFilterVisualiserDescription<BarndoorVisualiser> BarndoorVisualiser::g_visualiserDescription( "ai:lightFilter", "barndoor" );

BarndoorVisualiser::BarndoorVisualiser()
{
}

BarndoorVisualiser::~BarndoorVisualiser()
{
}

Visualisations BarndoorVisualiser::visualise( const IECore::InternedString &attributeName, const IECoreScene::ShaderNetwork *shaderNetwork, const IECoreScene::ShaderNetwork *lightShaderNetwork, const IECore::CompoundObject *attributes, IECoreGL::ConstStatePtr &state ) const
{
	if( !lightShaderNetwork )
	{
		return {};
	}

	IECoreGL::GroupPtr result = new IECoreGL::Group();

	const IECore::CompoundData *filterShaderParameters = shaderNetwork->outputShader()->parametersData();

	float topLeft = parameterOrDefault( filterShaderParameters, "barndoor_top_left", 0.0f );
	float topRight = parameterOrDefault( filterShaderParameters, "barndoor_top_right", 0.0f );

	float rightTop = parameterOrDefault( filterShaderParameters, "barndoor_right_top", 1.0f );
	float rightBottom = parameterOrDefault( filterShaderParameters, "barndoor_right_bottom", 1.0f );

	float bottomLeft = parameterOrDefault( filterShaderParameters, "barndoor_bottom_left", 1.0f );
	float bottomRight = parameterOrDefault( filterShaderParameters, "barndoor_bottom_right", 1.0f );

	float leftTop = parameterOrDefault( filterShaderParameters, "barndoor_left_top", 0.0f );
	float leftBottom = parameterOrDefault( filterShaderParameters, "barndoor_left_bottom", 0.0f );


	addBarndoor( result, BarndoorLocation::Top, topLeft, topRight );
	addBarndoor( result, BarndoorLocation::Bottom, 1 - bottomRight, 1 - bottomLeft );
	addBarndoor( result, BarndoorLocation::Left, leftBottom, leftTop );
	addBarndoor( result, BarndoorLocation::Right, 1 - rightTop, 1 - rightBottom );

	if( result->children().size() > 0 )
	{
		IECore::CompoundObjectPtr parameters = new CompoundObject;

		result->getState()->add(
			new IECoreGL::ShaderStateComponent(
				ShaderLoader::defaultShaderLoader(),
				TextureLoader::defaultTextureLoader(),
				"",
				"",
				barndoorFragSource(),
				parameters )
		);

		float innerAngle;
		float coneAngle;
		float radius;
		float lensRadius;

		StandardLightVisualiser::spotlightParameters( "ai:light", lightShaderNetwork, innerAngle, coneAngle, radius, lensRadius );

		const float halfAngle = 0.5 * M_PI * coneAngle / 180.0;
		const float baseRadius = sin( halfAngle ) + lensRadius;
		const float baseDistance = cos( halfAngle );

		Imath::M44f barndoorTrans;
		barndoorTrans.translate( V3f( 0, 0, -baseDistance * .5f ) );
		barndoorTrans.scale( V3f( baseRadius * .5f, baseRadius * .5f, 0 ) );
		result->setTransform( barndoorTrans );
	}

	return { Visualisation::createOrnament( result, false ) };

}

} // namespace

//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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
//     * Neither the name of Cinesite VFX Ltd. nor the names of any
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

#include "LightFilterVisualiserAlgo.h"

#include "GafferScene/Private/IECoreGLPreview/LightFilterVisualiser.h"

#include "IECoreGL/CurvesPrimitive.h"
#include "IECoreGL/Group.h"
#include "IECoreGL/Primitive.h"
#include "IECoreGL/QuadPrimitive.h"
#include "IECoreGL/ShaderLoader.h"
#include "IECoreGL/ShaderStateComponent.h"
#include "IECoreGL/TextureLoader.h"

using namespace Imath;
using namespace IECoreGLPreview;
using namespace IECoreScene;
using namespace IECore;
using namespace IECoreGL;

namespace
{

/// \todo We have similar methods in several places. Can we consolidate them all somewhere? Perhaps a new
/// method of CompoundData?
template<typename T>
T parameterOrDefault( const IECore::CompoundData *parameters, const IECore::InternedString &name, const T &defaultValue )
{
	if( const auto d = parameters->member<TypedData<T>>( name ) )
	{
		return d->readable();
	}

	return defaultValue;
}

const char *texturedFragSource()
{
	return
		"#if __VERSION__ <= 120\n"
		"#define in varying\n"
		"#endif\n"
		""
		"#include \"IECoreGL/ColorAlgo.h\"\n"
		""
		"in vec2 fragmentuv;"
		""
		"uniform sampler2D texture;"
		"uniform vec3 tint;"
		"uniform float saturation;"
		""
		"void main()"
		"{"
			"vec3 c = texture2D( texture, fragmentuv ).xyz;"
			"c = ieAdjustSaturation( c, saturation );"
			"c *= tint;"
			"gl_FragColor = vec4( c, 1.0 );"
		"}"
	;
}

void addWireframeCurveState( IECoreGL::Group *group )
{
	group->getState()->add( new IECoreGL::Primitive::DrawWireframe( false ) );
	group->getState()->add( new IECoreGL::Primitive::DrawSolid( true ) );
	group->getState()->add( new IECoreGL::CurvesPrimitive::UseGLLines( true ) );
	group->getState()->add( new IECoreGL::CurvesPrimitive::GLLineWidth( 2.0f ) );
	group->getState()->add( new IECoreGL::LineSmoothingStateComponent( true ) );
}

class CookieVisualiser final : public LightFilterVisualiser
{

	public :

		IE_CORE_DECLAREMEMBERPTR( CookieVisualiser )

		CookieVisualiser();
		~CookieVisualiser() override;

		Visualisations visualise( const InternedString &attributeName, const ShaderNetwork *filterShaderNetwork, const ShaderNetwork *lightShaderNetwork, const CompoundObject *attributes, IECoreGL::ConstStatePtr &state ) const override;

	protected :

		static LightFilterVisualiser::LightFilterVisualiserDescription<CookieVisualiser> g_visualiserDescription;

};

IE_CORE_DECLAREPTR( CookieVisualiser )

// Register the new visualiser
LightFilterVisualiser::LightFilterVisualiserDescription<CookieVisualiser> CookieVisualiser::g_visualiserDescription( "ri:lightFilter", "PxrCookieLightFilter" );

CookieVisualiser::CookieVisualiser()
{
}

CookieVisualiser::~CookieVisualiser()
{
}

Visualisations CookieVisualiser::visualise( const InternedString &attributeName, const ShaderNetwork *filterShaderNetwork, const ShaderNetwork *lightShaderNetwork, const CompoundObject *attributes, IECoreGL::ConstStatePtr &state ) const
{
	IECoreGL::GroupPtr result = new IECoreGL::Group();

	const StringData *visualiserDrawingModeData = attributes->member<StringData>( "gl:light:drawingMode" );
	const std::string visualiserDrawingMode = visualiserDrawingModeData ? visualiserDrawingModeData->readable() : "texture";

	const CompoundData *filterParameters = filterShaderNetwork->outputShader()->parametersData();

	CompoundObjectPtr shaderParameters = new CompoundObject();

	const V2f size( parameterOrDefault( filterParameters, "width", 1.f ), parameterOrDefault( filterParameters, "height", 1.f ) );

	if( visualiserDrawingMode != "wireframe" )
	{
		IECoreGL::PrimitivePtr quadPrimitive = new IECoreGL::QuadPrimitive( size.x, size.y );

		const std::string map = parameterOrDefault( filterParameters, "map", std::string() );

		if( map.empty() || visualiserDrawingMode == "color" )
		{
			result->getState()->add(
				new IECoreGL::ShaderStateComponent(
					ShaderLoader::defaultShaderLoader(),
					TextureLoader::defaultTextureLoader(),
					"",
					"",
					IECoreGL::Shader::constantFragmentSource(),
					shaderParameters
				)
			);
			quadPrimitive->addPrimitiveVariable(
				"Cs",
				PrimitiveVariable(
					IECoreScene::PrimitiveVariable::Interpolation::Constant,
					new Color3fData( map.empty() ? Color3f( 0.f ) : Color3f( 1.f ) )
				)
			);
		}
		else
		{
			shaderParameters->members()["texture"] = new StringData( map );

			const IntData *maxTextureResolutionData = attributes->member<IntData>( "gl:visualiser:maxTextureResolution" );
			const int resolution = maxTextureResolutionData ? maxTextureResolutionData->readable() : 512;
			shaderParameters->members()["texture:maxResolution"] = new IntData( resolution );

			shaderParameters->members()["tint"] = new Color3fData(
				parameterOrDefault( filterParameters, "tint", Color3f( 1.f ) )
			);
			shaderParameters->members()["saturation"] = new FloatData(
				parameterOrDefault( filterParameters, "saturation", 1.f )
			);

			result->getState()->add(
				new IECoreGL::ShaderStateComponent(
					ShaderLoader::defaultShaderLoader(),
					TextureLoader::defaultTextureLoader(),
					"",
					"",
					texturedFragSource(),
					shaderParameters
				)
			);
		}

		result->addChild(quadPrimitive );
	}

	IECoreGL::GroupPtr outlineResult = new IECoreGL::Group();
	addWireframeCurveState( outlineResult.get() );
	outlineResult->addChild( GafferRenderManUI::lightFilterRectangles( size, 0, V2f( 1.f ), V4f( 0.f ), V4f( 0.f ), 0.f ) );

	return {
		Visualisation::createGeometry( result, IECoreGLPreview::Visualisation::ColorSpace::Scene ),
		Visualisation::createGeometry( outlineResult )
	};
}

}  // namespace
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
T parameterOrDefault( const CompoundData *parameters, const InternedString &name, const T &defaultValue )
{
	if( const auto d = parameters->member<TypedData<T>>( name ) )
	{
		return d->readable();
	}

	return defaultValue;
}

void addWireframeCurveState( IECoreGL::Group *group )
{
	group->getState()->add( new IECoreGL::Primitive::DrawWireframe( false ) );
	group->getState()->add( new IECoreGL::Primitive::DrawSolid( true ) );
	group->getState()->add( new IECoreGL::CurvesPrimitive::UseGLLines( true ) );
	group->getState()->add( new IECoreGL::CurvesPrimitive::GLLineWidth( 2.0f ) );
	group->getState()->add( new IECoreGL::LineSmoothingStateComponent( true ) );
}

class BarnVisualiser final : public LightFilterVisualiser
{

	public :

		IE_CORE_DECLAREMEMBERPTR( BarnVisualiser )

		BarnVisualiser();
		~BarnVisualiser() override;

		Visualisations visualise( const InternedString &attributeName, const ShaderNetwork *filterShaderNetwork, const ShaderNetwork *lightShaderNetwork, const CompoundObject *attributes, IECoreGL::ConstStatePtr &state ) const override;

	protected :

		static LightFilterVisualiser::LightFilterVisualiserDescription<BarnVisualiser> g_visualiserDescription;

};

IE_CORE_DECLAREPTR( BarnVisualiser )

// Register the new visualiser
LightFilterVisualiser::LightFilterVisualiserDescription<BarnVisualiser> BarnVisualiser::g_visualiserDescription( "ri:lightFilter", "PxrBarnLightFilter" );

BarnVisualiser::BarnVisualiser()
{
}

BarnVisualiser::~BarnVisualiser()
{
}

Visualisations BarnVisualiser::visualise( const InternedString &attributeName, const ShaderNetwork *filterShaderNetwork, const ShaderNetwork *lightShaderNetwork, const CompoundObject *attributes, IECoreGL::ConstStatePtr &state ) const
{
	const CompoundData *barnParameters = filterShaderNetwork->outputShader()->parametersData();

	IECoreGL::GroupPtr result = new IECoreGL::Group();

	addWireframeCurveState( result.get() );

	CompoundObjectPtr parameters = new CompoundObject();
	result->getState()->add(
		new IECoreGL::ShaderStateComponent( ShaderLoader::defaultShaderLoader(), TextureLoader::defaultTextureLoader(), "", "", IECoreGL::Shader::constantFragmentSource(), parameters )
	);

	const V2f innerSize = V2f( parameterOrDefault( barnParameters, "width", 1.f ), parameterOrDefault( barnParameters, "height", 1.f ) );
	const float radius = parameterOrDefault( barnParameters, "radius", 0.f );
	const V2f innerScale(
		parameterOrDefault( barnParameters, "scaleWidth", 1.f ),
		parameterOrDefault( barnParameters, "scaleHeight", 1.f )
	);
	const V4f innerOffset(
		parameterOrDefault( barnParameters, "top", 0.f ),
		parameterOrDefault( barnParameters, "left", 0.f ),
		parameterOrDefault( barnParameters, "bottom", 0.f ),
		parameterOrDefault( barnParameters, "right", 0.f )
	);
	const V4f falloffScale(
		parameterOrDefault( barnParameters, "topEdge", 1.f ),
		parameterOrDefault( barnParameters, "leftEdge", 1.f ),
		parameterOrDefault( barnParameters, "bottomEdge", 1.f ),
		parameterOrDefault( barnParameters, "rightEdge", 1.f )
	);
	const float edge = parameterOrDefault( barnParameters, "edge", 0.f );

	IECoreGL::GroupPtr rects = GafferRenderManUI::lightFilterRectangles( innerSize, radius, innerScale, innerOffset, falloffScale, edge );
	result->addChild( rects );

	return { Visualisation::createGeometry( result ) };
}

}  // namespace
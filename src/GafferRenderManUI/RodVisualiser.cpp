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

#include "GafferScene/Private/IECoreGLPreview/LightFilterVisualiser.h"

#include "LightFilterVisualiserAlgo.h"

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
T parameterOrDefault( const IECore::CompoundData *parameters, const IECore::InternedString &name, const T &defaultValue )
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

class RodVisualiser final : public LightFilterVisualiser
{

	public :

		IE_CORE_DECLAREMEMBERPTR( RodVisualiser )

		RodVisualiser();
		~RodVisualiser() override;

		Visualisations visualise( const InternedString &attributeName, const ShaderNetwork *filterShaderNetwork, const ShaderNetwork *lightShaderNetwork, const CompoundObject *attributes, IECoreGL::ConstStatePtr &state ) const override;

	protected :

		static LightFilterVisualiser::LightFilterVisualiserDescription<RodVisualiser> g_visualiserDescription;

};

IE_CORE_DECLAREPTR( RodVisualiser )

// Register the new visualiser
LightFilterVisualiser::LightFilterVisualiserDescription<RodVisualiser> RodVisualiser::g_visualiserDescription( "ri:lightFilter", "PxrRodLightFilter" );

RodVisualiser::RodVisualiser()
{
}

RodVisualiser::~RodVisualiser()
{
}

Visualisations RodVisualiser::visualise( const InternedString &attributeName, const ShaderNetwork *filterShaderNetwork, const ShaderNetwork *lightShaderNetwork, const CompoundObject *attributes, IECoreGL::ConstStatePtr &state ) const
{
	const CompoundData *filterParameters = filterShaderNetwork->outputShader()->parametersData();

	IECoreGL::GroupPtr result = new IECoreGL::Group();

	addWireframeCurveState( result.get() );

	CompoundObjectPtr parameters = new CompoundObject();
	result->getState()->add(
		new IECoreGL::ShaderStateComponent( ShaderLoader::defaultShaderLoader(), TextureLoader::defaultTextureLoader(), "", "", IECoreGL::Shader::constantFragmentSource(), parameters )
	);

	for(
		const auto &[innerSize, radius, innerScale, innerOffset, falloffScale, edge, transform] : std::vector<std::tuple<V2f, float, V2f, V4f, V4f, float, M44f>> {
			{
				V2f( parameterOrDefault( filterParameters, "width", 1.f ) * 2.f, parameterOrDefault( filterParameters, "height", 1.f ) * 2.f ),
				parameterOrDefault( filterParameters, "radius", 0.f ),
				V2f(
					parameterOrDefault( filterParameters, "scaleWidth", 1.f ),
					parameterOrDefault( filterParameters, "scaleHeight", 1.f )
				),
				V4f(
					parameterOrDefault( filterParameters, "top", 0.f ),
					parameterOrDefault( filterParameters, "left", 0.f ),
					parameterOrDefault( filterParameters, "bottom", 0.f ),
					parameterOrDefault( filterParameters, "right", 0.f )
				),
				V4f(
					parameterOrDefault( filterParameters, "topEdge", 1.f ),
					parameterOrDefault( filterParameters, "leftEdge", 1.f ),
					parameterOrDefault( filterParameters, "bottomEdge", 1.f ),
					parameterOrDefault( filterParameters, "rightEdge", 1.f )
				),
				parameterOrDefault( filterParameters, "edge", 0.f ),
				M44f()
			},
			{
				V2f( parameterOrDefault( filterParameters, "width", 1.f ) * 2.f, parameterOrDefault( filterParameters, "depth", 1.f ) * 2.f ),
				parameterOrDefault( filterParameters, "radius", 0.f ),
				V2f(
					parameterOrDefault( filterParameters, "scaleWidth", 1.f ),
					parameterOrDefault( filterParameters, "scaleDepth", 1.f )
				),
				V4f(
					parameterOrDefault( filterParameters, "back", 0.f ),
					parameterOrDefault( filterParameters, "left", 0.f ),
					parameterOrDefault( filterParameters, "front", 0.f ),
					parameterOrDefault( filterParameters, "right", 0.f )
				),
				V4f(
					parameterOrDefault( filterParameters, "backEdge", 1.f ),
					parameterOrDefault( filterParameters, "leftEdge", 1.f ),
					parameterOrDefault( filterParameters, "frontEdge", 1.f ),
					parameterOrDefault( filterParameters, "rightEdge", 1.f )
				),
				parameterOrDefault( filterParameters, "edge", 0.f ),
				M44f().rotate( V3f( -M_PI * 0.5f, 0.f, 0.f ) )
			},
			{
				V2f( parameterOrDefault( filterParameters, "depth", 1.f ) * 2.f, parameterOrDefault( filterParameters, "height", 1.f ) * 2.f ),
				parameterOrDefault( filterParameters, "radius", 0.f ),
				V2f(
					parameterOrDefault( filterParameters, "scaleDepth", 1.f ),
					parameterOrDefault( filterParameters, "scaleHeight", 1.f )
				),
				V4f(
					parameterOrDefault( filterParameters, "top", 0.f ),
					parameterOrDefault( filterParameters, "front", 0.f ),
					parameterOrDefault( filterParameters, "bottom", 0.f ),
					parameterOrDefault( filterParameters, "back", 0.f )
				),
				V4f(
					parameterOrDefault( filterParameters, "topEdge", 1.f ),
					parameterOrDefault( filterParameters, "frontEdge", 1.f ),
					parameterOrDefault( filterParameters, "bottomEdge", 1.f ),
					parameterOrDefault( filterParameters, "backEdge", 1.f )
				),
				parameterOrDefault( filterParameters, "edge", 0.f ),
				M44f().rotate( V3f( 0.f, M_PI * 0.5f, 0.f ) )
			}
		}
	)
	{
		IECoreGL::GroupPtr axisGroup = GafferRenderManUI::lightFilterRectangles( innerSize, radius, innerScale, innerOffset, falloffScale, edge );
		axisGroup->setTransform( transform );
		result->addChild( axisGroup );
	}

	return { Visualisation::createGeometry( result ) };
}

}  // namespace
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

void addRect( const V2f &innerSize, std::vector<int> &vertsPerCurve, std::vector<V3f> &p )
{
	const V2f halfSize = innerSize * 0.5f;

	vertsPerCurve.push_back( 4 );
	p.push_back( V3f( -halfSize.x, -halfSize.y, 0.f ) );
	p.push_back( V3f( halfSize.x, -halfSize.y, 0.f ) );
	p.push_back( V3f( halfSize.x, halfSize.y, 0.f ) );
	p.push_back( V3f( -halfSize.x, halfSize.y, 0.f ) );
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
	IntVectorDataPtr innerVertsPerCurveData = new IntVectorData();
	V3fVectorDataPtr innerPData = new V3fVectorData();

	std::vector<int> &innerVertsPerCurve = innerVertsPerCurveData->writable();
	std::vector<V3f> &innerP = innerPData->writable();

	addRect(
		V2f( parameterOrDefault( barnParameters, "width", 1.f ), parameterOrDefault( barnParameters, "height", 1.f ) ),
		innerVertsPerCurve,
		innerP
	);

	IECoreGL::CurvesPrimitivePtr rect = new IECoreGL::CurvesPrimitive( CubicBasisf::linear(), /* periodic */ true, innerVertsPerCurveData );
	rect->addPrimitiveVariable( "P", PrimitiveVariable( PrimitiveVariable::Vertex, innerPData ) );
	rect->addPrimitiveVariable( "Cs", PrimitiveVariable( PrimitiveVariable::Constant, new Color3fData( Color3f( 255.f / 255.f, 171.f / 255.f, 15.f / 255.f ) ) ) );

	result->addChild( rect );

	return { Visualisation::createGeometry( result ) };
}

}  // namespace
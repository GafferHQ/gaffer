//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine. All rights reserved.
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

#include "Gaffer/Metadata.h"

#include "IECoreGL/CurvesPrimitive.h"
#include "IECoreGL/Group.h"
#include "IECoreGL/ShaderLoader.h"
#include "IECoreGL/ShaderStateComponent.h"
#include "IECoreGL/TextureLoader.h"

#include "IECoreScene/Shader.h"

using namespace std;
using namespace boost;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreGL;
using namespace IECoreGLPreview;
using namespace Gaffer;

namespace
{

const IECore::CompoundData *parametersAndMetadataTarget( const IECore::InternedString &attributeName, const IECoreScene::ShaderNetwork *filterShaderNetwork, InternedString &metadataTarget )
{
	const IECoreScene::Shader *shader = filterShaderNetwork->outputShader();
	metadataTarget = attributeName.string() + ":" + shader->getName();
	return shader->parametersData();
}

template<typename T>
T parameter( InternedString metadataTarget, const IECore::CompoundData *parameters, InternedString parameterNameMetadata, T defaultValue )
{
	ConstStringDataPtr parameterName = Metadata::value<StringData>( metadataTarget, parameterNameMetadata );
	if( !parameterName )
	{
		return defaultValue;
	}

	typedef IECore::TypedData<T> DataType;
	if( const DataType *parameterData = parameters->member<DataType>( parameterName->readable() ) )
	{
		return parameterData->readable();
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

void addQuad( const V3f &center, float size, vector<int> &vertsPerCurve, vector<V3f> &p )
{
	float halfSize = size * 0.5;

	p.push_back( center + V3f( -halfSize, -halfSize, 0  ) );
	p.push_back( center + V3f(  halfSize, -halfSize, 0  ) );
	p.push_back( center + V3f(  halfSize,  halfSize, 0  ) );
	p.push_back( center + V3f( -halfSize,  halfSize, 0  ) );

	vertsPerCurve.push_back( 4 );
}

void addCircle( const V3f &center, float radius, vector<int> &vertsPerCurve, vector<V3f> &p )
{
	const int numDivisions = 100;
	for( int i = 0; i < numDivisions; ++i )
	{
		const float angle = 2 * M_PI * (float)i/(float)(numDivisions-1);
		p.push_back( center + radius * V3f( cos( angle ), sin( angle ), 0 ) );
	}
	vertsPerCurve.push_back( numDivisions );
}

void addLine( const V3f &start, const V3f &end, vector<int> &vertsPerCurve, vector<V3f> &p )
{
	p.push_back( start );
	p.push_back( end );
	vertsPerCurve.push_back( 2 );
}

void addCube( const V3f &origin, float size, vector<int> &vertsPerCurve, vector<V3f> &p )
{
	float halfSize = size * 0.5;

	vertsPerCurve.push_back( 4 );
	p.push_back( V3f( -halfSize, -halfSize,  halfSize ) );
	p.push_back( V3f(  halfSize, -halfSize,  halfSize ) );
	p.push_back( V3f(  halfSize,  halfSize,  halfSize ) );
	p.push_back( V3f( -halfSize,  halfSize,  halfSize ) );

	vertsPerCurve.push_back( 4 );
	p.push_back( V3f( -halfSize, -halfSize, -halfSize ) );
	p.push_back( V3f(  halfSize, -halfSize, -halfSize ) );
	p.push_back( V3f(  halfSize,  halfSize, -halfSize ) );
	p.push_back( V3f( -halfSize,  halfSize, -halfSize ) );

	vertsPerCurve.push_back( 2 );
	p.push_back( V3f( -halfSize, -halfSize,  halfSize ) );
	p.push_back( V3f( -halfSize, -halfSize, -halfSize ) );

	vertsPerCurve.push_back( 2 );
	p.push_back( V3f(  halfSize, -halfSize,  halfSize ) );
	p.push_back( V3f(  halfSize, -halfSize, -halfSize ) );

	vertsPerCurve.push_back( 2 );
	p.push_back( V3f(  halfSize,  halfSize,  halfSize ) );
	p.push_back( V3f(  halfSize,  halfSize, -halfSize ) );

	vertsPerCurve.push_back( 2 );
	p.push_back( V3f( -halfSize,  halfSize,  halfSize ) );
	p.push_back( V3f( -halfSize,  halfSize, -halfSize ) );
}

void setFalloffGroupSettings( IECoreGL::Group *group, const IECore::CompoundData *shaderParameters )
{
	// Scale of falloff visualisation
	Imath::M44f falloffScale;
	ConstFloatDataPtr widthData = shaderParameters->member<FloatData>( "width_edge" );
	ConstFloatDataPtr heightData = shaderParameters->member<FloatData>( "height_edge" );

	falloffScale.setScale( V3f( 1 + widthData->readable() * 2, 1 + heightData->readable() * 2, 1 + widthData->readable() * 2 ) );
	group->setTransform( falloffScale );

	// Falloff visualisation uses half the line width
	group->getState()->add( new IECoreGL::CurvesPrimitive::GLLineWidth( 1.0f ) );
}

//////////////////////////////////////////////////////////////////////////
// LightBlockerVisualiser implementation.
//////////////////////////////////////////////////////////////////////////

class LightBlockerVisualiser : public LightFilterVisualiser
{

	public :

		IE_CORE_DECLAREMEMBERPTR( LightBlockerVisualiser )

		LightBlockerVisualiser();
		~LightBlockerVisualiser() override;

		virtual IECoreGL::ConstRenderablePtr visualise( const IECore::InternedString &attributeName, const IECoreScene::ShaderNetwork *filterShaderNetwork, const IECoreScene::ShaderNetwork *lightShaderNetwork, const IECore::CompoundObject *attributes, IECoreGL::ConstStatePtr &state ) const override;

	protected :

		static LightFilterVisualiser::LightFilterVisualiserDescription<LightBlockerVisualiser> g_visualiserDescription;

	private :

		/// \todo: can this be consolidated with the StandardLightVisualiser?
		static IECoreGL::ConstRenderablePtr boxShape( const IECore::CompoundData *shaderParameters );
		static IECoreGL::ConstRenderablePtr sphereShape( const IECore::CompoundData *shaderParameters );
		static IECoreGL::ConstRenderablePtr cylinderShape( const IECore::CompoundData *shaderParameters );
		static IECoreGL::ConstRenderablePtr planeShape( const IECore::CompoundData *shaderParameters );
};

IE_CORE_DECLAREPTR( LightBlockerVisualiser )

// register the new visualiser
LightFilterVisualiser::LightFilterVisualiserDescription<LightBlockerVisualiser> LightBlockerVisualiser::g_visualiserDescription( "ai:lightFilter", "light_blocker" );

LightBlockerVisualiser::LightBlockerVisualiser()
{
}

LightBlockerVisualiser::~LightBlockerVisualiser()
{
}

IECoreGL::ConstRenderablePtr LightBlockerVisualiser::visualise( const IECore::InternedString &attributeName, const IECoreScene::ShaderNetwork *filterShaderNetwork, const IECoreScene::ShaderNetwork *lightShaderNetwork, const IECore::CompoundObject *attributes, IECoreGL::ConstStatePtr &state ) const
{
	InternedString metadataTarget;
	const IECore::CompoundData *shaderParameters = parametersAndMetadataTarget( attributeName, filterShaderNetwork, metadataTarget );

	ConstStringDataPtr type = Metadata::value<StringData>( metadataTarget, "type" );
	ConstM44fDataPtr orientation = Metadata::value<M44fData>( metadataTarget, "visualiserOrientation" );

	IECoreGL::GroupPtr result = new IECoreGL::Group();

	// \todo: See respective comment in StandardLightVisualiser
	const float locatorScale = parameter<float>( metadataTarget, shaderParameters, "locatorScaleParameter", 1 );

	Imath::M44f topTrans;
	if( orientation )
	{
		topTrans = orientation->readable();
	}
	topTrans.scale( V3f( locatorScale ) );
	result->setTransform( topTrans );

	ConstStringDataPtr geometryTypeData = shaderParameters->member<StringData>( "geometry_type" );
	const std::string geometryType = geometryTypeData->readable();

	if( geometryType == "box" )
	{
		result->addChild( const_pointer_cast<IECoreGL::Renderable>( boxShape( shaderParameters ) ) );
	}
	else if( geometryType == "sphere" )
	{
		result->addChild( const_pointer_cast<IECoreGL::Renderable>( sphereShape( shaderParameters ) ) );
	}
	else if( geometryType == "cylinder" )
	{
		result->addChild( const_pointer_cast<IECoreGL::Renderable>( cylinderShape( shaderParameters ) ) );
	}
	else if( geometryType == "plane" )
	{
		result->addChild( const_pointer_cast<IECoreGL::Renderable>( planeShape( shaderParameters ) ) );
	}

	return result;
}

IECoreGL::ConstRenderablePtr LightBlockerVisualiser::boxShape( const IECore::CompoundData *shaderParameters )
{
	IECoreGL::GroupPtr group = new IECoreGL::Group();
	addWireframeCurveState( group.get() );

	IECore::CompoundObjectPtr parameters = new CompoundObject;
	group->getState()->add(
		new IECoreGL::ShaderStateComponent( ShaderLoader::defaultShaderLoader(), TextureLoader::defaultTextureLoader(), "", "", IECoreGL::Shader::constantFragmentSource(), parameters )
	);

	// Add main visualisation

	IntVectorDataPtr vertsPerCurveData = new IntVectorData;
	V3fVectorDataPtr pData = new V3fVectorData;

	vector<int> &vertsPerCurve = vertsPerCurveData->writable();
	vector<V3f> &p = pData->writable();

	addCube( /* origin */ { 0, 0, 0 }, /* size */ 1.0, vertsPerCurve, p );

	IECoreGL::CurvesPrimitivePtr cube = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), /* periodic = */ true, vertsPerCurveData );
	cube->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, pData ) );
	cube->addPrimitiveVariable( "Cs", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new Color3fData( Color3f( 255 / 255.0f, 171 / 255.0f, 15 / 255.0f ) ) ) );

	group->addChild( cube );

	// Add falloff visualisation

	IECoreGL::CurvesPrimitivePtr falloff = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), /* periodic = */ true, vertsPerCurveData );
	falloff->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, pData ) );
	falloff->addPrimitiveVariable( "Cs", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new Color3fData( Color3f( 0.0f, 0.0f, 0.0f ) ) ) );

	IECoreGL::GroupPtr falloffGroup = new IECoreGL::Group();
	setFalloffGroupSettings( falloffGroup.get(), shaderParameters );

	falloffGroup->addChild( falloff );
	group->addChild( falloffGroup );

	return group;
}

IECoreGL::ConstRenderablePtr LightBlockerVisualiser::sphereShape( const IECore::CompoundData *shaderParameters )
{
	IECoreGL::GroupPtr group = new IECoreGL::Group();
	addWireframeCurveState( group.get() );

	IECore::CompoundObjectPtr parameters = new CompoundObject;
	group->getState()->add(
		new IECoreGL::ShaderStateComponent( ShaderLoader::defaultShaderLoader(), TextureLoader::defaultTextureLoader(), "", "", IECoreGL::Shader::constantFragmentSource(), parameters )
	);

	// Add main visualisation

	IntVectorDataPtr vertsPerCurveData = new IntVectorData;
	V3fVectorDataPtr pData = new V3fVectorData;

	vector<int> &vertsPerCurve = vertsPerCurveData->writable();
	vector<V3f> &p = pData->writable();

	addCircle( { 0, 0, 0 }, 0.5, vertsPerCurve, p );

	IECoreGL::CurvesPrimitivePtr circleXY = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), /* periodic = */ true, vertsPerCurveData );
	circleXY->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, pData ) );
	circleXY->addPrimitiveVariable( "Cs", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new Color3fData( Color3f( 255 / 255.0f, 171 / 255.0f, 15 / 255.0f ) ) ) );

	IECoreGL::GroupPtr xy = new IECoreGL::Group();
	xy->addChild( circleXY );
	group->addChild( xy );


	IECoreGL::CurvesPrimitivePtr circleYZ = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), /* periodic = */ true, vertsPerCurveData );
	circleYZ->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, pData ) );
	circleYZ->addPrimitiveVariable( "Cs", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new Color3fData( Color3f( 255 / 255.0f, 171 / 255.0f, 15 / 255.0f ) ) ) );

	IECoreGL::GroupPtr yz = new IECoreGL::Group();
	yz->addChild( circleYZ );
	group->addChild( yz );

	Imath::M44f yzRotation;
	yzRotation.setEulerAngles( Imath::V3f( 0, 0.5 * M_PI, 0 ) );
	yz->setTransform( yzRotation );


	IECoreGL::CurvesPrimitivePtr circleXZ = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), /* periodic = */ true, vertsPerCurveData );
	circleXZ->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, pData ) );
	circleXZ->addPrimitiveVariable( "Cs", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new Color3fData( Color3f( 255 / 255.0f, 171 / 255.0f, 15 / 255.0f ) ) ) );

	IECoreGL::GroupPtr xz = new IECoreGL::Group();
	xz->addChild( circleXZ );
	group->addChild( xz );

	Imath::M44f xzRotation;
	xzRotation.setEulerAngles( Imath::V3f( 0.5 * M_PI, 0, 0 ) );
	xz->setTransform( xzRotation );

	// \todo: It's not clear to me at this point how the falloff is computed for
	// spheres. Needs a visualisation, though. Seems like both the width and
	// height edges are affecting all axes - and so does the ramp parameter?

	return group;
}

IECoreGL::ConstRenderablePtr LightBlockerVisualiser::cylinderShape( const IECore::CompoundData *shaderParameters )
{
	GroupPtr group = new IECoreGL::Group();
	addWireframeCurveState( group.get() );

	CompoundObjectPtr parameters = new CompoundObject;
	parameters->members()["aimType"] = new IntData( 0 );
	group->getState()->add(
		new IECoreGL::ShaderStateComponent( ShaderLoader::defaultShaderLoader(), TextureLoader::defaultTextureLoader(), "", "", IECoreGL::Shader::constantFragmentSource(), parameters )
	);

	// Add main visualisation

	IntVectorDataPtr vertsPerCurveData = new IntVectorData;
	vector<int> &vertsPerCurve = vertsPerCurveData->writable();
	V3fVectorDataPtr pData = new V3fVectorData;
	vector<V3f> &p = pData->writable();

	float radius = 0.5;

	addCircle( V3f( 0, 0, -radius ), radius, vertsPerCurve, p );
	addCircle( V3f( 0, 0,  radius ), radius, vertsPerCurve, p );

	addLine( { 0,  radius, -radius }, { 0,  radius, radius }, vertsPerCurve, p );
	addLine( { 0, -radius, -radius }, { 0, -radius, radius }, vertsPerCurve, p );

	CurvesPrimitivePtr cylinder = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), false, vertsPerCurveData );
	cylinder->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, pData ) );
	cylinder->addPrimitiveVariable( "Cs", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new Color3fData( Color3f( 255 / 255.0f, 171 / 255.0f, 15 / 255.0f ) ) ) );

	IECoreGL::GroupPtr cylinderGroup = new IECoreGL::Group();
	cylinderGroup->addChild( cylinder );
	group->addChild( cylinderGroup );

	// Arnold uses a cylinder that's rotated so that the y-axis is connecting the
	// two disks. Adjust vis accordingly.
	Imath::M44f rotation;
	rotation.setEulerAngles( Imath::V3f( 0.5 * M_PI, 0, 0 ) );
	cylinderGroup->setTransform( rotation );

	// Add falloff visualisation

	CurvesPrimitivePtr falloff = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), /* periodic = */ true, vertsPerCurveData );
	falloff->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, pData ) );
	falloff->addPrimitiveVariable( "Cs", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new Color3fData( Color3f( 0.0f, 0.0f, 0.0f ) ) ) );

	IECoreGL::GroupPtr falloffGroup = new IECoreGL::Group();
	falloffGroup->setTransform( rotation );
	setFalloffGroupSettings( falloffGroup.get(), shaderParameters );

	Imath::M44f falloffTransform( falloffGroup->getTransform() );
	falloffTransform.rotate( Imath::V3f( 0.5 * M_PI, 0, 0 ) );
	falloffGroup->setTransform( falloffTransform );

	falloffGroup->addChild( falloff );
	group->addChild( falloffGroup );

	return group;
}

IECoreGL::ConstRenderablePtr LightBlockerVisualiser::planeShape( const IECore::CompoundData *shaderParameters )
{
	IECoreGL::GroupPtr group = new IECoreGL::Group();
	addWireframeCurveState( group.get() );

	IECore::CompoundObjectPtr parameters = new CompoundObject;
	group->getState()->add(
		new IECoreGL::ShaderStateComponent( ShaderLoader::defaultShaderLoader(), TextureLoader::defaultTextureLoader(), "", "", IECoreGL::Shader::constantFragmentSource(), parameters )
	);

	// Add main visualisation

	IntVectorDataPtr vertsPerCurveData = new IntVectorData;
	V3fVectorDataPtr pData = new V3fVectorData;

	vector<int> &vertsPerCurve = vertsPerCurveData->writable();
	vector<V3f> &p = pData->writable();

	addQuad( /* origin */ { 0, 0, 0 }, /* size */ 1.0, vertsPerCurve, p );

	IECoreGL::CurvesPrimitivePtr quad = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), /* periodic = */ true, vertsPerCurveData );
	quad->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, pData ) );
	quad->addPrimitiveVariable( "Cs", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new Color3fData( Color3f( 255 / 255.0f, 171 / 255.0f, 15 / 255.0f ) ) ) );

	group->addChild( quad );

	// Add falloff visualisation

	CurvesPrimitivePtr falloff = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), /* periodic = */ true, vertsPerCurveData );
	falloff->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, pData ) );
	falloff->addPrimitiveVariable( "Cs", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new Color3fData( Color3f( 0.0f, 0.0f, 0.0f ) ) ) );

	IECoreGL::GroupPtr falloffGroup = new IECoreGL::Group();
	setFalloffGroupSettings( falloffGroup.get(), shaderParameters );

	falloffGroup->addChild( falloff );
	group->addChild( falloffGroup );

	return group;
}

} // namespace

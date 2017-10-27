//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, John Haddon. All rights reserved.
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

#include "IECore/MeshPrimitive.h"
#include "IECore/Shader.h"
#include "IECore/ObjectVector.h"
#include "IECore/Light.h"

#include "IECoreGL/CurvesPrimitive.h"
#include "IECoreGL/SpherePrimitive.h"
#include "IECoreGL/Group.h"
#include "IECoreGL/ShaderStateComponent.h"
#include "IECoreGL/ShaderLoader.h"
#include "IECoreGL/TextureLoader.h"
#include "IECoreGL/DiskPrimitive.h"
#include "IECoreGL/ToGLMeshConverter.h"

#include "Gaffer/Metadata.h"

#include "GafferSceneUI/StandardLightVisualiser.h"

using namespace std;
using namespace boost;
using namespace Imath;
using namespace IECore;
using namespace IECoreGL;
using namespace Gaffer;
using namespace GafferSceneUI;

//////////////////////////////////////////////////////////////////////////
// Utility methods. We define these in an anonymouse namespace rather
// than clutter up the header with private methods.
//////////////////////////////////////////////////////////////////////////

namespace
{

const IECore::CompoundData *parametersAndMetadataTarget( const IECore::InternedString &attributeName, const IECore::ObjectVector *shaderVector, InternedString &metadataTarget )
{
	if( !shaderVector || shaderVector->members().size() == 0 )
	{
		return nullptr;
	}

	if( const IECore::Shader *shader = IECore::runTimeCast<const IECore::Shader>( shaderVector->members().back().get() ) )
	{
		metadataTarget = attributeName.string() + ":" + shader->getName();
		return shader->parametersData();
	}
	else if( const IECore::Light *light = IECore::runTimeCast<const IECore::Light>( shaderVector->members().back().get() ) )
	{
		/// \todo Remove once all Light node derived classes are
		/// creating only shaders.
		metadataTarget = attributeName.string() + ":" + light->getName();
		return light->parametersData().get();
	}

	return nullptr;
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

V3f lightPlane( const V2f &p )
{
	return V3f( 0, p.y, -p.x );
}

// Coordinates are in the light plane.
void addRay( const V2f &start, const V2f &end, vector<int> &vertsPerCurve, vector<V3f> &p )
{
	const float arrowScale = 0.05;

	const V2f dir = end - start;
	const V2f perp( dir.y, -dir.x );

	p.push_back( lightPlane( start ) );
	p.push_back( lightPlane( end ) );
	vertsPerCurve.push_back( 2 );

	p.push_back( lightPlane( end + arrowScale * ( perp * 2 - dir * 3 ) ) );
	p.push_back( lightPlane( end ) );
	p.push_back( lightPlane( end + arrowScale * ( perp * -2 - dir * 3 ) ) );
	vertsPerCurve.push_back( 3 );
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

void addSolidArc( int axis, const V3f &center, float majorRadius, float minorRadius, float startFraction, float stopFraction, vector<int> &vertsPerPoly, vector<int> &vertIds, vector<V3f> &p )
{
	const int numSegmentsForCircle = 100;
	int numSegments = max( 1, (int)ceil( (stopFraction - startFraction) * numSegmentsForCircle ) );

	int start = p.size();
	for( int i = 0; i < numSegments + 1; ++i )
	{
		const float angle = 2 * M_PI * ( startFraction + (stopFraction - startFraction) * (float)i/(float)(numSegments) );
		V3f dir( -sin( angle ), cos( angle ), 0 );
		if( axis == 0 ) dir = V3f( 0, dir[1], -dir[0] );
		else if( axis == 1 ) dir = V3f( dir[1], 0, dir[0] );
		p.push_back( center + majorRadius * dir );
		p.push_back( center + minorRadius * dir );
	}
	for( int i = 0; i < numSegments; ++i )
	{
		vertIds.push_back( start + i * 2 );
		vertIds.push_back( start + i * 2  + 1);
		vertIds.push_back( start + i * 2  + 3);
		vertIds.push_back( start + i * 2  + 2);
		vertsPerPoly.push_back( 4 );
	}
}

void addCone( float angle, float startRadius, vector<int> &vertsPerCurve, vector<V3f> &p )
{
	const float halfAngle = 0.5 * M_PI * angle / 180.0;
	const float baseRadius = sin( halfAngle );
	const float baseDistance = cos( halfAngle );

	if( startRadius > 0 )
	{
		addCircle( V3f( 0 ), startRadius, vertsPerCurve, p );
	}
	addCircle( V3f( 0, 0, -baseDistance ), baseRadius + startRadius, vertsPerCurve, p );

	p.push_back( V3f( 0, startRadius, 0 ) );
	p.push_back( V3f( 0, baseRadius + startRadius, -baseDistance ) );
	vertsPerCurve.push_back( 2 );

	p.push_back( V3f( 0, -startRadius, 0 ) );
	p.push_back( V3f( 0, -baseRadius - startRadius, -baseDistance ) );
	vertsPerCurve.push_back( 2 );
}

const char *environmentSphereFragSource()
{
	return
		"#version 120\n"
		""
		"#if __VERSION__ <= 120\n"
		"#define in varying\n"
		"#endif\n"
		""
		"#include \"IECoreGL/ColorAlgo.h\"\n"
		""
		"in vec2 fragmentuv;"
		""
		"uniform vec3 lightMultiplier;"
		"uniform vec3 defaultColor;"
		"uniform float previewOpacity;"
		""
		"uniform sampler2D mapSampler;"
		""
		"void main()"
		"{"
			"vec3 c = defaultColor + texture2D( mapSampler, fragmentuv ).xyz;"
			"gl_FragColor = vec4( ieLinToSRGB( c * lightMultiplier ), previewOpacity );"
		"}"
	;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// StandardLightVisualiser implementation.
//////////////////////////////////////////////////////////////////////////

StandardLightVisualiser::StandardLightVisualiser()
{
}

StandardLightVisualiser::~StandardLightVisualiser()
{
}

IECoreGL::ConstRenderablePtr StandardLightVisualiser::visualise( const IECore::InternedString &attributeName, const IECore::ObjectVector *shaderVector, IECoreGL::ConstStatePtr &state ) const
{
	InternedString metadataTarget;
	const IECore::CompoundData *shaderParameters = parametersAndMetadataTarget( attributeName, shaderVector, metadataTarget );
	if( !shaderParameters )
	{
		return nullptr;
	}

	ConstStringDataPtr type = Metadata::value<StringData>( metadataTarget, "type" );
	ConstM44fDataPtr orientation = Metadata::value<M44fData>( metadataTarget, "visualiserOrientation" );

	const Color3f color = parameter<Color3f>( metadataTarget, shaderParameters, "colorParameter", Color3f( 1.0f ) );
	const float intensity = parameter<float>( metadataTarget, shaderParameters, "intensityParameter", 1 );
	const float exposure = parameter<float>( metadataTarget, shaderParameters, "exposureParameter", 0 );

	const Color3f finalColor = color * intensity * pow( 2.0f, exposure );

	GroupPtr result = new Group;

	/// \todo This is problematic for a few reasons :
	///
	/// - The name "locatorScale" doesn't fit Gaffer's terminology - perhaps "visualiserScale"
	///    would be better?
	/// - It doesn't make much sense to have a shader parameter which affects only the visualisation
	///   and not the rendering - no out-of-the-box light has one that I know of. Perhaps it should
	///   be an attribute that the `GafferScene::light()` node sets?
	/// - We don't actually want to apply it to the area light shapes created below for "quad" etc.
	///
	/// Since this feature is only used by lights internal to Image Engine, we can ignore all this for
	/// now, but it would be good to address in the future.
	const float locatorScale = parameter<float>( metadataTarget, shaderParameters, "locatorScaleParameter", 1 );
	Imath::M44f topTrans;
	if( orientation )
	{
		topTrans = orientation->readable();
	}
	topTrans.scale( V3f( locatorScale ) );
	result->setTransform( topTrans );

	if( type && type->readable() == "environment" )
	{
		const std::string textureName = parameter<std::string>( metadataTarget, shaderParameters, "textureNameParameter", "" );
		result->addChild( const_pointer_cast<IECoreGL::Renderable>( environmentSphere( finalColor, textureName ) ) );
	}
	else if( type && type->readable() == "spot" )
	{
		float innerAngle, outerAngle, lensRadius;
		spotlightParameters( attributeName, shaderVector, innerAngle, outerAngle, lensRadius );
		result->addChild( const_pointer_cast<IECoreGL::Renderable>( spotlightCone( innerAngle, outerAngle, lensRadius / locatorScale ) ) );
		result->addChild( const_pointer_cast<IECoreGL::Renderable>( ray() ) );
		result->addChild( const_pointer_cast<IECoreGL::Renderable>( colorIndicator( finalColor, /* cameraFacing = */ false ) ) );
	}
	else if( type && type->readable() == "distant" )
	{
		result->addChild( const_pointer_cast<IECoreGL::Renderable>( distantRays() ) );
		result->addChild( const_pointer_cast<IECoreGL::Renderable>( colorIndicator( finalColor, /* cameraFacing = */ false ) ) );
	}
	else if( type && type->readable() == "quad" )
	{
		result->addChild( const_pointer_cast<IECoreGL::Renderable>( quadShape() ) );
		result->addChild( const_pointer_cast<IECoreGL::Renderable>( ray() ) );
		result->addChild( const_pointer_cast<IECoreGL::Renderable>( colorIndicator( finalColor, /* cameraFacing = */ false ) ) );
	}
	else if( type && type->readable() == "disk" )
	{
		const float radius = parameter<float>( metadataTarget, shaderParameters, "radiusParameter", 1 );
		result->addChild( const_pointer_cast<IECoreGL::Renderable>( diskShape( radius ) ) );
		result->addChild( const_pointer_cast<IECoreGL::Renderable>( ray() ) );
		result->addChild( const_pointer_cast<IECoreGL::Renderable>( colorIndicator( finalColor, /* cameraFacing = */ false ) ) );
	}
	else if( type && type->readable() == "cylinder" )
	{
		const float radius = parameter<float>( metadataTarget, shaderParameters, "radiusParameter", 1 );
		result->addChild( const_pointer_cast<IECoreGL::Renderable>( cylinderShape( radius ) ) );
		result->addChild( const_pointer_cast<IECoreGL::Renderable>( cylinderRays( radius ) ) );
		result->addChild( const_pointer_cast<IECoreGL::Renderable>( colorIndicator( finalColor, /* cameraFacing = */ false ) ) );
	}
	else
	{
		// Treat everything else as a point light.
		result->addChild( const_pointer_cast<IECoreGL::Renderable>( pointRays() ) );
		result->addChild( const_pointer_cast<IECoreGL::Renderable>( colorIndicator( finalColor, /* cameraFacing = */ true ) ) );
	}

	return result;
}

void StandardLightVisualiser::spotlightParameters( const InternedString &attributeName, const IECore::ObjectVector *shaderVector, float &innerAngle, float &outerAngle, float &lensRadius )
{

	InternedString metadataTarget;
	const IECore::CompoundData *shaderParameters = parametersAndMetadataTarget( attributeName, shaderVector, metadataTarget );

	float coneAngle = parameter<float>( metadataTarget, shaderParameters, "coneAngleParameter", 0.0f );
	float penumbraAngle = parameter<float>( metadataTarget, shaderParameters, "penumbraAngleParameter", 0.0f );
	if( ConstStringDataPtr angleUnit = Metadata::value<StringData>( metadataTarget, "angleUnit" ) )
	{
		if( angleUnit->readable() == "radians" )
		{
			coneAngle *= 180.0 / M_PI;
			penumbraAngle *= 180 / M_PI;
		}
	}

	innerAngle = 0;
	outerAngle = 0;

	ConstStringDataPtr penumbraTypeData = Metadata::value<StringData>( metadataTarget, "penumbraType" );
	const std::string *penumbraType = penumbraTypeData ? &penumbraTypeData->readable() : NULL;

	if( !penumbraType || *penumbraType == "inset" )
	{
		outerAngle = coneAngle;
		innerAngle = coneAngle - 2.0f * penumbraAngle;
	}
	else if( *penumbraType == "outset" )
	{
		outerAngle = coneAngle + 2.0f * penumbraAngle;
		innerAngle = coneAngle ;
	}
	else if( *penumbraType == "absolute" )
	{
		outerAngle = coneAngle;
		innerAngle = penumbraAngle;
	}

	lensRadius = 0.0f;
	if( parameter<bool>( metadataTarget, shaderParameters, "lensRadiusEnableParameter", true ) )
	{
		lensRadius = parameter<float>( metadataTarget, shaderParameters, "lensRadiusParameter", 0.0f );
	}
}

const char *StandardLightVisualiser::faceCameraVertexSource()
{
	return

		"#version 120\n"
		""
		"#if __VERSION__ <= 120\n"
		"#define in attribute\n"
		"#define out varying\n"
		"#endif\n"
		""
		"uniform int aimType;"
		""
		"uniform vec3 Cs = vec3( 1, 1, 1 );"
		"uniform bool vertexCsActive = false;"
		""
		"in vec3 vertexP;"
		"in vec3 vertexN;"
		"in vec2 vertexuv;"
		"in vec3 vertexCs;"
		""
		"out vec3 geometryI;"
		"out vec3 geometryP;"
		"out vec3 geometryN;"
		"out vec2 geometryuv;"
		"out vec3 geometryCs;"
		""
		"out vec3 fragmentI;"
		"out vec3 fragmentP;"
		"out vec3 fragmentN;"
		"out vec2 fragmentuv;"
		"out vec3 fragmentCs;"
		""
		"void main()"
		"{"
		""
		""
		"	vec3 aimedXAxis, aimedYAxis, aimedZAxis;"
		"	if( aimType == 0 )"
		"	{"
		"		vec4 viewDirectionInObjectSpace = gl_ModelViewMatrixInverse * vec4( 0, 0, -1, 0 );"
		"		vec3 viewCross = cross( viewDirectionInObjectSpace.xyz, vec3( 0, 0, -1 ) );"
		"		aimedYAxis = length( viewCross ) > 0.0001 ? normalize( viewCross ) : vec3( 1, 0, 0 );"
		"		aimedXAxis = normalize( cross( aimedYAxis, vec3( 0, 0, -1 ) ) );"
		"		aimedZAxis = vec3( 0, 0, 1 );"
		"	}"
		"	else"
		"	{"
		"		aimedXAxis = normalize( gl_ModelViewMatrixInverse * vec4( 0, 0, -1, 0 ) ).xyz;"
		"		aimedYAxis = normalize( gl_ModelViewMatrixInverse * vec4( 0, 1, 0, 0 ) ).xyz;"
		"		aimedZAxis = normalize( gl_ModelViewMatrixInverse * vec4( 1, 0, 0, 0 ) ).xyz;"
		"	}"
		""
		"	vec3 pAimed = vertexP.x * aimedXAxis + vertexP.y * aimedYAxis + vertexP.z * aimedZAxis;"
		""
		"	vec4 pCam = gl_ModelViewMatrix * vec4( pAimed, 1 );"
		"	gl_Position = gl_ProjectionMatrix * pCam;"
		"	geometryP = pCam.xyz;"
		"	geometryN = normalize( gl_NormalMatrix * vertexN );"
		"	if( gl_ProjectionMatrix[2][3] != 0.0 )"
		"	{"
		"		geometryI = normalize( -pCam.xyz );"
		"	}"
		"	else"
		"	{"
		"		geometryI = vec3( 0, 0, -1 );"
		"	}"
		""
		"	geometryuv = vertexuv;"
		"	geometryCs = mix( Cs, vertexCs, float( vertexCsActive ) );"
		""
		"	fragmentI = geometryI;"
		"	fragmentP = geometryP;"
		"	fragmentN = geometryN;"
		"	fragmentuv = geometryuv;"
		"	fragmentCs = geometryCs;"
		"}"

	;
}

IECoreGL::ConstRenderablePtr StandardLightVisualiser::ray()
{
	IECoreGL::GroupPtr group = new IECoreGL::Group();
	addWireframeCurveState( group.get() );

	IECore::CompoundObjectPtr parameters = new CompoundObject;
	parameters->members()["aimType"] = new IntData( 0 );
	group->getState()->add(
		new IECoreGL::ShaderStateComponent( ShaderLoader::defaultShaderLoader(), TextureLoader::defaultTextureLoader(), faceCameraVertexSource(), "", IECoreGL::Shader::constantFragmentSource(), parameters )
	);

	IntVectorDataPtr vertsPerCurve = new IntVectorData;
	V3fVectorDataPtr p = new V3fVectorData;
	addRay( V2f( 0 ), V2f( 1, 0 ), vertsPerCurve->writable(), p->writable() );

	IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), false, vertsPerCurve );
	curves->addPrimitiveVariable( "P", IECore::PrimitiveVariable( IECore::PrimitiveVariable::Vertex, p ) );
	curves->addPrimitiveVariable( "Cs", IECore::PrimitiveVariable( IECore::PrimitiveVariable::Constant, new Color3fData( Color3f( 1.0f, 0.835f, 0.07f ) ) ) );

	group->addChild( curves );

	return group;
}

IECoreGL::ConstRenderablePtr StandardLightVisualiser::pointRays()
{
	IECoreGL::GroupPtr group = new IECoreGL::Group();
	addWireframeCurveState( group.get() );

	IECore::CompoundObjectPtr parameters = new CompoundObject;
	parameters->members()["aimType"] = new IntData( 1 );
	group->getState()->add(
		new IECoreGL::ShaderStateComponent( ShaderLoader::defaultShaderLoader(), TextureLoader::defaultTextureLoader(), faceCameraVertexSource(), "", IECoreGL::Shader::constantFragmentSource(), parameters )
	);

	IntVectorDataPtr vertsPerCurve = new IntVectorData;
	V3fVectorDataPtr p = new V3fVectorData;

	const int numRays = 8;
	for( int i = 0; i < numRays; ++i )
	{
		const float angle = M_PI * 2.0f * float(i)/(float)numRays;
		const V2f dir( cos( angle ), sin( angle ) );
		addRay( dir * .5, dir * 1, vertsPerCurve->writable(), p->writable() );
	}

	IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), false, vertsPerCurve );
	curves->addPrimitiveVariable( "P", IECore::PrimitiveVariable( IECore::PrimitiveVariable::Vertex, p ) );
	curves->addPrimitiveVariable( "Cs", IECore::PrimitiveVariable( IECore::PrimitiveVariable::Constant, new Color3fData( Color3f( 1.0f, 0.835f, 0.07f ) ) ) );

	group->addChild( curves );

	return group;
}

IECoreGL::ConstRenderablePtr StandardLightVisualiser::distantRays()
{
	GroupPtr result = new Group;
	for( int i = 0; i < 3; i++ )
	{
		IECoreGL::GroupPtr rayGroup = new IECoreGL::Group();

		Imath::M44f trans;
		trans.rotate( V3f( 0, 0, 2.0 * M_PI / 3.0 * i ) );
		trans.translate( V3f( 0, 0.4, 0.5 ) );
		rayGroup->addChild( const_pointer_cast<IECoreGL::Renderable>( ray() ) );
		rayGroup->setTransform( trans );

		result->addChild( rayGroup );
	}

	return result;
}

IECoreGL::ConstRenderablePtr StandardLightVisualiser::spotlightCone( float innerAngle, float outerAngle, float lensRadius )
{
	IECoreGL::GroupPtr group = new IECoreGL::Group();
	addWireframeCurveState( group.get() );

	group->getState()->add( new IECoreGL::CurvesPrimitive::GLLineWidth( 1.0f ) );

	IECore::CompoundObjectPtr parameters = new CompoundObject;
	parameters->members()["aimType"] = new IntData( 0 );
	group->getState()->add(
		new IECoreGL::ShaderStateComponent( ShaderLoader::defaultShaderLoader(), TextureLoader::defaultTextureLoader(), faceCameraVertexSource(), "", IECoreGL::Shader::constantFragmentSource(), parameters )
	);

	IntVectorDataPtr vertsPerCurve = new IntVectorData;
	V3fVectorDataPtr p = new V3fVectorData;
	addCone( innerAngle, lensRadius, vertsPerCurve->writable(), p->writable() );

	IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), false, vertsPerCurve );
	curves->addPrimitiveVariable( "P", IECore::PrimitiveVariable( IECore::PrimitiveVariable::Vertex, p ) );
	curves->addPrimitiveVariable( "Cs", IECore::PrimitiveVariable( IECore::PrimitiveVariable::Constant, new Color3fData( Color3f( 1.0f, 0.835f, 0.07f ) ) ) );

	group->addChild( curves );

	if( fabs( innerAngle - outerAngle ) > 0.1 )
	{
		IECoreGL::GroupPtr outerGroup = new Group;
		outerGroup->getState()->add( new IECoreGL::CurvesPrimitive::GLLineWidth( 0.5f ) );

		IntVectorDataPtr vertsPerCurve = new IntVectorData;
		V3fVectorDataPtr p = new V3fVectorData;
		addCone( outerAngle, lensRadius, vertsPerCurve->writable(), p->writable() );

		IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), false, vertsPerCurve );
		curves->addPrimitiveVariable( "P", IECore::PrimitiveVariable( IECore::PrimitiveVariable::Vertex, p ) );
		curves->addPrimitiveVariable( "Cs", IECore::PrimitiveVariable( IECore::PrimitiveVariable::Constant, new Color3fData( Color3f( 1.0f, 0.835f, 0.07f ) ) ) );

		outerGroup->addChild( curves );

		group->addChild( outerGroup );
	}

	return group;
}

IECoreGL::ConstRenderablePtr StandardLightVisualiser::environmentSphere( const Imath::Color3f &color, const std::string &textureFileName )
{
	IECoreGL::GroupPtr group = new IECoreGL::Group();

	Imath::M44f trans;
	trans.scale( V3f( 1, 1, -1 ) );
	trans.rotate( V3f( -0.5 * M_PI, -0.5 * M_PI, 0 ) );
	group->setTransform( trans );

	IECoreGL::SpherePrimitivePtr sphere = new IECoreGL::SpherePrimitive();
	group->addChild( sphere );

	IECore::CompoundObjectPtr parameters = new CompoundObject;
	parameters->members()["lightMultiplier"] = new Color3fData( color );
	parameters->members()["previewOpacity"] = new FloatData( 1 );
	parameters->members()["mapSampler"] = new StringData( textureFileName );
	parameters->members()["defaultColor"] = new Color3fData( Color3f( textureFileName == "" ? 1.0f : 0.0f ) );
	group->getState()->add(
		new IECoreGL::ShaderStateComponent( ShaderLoader::defaultShaderLoader(), TextureLoader::defaultTextureLoader(), IECoreGL::Shader::defaultVertexSource(), "", environmentSphereFragSource(), parameters )
	);
	group->getState()->add(
		new IECoreGL::DoubleSidedStateComponent( false )
	);

	return group;
}

IECoreGL::ConstRenderablePtr StandardLightVisualiser::colorIndicator( const Imath::Color3f &color, bool faceCamera )
{

	float maxChannel = std::max( color[0], std::max( color[1], color[2] ) );
	float exposure = 0;
	Imath::Color3f indicatorColor = color;
	if( maxChannel > 1 )
	{
		indicatorColor = color / maxChannel;
		exposure = log( maxChannel ) / log( 2 );
	}
	IECoreGL::GroupPtr group = new IECoreGL::Group();
	IECoreGL::GroupPtr wirelessGroup = new IECoreGL::Group();

	IECore::CompoundObjectPtr parameters = new CompoundObject;
	parameters->members()["aimType"] = new IntData( 1 );
	group->getState()->add(
		new IECoreGL::ShaderStateComponent( ShaderLoader::defaultShaderLoader(), TextureLoader::defaultTextureLoader(), faceCamera ? faceCameraVertexSource() : "", "", IECoreGL::Shader::constantFragmentSource(), parameters )
	);

	wirelessGroup->getState()->add( new IECoreGL::Primitive::DrawWireframe( false ) );

	float indicatorRad = 0.3;
	int indicatorAxis = faceCamera ? 0 : 2;

	{
		IntVectorDataPtr vertsPerPoly = new IntVectorData;
		IntVectorDataPtr vertIds = new IntVectorData;
		V3fVectorDataPtr p = new V3fVectorData;

		addSolidArc( indicatorAxis, V3f( 0 ), indicatorRad, indicatorRad * 0.9, 0, 1, vertsPerPoly->writable(), vertIds->writable(), p->writable() );

		IECore::MeshPrimitivePtr mesh = new IECore::MeshPrimitive( vertsPerPoly, vertIds, "linear", p );
		mesh->variables["N"] = IECore::PrimitiveVariable( IECore::PrimitiveVariable::Constant, new V3fData( V3f( 0 ) ) );
		mesh->variables["Cs"] = IECore::PrimitiveVariable( IECore::PrimitiveVariable::Constant, new Color3fData( indicatorColor ) );
		ToGLMeshConverterPtr meshConverter = new ToGLMeshConverter( mesh );
		group->addChild( IECore::runTimeCast<IECoreGL::Renderable>( meshConverter->convert() ) );
	}
	{
		IntVectorDataPtr vertsPerPoly = new IntVectorData;
		IntVectorDataPtr vertIds = new IntVectorData;
		V3fVectorDataPtr p = new V3fVectorData;

		addSolidArc( indicatorAxis, V3f( 0 ), indicatorRad * 0.4, 0.0, 0, 1, vertsPerPoly->writable(), vertIds->writable(), p->writable() );

		for( int i = 0; i < exposure && i < 20; i++ )
		{
			float startAngle = 1 - pow( 0.875, i );
			float endAngle = 1 - pow( 0.875, std::min( i+1.0, (double)exposure ) );
			float maxEndAngle = 1 - pow( 0.875, i+1.0);
			float sectorScale = ( maxEndAngle - startAngle - 0.008 ) / ( maxEndAngle - startAngle );
			addSolidArc( indicatorAxis, V3f( 0 ), indicatorRad * 0.85, indicatorRad * 0.45, startAngle, startAngle + ( endAngle - startAngle ) * sectorScale, vertsPerPoly->writable(), vertIds->writable(), p->writable() );
		}

		IECore::MeshPrimitivePtr mesh = new IECore::MeshPrimitive( vertsPerPoly, vertIds, "linear", p );
		mesh->variables["N"] = IECore::PrimitiveVariable( IECore::PrimitiveVariable::Constant, new V3fData( V3f( 0 ) ) );
		mesh->variables["Cs"] = IECore::PrimitiveVariable( IECore::PrimitiveVariable::Constant, new Color3fData( indicatorColor ) );
		ToGLMeshConverterPtr meshConverter = new ToGLMeshConverter( mesh );
		wirelessGroup->addChild( IECore::runTimeCast<IECoreGL::Renderable>( meshConverter->convert() ) );
	}

	// For exposures greater than 20, draw an additional solid bar of a darker color at the very end, without any segment dividers
	if( exposure > 20 )
	{
		IntVectorDataPtr vertsPerPoly = new IntVectorData;
		IntVectorDataPtr vertIds = new IntVectorData;
		V3fVectorDataPtr p = new V3fVectorData;

		float startAngle = 1 - pow( 0.875, 20 );
		float endAngle = 1 - pow( 0.875, (double)exposure );
		addSolidArc( indicatorAxis, V3f( 0 ), indicatorRad * 0.85, indicatorRad * 0.45, startAngle, endAngle, vertsPerPoly->writable(), vertIds->writable(), p->writable() );

		IECore::MeshPrimitivePtr mesh = new IECore::MeshPrimitive( vertsPerPoly, vertIds, "linear", p );
		mesh->variables["N"] = IECore::PrimitiveVariable( IECore::PrimitiveVariable::Constant, new V3fData( V3f( 0 ) ) );
		mesh->variables["Cs"] = IECore::PrimitiveVariable( IECore::PrimitiveVariable::Constant, new Color3fData( 0.5f * indicatorColor ) );
		ToGLMeshConverterPtr meshConverter = new ToGLMeshConverter( mesh );
		wirelessGroup->addChild( IECore::runTimeCast<IECoreGL::Renderable>( meshConverter->convert() ) );
	}

	group->addChild( wirelessGroup );

	return group;
}

IECoreGL::ConstRenderablePtr StandardLightVisualiser::quadShape()
{
	IECoreGL::GroupPtr group = new IECoreGL::Group();
	addWireframeCurveState( group.get() );

	IECore::CompoundObjectPtr parameters = new CompoundObject;
	group->getState()->add(
		new IECoreGL::ShaderStateComponent( ShaderLoader::defaultShaderLoader(), TextureLoader::defaultTextureLoader(), "", "", IECoreGL::Shader::constantFragmentSource(), parameters )
	);

	IntVectorDataPtr vertsPerCurveData = new IntVectorData;
	V3fVectorDataPtr pData = new V3fVectorData;

	vector<int> &vertsPerCurve = vertsPerCurveData->writable();
	vector<V3f> &p = pData->writable();

	vertsPerCurve.push_back( 4 );
	p.push_back( V3f( -1, -1, 0  ) );
	p.push_back( V3f( 1, -1, 0  ) );
	p.push_back( V3f( 1, 1, 0  ) );
	p.push_back( V3f( -1, 1, 0  ) );

	IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), /* periodic = */ true, vertsPerCurveData );
	curves->addPrimitiveVariable( "P", IECore::PrimitiveVariable( IECore::PrimitiveVariable::Vertex, pData ) );
	curves->addPrimitiveVariable( "Cs", IECore::PrimitiveVariable( IECore::PrimitiveVariable::Constant, new Color3fData( Color3f( 1.0f, 0.835f, 0.07f ) ) ) );

	group->addChild( curves );

	return group;
}

IECoreGL::ConstRenderablePtr StandardLightVisualiser::diskShape( float radius )
{
	IECoreGL::GroupPtr group = new IECoreGL::Group();
	addWireframeCurveState( group.get() );

	IECore::CompoundObjectPtr parameters = new CompoundObject;
	group->getState()->add(
		new IECoreGL::ShaderStateComponent( ShaderLoader::defaultShaderLoader(), TextureLoader::defaultTextureLoader(), "", "", IECoreGL::Shader::constantFragmentSource(), parameters )
	);

	IntVectorDataPtr vertsPerCurveData = new IntVectorData;
	V3fVectorDataPtr pData = new V3fVectorData;

	addCircle( V3f( 0 ), radius, vertsPerCurveData->writable(), pData->writable() );

	IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), /* periodic = */ false, vertsPerCurveData );
	curves->addPrimitiveVariable( "P", IECore::PrimitiveVariable( IECore::PrimitiveVariable::Vertex, pData ) );
	curves->addPrimitiveVariable( "Cs", IECore::PrimitiveVariable( IECore::PrimitiveVariable::Constant, new Color3fData( Color3f( 1.0f, 0.835f, 0.07f ) ) ) );

	group->addChild( curves );

	return group;
}

IECoreGL::ConstRenderablePtr StandardLightVisualiser::cylinderShape( float radius )
{
	IECoreGL::GroupPtr group = new IECoreGL::Group();
	addWireframeCurveState( group.get() );

	IECore::CompoundObjectPtr parameters = new CompoundObject;
	parameters->members()["aimType"] = new IntData( 0 );
	group->getState()->add(
		new IECoreGL::ShaderStateComponent( ShaderLoader::defaultShaderLoader(), TextureLoader::defaultTextureLoader(), StandardLightVisualiser::faceCameraVertexSource(), "", IECoreGL::Shader::constantFragmentSource(), parameters )
	);

	IntVectorDataPtr vertsPerCurveData = new IntVectorData;
	vector<int> &vertsPerCurve = vertsPerCurveData->writable();
	V3fVectorDataPtr pData = new V3fVectorData;
	vector<V3f> &p = pData->writable();

	addCircle( V3f( 0, 0, -1 ), radius, vertsPerCurve, p );
	addCircle( V3f( 0, 0, 1 ), radius, vertsPerCurve, p );

	p.push_back( V3f( 0, radius, -1 ) );
	p.push_back( V3f( 0, radius, 1 ) );
	vertsPerCurve.push_back( 2 );

	p.push_back( V3f( 0, -radius, -1 ) );
	p.push_back( V3f( 0, -radius, 1 ) );
	vertsPerCurve.push_back( 2 );

	IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), false, vertsPerCurveData );
	curves->addPrimitiveVariable( "P", IECore::PrimitiveVariable( IECore::PrimitiveVariable::Vertex, pData ) );
	curves->addPrimitiveVariable( "Cs", IECore::PrimitiveVariable( IECore::PrimitiveVariable::Constant, new Color3fData( Color3f( 1.0f, 0.835f, 0.07f ) ) ) );

	group->addChild( curves );

	return group;
}

/// \todo Expose publicly when we've decided what the
/// parameters should be.
IECoreGL::ConstRenderablePtr StandardLightVisualiser::cylinderRays( float radius )
{
	IECoreGL::GroupPtr group = new IECoreGL::Group();
	addWireframeCurveState( group.get() );

	IECore::CompoundObjectPtr parameters = new CompoundObject;
	parameters->members()["aimType"] = new IntData( 0 );
	group->getState()->add(
		new IECoreGL::ShaderStateComponent( ShaderLoader::defaultShaderLoader(), TextureLoader::defaultTextureLoader(), StandardLightVisualiser::faceCameraVertexSource(), "", IECoreGL::Shader::constantFragmentSource(), parameters )
	);

	const int numRays = 8;
	for( int i = 0; i < numRays; ++i )
	{
		GroupPtr rayGroup = new Group;
		rayGroup->addChild( const_pointer_cast<IECoreGL::Renderable>( StandardLightVisualiser::ray() ) );

		const float angle = M_PI * 2.0f * float(i)/(float)numRays;
		M44f m;
		m.rotate( V3f( angle, 0, 0 ) );
		m.translate( V3f( 0, 0, -radius ) );

		rayGroup->setTransform( m );
		group->addChild( rayGroup );
	}

	group->setTransform( M44f().rotate( V3f( 0, M_PI / 2.0, 0 ) ) );

	return group;
}

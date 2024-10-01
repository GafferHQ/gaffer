//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/LightToCamera.h"

#include "Gaffer/Context.h"
#include "Gaffer/Metadata.h"

#include "IECoreScene/Camera.h"
#include "IECoreScene/Shader.h"
#include "IECoreScene/ShaderNetwork.h"

#include "IECore/CompoundData.h"
#include "IECore/Export.h"
#include "IECore/AngleConversion.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "Imath/ImathMatrix.h"
#include "Imath/ImathVec.h"
IECORE_POP_DEFAULT_VISIBILITY

#include "boost/algorithm/string.hpp"

using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;
using namespace Imath;

static IECore::InternedString g_lightsSetName( "__lights" );
static IECore::InternedString g_camerasSetName( "__cameras" );

/// \todo: This stuff should all end up as part of the light accessor API once that exists
/// In the meantime, I've tried to set it up vaguely similarly to how that will work
namespace
{

template<typename T>
T parameter( InternedString metadataTarget, const IECore::CompoundData *parameters, InternedString parameterNameMetadata, T defaultValue )
{
	ConstStringDataPtr parameterName = Metadata::value<StringData>( metadataTarget, parameterNameMetadata );
	if( !parameterName )
	{
		return defaultValue;
	}

	using DataType = IECore::TypedData<T>;
	if( const DataType *parameterData = parameters->member<DataType>( parameterName->readable() ) )
	{
		return parameterData->readable();
	}

	return defaultValue;
}

// Return the first light shader found in attributes
void light( const CompoundObject *attributes, const IECore::CompoundData* &shaderParameters, std::string &metadataTarget )
{
	for( IECore::CompoundObject::ObjectMap::const_iterator it = attributes->members().begin();
		it != attributes->members().end(); it++ )
	{
		const std::string &attributeName = it->first.string();
		if( !( boost::ends_with( attributeName, ":light" ) || attributeName == "light" ) )
		{
			continue;
		}

		const IECoreScene::ShaderNetwork *shaderNetwork = IECore::runTimeCast<const IECoreScene::ShaderNetwork>( it->second.get() );
		if( !shaderNetwork || !shaderNetwork->size() )
		{
			continue;
		}

		const IECoreScene::Shader *shader = shaderNetwork->outputShader();
		if( !shader )
		{
			continue;
		}

		metadataTarget = attributeName + ":" + shader->getName();
		shaderParameters = shader->parametersData();
		return;
	}

	metadataTarget = "";
	shaderParameters = nullptr;
	return;
}

const char *lightType( const IECore::CompoundData *shaderParameters, const std::string &metadataTarget )
{
	ConstStringDataPtr type = Metadata::value<StringData>( metadataTarget, "type" );
	if( !type || !shaderParameters )
	{
		return "";
	}

	if( boost::starts_with( metadataTarget, "light:" ) && shaderParameters->member<FloatData>( "shaping:cone:angle" ) )
	{
		// USD lights with a cone angle defined are treated as spot lights
		return "spot";
	}

	return type->readable().c_str();
}

float lightOuterAngle( const IECore::CompoundData *shaderParameters, const std::string &metadataTarget )
{
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

	if( ConstStringDataPtr coneAngleType = Metadata::value<StringData>( metadataTarget, "coneAngleType" ) )
	{
		if( coneAngleType->readable() == "half" )
		{
			coneAngle *= 2.0f;
		}
	}

	const std::string *penumbraType = nullptr;
	ConstStringDataPtr penumbraTypeData = Metadata::value<StringData>( metadataTarget, "penumbraType" );
	if( penumbraTypeData )
	{
		penumbraType = &penumbraTypeData->readable();
	}

	float outerAngle = coneAngle;

	// In "inset" or "absolute" modes, the outer angle is just the cone angle.  "outset" needs
	// adjustment
	if( penumbraType && *penumbraType == "outset" )
	{
		outerAngle = coneAngle + 2.0f * penumbraAngle;
	}

	// Match the minimum coneAngle supported by Arnold to avoid special cases
	outerAngle = std::max( 0.25f, outerAngle );

	return outerAngle;
}

float lightLensRadius( const IECore::CompoundData *shaderParameters, const std::string &metadataTarget )
{
	if( parameter<bool>( metadataTarget, shaderParameters, "lensRadiusEnableParameter", true ) )
	{
		return parameter<float>( metadataTarget, shaderParameters, "lensRadiusParameter", 0.0f );
	}
	return 0.0f;
}

float lightFocalPointOffset( float lensRadius, float outerAngle )
{
	return lensRadius / tan( 0.5f * outerAngle * M_PI / 180.0f );
}

M44f lightCameraTransform( const IECore::CompoundData *shaderParameters, const std::string &metadataTarget )
{
	const char *type = lightType( shaderParameters, metadataTarget );

	if( type && !strcmp( type, "spot" ) )
	{
		float lensRadius = lightLensRadius( shaderParameters, metadataTarget );
		float outerAngle = lightOuterAngle( shaderParameters, metadataTarget );

		float focalPointOffset = lightFocalPointOffset( lensRadius, outerAngle );
		M44f transformOffset;
		transformOffset.setTranslation( V3f( 0.0f, 0.0f, focalPointOffset ) );
		return transformOffset;
	}
	else
	{
		return M44f();
	}
}

IECoreScene::CameraPtr lightToCamera( const IECore::CompoundData *shaderParameters, Camera::FilmFit filmFit, float distantAperture, V2f clippingPlanes, const std::string &metadataTarget )
{
	IECoreScene::CameraPtr result = new IECoreScene::Camera();
	const char *type = lightType( shaderParameters, metadataTarget );

	if( type && !strcmp( type, "distant" ) )
	{
		result->setProjection( "orthographic" );
		result->setClippingPlanes( clippingPlanes );
		result->setAperture( V2f( distantAperture ) );
	}
	else if( type && !strcmp( type, "spot" ) )
	{
		float lensRadius = lightLensRadius( shaderParameters, metadataTarget );
		float outerAngle = lightOuterAngle( shaderParameters, metadataTarget );

		float focalPointOffset = lightFocalPointOffset( lensRadius, outerAngle );

		if( clippingPlanes.x <= 0 )
		{
			// If we haven't specified a near clip that is valid for a perspective camera,
			// use a default
			clippingPlanes.x = 0.01f;
		}

		// Keep the near clip past the origin of the light, in case the point of the frustum isn't at
		// the origin of the light.  Add an extra little offset so we don't see
		// the light's color indicator when looking through it in the viewport
		clippingPlanes.x = std::max( focalPointOffset + 0.0001f, clippingPlanes.x );
		result->setClippingPlanes( clippingPlanes );
		result->setProjection( "perspective" );
		result->setAperture( V2f( 1.0f ) );
		result->setFocalLengthFromFieldOfView( outerAngle );
	}
	else
	{
		return nullptr;
	}
	result->setFilmFit( filmFit );

	return result;
}

} // namespace

GAFFER_NODE_DEFINE_TYPE( LightToCamera );

size_t LightToCamera::g_firstPlugIndex = 0;

LightToCamera::LightToCamera( const std::string &name )
	:	SceneElementProcessor( name, IECore::PathMatcher::NoMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new IntPlug( "filmFit", Plug::In, IECoreScene::Camera::Fit ) );
	addChild( new FloatPlug( "distantAperture", Plug::In, 2.0f ) );
	addChild( new V2fPlug( "clippingPlanes", Plug::In, V2f( -100000, 100000 ) ) );

	// Fast pass-throughs for things we don't modify
	outPlug()->boundPlug()->setInput( inPlug()->boundPlug() );

	// We do modify sets
	outPlug()->setNamesPlug()->setInput( nullptr );
	outPlug()->setPlug()->setInput( nullptr );
}

LightToCamera::~LightToCamera()
{
}

Gaffer::IntPlug *LightToCamera::filmFitPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *LightToCamera::filmFitPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

Gaffer::FloatPlug *LightToCamera::distantAperturePlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::FloatPlug *LightToCamera::distantAperturePlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

Gaffer::V2fPlug *LightToCamera::clippingPlanesPlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::V2fPlug *LightToCamera::clippingPlanesPlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex + 2 );
}

void LightToCamera::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );

	if( input == filmFitPlug() || input == distantAperturePlug() || input->parent() == clippingPlanesPlug() )
	{
		outputs.push_back( outPlug()->objectPlug() );
	}
	else if( input == inPlug()->attributesPlug() )
	{
		outputs.push_back( outPlug()->objectPlug() );
		outputs.push_back( outPlug()->transformPlug() );
		outputs.push_back( outPlug()->setPlug() );
		outputs.push_back( outPlug()->setNamesPlug() );
	}
	else if( input == filterPlug() )
	{
		outputs.push_back( outPlug()->setPlug() );
		outputs.push_back( outPlug()->setNamesPlug() );
	}
}

bool LightToCamera::processesObject() const
{
	return true;
}

void LightToCamera::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	filmFitPlug()->hash( h );
	distantAperturePlug()->hash( h );
	clippingPlanesPlug()->hash( h );
	inPlug()->attributesPlug()->hash( h );
}

IECore::ConstObjectPtr LightToCamera::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const
{
	const IECore::CompoundData* shaderParameters;
	std::string metadataTarget;
	IECore::ConstCompoundObjectPtr attributes = inPlug()->attributesPlug()->getValue();
	light( attributes.get(), shaderParameters, metadataTarget );
	IECoreScene::CameraPtr camera = nullptr;
	if( shaderParameters )
	{
		camera = lightToCamera(
			shaderParameters,
			(Camera::FilmFit)filmFitPlug()->getValue(),
			distantAperturePlug()->getValue(),
			clippingPlanesPlug()->getValue(),
			metadataTarget
		);
	}

	if( !camera )
	{
		camera = new IECoreScene::Camera();
		camera->setProjection( "perspective" );
	}

	return camera;
}

bool LightToCamera::processesTransform() const
{
	return true;
}

void LightToCamera::hashProcessedTransform( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	inPlug()->attributesPlug()->hash( h );
}

M44f LightToCamera::computeProcessedTransform( const ScenePath &path, const Gaffer::Context *context, const M44f &inputTransform ) const
{
	const IECore::CompoundData* shaderParameters;
	std::string metadataTarget;
	light( inPlug()->attributesPlug()->getValue().get(), shaderParameters, metadataTarget );
	IECoreScene::ConstCameraPtr camera = nullptr;
	if( shaderParameters )
	{
		return lightCameraTransform( shaderParameters, metadataTarget ) * inputTransform;
	}

	return inputTransform;
}

bool LightToCamera::processesAttributes() const
{
	return true;
}

void LightToCamera::hashProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	// Attributes depend only on input attributes
}

IECore::ConstCompoundObjectPtr LightToCamera::computeProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputAttributes ) const
{
	CompoundObjectPtr result = new CompoundObject;
	for( CompoundObject::ObjectMap::const_iterator it = inputAttributes->members().begin(), eIt = inputAttributes->members().end(); it != eIt; ++it )
	{
		const std::string &attributeName = it->first.string();
		if( !( boost::ends_with( attributeName, ":light" ) || attributeName == "light" ) )
		{
			result->members()[it->first] = it->second;
		}
	}

	return result;
}

void LightToCamera::hashSetNames( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneElementProcessor::hashSetNames( context, parent, h );
	// We always just add a __cameras set if it doesn't yet exist, without spending time checking
	// whether it will be non-empty ( usually there will already be a __cameras set anyway )
}

IECore::ConstInternedStringVectorDataPtr LightToCamera::computeSetNames( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstInternedStringVectorDataPtr inputSetNamesData = inPlug()->setNamesPlug()->getValue();
	const std::vector<InternedString> &inNames = inputSetNamesData->readable();

	if( std::find( inNames.begin(), inNames.end(), g_camerasSetName ) != inNames.end() )
	{
		return inputSetNamesData;
	}

	InternedStringVectorDataPtr resultData = inputSetNamesData->copy();
	resultData->writable().push_back( g_camerasSetName );
	return resultData;
}

void LightToCamera::hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( setName != g_camerasSetName && setName != g_lightsSetName )
	{
		h = inPlug()->setPlug()->hash();
		return;
	}

	SceneElementProcessor::hashSet( setName, context, parent, h );
	inPlug()->setPlug()->hash( h );

	// This setup is copied from Prune

	// The sets themselves do not depend on the "scene:path"
	// context entry - the whole point is that they're global.
	// However, the PathFilter is dependent on scene:path, so
	// we must remove the path before hashing in the filter in
	// case we're computed from multiple contexts with different
	// paths (from a SetFilter for instance). If we didn't do this,
	// our different hashes would lead to huge numbers of redundant
	// calls to computeSet() and a huge overhead in recomputing
	// the same sets repeatedly.
	//
	// See further comments in acceptsInput
	FilterPlug::SceneScope sceneScope( context, inPlug() );
	sceneScope.remove( ScenePlug::scenePathContextName );
	filterPlug()->hash( h );
}

IECore::ConstPathMatcherDataPtr LightToCamera::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstPathMatcherDataPtr inputSetData = inPlug()->setPlug()->getValue();

	bool isLightSet = setName == g_lightsSetName;
	bool isCameraSet = setName == g_camerasSetName;
	if( !( isLightSet || isCameraSet ) )
	{
		return inputSetData;
	}

	ConstPathMatcherDataPtr lightSetData;
	if( isLightSet )
	{
		lightSetData = inputSetData;
	}
	else
	{
		lightSetData = inPlug()->set( g_lightsSetName );
	}

	const PathMatcher &lightSet = lightSetData->readable();

	PathMatcherDataPtr outputSetData = inputSetData->copy();
	PathMatcher &outputSet = outputSetData->writable();

	FilterPlug::SceneScope sceneScope( context, inPlug() );

	/// \todo We're assuming here that the filter won't match
	/// anything outside the light set, but we're not doing anything
	/// to enforce that. If we had a FilterResults node, we could use
	/// that internally in conjunction with a Sets node to do all the
	/// work for us.
	for( PathMatcher::Iterator pIt = lightSet.begin(), peIt = lightSet.end(); pIt != peIt; ++pIt )
	{
		sceneScope.set( ScenePlug::scenePathContextName, &(*pIt) );
		const int m = filterPlug()->getValue();
		if( m & IECore::PathMatcher::ExactMatch )
		{
			if( isLightSet )
			{
				outputSet.removePath( *pIt );
			}
			else
			{
				outputSet.addPath( *pIt );
			}
		}
	}

	return outputSetData;
}

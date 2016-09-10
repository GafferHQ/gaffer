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

#include "boost/algorithm/string.hpp"

#include "OpenEXR/ImathMatrix.h"
#include "OpenEXR/ImathVec.h"

#include "IECore/CompoundData.h"
#include "IECore/Camera.h"
#include "IECore/Shader.h"
#include "IECore/Transform.h"

#include "Gaffer/Metadata.h"
#include "Gaffer/Context.h"

#include "GafferScene/LightToCamera.h"

using namespace IECore;
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

	typedef IECore::TypedData<T> DataType;
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

		const IECore::ObjectVector *shaderVector = IECore::runTimeCast<const IECore::ObjectVector>( it->second.get() );
		if( !shaderVector || shaderVector->members().empty() )
		{
			continue;
		}

		IECore::InternedString shaderName;
		const IECore::Shader *shader = IECore::runTimeCast<const IECore::Shader>( shaderVector->members().back().get() );
		if( !shader )
		{
			continue;
		}

		metadataTarget = attributeName + ":" + shader->getName();
		shaderParameters = shader->parametersData();
		return;
	}

	metadataTarget = "";
	shaderParameters = NULL;
	return;
}

const char *lightType( const IECore::CompoundData *shaderParameters, const std::string &metadataTarget )
{
	ConstStringDataPtr type = Metadata::value<StringData>( metadataTarget, "type" );
	if( !type || !shaderParameters )
	{
		return "";
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

	const std::string *penumbraType = NULL;
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

IECore::CameraPtr lightToCamera( const IECore::CompoundData *shaderParameters, const std::string &metadataTarget )
{
	IECore::CameraPtr result = new IECore::Camera();
	const char *type = lightType( shaderParameters, metadataTarget );


	float screenWindowScale = 1.0f;
	if( type && !strcmp( type, "distant" ) )
	{
		const float locatorScale = parameter<float>( metadataTarget, shaderParameters, "locatorScaleParameter", 1 );

		result->parameters()["projection"] = new StringData( "orthographic" );
		result->parameters()["clippingPlanes"] = new V2fData( V2f( -100000, 100000 ) );
		screenWindowScale = locatorScale;
	}
	else if( type && !strcmp( type, "spot" ) )
	{
		float lensRadius = lightLensRadius( shaderParameters, metadataTarget );
		float outerAngle = lightOuterAngle( shaderParameters, metadataTarget );

		float focalPointOffset = lightFocalPointOffset( lensRadius, outerAngle );

		// Set clipping plane to cover the area in front of the spot, with small adjustments
		// to make sure that we don't go under 0.01 in near clip to preserve depth range,
		// and we keep the near clip slightly past the origin of the light so we don't see
		// the light's color indicator when looking through it in the viewport
		result->parameters()["clippingPlanes"] = new V2fData( V2f( std::max( focalPointOffset + 0.0001f, 0.01f ), 100000 ) );
		result->parameters()["projection"] = new StringData( "perspective" );
		result->parameters()["projection:fov"] = new FloatData( outerAngle );
	}
	else
	{
		return NULL;
	}

	// Hardcode resolution to some sort of square by default, interface for selecting resolution
	// not yet decided, as per John
	result->parameters()["resolutionOverride"] = new V2iData( V2i( 512, 512 ) );
	Box2f screenWindow( screenWindowScale * V2f( -1.0f ), screenWindowScale * V2f( 1.0f ) );
	result->parameters()["screenWindow"] = new Box2fData( screenWindow );

	return result;
}

} // namespace

IE_CORE_DEFINERUNTIMETYPED( LightToCamera );

size_t LightToCamera::g_firstPlugIndex = 0;

LightToCamera::LightToCamera( const std::string &name )
	:	SceneElementProcessor( name, GafferScene::Filter::NoMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	// Fast pass-throughs for things we don't modify
	outPlug()->boundPlug()->setInput( inPlug()->boundPlug() );

	// We do modify sets
	outPlug()->setNamesPlug()->setInput( NULL );
	outPlug()->setPlug()->setInput( NULL );
}

LightToCamera::~LightToCamera()
{
}

void LightToCamera::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );

	if( input == inPlug()->attributesPlug() )
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

bool LightToCamera::acceptsInput( const Gaffer::Plug *plug, const Gaffer::Plug *inputPlug ) const
{
	if( !SceneElementProcessor::acceptsInput( plug, inputPlug ) )
	{
		return false;
	}

	if( plug == filterPlug() )
	{
		if( const Filter *filter = runTimeCast<const Filter>( inputPlug->source<Plug>()->node() ) )
		{
			if(
				filter->sceneAffectsMatch( inPlug(), inPlug()->boundPlug() ) ||
				filter->sceneAffectsMatch( inPlug(), inPlug()->transformPlug() ) ||
				filter->sceneAffectsMatch( inPlug(), inPlug()->attributesPlug() ) ||
				filter->sceneAffectsMatch( inPlug(), inPlug()->objectPlug() ) ||
				filter->sceneAffectsMatch( inPlug(), inPlug()->childNamesPlug() )
			)
			{
				// We make a single call to filterHash() in hashSet(), to account for
				// the fact that the filter is used in remapping sets. This wouldn't
				// work for filter types which actually vary based on data within the
				// scene hierarchy, because then multiple calls would be necessary.
				// We could make more calls here, but that would be expensive.
				/// \todo In an ideal world we'd be able to compute a hash for the
				/// filter across a whole hierarchy.
				return false;
			}
		}
	}

	return true;
}


bool LightToCamera::processesObject() const
{
	return true;
}

void LightToCamera::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	inPlug()->attributesPlug()->hash( h );
}

IECore::ConstObjectPtr LightToCamera::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const
{
	const IECore::CompoundData* shaderParameters;
	std::string metadataTarget;
	light( inPlug()->attributesPlug()->getValue().get(), shaderParameters, metadataTarget );
	IECore::ConstCameraPtr camera = NULL;
	if( shaderParameters )
	{
		camera = lightToCamera( shaderParameters, metadataTarget );
	}

	if( camera )
	{
		return camera;
	}
	else
	{
		IECore::CameraPtr defaultCamera = new IECore::Camera();
		defaultCamera->parameters()["projection"] = new StringData( "perspective" );
		defaultCamera->parameters()["resolutionOverride"] = new V2iData( V2i( 512, 512 ) );
		return defaultCamera;
	}
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
	IECore::ConstCameraPtr camera = NULL;
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
	ContextPtr c = filterContext( context );
	c->remove( ScenePlug::scenePathContextName );
	Context::Scope s( c.get() );
	filterPlug()->hash( h );
}

GafferScene::ConstPathMatcherDataPtr LightToCamera::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const
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

	ContextPtr tmpContext = filterContext( context );
	Context::Scope scopedContext( tmpContext.get() );

	/// \todo We're assuming here that the filter won't match
	/// anything outside the light set, but we're not doing anything
	/// to enforce that. If we had a FilterResults node, we could use
	/// that internally in conjunction with a Sets node to do all the
	/// work for us.
	for( PathMatcher::Iterator pIt = lightSet.begin(), peIt = lightSet.end(); pIt != peIt; ++pIt )
	{
		tmpContext->set( ScenePlug::scenePathContextName, *pIt );
		const int m = filterPlug()->getValue();
		if( m & Filter::ExactMatch )
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


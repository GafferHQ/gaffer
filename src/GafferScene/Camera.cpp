//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/Camera.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/Camera.h"
#include "IECoreScene/Transform.h"

#include "IECore/AngleConversion.h"


using namespace Gaffer;
using namespace GafferScene;
using namespace Imath;
using namespace IECore;

static IECore::InternedString g_camerasSetName( "__cameras" );

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( Camera );

size_t Camera::g_firstPlugIndex = 0;

Camera::Camera( const std::string &name )
	:	ObjectSource( name, "camera" )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "projection", Plug::In, "perspective" ) );
	addChild( new IntPlug( "perspectiveMode", Plug::In, FieldOfView ) );
	addChild( new FloatPlug( "fieldOfView", Plug::In, 50.0f, 0.0f, 180.0f ) );
	addChild( new FloatPlug( "apertureAspectRatio", Plug::In, 1.0f, 0.0f ) );
	addChild( new V2fPlug( "aperture", Plug::In, V2f( 36.0f, 24.0f ), V2f( 0.0f ) ) );
	addChild( new FloatPlug( "focalLength", Plug::In, 35.0f, 0.0f ) );
	addChild( new V2fPlug( "orthographicAperture", Plug::In, V2f( 2.0f, 2.0f ), V2f( 0.0f ) ) );
	addChild( new V2fPlug( "apertureOffset", Plug::In, V2f( 0.0f ) ) );
	addChild( new FloatPlug( "fStop", Plug::In, 5.6f, 0.0f ) );
	addChild( new FloatPlug( "focalLengthWorldScale", Plug::In, 0.1f, 0.0f ) );
	addChild( new FloatPlug( "focusDistance", Plug::In, 1.0f ) );
	addChild( new V2fPlug( "clippingPlanes", Plug::In, V2f( 0.01, 100000 ), V2f( 0 ) ) );

	addChild( new CompoundDataPlug( "renderSettingOverrides" ) );
	renderSettingOverridesPlug()->addChild( new NameValuePlug( "filmFit",  new IntData( IECoreScene::Camera::Horizontal ), false, "filmFit" ) );
	renderSettingOverridesPlug()->addChild( new NameValuePlug( "shutter", new V2fData( V2f( -0.5, 0.5 ) ), false, "shutter" ) );
	renderSettingOverridesPlug()->addChild( new NameValuePlug( "resolution", new V2iData( V2i( 1024, 1024 ) ), false, "resolution" ) );
	renderSettingOverridesPlug()->addChild( new NameValuePlug( "pixelAspectRatio", new FloatData( 1.0f ), false, "pixelAspectRatio" ) );
	renderSettingOverridesPlug()->addChild( new NameValuePlug( "resolutionMultiplier", new FloatData( 1.0f ), false, "resolutionMultiplier" ) );
	renderSettingOverridesPlug()->addChild( new NameValuePlug( "overscan", new BoolData( false ), false, "overscan" ) );
	renderSettingOverridesPlug()->addChild( new NameValuePlug( "overscanLeft", new FloatData( 0.0f ), false, "overscanLeft" ) );
	renderSettingOverridesPlug()->addChild( new NameValuePlug( "overscanRight", new FloatData( 0.0f ), false, "overscanRight" ) );
	renderSettingOverridesPlug()->addChild( new NameValuePlug( "overscanTop", new FloatData( 0.0f ), false, "overscanTop" ) );
	renderSettingOverridesPlug()->addChild( new NameValuePlug( "overscanBottom", new FloatData( 0.0f ), false, "overscanBottom" ) );
	renderSettingOverridesPlug()->addChild( new NameValuePlug( "cropWindow", new Box2fData( Box2f( V2f(0.0f), V2f(1.0f) ) ), false, "cropWindow" ) );
	renderSettingOverridesPlug()->addChild( new NameValuePlug( "depthOfField", new BoolData( false ), false, "depthOfField" ) );

	addChild( new CompoundDataPlug( "visualiserAttributes" ) );
	visualiserAttributesPlug()->addChild( new NameValuePlug( "gl:visualiser:frustum", new BoolData( true ), false, "frustum" ) );
}

Camera::~Camera()
{
}

Gaffer::StringPlug *Camera::projectionPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *Camera::projectionPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *Camera::perspectiveModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *Camera::perspectiveModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

Gaffer::FloatPlug *Camera::fieldOfViewPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::FloatPlug *Camera::fieldOfViewPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

Gaffer::FloatPlug *Camera::apertureAspectRatioPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::FloatPlug *Camera::apertureAspectRatioPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 3 );
}

Gaffer::V2fPlug *Camera::aperturePlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::V2fPlug *Camera::aperturePlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex + 4 );
}

Gaffer::FloatPlug *Camera::focalLengthPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::FloatPlug *Camera::focalLengthPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 5 );
}

Gaffer::V2fPlug *Camera::orthographicAperturePlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::V2fPlug *Camera::orthographicAperturePlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex + 6 );
}

Gaffer::V2fPlug *Camera::apertureOffsetPlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex + 7 );
}

const Gaffer::V2fPlug *Camera::apertureOffsetPlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex + 7 );
}

Gaffer::FloatPlug *Camera::fStopPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 8 );
}

const Gaffer::FloatPlug *Camera::fStopPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 8 );
}

Gaffer::FloatPlug *Camera::focalLengthWorldScalePlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 9 );
}

const Gaffer::FloatPlug *Camera::focalLengthWorldScalePlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 9 );
}

Gaffer::FloatPlug *Camera::focusDistancePlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 10 );
}

const Gaffer::FloatPlug *Camera::focusDistancePlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 10 );
}

Gaffer::V2fPlug *Camera::clippingPlanesPlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex + 11 );
}

const Gaffer::V2fPlug *Camera::clippingPlanesPlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex + 11 );
}

Gaffer::CompoundDataPlug *Camera::renderSettingOverridesPlug()
{
	return getChild<CompoundDataPlug>( g_firstPlugIndex + 12 );
}

const Gaffer::CompoundDataPlug *Camera::renderSettingOverridesPlug() const
{
	return getChild<CompoundDataPlug>( g_firstPlugIndex + 12 );
}

Gaffer::CompoundDataPlug *Camera::visualiserAttributesPlug()
{
	return getChild<CompoundDataPlug>( g_firstPlugIndex + 13 );
}

const Gaffer::CompoundDataPlug *Camera::visualiserAttributesPlug() const
{
	return getChild<CompoundDataPlug>( g_firstPlugIndex + 13 );
}

void Camera::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ObjectSource::affects( input, outputs );

	if(
		input == projectionPlug() ||
		input == perspectiveModePlug() ||
		input == fieldOfViewPlug() ||
		input == apertureAspectRatioPlug() ||
		input->parent<Plug>() == aperturePlug() ||
		input == focalLengthPlug() ||
		input->parent<Plug>() == orthographicAperturePlug() ||
		input->parent<Plug>() == apertureOffsetPlug() ||
		input == fStopPlug() ||
		input == focalLengthWorldScalePlug() ||
		input == focusDistancePlug() ||
		input->parent<Plug>() == clippingPlanesPlug() ||
		renderSettingOverridesPlug()->isAncestorOf( input )
	)
	{
		outputs.push_back( sourcePlug() );
	}

	if( visualiserAttributesPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->attributesPlug() );
	}
}

void Camera::hashSource( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	projectionPlug()->hash( h );
	perspectiveModePlug()->hash( h );
	fieldOfViewPlug()->hash( h );
	apertureAspectRatioPlug()->hash( h );
	aperturePlug()->hash( h );
	focalLengthPlug()->hash( h );
	orthographicAperturePlug()->hash( h );
	apertureOffsetPlug()->hash( h );
	fStopPlug()->hash( h );
	focalLengthWorldScalePlug()->hash( h );
	focusDistancePlug()->hash( h );
	clippingPlanesPlug()->hash( h );
	renderSettingOverridesPlug()->hash( h );
}

IECore::ConstObjectPtr Camera::computeSource( const Context *context ) const
{
	IECoreScene::CameraPtr result = new IECoreScene::Camera;
	const std::string &projection = projectionPlug()->getValue();
	result->setProjection( projection );
	V2f aperture;
	if( projection == "perspective" )
	{
		if( perspectiveModePlug()->getValue() == FieldOfView )
		{
			result->setAperture( V2f( 1.0f, 1.0f / apertureAspectRatioPlug()->getValue() ) );
			result->setFocalLengthFromFieldOfView( fieldOfViewPlug()->getValue() );
		}
		else
		{
			result->setFocalLength( focalLengthPlug()->getValue() );
			result->setAperture( aperturePlug()->getValue() );
		}
	}
	else
	{
		result->setAperture( orthographicAperturePlug()->getValue() );
	}

	result->setApertureOffset( apertureOffsetPlug()->getValue() );
	result->setFStop( fStopPlug()->getValue() );
	result->setFocalLengthWorldScale( focalLengthWorldScalePlug()->getValue() );
	result->setFocusDistance( focusDistancePlug()->getValue() );
	result->setClippingPlanes( clippingPlanesPlug()->getValue() );

	renderSettingOverridesPlug()->fillCompoundData( result->parametersData()->writable() );

	return result;
}

IECore::ConstInternedStringVectorDataPtr Camera::computeStandardSetNames() const
{
	IECore::InternedStringVectorDataPtr result = new IECore::InternedStringVectorData();
	result->writable().push_back( g_camerasSetName );
	return result;
}

void Camera::hashAttributes( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ObjectSource::hashAttributes( path, context, parent, h );
	visualiserAttributesPlug()->hash( h );
}

IECore::ConstCompoundObjectPtr Camera::computeAttributes( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	IECore::CompoundObjectPtr result = new IECore::CompoundObject;
	IECore::ConstCompoundObjectPtr attr = ObjectSource::computeAttributes( path, context, parent );
	result->members() = attr->members(); // Shallow copy for speed - do not modify in place!
	visualiserAttributesPlug()->fillCompoundObject( result->members() );
	return result;
}

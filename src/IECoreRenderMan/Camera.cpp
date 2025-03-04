//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

#include "Camera.h"

#include "ParamListAlgo.h"
#include "Transform.h"

#include "RixPredefinedStrings.hpp"

#include "boost/algorithm/string/predicate.hpp"

#include "fmt/format.h"

using namespace std;
using namespace Imath;
using namespace IECoreRenderMan;

namespace
{

const RtUString g_projectionHandle( "projection" );
const RtUString g_pxrCamera( "PxrCamera" );
const RtUString g_pxrOrthographic( "PxrOrthographic" );

} // namespace

/// \todo Overscan, depth of field
Camera::Camera( const std::string &name, const IECoreScene::Camera *camera, Session *session )
	:	m_session( session )
{
	// Parameters

	RtParamList cameraParamList;
	cameraParamList.SetFloat( Rix::k_nearClip, camera->getClippingPlanes()[0] );
	cameraParamList.SetFloat( Rix::k_farClip, camera->getClippingPlanes()[1] );

	const Box2f frustum = camera->frustum();
	array<float, 4> screenWindow = { frustum.min.x, frustum.max.x, frustum.min.y, frustum.max.y };
	cameraParamList.SetFloatArray( Rix::k_Ri_ScreenWindow, screenWindow.data(), screenWindow.size() );

	// Projection shader

	const string projection = camera->getProjection();
	RtUString projectionShaderName = g_pxrCamera;
	if( projection == "perspective" )
	{
		projectionShaderName = g_pxrCamera;
	}
	else if( projection == "orthographic" )
	{
		projectionShaderName = g_pxrOrthographic;
	}
	else if( boost::starts_with( projection, "ri:" ) )
	{
		projectionShaderName = RtUString( projection.c_str() + 3 );
	}
	else
	{
		IECore::msg( IECore::Msg::Warning, "Camera", fmt::format( "Unknown projection \"{}\"", projection ) );
	}

	RtParamList projectionParamList;
	for( const auto &[parameterName, parameterValue] : camera->parameters() )
	{
		if( boost::starts_with( name.c_str(), "ri:" ) )
		{
			ParamListAlgo::convertParameter( RtUString( parameterName.c_str() + 3 ), parameterValue.get(), projectionParamList );
		}
	}

	riley::ShadingNode projectionShader = {
		/* type = */ riley::ShadingNode::Type::k_Projection,
		/* name = */ projectionShaderName,
		/* handle = */ g_projectionHandle,
		/* params = */ projectionParamList
	};

	// Options. We specify things like format and crop on `IECoreScene::Camera`
	// objects, but RenderMan wants them to be specified as options. We figure
	// out the options here and store them in the Session for later usage.

	RtParamList options;

	const Imath::V2i resolution = camera->renderResolution();
	options.SetIntegerArray( Rix::k_Ri_FormatResolution, resolution.getValue(), 2 );
	options.SetFloat( Rix::k_Ri_FormatPixelAspectRatio, camera->getPixelAspectRatio() );

	Box2f cropWindow = camera->getCropWindow();
	if( cropWindow.isEmpty() )
	{
		/// \todo Would be better if IECoreScene::Camera defaulted to this rather
		/// than empty box.
		cropWindow = Box2f( V2f( 0 ), V2f( 1 ) );
	}
	float renderManCropWindow[4] = { cropWindow.min.x, cropWindow.max.x, cropWindow.min.y, cropWindow.max.y };
	options.SetFloatArray( Rix::k_Ri_CropWindow, renderManCropWindow, 4 );

	// Camera

	m_cameraId = m_session->createCamera(
		RtUString( name.c_str() ),
		projectionShader,
		IdentityTransform(),
		cameraParamList,
		options
	);

}

Camera::~Camera()
{
	if( m_session->renderType == IECoreScenePreview::Renderer::Interactive )
	{
		if( m_cameraId != riley::CameraId::InvalidId() )
		{
			m_session->deleteCamera( m_cameraId );
		}
	}
}

void Camera::transform( const Imath::M44f &transform )
{
	transformInternal( { transform }, { 0.0f } );
}

void Camera::transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times )
{
	transformInternal( samples, times );
}

bool Camera::attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes )
{
	return true;
}

void Camera::link( const IECore::InternedString &type, const IECoreScenePreview::Renderer::ConstObjectSetPtr &objects )
{
}

void Camera::assignID( uint32_t id )
{
}

void Camera::transformInternal( std::vector<Imath::M44f> samples, const std::vector<float> &times )
{
	for( auto &m : samples )
	{
		m = M44f().scale( V3f( 1, 1, -1 ) ) * m;
	}

	AnimatedTransform transform( samples, times );

	const auto result = m_session->riley->ModifyCamera(
		m_cameraId,
		nullptr,
		&transform,
		nullptr
	);

	if( result != riley::CameraResult::k_Success )
	{
		IECore::msg( IECore::Msg::Warning, "IECoreRenderMan::Camera::transform", "Unexpected edit failure" );
	}
}

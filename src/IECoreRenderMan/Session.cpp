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

#include "Session.h"

#include "Imath/ImathMatrixAlgo.h"

#include "RixPredefinedStrings.hpp"
#include "XcptErrorCodes.h"

#include "fmt/format.h"

using namespace std;
using namespace IECoreRenderMan;

namespace
{

const RtUString g_domeColorMapUStr( "domeColorMap" );
const RtUString g_intensityUStr( "intensity" );
const RtUString g_intensityMultUStr( "intensityMult" );
const RtUString g_lightingMuteUStr( "lighting:mute" );
const RtUString g_lightColorUStr( "lightColor" );
const RtUString g_lightColorMapUStr( "lightColorMap" );
const RtUString g_portalNameUStr( "portalName" );
const RtUString g_portalToDomeUStr( "portalToDome" );
const RtUString g_pxrDomeLightUStr( "PxrDomeLight" );
const RtUString g_pxrPortalLightUStr( "PxrPortalLight" );
const RtUString g_tintUStr( "tint" );

const riley::CoordinateSystemList g_emptyCoordinateSystems = { 0, nullptr };

// Returns a unique portal name based on a color map and rotation, to
// satisfy these requirements from the RenderMan docs :
//
// > All portal lights that are associated with the same parent dome light
// > and the same portal name must have the same rotation. If you need
// > to change a portal light's rotation, then you need to have a new portal
// > name. However, different translation and scaling can share the same portal
// > name.
//
// I don't really know why this is, but I assume that somehow the name
// is used to share an acceleration table or some such behind the scenes.
// Why it should be our responsibility to facilitate that is beyond me.
RtUString portalName( RtUString colorMap, const RtMatrix4x4 domeTransform, const RtMatrix4x4 portalTransform )
{
	Imath::V3f domeRotation;
	Imath::extractEulerXYZ( Imath::M44f( domeTransform.m ), domeRotation );

	Imath::V3f portalRotation;
	Imath::extractEulerXYZ( Imath::M44f( portalTransform.m ), portalRotation );

	IECore::MurmurHash h;
	if( !colorMap.Empty() )
	{
		h.append( colorMap.CStr() );
	}
	h.append( domeRotation );
	h.append( portalRotation );

	return RtUString( h.toString().c_str() );
}

} // namespace

struct Session::ExceptionHandler : public RixXcpt::XcptHandler
{

	ExceptionHandler( const IECore::MessageHandlerPtr &messageHandler )
		:	m_messageHandler( messageHandler )
	{
	}

	void HandleXcpt( int code, int severity, const char *message ) override
	{
		IECore::Msg::Level level;
		switch( severity )
		{
			case RIE_INFO :
				level = IECore::Msg::Level::Info;
				break;
			case RIE_WARNING :
				level = IECore::Msg::Level::Warning;
				break;
			default :
				level = IECore::Msg::Level::Error;
				break;
		}

		m_messageHandler->handle( level, "RenderMan", message );
	}

	void HandleExitRequest( int code ) override
	{
		/// \todo Not sure how best to handle this. We don't want
		/// to exit the application, but perhaps we want to prevent
		/// any further attempt to interact with the renderer?
	}

	private :

		IECore::MessageHandlerPtr m_messageHandler;

};


Session::Session( IECoreScenePreview::Renderer::RenderType renderType, const RtParamList &options, const IECore::MessageHandlerPtr &messageHandler )
	:	riley( nullptr ), renderType( renderType ), m_portalsDirty( false )
{
	// `argv[0]==""` prevents RenderMan doing its own signal handling.
	vector<const char *> args = { "" };
	PRManSystemBegin( args.size(), args.data() );
	PRManRenderBegin( args.size(), args.data() );

	if( messageHandler )
	{
		m_exceptionHandler = std::make_unique<ExceptionHandler>( messageHandler );
		auto rixXcpt = (RixXcpt *)RixGetContext()->GetRixInterface( k_RixXcpt );
		rixXcpt->Register( m_exceptionHandler.get() );
	}

	auto rileyManager = (RixRileyManager *)RixGetContext()->GetRixInterface( k_RixRileyManager );
	/// \todo What is the `rileyVariant` argument for? XPU?
	riley = rileyManager->CreateRiley( RtUString(), RtParamList() );

	riley->SetOptions( options );
}

Session::~Session()
{
	auto rileyManager = (RixRileyManager *)RixGetContext()->GetRixInterface( k_RixRileyManager );
	rileyManager->DestroyRiley( riley );

	if( m_exceptionHandler )
	{
		auto rixXcpt = (RixXcpt *)RixGetContext()->GetRixInterface( k_RixXcpt );
		rixXcpt->Unregister( m_exceptionHandler.get() );
	}

	PRManRenderEnd();
	PRManSystemEnd();
}

riley::CameraId Session::createCamera( RtUString name, const riley::ShadingNode &projection, const riley::Transform &transform, const RtParamList &properties, const RtParamList &options )
{
	riley::CameraId result = riley->CreateCamera( riley::UserId(), name, projection, transform, properties );
	std::lock_guard lock( m_camerasMutex );
	m_cameras.insert( { name.CStr(), result, options } );
	return result;
}

void Session::deleteCamera( riley::CameraId cameraId )
{
	riley->DeleteCamera( cameraId );
	std::lock_guard lock( m_camerasMutex );
	m_cameras.erase( cameraId );
}


riley::LightShaderId Session::createLightShader( const riley::ShadingNetwork &light )
{
	riley::LightShaderId result = riley->CreateLightShader( riley::UserId(), light, { 0, nullptr } );
	RtUString type = light.nodeCount ? light.nodes[light.nodeCount-1].name : RtUString();
	if( type == g_pxrDomeLightUStr || type == g_pxrPortalLightUStr )
	{
		LightShaderInfo &lightShaderInfo = m_domeAndPortalShaders[result.AsUInt32()];
		assert( lightShaderInfo.shaders.empty() ); // ID should be unique.
		lightShaderInfo.shaders.insert( lightShaderInfo.shaders.end(), light.nodes, light.nodes + light.nodeCount );
		m_portalsDirty = true;
	}

	return result;
}

void Session::deleteLightShader( riley::LightShaderId lightShaderId )
{
	riley->DeleteLightShader( lightShaderId );
	auto it = m_domeAndPortalShaders.find( lightShaderId.AsUInt32() );
	if( it != m_domeAndPortalShaders.end() )
	{
		// We can't erase from the map immediately because that isn't
		// thread-safe. Instead just clear the shaders and erase in
		// `updatePortals()`. We can safely call `clear()` because
		// there will be no concurrent access to this _particular_ map
		// entry - the light shader is being deleted, so it would be
		// a coding error to try to use it in another thread anyway.
		it->second.shaders.clear();
		m_portalsDirty = true;
	}
}

riley::LightInstanceId Session::createLightInstance( riley::GeometryPrototypeId geometry, riley::MaterialId materialId, riley::LightShaderId lightShaderId, const riley::Transform &transform, const RtParamList &attributes )
{
	riley::LightInstanceId result = riley->CreateLightInstance(
		riley::UserId(), riley::GeometryPrototypeId(), geometry,
		materialId, lightShaderId,
		g_emptyCoordinateSystems, transform, attributes
	);

	if( m_domeAndPortalShaders.count( lightShaderId.AsUInt32() ) )
	{
		m_domeAndPortalLights[result.AsUInt32()] = {
			lightShaderId,
			*transform.matrix,
			attributes
		};
		m_portalsDirty = true;
	}

	return result;
}

riley::LightInstanceResult Session::modifyLightInstance(
	riley::LightInstanceId lightInstanceId, const riley::MaterialId *materialId, const riley::LightShaderId *lightShaderId, const riley::Transform *transform,
	const RtParamList *attributes
)
{
	riley::LightInstanceResult result = riley->ModifyLightInstance(
		riley::GeometryPrototypeId(), lightInstanceId,
		materialId, lightShaderId, nullptr, transform, attributes
	);

	/// \todo Consider the possibility of a non-portal/dome turning
	/// into a portal/dome. We'll have incomplete information, so
	/// perhaps should fail the edit, and cause the controller to
	/// re-send.

	auto it = m_domeAndPortalLights.find( lightInstanceId.AsUInt32() );
	if( it != m_domeAndPortalLights.end() )
	{
		if( lightShaderId )
		{
			it->second.lightShader = *lightShaderId;
		}
		if( transform )
		{
			it->second.transform = *(transform->matrix);
		}
		if( attributes )
		{
			it->second.attributes = *attributes;
		}
		m_portalsDirty = true;
	}

	return result;
}

void Session::deleteLightInstance( riley::LightInstanceId lightInstanceId )
{
	riley->DeleteLightInstance( riley::GeometryPrototypeId(), lightInstanceId );
	auto it = m_domeAndPortalLights.find( lightInstanceId.AsUInt32() );
	if( it != m_domeAndPortalLights.end() )
	{
		// Can't erase now - mark for removal in `updatePortals()`.
		it->second.lightShader = riley::LightShaderId::InvalidId();
		m_portalsDirty = true;
	}
}

Session::CameraInfo Session::cameraInfo( const std::string &name ) const
{
	std::lock_guard lock( m_camerasMutex );
	const auto &nameIndex = m_cameras.get<1>();
	auto it = nameIndex.find( name );
	if( it != nameIndex.end() )
	{
		return *it;
	}

	return { "", riley::CameraId::InvalidId(), RtParamList() };
}

void Session::updatePortals()
{
	if( !m_portalsDirty )
	{
		return;
	}

	// Clean up any zombies created by `deleteLightShader()`.

	for( auto it = m_domeAndPortalShaders.begin(); it != m_domeAndPortalShaders.end(); )
	{
		if( it->second.shaders.empty() )
		{
			it = m_domeAndPortalShaders.unsafe_erase( it );
		}
		else
		{
			++it;
		}
	}

	// Find the dome light, while cleaning up any zombies created
	// by `deleteLightInstance()`.

	auto isPortal = [&] ( riley::LightShaderId lightShader ) {
		auto it = m_domeAndPortalShaders.find( lightShader.AsUInt32() );
		if( it != m_domeAndPortalShaders.end() )
		{
			return it->second.shaders.back().name == g_pxrPortalLightUStr;
		}
		return false;
	};

	const LightInfo *domeLight = nullptr;
	bool havePortals = false;
	size_t numDomes = 0;
	for( auto it = m_domeAndPortalLights.begin(); it != m_domeAndPortalLights.end(); )
	{
		if( it->second.lightShader == riley::LightShaderId::InvalidId() )
		{
			it = m_domeAndPortalLights.unsafe_erase( it );
			continue;
		}

		if( isPortal( it->second.lightShader ) )
		{
			havePortals = true;
		}
		else
		{
			numDomes++;
			if( !domeLight )
			{
				domeLight = &it->second;
			}
		}
		++it;
	}

	if( havePortals && numDomes > 1 )
	{
		/// \todo To support multiple domes, we need to add a mechanism for
		/// linking them to portals. Perhaps this can be achieved via
		/// `ObjectInterface::link()`?
		IECore::msg( IECore::Msg::Warning, "IECoreRenderMan::Renderer", "PxrPortalLights combined with multiple PxrDomeLights are not yet supported" );
	}

	// Link the lights appropriately.

	RtParamList mutedAttributes;
	mutedAttributes.SetInteger( Rix::k_lighting_mute, 1 );

	for( const auto &[id, info] : m_domeAndPortalLights )
	{
		if( isPortal( info.lightShader ) )
		{
			// Connect portals to dome if we have one,
			// otherwise mute them.
			if( domeLight )
			{
				// Copy parameters from dome to portal, since we want users
				// to control them all in one place, not on each individual portal.
				// Portal lights have all the same parameters as dome lights, so this
				// is easy.
				const RtParamList &domeParams = m_domeAndPortalShaders.at( domeLight->lightShader.AsUInt32() ).shaders.back().params;
				LightShaderInfo &portalShader = m_domeAndPortalShaders.at( info.lightShader.AsUInt32() );
				RtParamList &portalParams = portalShader.shaders.back().params;
				portalParams.Update( domeParams );
				//  Except that `lightColorMap` is unhelpfully renamed to
				// `domeColorMap`, so sort that out.
				portalParams.Remove( g_lightColorMapUStr );
				RtUString colorMap; domeParams.GetString( g_lightColorMapUStr, colorMap );
				portalParams.SetString( g_domeColorMapUStr, colorMap );
				// And of course the portal shader couldn't possibly apply tint
				// etc itself. That is obviously the responsibility of every
				// single bridge project.
				float intensity = 1;
				portalParams.GetFloat( g_intensityUStr, intensity );
				float intensityMult = 1;
				portalParams.GetFloat( g_intensityMultUStr, intensityMult );
				pxrcore::ColorRGB lightColor( 1, 1, 1 );
				portalParams.GetColor( g_lightColorUStr, lightColor );
				pxrcore::ColorRGB tint( 1, 1, 1 );
				portalParams.GetColor( g_tintUStr, tint );
				intensity = intensity * intensityMult;
				portalParams.SetFloat( g_intensityUStr, intensity );
				lightColor = lightColor * tint;
				portalParams.SetColor( g_lightColorUStr, lightColor );

				// We are also responsible for adding a parameter providing the
				// transform between the portal and the dome.
				RtMatrix4x4 domeInverse; domeInverse.Identity();
				domeLight->transform.Inverse( &domeInverse );
				const RtMatrix4x4 portalToDome = info.transform * domeInverse;
				portalParams.SetMatrix( g_portalToDomeUStr, portalToDome );

				// And most bizarrely of all, we are required to compute `portalName`,
				// which must change any time the rotation does.
				portalParams.SetString( g_portalNameUStr, portalName( colorMap, domeLight->transform, info.transform ) );

				// Update the light shader. We can modify the existing one in
				// place because we know we're only using it on this one light.
				riley::ShadingNetwork shaders = { (uint32_t)portalShader.shaders.size(), portalShader.shaders.data() };
				riley->ModifyLightShader( info.lightShader, &shaders, /* lightFilter = */ nullptr );

				// Unmute, in case we muted previously due to lack of a dome.
				riley->ModifyLightInstance(
					riley::GeometryPrototypeId(), riley::LightInstanceId( id ),
					nullptr, nullptr, nullptr, nullptr, &info.attributes
				);
			}
			else
			{
				riley->ModifyLightInstance(
					riley::GeometryPrototypeId(), riley::LightInstanceId( id ),
					nullptr, nullptr, nullptr, nullptr, &mutedAttributes
				);
			}
		}
		else
		{
			// Mute domes if there are portals.
			riley->ModifyLightInstance(
				riley::GeometryPrototypeId(), riley::LightInstanceId( id ),
				nullptr, nullptr, nullptr, nullptr, havePortals ? &mutedAttributes : &info.attributes
			);
		}
	}

	m_portalsDirty = false;
}

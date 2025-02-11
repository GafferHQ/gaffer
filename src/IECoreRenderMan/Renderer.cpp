//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, John Haddon. All rights reserved.
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

#include "Attributes.h"
#include "Camera.h"
#include "GeometryAlgo.h"
#include "GeometryPrototypeCache.h"
#include "Globals.h"
#include "Light.h"
#include "MaterialCache.h"
#include "Globals.h"
#include "Object.h"
#include "ParamListAlgo.h"
#include "Session.h"
#include "Transform.h"

#include "GafferScene/Private/IECoreScenePreview/Renderer.h"

#include "IECoreScene/MeshPrimitive.h"

#include "IECore/SimpleTypedData.h"

#include "Riley.h"
#include "RixPredefinedStrings.hpp"

#include "tbb/spin_rw_mutex.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreRenderMan;

namespace
{

const CompoundDataMap::value_type g_forMeshLightBlindData( "__ieCoreRenderMan:forMeshLight", new BoolData( true ) );

class RenderManRenderer final : public IECoreScenePreview::Renderer
{

	public :

		RenderManRenderer( RenderType renderType, const std::string &fileName, const MessageHandlerPtr &messageHandler )
			:	m_messageHandler( messageHandler ), m_session( nullptr )
		{
			if( renderType == SceneDescription )
			{
				throw IECore::Exception( "SceneDescription mode not supported by RenderMan" );
			}

			bool haveInstance = false;
			if( !g_haveInstance.compare_exchange_strong( haveInstance, true ) )
			{
				throw IECore::Exception( "RenderMan doesn't allow multiple active sessions" );
			}

			m_globals = std::make_unique<Globals>( renderType, messageHandler );
		}

		~RenderManRenderer() override
		{
			m_materialCache.reset();
			m_geometryPrototypeCache.reset();
			m_globals.reset();
			g_haveInstance = false;
		}

		IECore::InternedString name() const override
		{
			return "RenderMan";
		}

		void option( const IECore::InternedString &name, const IECore::Object *value ) override
		{
			m_globals->option( name, value );
		}

		void output( const IECore::InternedString &name, const Output *output ) override
		{
			m_globals->output( name, output );
		}

		Renderer::AttributesInterfacePtr attributes( const IECore::CompoundObject *attributes ) override
		{
			const IECore::MessageHandler::Scope messageScope( m_messageHandler.get() );
			acquireSession();
			return new Attributes( attributes, m_materialCache.get() );
		}

		ObjectInterfacePtr camera( const std::string &name, const IECoreScene::Camera *camera, const AttributesInterface *attributes ) override
		{
			const IECore::MessageHandler::Scope messageScope( m_messageHandler.get() );
			IECoreRenderMan::CameraPtr result = new IECoreRenderMan::Camera( name, camera, acquireSession() );
			result->attributes( attributes );
			return result;
		}

		ObjectInterfacePtr light( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			const IECore::MessageHandler::Scope messageScope( m_messageHandler.get() );
			acquireSession();

			auto typedAttributes = static_cast<const Attributes *>( attributes );

			ConstGeometryPrototypePtr geometryPrototype;
			if( auto mesh = runTimeCast<const MeshPrimitive>( object ) )
			{
				// RenderMan refuses to share mesh prototypes between GeometryInstances and
				// LightInstances, so we insert some blind data to give the mesh geometry
				// a different hash, causing the GeometryPrototypeCache to create a prototype
				// that won't be used by `Renderer::object()`.
				MeshPrimitivePtr meshCopy = mesh->copy();
				meshCopy->blindData()->writable().insert( g_forMeshLightBlindData );
				geometryPrototype = m_geometryPrototypeCache->get( meshCopy.get(), typedAttributes, /* messageContext = */ name );
			}

			return new IECoreRenderMan::Light( geometryPrototype, typedAttributes, m_session );
		}

		ObjectInterfacePtr lightFilter( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			const IECore::MessageHandler::Scope messageScope( m_messageHandler.get() );
			return nullptr;
		}

		Renderer::ObjectInterfacePtr object( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			if( !object )
			{
				return nullptr;
			}

			const IECore::MessageHandler::Scope messageScope( m_messageHandler.get() );
			acquireSession();

			auto typedAttributes = static_cast<const Attributes *>( attributes );
			ConstGeometryPrototypePtr geometryPrototype = m_geometryPrototypeCache->get( object, typedAttributes, /* messageContext = */ name );
			if( !geometryPrototype )
			{
				return nullptr;
			}

			return new IECoreRenderMan::Object( geometryPrototype, typedAttributes, m_session );
		}

		ObjectInterfacePtr object( const std::string &name, const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const AttributesInterface *attributes ) override
		{
			const IECore::MessageHandler::Scope messageScope( m_messageHandler.get() );
			acquireSession();

			auto typedAttributes = static_cast<const Attributes *>( attributes );
			ConstGeometryPrototypePtr geometryPrototype = m_geometryPrototypeCache->get( samples, times, typedAttributes, /* messageContext = */ name );
			if( !geometryPrototype )
			{
				return nullptr;
			}

			return new IECoreRenderMan::Object( geometryPrototype, typedAttributes, m_session );
		}

		void render() override
		{
			const IECore::MessageHandler::Scope messageScope( m_messageHandler.get() );
			acquireSession();
			m_materialCache->clearUnused();
			m_globals->render();
		}

		void pause() override
		{
			const IECore::MessageHandler::Scope messageScope( m_messageHandler.get() );
			m_globals->pause();
		}

		IECore::DataPtr command( const IECore::InternedString name, const IECore::CompoundDataMap &parameters ) override
		{
			const IECore::MessageHandler::Scope messageScope( m_messageHandler.get() );
			return nullptr;
		}

	private :

		IECore::MessageHandlerPtr m_messageHandler;
		std::unique_ptr<Globals> m_globals;

		// Used to acquire the Session via `m_globals` at the first point we need it.
		// Also initialises other members that depend on the session. Needs to be thread-safe
		// because it is called from `object()`, `attributes()` etc.
		Session *acquireSession()
		{
			tbb::spin_rw_mutex::scoped_lock lock( m_acquireSessionMutex, /* write = */ false );
			if( !m_session )
			{
				lock.upgrade_to_writer();
				if( !m_session )
				{
					m_session = m_globals->acquireSession();
					m_materialCache = std::make_unique<MaterialCache>( m_session );
					m_geometryPrototypeCache = std::make_unique<GeometryPrototypeCache>( m_session );
				}
			}
			return m_session;
		}

		tbb::spin_rw_mutex m_acquireSessionMutex;
		// The following members may only be accessed after calling
		// `acquireSession()`.
		Session *m_session;
		std::unique_ptr<MaterialCache> m_materialCache;
		std::unique_ptr<GeometryPrototypeCache> m_geometryPrototypeCache;

		static Renderer::TypeDescription<RenderManRenderer> g_typeDescription;
		static std::atomic_bool g_haveInstance;

};

IECoreScenePreview::Renderer::TypeDescription<RenderManRenderer> RenderManRenderer::g_typeDescription( "RenderMan" );
std::atomic_bool RenderManRenderer::g_haveInstance = false;

} // namespace

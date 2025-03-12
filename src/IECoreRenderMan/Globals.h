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

#pragma once

#include "Session.h"

#include "IECoreScene/Output.h"
#include "IECoreScene/Shader.h"
#include "IECoreScene/ShaderNetwork.h"

#include "GafferScene/Private/IECoreScenePreview/Renderer.h"

#include "boost/noncopyable.hpp"

#include <thread>

namespace IECoreRenderMan
{

/// Handles global operations for Renderer. Creates and owns the
/// Session, because a session cannot be created without a complete
/// set of options.
class Globals : public boost::noncopyable
{

	public :

		Globals( IECoreScenePreview::Renderer::RenderType renderType, const IECore::MessageHandlerPtr &messageHandler );
		~Globals();

		void option( const IECore::InternedString &name, const IECore::Object *value );
		void output( const IECore::InternedString &name, const IECoreScene::Output *output );

		/// Creates the session on first call, using all the options specified
		/// so far. We want to defer this call until the last moment possible,
		/// as Riley doesn't support subsequent edits to many scene options.
		Session *acquireSession();

		void render();
		void pause();

	private :

		bool worldBegun();
		void updateIntegrator();
		void updateDisplayFilter();
		void updateSampleFilter();
		void updateRenderView();
		void deleteRenderView();

		const IECoreScenePreview::Renderer::RenderType m_renderType;
		const IECore::MessageHandlerPtr m_messageHandler;

		// We are not allowed to call anything in the Riley API before we've
		// called `Riley::SetOptions()`. So we buffer all the options and outputs
		// into the following member variables, and create the Riley session
		// only when we must.

		RtParamList m_options;
		std::string m_cameraOption;
		IECoreScene::ConstShaderPtr m_integratorToConvert;
		IECoreScene::ConstShaderNetworkPtr m_displayFilterToConvert;
		IECoreScene::ConstShaderNetworkPtr m_sampleFilterToConvert;
		std::unordered_map<IECore::InternedString, IECoreScene::ConstOutputPtr> m_outputs;
		RtUString m_pixelFilter;
		riley::FilterSize m_pixelFilterSize;
		float m_pixelVariance;

		// When we require the Riley session, we create it in `acquireSession()`.

		std::unique_ptr<Session> m_session;

		// Then once we have the session, we are free to use the Riley API
		// to populate the scene, which we store in the following members.

		riley::IntegratorId m_integratorId;
		riley::CameraId m_defaultCamera;

		// We assume RenderOutputs to be lightweight, and equivalent to
		// an RiDisplayChannel. So we just make them on demand, and never
		// destroy them in case we might reuse them later.
		const std::vector<riley::RenderOutputId> &acquireRenderOutputs( const IECoreScene::Output *output );
		std::unordered_map<IECore::MurmurHash, std::vector<riley::RenderOutputId>> m_renderOutputs;

		riley::DisplayFilterId m_displayFilterId;
		riley::SampleFilterId m_sampleFilterId;
		std::vector<riley::DisplayId> m_displays;
		riley::RenderTargetId m_renderTarget;
		riley::Extent m_renderTargetExtent;
		riley::RenderViewId m_renderView;

		std::thread m_interactiveRenderThread;

};




} // namespace IECoreRenderMan

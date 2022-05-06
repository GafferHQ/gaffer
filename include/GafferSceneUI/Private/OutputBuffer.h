//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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
//     * Neither the name of Image Engine Design nor the names of any
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

#ifndef GAFFERSCENEUI_OUTPUTBUFFER_H
#define GAFFERSCENEUI_OUTPUTBUFFER_H

#include "GafferScene/ScenePlug.h"
#include "GafferScene/Private/IECoreScenePreview/Renderer.h"

#include "Gaffer/Signals.h"

#include "IECoreGL/Shader.h"
#include "IECoreGL/Texture.h"

#include "IECore/PathMatcher.h"

#include <mutex>

namespace GafferSceneUI
{

/// Provides OpenGL rendering of beauty, depth and ID outputs from an
/// `IECoreScenePreview::Renderer`.
class OutputBuffer
{

	public :

		/// Calls `renderer->output()` to create outputs that will be sent to
		/// this buffer.
		OutputBuffer( IECoreScenePreview::Renderer *renderer );
		~OutputBuffer();

		/// Renders the output buffers to OpenGL.
		void render() const;

		/// Specifies a set of objects to be drawn as highlighted.
		void setSelection( const std::vector<uint32_t> &ids );
		const std::vector<uint32_t> &getSelection() const;

		/// Returns the ID for the object found at the specified NDC position, filling `depth` with its
		/// depth from the camera. Returns 0 if no object is found.
		uint32_t idAt( const Imath::V2f &ndcPosition, float &depth ) const;
		/// Returns the IDs of all objects found in the specified region of NDC space.
		std::vector<uint32_t> idsAt( const Imath::Box2f &ndcBox ) const;

		/// Signal emitted when the buffers have changed and `render()`
		/// should be called.
		using BufferChangedSignal = Gaffer::Signals::Signal<void()>;
		BufferChangedSignal &bufferChangedSignal();

	private :

		class DisplayDriver;

		void imageFormat( const Imath::Box2i &displayWindow, const Imath::Box2i &dataWindow );
		template<typename T>
		void updateBuffer( const Imath::Box2i &box, const T *data, int numChannels, std::vector<T> &buffer );
		void dirtyTexture();

		// Used to prevent the buffers being reallocated by an `imageFormat()` call
		// on a background thread while they are being read from by the foreground
		// thread. _Not_ used to synchronise reads/writes - see `updateBuffer()`.
		mutable std::mutex m_bufferReallocationMutex;

		Imath::Box2i m_dataWindow;
		std::vector<float> m_rgbaBuffer;
		std::vector<float> m_depthBuffer;
		std::vector<uint32_t> m_idBuffer;
		std::vector<uint32_t> m_selectionBuffer;
		BufferChangedSignal m_bufferChangedSignal;

		mutable std::atomic_bool m_texturesDirty;
		mutable IECoreGL::TexturePtr m_rgbaTexture;
		mutable IECoreGL::TexturePtr m_depthTexture;
		mutable IECoreGL::TexturePtr m_idTexture;
		class BufferTexture;
		mutable std::unique_ptr<BufferTexture> m_selectionTexture;
		mutable IECoreGL::ShaderPtr m_shader;
		mutable IECoreGL::Shader::SetupPtr m_shaderSetup;

};

} // namespace GafferSceneUI

#endif // GAFFERSCENEUI_OUTPUTBUFFER_H

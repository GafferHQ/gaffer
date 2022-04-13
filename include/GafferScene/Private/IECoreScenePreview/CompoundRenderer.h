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

#ifndef IECORESCENEPREVIEW_COMPOUNDRENDERER_H
#define IECORESCENEPREVIEW_COMPOUNDRENDERER_H

#include "GafferScene/Private/IECoreScenePreview/Renderer.h"

namespace IECoreScenePreview
{

/// Renderer implementation that simply forwards all calls to other renderers.
class GAFFERSCENE_API CompoundRenderer final : public IECoreScenePreview::Renderer
{

	public :

		IE_CORE_DECLAREMEMBERPTR( CompoundRenderer )

		/// Using `std::array` of fixed length since we currently only
		/// need two renderers, and it minimises the size of internal
		/// data structures.
		using Renderers = std::array<RendererPtr, 2>;

		/// CompoundRenderer is constructed directly rather than via
		/// `Renderer::create()`, so that the renderers can be provided to it.
		CompoundRenderer( const Renderers &renderers );
		~CompoundRenderer() override;

		IECore::InternedString name() const override;
		void option( const IECore::InternedString &name, const IECore::Object *value ) override;
		void output( const IECore::InternedString &name, const IECoreScene::Output *output ) override;
		Renderer::AttributesInterfacePtr attributes( const IECore::CompoundObject *attributes ) override;
		ObjectInterfacePtr camera( const std::string &name, const IECoreScene::Camera *camera, const AttributesInterface *attributes ) override;
		ObjectInterfacePtr light( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override;
		ObjectInterfacePtr lightFilter( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override;
		Renderer::ObjectInterfacePtr object( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override;
		ObjectInterfacePtr object( const std::string &name, const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const AttributesInterface *attributes ) override;
		void render() override;
		void pause() override;
		IECore::DataPtr command( const IECore::InternedString name, const IECore::CompoundDataMap &parameters ) override;

	private :

		Renderers m_renderers;

};

IE_CORE_DECLAREPTR( CompoundRenderer )

} // namespace IECoreScenePreview

#endif // IECORESCENEPREVIEW_COMPOUNDRENDERER_H

//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/Private/IECoreScenePreview/Procedural.h"
#include "GafferScene/Private/RendererAlgo.h"
#include "GafferScene/ScenePlug.h"

#include "Gaffer/Context.h"

namespace GafferScene
{

IE_CORE_FORWARDDECLARE( ScenePlug )

/// Procedural that renders a subtree of a Gaffer scene.
class GAFFERSCENE_API Capsule : public IECoreScenePreview::Procedural
{

	public :

		Capsule();
		/// A copy of `context` is taken. It is the responsibility of the
		/// caller to provide a `hash` that uniquely identifies the entire
		/// subtree from the root down, taking into account the context.
		///
		/// The capsule is invalidated by any subsequent graph edits that
		/// modify the scene below `root`. Usage of an invalidated capsule
		/// is undefined behaviour. In practice, nodes that create capsules
		/// avoid such usage in two ways :
		///
		/// 1. Before any node graph edit is made, all existing processes
		///    performing computes are cancelled. This prevents renderers
		///    from continuing to use the capsule.
		/// 2. After the node graph is edited, the capsule-generating
		///    node generates a new `objectHash()` so that any new processes
		///    will retrieve a new capsule from the node.
		///
		/// Invalidated capsules _do_ live on in the ValuePlug's compute cache,
		/// but because the node's `objectHash()` has changed, they will not
		/// be reused, and will eventually be evicted.
		Capsule(
			const ScenePlug *scene,
			const ScenePlug::ScenePath &root,
			const Gaffer::Context &context,
			const IECore::MurmurHash &hash,
			const Imath::Box3f &bound
		);
		~Capsule() override;

		IE_CORE_DECLAREEXTENSIONOBJECT( GafferScene::Capsule, GafferScene::CapsuleTypeId, IECoreScenePreview::Procedural );

		Imath::Box3f bound() const override;
		void render( IECoreScenePreview::Renderer *renderer ) const override;

		const ScenePlug *scene() const;
		const ScenePlug::ScenePath &root() const;
		const Gaffer::Context *context() const;

		/// Used to apply the correct render settings to the capsule before rendering it.
		/// For internal use only.
		void setRenderOptions( const GafferScene::Private::RendererAlgo::RenderOptions &renderOptions );
		std::optional<GafferScene::Private::RendererAlgo::RenderOptions> getRenderOptions() const;

	private :

		void throwIfNoScene() const;

		IECore::MurmurHash m_hash;
		Imath::Box3f m_bound;
		// We don't own a reference to `m_scene` because it could cause its deletion
		// when the capsule is evicted from the ValuePlug's compute cache. That would
		// be equivalent to making a graph edit from within a compute, which is forbidden.
		// Instead we rely on the invalidation rules documented on the constructor to
		// ensure that `m_scene` is still alive at the point of use.
		/// \todo If we had weak pointer support in `IECore::RefCounted` or `Gaffer::GraphComponent`,
		/// then we could store a weak pointer, and use it to check for expiry of the scene.
		const ScenePlug *m_scene;
		ScenePlug::ScenePath m_root;
		Gaffer::ConstContextPtr m_context;
		std::optional<GafferScene::Private::RendererAlgo::RenderOptions> m_renderOptions;

};

IE_CORE_DECLAREPTR( Capsule )

} // namespace GafferScene

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

#ifndef GAFFERSCENE_CAPSULE_H
#define GAFFERSCENE_CAPSULE_H

#include "Gaffer/Context.h"

#include "Gaffer/Export.h"
#include "GafferScene/ScenePlug.h"
#include "GafferScene/Private/IECoreScenePreview/Procedural.h"

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
		/// The capsule is invalidated by any subsequent graph edits
		/// that dirty the scene (because the stored hash will no longer
		/// match the scene). Any attempt to use such an expired capsule
		/// will throw an exception.
		Capsule(
			const ScenePlug *scene,
			const ScenePlug::ScenePath &root,
			const Gaffer::Context &context,
			const IECore::MurmurHash &hash,
			const Imath::Box3f &bound
		);
		virtual ~Capsule();

		IE_CORE_DECLAREEXTENSIONOBJECT( GafferScene::Capsule, GafferScene::CapsuleTypeId, IECoreScenePreview::Procedural );

		Imath::Box3f bound() const override;
		void render( IECoreScenePreview::Renderer *renderer ) const override;

		const ScenePlug *scene() const;
		const ScenePlug::ScenePath &root() const;
		const Gaffer::Context *context() const;

	private :

		void setScene( const ScenePlug *scene );
		void plugDirtied( const Gaffer::Plug *plug );
		void parentChanged( const Gaffer::GraphComponent *graphComponent );
		void throwIfExpired() const;

		IECore::MurmurHash m_hash;
		Imath::Box3f m_bound;
		// Note that we don't own a reference to m_scene because we expect
		// the graph to remain unchanged. Instead we use parentChanged to
		// detect any unparenting and then expire the capsule.
		const ScenePlug *m_scene;
		ScenePlug::ScenePath m_root;
		Gaffer::ConstContextPtr m_context;

};

IE_CORE_DECLAREPTR( Capsule )

} // namespace GafferScene

#endif // GAFFERSCENE_CAPSULE_H

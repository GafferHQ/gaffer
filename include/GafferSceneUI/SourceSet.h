//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
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

#ifndef GAFFERSCENEUI_SOURCESET_H
#define GAFFERSCENEUI_SOURCESET_H

#include "GafferSceneUI/TypeIds.h"

#include "GafferScene/ScenePlug.h"
#include "GafferScene/SceneNode.h"

#include "Gaffer/Context.h"
#include "Gaffer/Set.h"
#include "Gaffer/StandardSet.h"

#include "IECore/PathMatcher.h"

namespace GafferSceneUI
{

/// The SourceSet provides a Set implementation that adjusts its membership such that
/// it contains the source node for the current scene selection, given a context and
/// a target node from which to observe the scene.
///
/// When there is no scene selection, or the supplied node set contains no SceneNodes,
/// it falls back to the node in the node set.
///
/// When multiple locations are selected or there are multiple nodes in the node set,
/// the last of each will be used to determine which source node is presented by the set.
///
/// The SourceSet requires a valid context and node set in order to determine source nodes
/// other than the direct selection of non-SceneNodes.
class GAFFER_API SourceSet : public Gaffer::Set
{

	public :

		SourceSet( Gaffer::ContextPtr context, Gaffer::SetPtr nodeSet );
		~SourceSet() override;

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferSceneUI::SourceSet, SourceSetTypeId, Gaffer::Set );

		void setContext( Gaffer::ContextPtr context );
		Gaffer::Context *getContext() const;

		void setNodeSet( Gaffer::SetPtr nodeSet );
		Gaffer::Set *getNodeSet() const;

		/// @name Set interface
		////////////////////////////////////////////////////////////////////
		//@{
		bool contains( const Member *object ) const override;
		Member *member( size_t index ) override;
		const Member *member( size_t index ) const override;
		size_t size() const override;
		//@}

	private :

		Gaffer::ContextPtr m_context;
		Gaffer::SetPtr m_nodes;

		GafferScene::ScenePlugPtr m_scenePlug;
		void updateScenePlug();

		Gaffer::NodePtr m_sourceNode;
		void updateSourceNode();

		void contextChanged( const IECore::InternedString &name );
		void plugDirtied( const Gaffer::Plug *plug );
		boost::signals::scoped_connection m_contextChangedConnection;
		boost::signals::scoped_connection m_plugDirtiedConnection;
		boost::signals::scoped_connection m_nodeAddedConnection;
		boost::signals::scoped_connection m_nodeRemovedConnection;
};

IE_CORE_DECLAREPTR( SourceSet );

} // namespace GafferSceneUI

#endif // GAFFERSCENEUI_SOURCESET_H

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

#include "GafferUI/Export.h"

#include "Gaffer/Set.h"
#include "Gaffer/Signals.h"

#include "IECore/RefCounted.h"

#include <unordered_map>

namespace Gaffer
{

class Plug;
class ScriptNode;
IE_CORE_FORWARDDECLARE( Node );
IE_CORE_FORWARDDECLARE( Context )

} // namespace Gaffer

namespace GafferUI
{

/// Utility class for UI components which display context-sensitive information
/// to users. This tracks which upstream nodes contribute to the result at a
/// particular target node, and also what context they should be evaluated in
/// with respect to that node.
class GAFFERUI_API ContextTracker final : public IECore::RefCounted, public Gaffer::Signals::Trackable
{

	public :

		/// Constructs an instance that will track the graph upstream of the
		/// target `node`, taking into account what connections are active in
		/// the target `context`.
		ContextTracker( const Gaffer::NodePtr &node, const Gaffer::ContextPtr &context );
		~ContextTracker() override;

		IE_CORE_DECLAREMEMBERPTR( ContextTracker );

		/// Shared instances
		/// ================
		///
		/// Tracking the upstream contexts can involve significant computation,
		/// so it is recommended that ContextTracker instances are shared
		/// between UI components. The `aquire()` methods maintain a pool of
		/// instances for this purpose. Acquisition and destruction of shared
		/// instances is not threadsafe, and must always be done on the UI
		/// thread.

		/// Returns a shared instance for the target `node`. The node must
		/// belong to a ScriptNode, so that `ScriptNode::context()` can be used
		/// to provide the target context.
		static Ptr acquire( const Gaffer::NodePtr &node );
		/// Returns an shared instance that will automatically track the focus
		/// node in the specified `script`.
		static Ptr acquireForFocus( Gaffer::ScriptNode *script );

		/// Target
		/// ======

		const Gaffer::Node *targetNode() const;
		const Gaffer::Context *targetContext() const;

		/// Queries
		/// =======

		/// Returns true if the specified plug or node is active with respect to
		/// the target node and context.
		bool isActive( const Gaffer::Plug *plug ) const;
		bool isActive( const Gaffer::Node *node ) const;

		/// Returns the most suitable context for the UI to evaluate a plug or
		/// node in. This will always return a valid context, even if
		/// `isActive()` returns false.
		Gaffer::ConstContextPtr context( const Gaffer::Plug *plug ) const;
		Gaffer::ConstContextPtr context( const Gaffer::Node *node ) const;

	private :

		void updateNode( const Gaffer::NodePtr &node );
		void plugDirtied( const Gaffer::Plug *plug );
		void contextChanged( IECore::InternedString variable );
		void update();
		const Gaffer::Context *findPlugContext( const Gaffer::Plug *plug ) const;

		Gaffer::ConstNodePtr m_node;
		Gaffer::ConstContextPtr m_context;
		Gaffer::Signals::ScopedConnection m_plugDirtiedConnection;

		struct NodeData
		{
			Gaffer::ConstContextPtr context = nullptr;
			// If `true`, then all input plugs on the node are assumed to be
			// active in the Node's context. This is just an optimisation that
			// allows us to keep the size of `m_plugContexts` to a minimum.
			bool allInputsActive = false;
		};

		using NodeContexts = std::unordered_map<Gaffer::ConstNodePtr, NodeData>;
		NodeContexts m_nodeContexts;
		using PlugContexts = std::unordered_map<Gaffer::ConstPlugPtr, Gaffer::ConstContextPtr>;
		// Stores plug-specific contexts, which take precedence over `m_nodeContexts`.
		PlugContexts m_plugContexts;

};

IE_CORE_DECLAREPTR( ContextTracker )

} // namespace GafferUI

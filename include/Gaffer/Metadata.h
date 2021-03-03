//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_METADATA_H
#define GAFFER_METADATA_H

#include "Gaffer/Export.h"
#include "Gaffer/Signals.h"

#include "IECore/Data.h"
#include "IECore/InternedString.h"
#include "IECore/StringAlgo.h"

#include <functional>

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( GraphComponent )
IE_CORE_FORWARDDECLARE( Node )
IE_CORE_FORWARDDECLARE( Plug )

/// The Metadata class provides a registry of metadata for the different types
/// of Nodes and Plugs. This metadata assists in creating UIs and can be used to
/// generate documentation. Metadata can consist of either static values represented
/// as IECore::Data, or can be computed dynamically.
class GAFFER_API Metadata
{

	public :

		using ValueFunction = std::function<IECore::ConstDataPtr ()>;
		using GraphComponentValueFunction = std::function<IECore::ConstDataPtr ( const GraphComponent * )>;
		using PlugValueFunction = std::function<IECore::ConstDataPtr ( const Plug * )>;

		/// Value registration
		/// ==================

		/// Registers a static value.
		static void registerValue( IECore::InternedString target, IECore::InternedString key, IECore::ConstDataPtr value );
		/// Registers a dynamic value. Each time the data is retrieved, the ValueFunction will
		/// be called to compute it.
		static void registerValue( IECore::InternedString target, IECore::InternedString key, ValueFunction value );

		/// Registers a static metadata value for the specified GraphComponent type.
		static void registerValue( IECore::TypeId typeId, IECore::InternedString key, IECore::ConstDataPtr value );
		/// Registers a dynamic metadata value for the specified GraphComponent type. Each time the data is retrieved, the
		/// GraphComponentValueFunction will be called to compute it.
		static void registerValue( IECore::TypeId typeId, IECore::InternedString key, GraphComponentValueFunction value );

		/// Registers a static metadata value for plugs with the specified path relative to the ancestor type.
		static void registerValue( IECore::TypeId ancestorTypeId, const IECore::StringAlgo::MatchPattern &plugPath, IECore::InternedString key, IECore::ConstDataPtr value );
		/// Registers a dynamic metadata value for the specified plug. Each time the data is retrieved, the
		/// PlugValueFunction will be called to compute it.
		static void registerValue( IECore::TypeId ancestorTypeId, const IECore::StringAlgo::MatchPattern &plugPath, IECore::InternedString key, PlugValueFunction value );

		/// Registers a metadata value specific to a single instance - this will take precedence over any
		/// values registered above. If persistent is true, the value will be preserved across script save/load and cut/paste.
		/// \undoable
		static void registerValue( GraphComponent *target, IECore::InternedString key, IECore::ConstDataPtr value, bool persistent = true );

		/// Registration queries
		/// ====================

		/// Fills the keys vector with keys for all values registered with the methods above.
		static void registeredValues( IECore::InternedString target, std::vector<IECore::InternedString> &keys );
		/// Fills the keys vector with keys for all values registered for the specified graphComponent.
		/// If instanceOnly is true, then only the values registered for that exact instance are returned.
		/// If persistentOnly is true, then non-persistent instance values are ignored.
		static void registeredValues( const GraphComponent *target, std::vector<IECore::InternedString> &keys, bool instanceOnly = false, bool persistentOnly = false );

		/// Value retrieval
		/// ===============

		/// Retrieves a value, returning null if none exists.
		template<typename T=IECore::Data>
		static typename T::ConstPtr value( IECore::InternedString target, IECore::InternedString key );
		template<typename T=IECore::Data>
		static typename T::ConstPtr value( const GraphComponent *target, IECore::InternedString key, bool instanceOnly = false );

		/// Value deregistration
		/// ====================

		static void deregisterValue( IECore::InternedString target, IECore::InternedString key );
		static void deregisterValue( IECore::TypeId typeId, IECore::InternedString key );
		static void deregisterValue( IECore::TypeId ancestorTypeId, const IECore::StringAlgo::MatchPattern &plugPath, IECore::InternedString key );

		/// \undoable
		static void deregisterValue( GraphComponent *target, IECore::InternedString key );

		/// Utilities
		/// =========

		/// Lists all node descendants of "root" with the specified metadata key.
		/// If instanceOnly is true the search is restricted to instance metadata.
		static std::vector<Node*> nodesWithMetadata( GraphComponent *root, IECore::InternedString key, bool instanceOnly = false );

		/// Lists all plug descendants of "root" with the specified metadata key.
		/// If instanceOnly is true the search is restricted to instance metadata.
		static std::vector<Plug*> plugsWithMetadata( GraphComponent *root, IECore::InternedString key, bool instanceOnly = false );

		/// Signals
		/// =======
		///
		/// These are emitted when the Metadata has been changed with one
		/// of the register*() methods. If dynamic metadata is registered
		/// with a GraphComponentValueFunction or PlugValueFunction then it is the
		/// responsibility of the registrant to manually emit the signals
		/// when necessary.

		enum class ValueChangedReason
		{
			StaticRegistration,
			StaticDeregistration,
			InstanceRegistration,
			InstanceDeregistration
		};

		using ValueChangedSignal = Signals::Signal<void ( IECore::InternedString target, IECore::InternedString key ), Signals::CatchingCombiner<void>>;
		using NodeValueChangedSignal = Signals::Signal<void ( Node *node, IECore::InternedString key, ValueChangedReason reason ), Signals::CatchingCombiner<void>>;
		using PlugValueChangedSignal = Signals::Signal<void ( Plug *plug, IECore::InternedString key, ValueChangedReason reason ), Signals::CatchingCombiner<void>>;

		static ValueChangedSignal &valueChangedSignal();
		/// Returns a signal that will be emitted when metadata has changed for `node`.
		static NodeValueChangedSignal &nodeValueChangedSignal( Node *node );
		/// Returns a signal that will be emitted when metadata has changed for any plug on `node`.
		static PlugValueChangedSignal &plugValueChangedSignal( Node *node );

		/// Legacy signals
		/// ==============
		///
		/// These signals are emitted when metadata is changed on _any_ node or
		/// plug. Their usage leads to performance bottlenecks whereby all observers
		/// are triggered by all edits. They will be removed in future.

		using LegacyNodeValueChangedSignal = Signals::Signal<void ( IECore::TypeId nodeTypeId, IECore::InternedString key, Gaffer::Node *node ), Signals::CatchingCombiner<void>>;
		using LegacyPlugValueChangedSignal = Signals::Signal<void ( IECore::TypeId typeId, const IECore::StringAlgo::MatchPattern &plugPath, IECore::InternedString key, Gaffer::Plug *plug ), Signals::CatchingCombiner<void>>;

		/// Deprecated, but currently necessary for tracking inherited
		/// changes to read-only metadata.
		/// \deprecated
		static LegacyNodeValueChangedSignal &nodeValueChangedSignal();
		/// \deprecated
		static LegacyPlugValueChangedSignal &plugValueChangedSignal();

	private :

		/// Per-instance Metadata is stored as a mapping from GraphComponent * to the
		/// metadata values, and needs to be removed when the instance dies. Currently
		/// there is no callback when a RefCounted object passes away, so we must rely
		/// on the destructors for Node and Plug to call instanceDestroyed() for us.
		/// \todo This situation isn't particularly satisfactory - if we introduced
		/// weak pointers and destruction callbacks for RefCounted objects then we could
		/// tidy this up.
		friend class Node;
		friend class Plug;
		static void instanceDestroyed( GraphComponent *graphComponent );

		static IECore::ConstDataPtr valueInternal( IECore::InternedString target, IECore::InternedString key );
		static IECore::ConstDataPtr valueInternal( const GraphComponent *target, IECore::InternedString key, bool instanceOnly );

};

} // namespace Gaffer

#include "Gaffer/Metadata.inl"

#endif // GAFFER_METADATA_H

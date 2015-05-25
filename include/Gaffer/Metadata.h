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

#include "boost/function.hpp"
#include "boost/signals.hpp"

#include "IECore/InternedString.h"
#include "IECore/Data.h"

#include "Gaffer/StringAlgo.h"
#include "Gaffer/CatchingSignalCombiner.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( GraphComponent )
IE_CORE_FORWARDDECLARE( Node )
IE_CORE_FORWARDDECLARE( Plug )

/// The Metadata class provides a registry of metadata for the different types
/// of Nodes and Plugs. This metadata assists in creating UIs and can be used to
/// generate documentation. Metadata can consist of either static values represented
/// as IECore::Data, or can be computed dynamically.
class Metadata
{

	public :

		/// Type for a singal emitted when new metadata is registered.
		typedef boost::signal<void ( IECore::InternedString target, IECore::InternedString key ), CatchingSignalCombiner<void> > ValueChangedSignal;
		/// Type for a signal emitted when new node metadata is registered. The
		/// node argument will be NULL when generic (rather than per-instance)
		/// metadata is registered.
		typedef boost::signal<void ( IECore::TypeId nodeTypeId, IECore::InternedString key, Gaffer::Node *node ), CatchingSignalCombiner<void> > NodeValueChangedSignal;
		/// Type for a signal emitted when new plug metadata is registered. The
		/// plug argument will be NULL when generic (rather than per-instance)
		/// metadata is registered.
		typedef boost::signal<void ( IECore::TypeId nodeTypeId, const MatchPattern &plugPath, IECore::InternedString key, Gaffer::Plug *plug ), CatchingSignalCombiner<void> > PlugValueChangedSignal;

		typedef boost::function<IECore::ConstDataPtr ()> ValueFunction;
		typedef boost::function<IECore::ConstDataPtr ( const Node *node )> NodeValueFunction;
		typedef boost::function<IECore::ConstDataPtr ( const Plug *plug )> PlugValueFunction;

		/// Registers a static value.
		static void registerValue( IECore::InternedString target, IECore::InternedString key, IECore::ConstDataPtr value );
		/// Registers a dynamic value. Each time the data is retrieved, the ValueFunction will
		/// be called to compute it.
		static void registerValue( IECore::InternedString target, IECore::InternedString key, ValueFunction value );
		/// Fills the keys vector with keys for all values registered with the methods above.
		static void registeredValues( IECore::InternedString target, std::vector<IECore::InternedString> &keys );
		/// Retrieves a value, returning NULL if none exists.
		template<typename T>
		static typename T::ConstPtr value( IECore::InternedString target, IECore::InternedString key );

		/// Registers a static metadata value for the specified node type.
		static void registerNodeValue( IECore::TypeId nodeTypeId, IECore::InternedString key, IECore::ConstDataPtr value );
		/// Registers a dynamic metadata value for the specified node type. Each time the data is retrieved, the
		/// NodeValueFunction will be called to compute it.
		static void registerNodeValue( IECore::TypeId nodeTypeId, IECore::InternedString key, NodeValueFunction value );
		/// Registers a metadata value specific to a single instance - this will take precedence over any
		/// values registered above. If persistent is true, the value will be preserved across script save/load and cut/paste.
		/// \undoable
		static void registerNodeValue( Node *node, IECore::InternedString key, IECore::ConstDataPtr value, bool persistent = true );

		/// Fills the keys vector with keys for all values registered for the specified node. If instanceOnly is true,
		/// then only the values registered for that exact instance are returned. If persistentOnly is true, then
		/// non-persistent instance values are ignored.
		static void registeredNodeValues( const Node *node, std::vector<IECore::InternedString> &keys, bool inherit = true, bool instanceOnly = false, bool persistentOnly = false );

		/// Retrieves a previously registered value, returning NULL if none exists. If inherit is true
		/// then the search falls through to the base classes of the node if the node itself doesn't have a value.
		template<typename T>
		static typename T::ConstPtr nodeValue( const Node *node, IECore::InternedString key, bool inherit = true, bool instanceOnly = false );

		/// Deregisters a previously registered node value.
		static void deregisterNodeValue( IECore::TypeId nodeTypeId, IECore::InternedString key );
		/// Deregisters a previously registered node value.
		/// \undoable
		static void deregisterNodeValue( Node *node, IECore::InternedString key );

		/// Utility method calling registerNodeValue( nodeTypeId, "description", description ).
		static void registerNodeDescription( IECore::TypeId nodeTypeId, const std::string &description );
		static void registerNodeDescription( IECore::TypeId nodeTypeId, NodeValueFunction description );
		/// Utility method calling nodeValue( node, "description", inherit );
		static std::string nodeDescription( const Node *node, bool inherit = true );

		/// Lists all node descendants of "root" with the specified metadata key. If inherit is true
		/// then the search falls through to the base classes of the node if the node itself doesn't have a value,
		/// and if instanceOnly is true the search is restricted to instance metadata.
		static std::vector<Node*> nodesWithMetadata( GraphComponent *root, IECore::InternedString key, bool inherit = true, bool instanceOnly = false );

		/// Registers a static metadata value for plugs with the specified path on the specified node type.
		static void registerPlugValue( IECore::TypeId nodeTypeId, const MatchPattern &plugPath, IECore::InternedString key, IECore::ConstDataPtr value );
		/// Registers a dynamic metadata value for the specified plug. Each time the data is retrieved, the
		/// PlugValueFunction will be called to compute it.
		static void registerPlugValue( IECore::TypeId nodeTypeId, const MatchPattern &plugPath, IECore::InternedString key, PlugValueFunction value );
		/// Registers a metadata value specific to a single instance - this will take precedence over any
		/// values registered above. If persistent is true, the value will be preserved across script
		/// save/load and cut/paste.
		/// \undoable
		static void registerPlugValue( Plug *plug, IECore::InternedString key, IECore::ConstDataPtr value, bool persistent = true );

		/// Fills the keys vector with keys for all values registered for the specified plug. If instanceOnly is true,
		/// then only the values registered for that exact instance are returned. If persistentOnly is true, then
		/// non-persistent instance values are ignored.
		static void registeredPlugValues( const Plug *plug, std::vector<IECore::InternedString> &keys, bool inherit = true, bool instanceOnly = false, bool persistentOnly = false );

		/// Retrieves a previously registered value, returning NULL if none exists. If inherit is true
		/// then the search falls through to the base classes of the node if the node itself doesn't have a value.
		template<typename T>
		static typename T::ConstPtr plugValue( const Plug *plug, IECore::InternedString key, bool inherit = true, bool instanceOnly = false );

		/// Deregisters a previously registered plug value.
		static void deregisterPlugValue( IECore::TypeId nodeTypeId, const MatchPattern &plugPath, IECore::InternedString key );
		/// Deregisters a previously registered plug value.
		/// \undoable
		static void deregisterPlugValue( Plug *plug, IECore::InternedString key );

		/// Utility function calling registerPlugValue( nodeTypeId, plugPath, "description", description )
		static void registerPlugDescription( IECore::TypeId nodeTypeId, const MatchPattern &plugPath, const std::string &description );
		static void registerPlugDescription( IECore::TypeId nodeTypeId, const MatchPattern &plugPath, PlugValueFunction description );
		/// Utility function calling plugValue( plug, "description", inherit )
		static std::string plugDescription( const Plug *plug, bool inherit = true );

		/// Lists all plug descendants of "root" with the specified metadata key. If inherit is true
		/// then the search falls through to the base classes of the node if the node itself doesn't have a value,
		/// and if instanceOnly is true the search is restricted to instance metadata.
		static std::vector<Plug*> plugsWithMetadata( GraphComponent *root, IECore::InternedString key, bool inherit = true, bool instanceOnly = false );

		/// @name Signals
		/// These are emitted when the Metadata has been changed with one
		/// of the register*() methods. If dynamic metadata is registered
		/// with a NodeValueFunction or PlugValueFunction then it is the
		/// responsibility of the registrant to manually emit the signals
		/// when necessary.
		////////////////////////////////////////////////////////////////////
		//@{
		static ValueChangedSignal &valueChangedSignal();
		static NodeValueChangedSignal &nodeValueChangedSignal();
		static PlugValueChangedSignal &plugValueChangedSignal();
		//@}

	private :

		/// Per-instance Metadata is stored as a mapping from GraphComponent * to the
		/// metadata values, and needs to be removed when the instance dies. Currently
		/// there is no callback when a RefCounted object passes away, so we must rely
		/// on the destructors for Node and Plug to call clearInstanceMetadata() for us.
		/// \todo This situation isn't particularly satisfactory - if we introduced
		/// weak pointers and destruction callbacks for RefCounted objects then we could
		/// tidy this up.
		friend class Node;
		friend class Plug;
		static void clearInstanceMetadata( const GraphComponent *graphComponent );

		static IECore::ConstDataPtr valueInternal( IECore::InternedString target, IECore::InternedString key );
		static IECore::ConstDataPtr nodeValueInternal( const Node *node, IECore::InternedString key, bool inherit, bool instanceOnly );
		static IECore::ConstDataPtr plugValueInternal( const Plug *plug, IECore::InternedString key, bool inherit, bool instanceOnly );

};

} // namespace Gaffer

#include "Gaffer/Metadata.inl"

#endif // GAFFER_METADATA_H

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

#include "IECore/InternedString.h"
#include "IECore/Data.h"

#include "Gaffer/StringAlgo.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Node )
IE_CORE_FORWARDDECLARE( Plug )

/// The Metadata class provides a registry of metadata for the different types
/// of Nodes and Plugs. This metadata assists in creating UIs and can be used to
/// generate documentation. Metadata can consist of either static values represented
/// as IECore::Data, or can be computed dynamically.
class Metadata
{

	public :

		typedef boost::signal<void ( IECore::TypeId nodeTypeId, IECore::InternedString key )> NodeValueChangedSignal;
		typedef boost::signal<void ( IECore::TypeId nodeTypeId, const MatchPattern &plugPath, IECore::InternedString key )> PlugValueChangedSignal;

		typedef boost::function<IECore::ConstDataPtr ( const Node *node )> NodeValueFunction;
		typedef boost::function<IECore::ConstDataPtr ( const Plug *plug )> PlugValueFunction;

		/// Registers a static metadata value for the specified node type.
		static void registerNodeValue( IECore::TypeId nodeTypeId, IECore::InternedString key, IECore::ConstDataPtr value );
		/// Registers a dynamic metadata value for the specified node type. Each time the data is retrieved, the
		/// NodeValueFunction will be called to compute it.
		static void registerNodeValue( IECore::TypeId nodeTypeId, IECore::InternedString key, NodeValueFunction value );
		/// Registers a metadata value specific to a single instance - this will take precedence over any
		/// values registered above. Instance values are preserved across script save/load and cut/paste.
		/// \undoable
		static void registerNodeValue( Node *node, IECore::InternedString key, IECore::ConstDataPtr value );

		/// Fills the keys vector with keys for all values registered for the specified node. If instanceOnly is true,
		/// then only the values registered for that exact instance are returned.
		static void registeredNodeValues( const Node *node, std::vector<IECore::InternedString> &keys, bool inherit = true, bool instanceOnly = false );

		/// Retrieves a previously registered value, returning NULL if none exists. If inherit is true
		/// then the search falls through to the base classes of the node if the node itself doesn't have a value.
		template<typename T>
		static typename T::ConstPtr nodeValue( const Node *node, IECore::InternedString key, bool inherit = true, bool instanceOnly = false );

		/// Utility method calling registerNodeValue( nodeTypeId, "description", description ).
		static void registerNodeDescription( IECore::TypeId nodeTypeId, const std::string &description );
		static void registerNodeDescription( IECore::TypeId nodeTypeId, NodeValueFunction description );
		/// Utility method calling nodeValue( node, "description", inherit );
		static std::string nodeDescription( const Node *node, bool inherit = true );

		/// Registers a static metadata value for plugs with the specified path on the specified node type.
		static void registerPlugValue( IECore::TypeId nodeTypeId, const MatchPattern &plugPath, IECore::InternedString key, IECore::ConstDataPtr value );
		/// Registers a dynamic metadata value for the specified plug. Each time the data is retrieved, the
		/// PlugValueFunction will be called to compute it.
		static void registerPlugValue( IECore::TypeId nodeTypeId, const MatchPattern &plugPath, IECore::InternedString key, PlugValueFunction value );
		/// Registers a metadata value specific to a single instance - this will take precedence over any
		/// values registered above. Instance values are preserved across script save/load and cut/paste.
		/// \undoable
		static void registerPlugValue( Plug *plug, IECore::InternedString key, IECore::ConstDataPtr value );

		/// Fills the keys vector with keys for all values registered for the specified plug. If instanceOnly is true,
		/// then only the values registered for that exact instance are returned.
		static void registeredPlugValues( const Plug *plug, std::vector<IECore::InternedString> &keys, bool inherit = true, bool instanceOnly = false );

		/// Retrieves a previously registered value, returning NULL if none exists. If inherit is true
		/// then the search falls through to the base classes of the node if the node itself doesn't have a value.
		template<typename T>
		static typename T::ConstPtr plugValue( const Plug *plug, IECore::InternedString key, bool inherit = true, bool instanceOnly = false );

		/// Utility function calling registerPlugValue( nodeTypeId, plugPath, "description", description )
		static void registerPlugDescription( IECore::TypeId nodeTypeId, const MatchPattern &plugPath, const std::string &description );
		static void registerPlugDescription( IECore::TypeId nodeTypeId, const MatchPattern &plugPath, PlugValueFunction description );
		/// Utility function calling plugValue( plug, "description", inherit )
		static std::string plugDescription( const Plug *plug, bool inherit = true );

		/// @name Signals
		/// These are emitted when the Metadata has been changed with one
		/// of the register*() methods. If dynamic metadata is registered
		/// with a NodeValueFunction or PlugValueFunction then it is the
		/// responsibility of the registrant to manually emit the signals
		/// when necessary.
		////////////////////////////////////////////////////////////////////
		//@{
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

		static IECore::ConstDataPtr nodeValueInternal( const Node *node, IECore::InternedString key, bool inherit, bool instanceOnly );
		static IECore::ConstDataPtr plugValueInternal( const Plug *plug, IECore::InternedString key, bool inherit, bool instanceOnly );

};

} // namespace Gaffer

#include "Gaffer/Metadata.inl"

#endif // GAFFER_METADATA_H

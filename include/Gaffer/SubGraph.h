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

#pragma once

#include "Gaffer/DependencyNode.h"

#include <filesystem>

namespace Gaffer
{

/// > Caution : This is _not_ expected to be used as a base class for
/// > custom nodes. Any Node can use an internal network without needing to
/// > inherit from SubGraph. SubGraph is only intended for use when the user
/// > will interact directly with the internal network.
class GAFFER_API SubGraph : public DependencyNode
{

	public :

		explicit SubGraph( const std::string &name=defaultName<SubGraph>() );
		~SubGraph() override;

		GAFFER_NODE_DECLARE_TYPE( Gaffer::SubGraph, SubGraphTypeId, DependencyNode );

		/// Referencing
		/// -----------
		///
		/// By default, a SubGraph's internal nodes are considered to be local,
		/// meaning that they are serialised into the same `.gfr` file as the
		/// SubGraph itself. In this state, the child nodes are user-editable.
		/// Alternatively, SubGraphs may reference child nodes stored externally
		/// in a separate `.grf` file. This allows self-contained node graphs
		/// to be published and then referenced into multiple `.gfr` files. When
		/// referencing, the child nodes are not user-editable.

		/// Exports the internal node graph as a `.grf` file, ready for referencing.
		void exportReference( const std::filesystem::path &fileName ) const;
		/// Loads a previously exported `.grf` file, replacing the internal node graph.
		void loadReference( const std::filesystem::path &fileName );

		/// Returns the referenced file. If `isReference()` is false, returns an
		/// empty path.
		const std::filesystem::path &referenceFileName() const;

		using ReferenceChangedSignal = Signals::Signal<void ( SubGraph * )>;
		/// Emitted when `referenceFileName()` changes, or when a reference
		/// is reloaded.
		ReferenceChangedSignal &referenceChangedSignal();

		/// Reference Edits
		/// ===============
		///
		/// Although child nodes can not be edited when referenced, promoted
		/// plugs can be. This allows the user to control the internal network
		/// via an interface defined when the reference was published.
		///
		/// The SubGraph node provides some - currently limited - tracking of
		//// such edits, exposing them via the following methods.

		bool hasMetadataEdit( const Plug *plug, const IECore::InternedString key ) const;
		/// Returns true if `plug` has been added as a child of a referenced plug.
		bool isChildEdit( const Plug *plug ) const;

		/// DependencyNode API
		/// ------------------

		/// Does nothing
		void affects( const Plug *input, AffectedPlugsContainer &outputs ) const override;

		/// Returns getChild<BoolPlug>( "enabled" ).
		BoolPlug *enabledPlug() override;
		const BoolPlug *enabledPlug() const override;

		/// Implemented to allow a user to define a pass-through behaviour
		/// by connecting to the `passThrough` plug of an internal BoxOut node.
		Plug *correspondingInput( const Plug *output ) override;
		const Plug *correspondingInput( const Plug *output ) const override;

	private :

		void loadReferenceInternal( const std::filesystem::path &fileName );
		bool isReferencePlug( const Plug *plug ) const;

		ReferenceChangedSignal m_referenceChangedSignal;

		class PlugEdits;
		struct ReferenceState;
		// Initialised lazily, when we first load a reference.
		std::unique_ptr<ReferenceState> m_referenceState;

};

IE_CORE_DECLAREPTR( SubGraph )

} // namespace Gaffer

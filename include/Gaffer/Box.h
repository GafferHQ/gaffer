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

#ifndef GAFFER_BOX_H
#define GAFFER_BOX_H

#include "Gaffer/DependencyNode.h"

namespace GafferBindings
{

class BoxSerialiser;

} // namespace GafferBindings

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Box )
IE_CORE_FORWARDDECLARE( Set )

/// A Box is simply a Node which is intended to hold other Nodes
/// as children.
class Box : public DependencyNode
{

	public :

		Box( const std::string &name=defaultName<Box>() );
		virtual ~Box();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::Box, BoxTypeId, DependencyNode );

		/// Returns true if it would be valid to call promotePlug( descendantPlug, asUserPlug ),
		/// and false otherwise.
		bool canPromotePlug( const Plug *descendantPlug, bool asUserPlug = true ) const;
		/// Promotes the internal descendantPlug so that it is represented
		/// as an external plug on the Box. The descendantPlug must belong
		/// to one of the nodes contained in the box.
		/// Returns the newly created plug.
		/// \undoable
		/// \note If asUserPlug is true, then the external plug will be parented
		/// under userPlug(), otherwise it will be parented directly to the Box.
		/// The asUserPlug parameter will be removed in a future version, and
		/// promoted plugs will always be parented directly under the Box -
		/// see issue #801 for further information.
		Plug *promotePlug( Plug *descendantPlug, bool asUserPlug = true );
		/// Returns true if the descendantPlug has been promoted.
		bool plugIsPromoted( const Plug *descendantPlug ) const;
		/// Unpromotes a previously promoted plug, removing the
		/// plug on the Box where possible.
		/// \undoable
		void unpromotePlug( Plug *promotedDescandantPlug );

		/// Exports the contents of the Box so that it can be referenced
		/// by a Reference node.
		void exportForReference( const std::string &fileName ) const;

		/// Creates a Box by containing a set of child nodes which
		/// were previously held by a different parent.
		/// \undoable
		static BoxPtr create( Node *parent, const Set *childNodes );

		/// Does nothing.
		virtual void affects( const Plug *input, AffectedPlugsContainer &outputs ) const;

		/// Returns getChild<BoolPlug>( "enabled" ). It is the user's
		/// responsibility to create this plug if they need it - it is
		/// not created automatically by the Box.
		virtual BoolPlug *enabledPlug();
		virtual const BoolPlug *enabledPlug() const;

		/// Implemented to allow a user to define a pass-through behaviour
		/// by wiring the box up appropriately. The input to the output
		/// plug must be connected from a node inside the Box,
		/// where that node itself has its enabled plug driven
		/// by the box's enabled plug, and the correspondingInput for the
		/// node comes from one of the inputs to the box.
		virtual Plug *correspondingInput( const Plug *output );
		virtual const Plug *correspondingInput( const Plug *output ) const;

	private :

		bool validatePromotability( const Plug *descendantPlug, bool asUserPlug, bool throwExceptions, bool childPlug = false ) const;

};

typedef FilteredChildIterator<TypePredicate<Box> > BoxIterator;
typedef FilteredRecursiveChildIterator<TypePredicate<Box> > RecursiveBoxIterator;

} // namespace Gaffer

#endif // GAFFER_BOX_H

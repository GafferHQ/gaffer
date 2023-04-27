//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/SubGraph.h"

#include <filesystem>

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Box )
IE_CORE_FORWARDDECLARE( Set )

/// A Box is simply a Node which is intended to hold other Nodes
/// as children.
class GAFFER_API Box : public SubGraph
{

	public :

		explicit Box( const std::string &name=defaultName<Box>() );
		~Box() override;

		GAFFER_NODE_DECLARE_TYPE( Gaffer::Box, BoxTypeId, SubGraph );

		/// \deprecated Use PlugAlgo::canPromote() instead.
		bool canPromotePlug( const Plug *descendantPlug ) const;
		/// \deprecated Use PlugAlgo::promote() instead.
		Plug *promotePlug( Plug *descendantPlug );
		/// \deprecated Use PlugAlgo::isPromoted() instead.
		bool plugIsPromoted( const Plug *descendantPlug ) const;
		/// \deprecated Use PlugAlgo::unpromote() instead.
		void unpromotePlug( Plug *promotedDescendantPlug );

		/// Exports the contents of the Box so that it can be referenced
		/// by a Reference node.
		void exportForReference( const std::filesystem::path &fileName ) const;

		/// Creates a Box by containing a set of child nodes which
		/// were previously held by a different parent.
		/// \undoable
		static BoxPtr create( Node *parent, const Set *childNodes );

};

/// \deprecated Use Box::Iterator etc instead.
using BoxIterator = FilteredChildIterator<TypePredicate<Box> >;
using RecursiveBoxIterator = FilteredRecursiveChildIterator<TypePredicate<Box> >;

} // namespace Gaffer

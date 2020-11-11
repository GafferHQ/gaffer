//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

#ifndef GAFFERUI_INDIVIDUALCONTAINER_H
#define GAFFERUI_INDIVIDUALCONTAINER_H

#include "GafferUI/ContainerGadget.h"

namespace GafferUI
{

/// The IndividualContainer class allows a single child to be held,
/// and rejects efforts to add any more.
class GAFFERUI_API IndividualContainer : public ContainerGadget
{

	public :

		IndividualContainer( GadgetPtr child=nullptr );
		~IndividualContainer() override;

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferUI::IndividualContainer, IndividualContainerTypeId, ContainerGadget );

		/// Accepts the child only if there are currently no children.
		bool acceptsChild( const Gaffer::GraphComponent *potentialChild ) const override;

		/// Removes the current child if there is one, and replaces it
		/// with the specified gadget.
		void setChild( GadgetPtr child );
		/// Returns the child, performing a runTimeCast to T.
		template<typename T=Gadget>
		T *getChild();
		/// Returns the child, performing a runTimeCast to T.
		template<typename T=Gadget>
		const T *getChild() const;

};

IE_CORE_DECLAREPTR( IndividualContainer );

[[deprecated("Use `IndividualContainer::Iterator` instead")]]
typedef Gaffer::FilteredChildIterator<Gaffer::TypePredicate<IndividualContainer> > IndividualContainerIterator;
[[deprecated("Use `IndividualContainer::RecursiveIterator` instead")]]
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::TypePredicate<IndividualContainer> > RecursiveIndividualContainerIterator;

} // namespace GafferUI

#include "GafferUI/IndividualContainer.inl"

#endif // GAFFERUI_INDIVIDUALCONTAINER_H
